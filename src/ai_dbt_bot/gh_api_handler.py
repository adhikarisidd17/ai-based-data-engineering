````python
# src/ai_dbt_bot/gh_api_handler.py
import os
import re
import uuid
import subprocess
from dotenv import load_dotenv
from github import Github
import openai

# Load environment
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


def find_repo_file_paths(suffix: str) -> list:
    """
    Returns file paths in the repo tree ending with the given suffix.
    """
    tree = repo.get_git_tree(DEFAULT_BRANCH, recursive=True).tree
    return [item.path for item in tree if item.path.lower().endswith(suffix.lower())]


def run_sqlfluff_fix(content: str, filename: str) -> str:
    """
    Runs sqlfluff fix on the given SQL content and returns the fixed SQL.
    """
    proc = subprocess.run([
        "sqlfluff", "fix", "-",
        "--dialect", "bigquery",
        "--stdin-filename", filename
    ], input=content.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"SQLFluff fix failed for {filename}: {proc.stderr.decode()}")
    return proc.stdout.decode()


def generate_updated_content(original: str, prompt: str, file_type: str, file_path: str) -> str:
    """
    Uses LLM to return full updated file content for any file type.
    Instructs LLM not to wrap with triple backticks.
    """
    sys_msg = (
        "You are a coding assistant. "
        "Don't add ``` lines before start and end of the file. "
        f"The user requests to modify this {file_type} file as follows: '{prompt}'.\n"
        "Here is the original content:"
    )
    user_msg = original
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=0
    )
    updated = resp.choices[0].message.content.strip()
    # Run lint fix for SQL files
    if file_type.lower() == 'sql':
        updated = run_sqlfluff_fix(updated, file_path)
    return updated


def generate_summary(prompt: str) -> str:
    """
    Generates a concise PR title (<=60 chars) summarizing the prompt.
    """
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a helpful assistant that creates concise PR titles "
                "(no more than 60 characters) summarizing the user's request."
            )},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=20
    )
    title = resp.choices[0].message.content.strip().strip('"')
    return title


def create_pr_for_prompt(analyst_prompt: str) -> str:
    """
    Generic workflow for modifying any files in the repo:
    1. Extract target file names from prompt
    2. Locate files
    3. Create feature branch
    4. LLM + lint fix updates
    5. Create PR
    """
    # 1. Extract file names
    file_names = re.findall(r"\b[\w\/\-\.]+\.(?:sql|yml|yaml|md|py|json|csv)\b", analyst_prompt, flags=re.IGNORECASE)
    if not file_names:
        raise ValueError("No target file names found in prompt. Include file paths/extensions explicitly.")

    # 2. Locate full paths
    file_paths = []
    for fname in file_names:
        basename = os.path.basename(fname)
        matches = [p for p in find_repo_file_paths(basename) if p.lower().endswith(fname.lower())]
        if not matches:
            raise FileNotFoundError(f"File '{fname}' not found in repo")
        file_paths.append(matches[0])

    # 3. Create branch
    main_ref = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
    branch_name = f"api/{uuid.uuid4().hex[:6]}"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    # 4. Update each file
    updated_paths = []
    for file_path in file_paths:
        content_file = repo.get_contents(file_path, ref=DEFAULT_BRANCH)
        original = content_file.decoded_content.decode()
        ext = os.path.splitext(file_path)[1].lstrip('.')
        updated = generate_updated_content(original, analyst_prompt, ext, file_path)
        repo.update_file(
            path=file_path,
            message=f"chore: update {file_path} per analyst request",
            content=updated,
            sha=content_file.sha,
            branch=branch_name
        )
        updated_paths.append(file_path)

    # 5. Open PR
    title = generate_summary(analyst_prompt) or f"Update files: {', '.join(updated_paths)}"
    pr = repo.create_pull(
        title=title,
        body=(f"Automated change to files {updated_paths} per request:\n> {analyst_prompt}"),
        head=branch_name,
        base=DEFAULT_BRANCH
    )
    return pr.html_url
````
