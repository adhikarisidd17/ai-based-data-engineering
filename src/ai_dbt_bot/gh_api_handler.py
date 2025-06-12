import os
import re
import uuid
import subprocess
import difflib
from dotenv import load_dotenv
from github import Github
import openai

# Load environment variables
load_dotenv()

# Configure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure GitHub credentials
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME    = os.getenv("GITHUB_REPO")
if not GITHUB_TOKEN or not REPO_NAME:
    raise EnvironmentError("GITHUB_TOKEN and GITHUB_REPO must be set in environment")

# Initialize GitHub client
gh   = Github(GITHUB_TOKEN, verify=False)
repo = gh.get_repo(REPO_NAME)
DEFAULT_BRANCH = repo.default_branch

# In-memory session map
session_pr_map = {}
# Confirmation keywords
CONFIRM_KEYWORDS = {"confirm", "ready", "approve", "looks good"}


def find_repo_file_paths(suffix: str) -> list:
    """
    Returns all repository file paths ending with the given suffix.
    """
    tree = repo.get_git_tree(DEFAULT_BRANCH, recursive=True).tree
    return [item.path for item in tree if item.path.lower().endswith(suffix.lower())]


def run_sqlfluff_fix(sql_content: str, filename: str) -> str:
    proc = subprocess.run(
        ["sqlfluff", "fix", "-", "--dialect", "bigquery", "--stdin-filename", filename],
        input=sql_content.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        print(f"Warning: SQLFluff fix skipped for {filename}: {proc.stderr.decode()}")
        return sql_content
    return proc.stdout.decode()


def generate_updated_content(original: str, prompt: str, file_type: str, target_path: str) -> str:
    system_message = (
        "You are a coding assistant. Do not wrap your output in triple backticks. "
        "Do not include any comments or explanations. "
        "Modify the provided file content based on the user's request. "
        "Ensure the output is valid code for the specified file type. "
        "If the file is SQL, consider it is dbt model code and only apply changes that are valid in dbt context. "
        "If the file is YAML, ensure it is valid YAML syntax. "
        f"User request: '{prompt}'. Provide the full updated content of this file."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user",   "content": original}
        ],
        temperature=0
    )
    updated = response.choices[0].message.content.strip()
    if file_type.lower() == 'sql':
        updated = run_sqlfluff_fix(updated, target_path)
    return updated


def generate_summary(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a helpful assistant that writes concise PR titles "
                "(max 60 chars) summarizing the request."
            )},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=20
    )
    title = response.choices[0].message.content.strip().strip('"')
    return title or "Update files"


def mark_pr_ready(pr) -> str:
    path = f"/repos/{REPO_NAME}/pulls/{pr.number}"
    payload = {"draft": False}
    headers = {"Accept": "application/vnd.github.shadow-cat-preview+json"}
    repo._requester.requestJsonAndCheck(
        "PATCH",
        path,
        input=payload,
        headers=headers
    )
    updated = repo.get_pull(pr.number)
    return updated.html_url


def create_or_update_pr(session_id: str, analyst_prompt: str) -> str:
    """
    Creates or updates a draft PR for iterative changes.
    """
    sid = session_id or str(uuid.uuid4())
    pr = None
    branch_name = None

    # Existing session?
    if sid in session_pr_map:
        data = session_pr_map[sid]
        branch_name   = data['branch']
        pr_number     = data['pr_number']
        original_prompt = data['prompt']
        pr = repo.get_pull(pr_number)
        # Confirmation step
        if analyst_prompt.strip().lower() in CONFIRM_KEYWORDS:
            # update title
            new_title = generate_summary(original_prompt) or pr.title
            pr.edit(title=new_title)
            # mark ready
            ready_url = mark_pr_ready(pr)
            session_pr_map.pop(sid)
            return f"PR #{pr.number} is ready for review: {ready_url}"
    else:
        # New draft session
        branch_name = f"api/{uuid.uuid4().hex[:6]}"
        main_ref    = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    # Extract file names
    file_names = re.findall(
        r"\b[\w/\-\.]+\.(?:sql|yml|yaml|md|py|json|csv)\b",
        analyst_prompt,
        flags=re.IGNORECASE
    )
    if not file_names:
        raise ValueError("No target files found; include file names with extensions.")

        # Get available repo SQL and YAML files
        # Get available repo SQL and YAML files under models/
    all_sql = find_repo_file_paths('.sql')
    available_sql = [p for p in all_sql if p.startswith('models/')]
    all_yml = find_repo_file_paths('.yml') + find_repo_file_paths('.yaml')
    available_yml = [p for p in all_yml if p.startswith('models/')]

    # Resolve each target filename to a repository path
    file_paths = []
    for fname in file_names:
        base = os.path.basename(fname)
        name, ext = os.path.splitext(base)
        pool = available_sql if ext.lower() == '.sql' else available_yml
        # 1) Exact basename match
        candidates = [p for p in pool if os.path.basename(p).lower() == base.lower()]
        # 2) Fallback: suffix match
        if not candidates:
            candidates = [p for p in pool if p.lower().endswith('/' + base.lower())]
        # 3) Fuzzy fallback on name
        if not candidates:
            stems = [os.path.splitext(os.path.basename(p))[0] for p in pool]
            match = difflib.get_close_matches(name, stems, n=1)
            if match:
                idx = stems.index(match[0])
                candidates = [pool[idx]]
        if not candidates:
            raise FileNotFoundError(f"File '{fname}' not found in repository or via fuzzy match.")
        file_paths.append(candidates[0])

    # Apply edits
    for path in file_paths:
        ref = DEFAULT_BRANCH if pr is None else branch_name
        content_file = repo.get_contents(path, ref=ref)
        original     = content_file.decoded_content.decode()
        ext = os.path.splitext(path)[1].lstrip('.')
        updated = generate_updated_content(original, analyst_prompt, ext, path)
        repo.update_file(
            path=path,
            message=f"chore: update {path} per request",
            content=updated,
            sha=content_file.sha,
            branch=branch_name
        )

    # Create draft PR if new
    if pr is None:
        pr = repo.create_pull(
            title="(Draft) Pending changes…",
            body ="Draft PR for iterative edits. Reply with changes or 'confirm' to finalize.",
            head =branch_name,
            base =DEFAULT_BRANCH,
            draft=True
        )
        session_pr_map[sid] = {'branch':branch_name,'pr_number':pr.number,'prompt':analyst_prompt}
        return f"Draft PR created: {pr.html_url} (session_id={sid})"

    # Update existing draft
    return f"Draft PR updated: {pr.html_url} (session_id={sid})"
