import os
import re
import uuid
import subprocess
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

# In-memory map of session_id to details
session_pr_map = {}
dession_pr_map = {}
# Confirmation keywords
CONFIRM_KEYWORDS = {"confirm", "ready", "approve", "looks good"}


def find_repo_file_paths(suffix: str) -> list:
    """
    Returns all repository file paths ending with the given suffix.
    """
    tree = repo.get_git_tree(DEFAULT_BRANCH, recursive=True).tree
    return [item.path for item in tree if item.path.lower().endswith(suffix.lower())]


def run_sqlfluff_fix(sql_content: str, filename: str) -> str:
    """
    Runs sqlfluff fix on the provided SQL content and returns the fixed SQL.
    If fix fails, returns the original content.
    """
    proc = subprocess.run(
        ["sqlfluff", "fix", "-", "--dialect", "bigquery", "--stdin-filename", filename],
        input=sql_content.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        print(f"Warning: SQLFluff fix skipped for {filename}: {proc.stderr.decode()}")
        return sql_content
    return proc.stdout.decode()


def generate_updated_content(original: str, prompt: str, file_type: str, target_path: str) -> str:
    """
    Uses the LLM to generate the full updated file content based on the prompt.
    For SQL files, applies sqlfluff fix to the result.
    """
    system_message = (
        "You are a coding assistant. Do not wrap your output in triple backticks. "
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
    """
    Generates a concise PR title (≤60 characters) summarizing the prompt.
    """
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


import requests

def mark_pr_ready(pr) -> str:
    """
    Uses GitHub GraphQL API to mark a draft pull request ready for review.
    Returns the PR URL.
    """
    token = GITHUB_TOKEN
    # 1. Fetch node ID
    pr_node_id = pr.node_id
    # 2. GraphQL mutation
    mutation = '''
    mutation($prId: ID!) {
      markPullRequestReadyForReview(input: { pullRequestId: $prId }) {
        pullRequest { number, isDraft, url }
      }
    }
    '''
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"query": mutation, "variables": {"prId": pr_node_id}}
    resp = requests.post("https://api.github.com/graphql", json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        msgs = "; ".join(err.get("message","") for err in data["errors"])
        raise RuntimeError(f"GraphQL error marking PR ready: {msgs}")
    pr_data = data.get("data", {}).get("markPullRequestReadyForReview", {}).get("pullRequest")
    if not pr_data or pr_data.get("isDraft"):
        raise RuntimeError(f"Failed to mark PR ready; response: {data}")
    return pr_data.get("url")


def create_or_update_pr(session_id: str, analyst_prompt: str) -> str:
    """
    Creates or updates a draft PR for iterative changes.
    - New session: creates branch, commits edits, then opens draft PR.
    - Existing session: commits edits or finalizes on confirmation.
    """
    sid = session_id or str(uuid.uuid4())
    pr = None
    branch_name = None

    # Confirmation for existing draft
    if sid in session_pr_map:
        data = session_pr_map[sid]
        branch_name = data['branch']
        pr_number  = data['pr_number']
        original_prompt = data['prompt']
        pr = repo.get_pull(pr_number)
        if analyst_prompt.strip().lower() in CONFIRM_KEYWORDS:
            new_title = generate_summary(original_prompt) or pr.title
            pr.edit(title=new_title)
            ready_url = mark_pr_ready(pr)
            session_pr_map.pop(sid)
            return f"PR #{pr.number} is ready for review: {ready_url}"
    else:
        branch_name = f"api/{uuid.uuid4().hex[:6]}"
        main_ref = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    file_names = re.findall(
        r"\b[\w/\-.]+\.(?:sql|yml|yaml|md|py|json|csv)\b",
        analyst_prompt,
        flags=re.IGNORECASE
    )
    if not file_names:
        raise ValueError("No target files found; include file names with extensions.")

    file_paths = []
    for fname in file_names:
        base = os.path.basename(fname)
        candidates = [p for p in find_repo_file_paths(base) if p.lower().endswith(fname.lower())]
        if not candidates:
            raise FileNotFoundError(f"File '{fname}' not found in repository")
        file_paths.append(candidates[0])

    for path in file_paths:
        ref = DEFAULT_BRANCH if pr is None else branch_name
        content = repo.get_contents(path, ref=ref)
        original = content.decoded_content.decode()
        ext = os.path.splitext(path)[1].lstrip('.')
        updated = generate_updated_content(original, analyst_prompt, ext, path)
        repo.update_file(
            path=path,
            message=f"chore: update {path} per request",
            content=updated,
            sha=content.sha,
            branch=branch_name
        )

    if pr is None:
        pr = repo.create_pull(
            title="(Draft) Pending changes…",
            body="Draft PR for iterative edits. Reply with changes or 'confirm' to finalize.",
            head=branch_name,
            base=DEFAULT_BRANCH,
            draft=True
        )
        session_pr_map[sid] = {'branch': branch_name, 'pr_number': pr.number, 'prompt': analyst_prompt}
        return f"Draft PR created: {pr.html_url} (session_id={sid})"

    return f"Draft PR updated: {pr.html_url} (session_id={sid})"