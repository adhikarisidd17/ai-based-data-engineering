import os
import re
import uuid
import subprocess
from dotenv import load_dotenv
from github import Github
import openai

load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")
if not GITHUB_TOKEN or not REPO_NAME:
    raise EnvironmentError("GITHUB_TOKEN and GITHUB_REPO must be set in environment")

# Initialize GitHub client
gh = Github(GITHUB_TOKEN, verify=False)
repo = gh.get_repo(REPO_NAME)
DEFAULT_BRANCH = repo.default_branch

# In-memory mapping of user sessions to PR branches
# In real system, persist this mapping to a database
session_pr_map = {}


def find_repo_file_paths(suffix: str) -> list:
    tree = repo.get_git_tree(DEFAULT_BRANCH, recursive=True).tree
    return [item.path for item in tree if item.path.lower().endswith(suffix.lower())]


def run_sqlfluff_fix(sql_content: str, filename: str) -> str:
    proc = subprocess.run([
        "sqlfluff", "fix", "-",
        "--dialect", "bigquery",
        "--stdin-filename", filename
    ], input=sql_content.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        print(f"Warning: SQLFluff fix skipped for {filename}: {proc.stderr.decode()}")
        return sql_content
    return proc.stdout.decode()


def generate_updated_content(original: str, prompt: str, file_type: str, target_path: str) -> str:
    sys_msg = (
        "You are a coding assistant. Do not use triple backticks. Do not add any additional text or explanations. "
        f"The user requests modifications: '{prompt}'. Provide full updated content."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": original}
        ],
        temperature=0
    )
    updated = response.choices[0].message.content.strip()
    if file_type.lower() == 'sql':
        updated = run_sqlfluff_fix(updated, target_path)
    return updated


def create_or_update_pr(session_id: str, analyst_prompt: str) -> str:
    # Determine branch and PR
    if session_id in session_pr_map:
        branch_name, pr_number = session_pr_map[session_id]
        pr = repo.get_pull(pr_number)
        updating = True
    else:
        # new draft PR
        branch_name = f"api/{uuid.uuid4().hex[:6]}"
        main_ref = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)
        pr = repo.create_pull(
            title="(Draft) Pending changes...",
            body="Draft PR for model edits. Respond with further changes or 'confirm' to finalize.",
            head=branch_name,
            base=DEFAULT_BRANCH,
            draft=True
        )
        pr_number = pr.number
        session_pr_map[session_id] = (branch_name, pr_number)
        updating = False

    # Extract file paths
    file_names = re.findall(r"\b[\w\/\-\.]+\.(?:sql|yml|yaml|md|py|json|csv)\b", analyst_prompt)
    if not file_names:
        raise ValueError("No target files found in prompt.")
    file_paths = []
    for fname in file_names:
        matches = [p for p in find_repo_file_paths(os.path.basename(fname)) if p.lower().endswith(fname.lower())]
        if not matches:
            raise FileNotFoundError(f"File '{fname}' not found")
        file_paths.append(matches[0])

    # Apply edits
    for path in file_paths:
        content_file = repo.get_contents(path, ref=branch_name)
        original = content_file.decoded_content.decode()
        ext = os.path.splitext(path)[1].lstrip('.')
        updated = generate_updated_content(original, analyst_prompt, ext, path)
        repo.update_file(path, f"update {path}", updated, content_file.sha, branch=branch_name)

    # If user confirms, mark PR ready
    if analyst_prompt.strip().lower() in ['confirm', 'ready', 'approve', 'looks good']:
        pr.update(draft=False, title=generate_summary(analyst_prompt) or pr.title)
        session_pr_map.pop(session_id, None)
        return f"PR #{pr.number} is marked ready: {pr.html_url}"

    return f"Draft PR updated: {pr.html_url}"