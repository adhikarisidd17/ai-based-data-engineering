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


def run_sqlfluff_fix(sql_content: str, filename: str) -> str:
    """
    Runs sqlfluff fix on SQL content; returns the fixed SQL or raises on error.
    """
    proc = subprocess.run([
        "sqlfluff", "fix", "-",
        "--dialect", "bigquery",
        "--stdin-filename", filename
    ], input=sql_content.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"SQLFluff fix failed for {filename}: {proc.stderr.decode()}")
    return proc.stdout.decode()


def generate_updated_content(original: str, prompt: str, file_type: str, target_path: str) -> str:
    """
    Uses the LLM to generate full updated content of a file.
    For SQL files, applies sqlfluff fix to ensure lint-compliance.

    Args:
      original: The original file content
      prompt: The user request
      file_type: The file extension (e.g. 'sql', 'yml')
      target_path: The repository path (used as filename for linting)
    Returns:
      The updated file content as a string.
    """
    system_message = (
        "You are a coding assistant. "
        "Do not wrap your output in triple backticks. "
        "Do not add any additional text or explanations. "
        f"The user request: '{prompt}'.\n"
        f"Here is the original {file_type} content. Provide the full updated content only."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": original}
        ],
        temperature=0
    )
    updated = response.choices[0].message.content.strip()
    # If SQL, run lint fix
    if file_type.lower() == 'sql':
        try:
            updated = run_sqlfluff_fix(updated, target_path)
        except RuntimeError as e:
            # If fix fails due to unfixable violations, skip auto-fix and proceed with original LLM output
            print(f"Warning: SQLFluff fix skipped for {target_path}: {e}")
    return updated


def generate_summary(prompt: str) -> str:
    """
    Creates a concise PR title (<=60 chars) summarizing the prompt.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a helpful assistant that writes concise PR titles "
                "(max 60 characters) summarizing user requests."
            )},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=20
    )
    title = response.choices[0].message.content.strip().strip('"')
    return title or f"Update files"


def create_pr_for_prompt(analyst_prompt: str) -> str:
    """
    Workflow:
      1. Extract file names from prompt
      2. Locate their actual paths in the repo
      3. Create a new feature branch
      4. For each file, fetch, regenerate, and update content
      5. Open a PR with a summary title
    """
    # 1. Extract filenames
    file_names = re.findall(
        r"\b[\w\/\-\.]+\.(?:sql|yml|yaml|md|py|json|csv)\b",
        analyst_prompt,
        flags=re.IGNORECASE
    )
    if not file_names:
        raise ValueError("No target files found in prompt; include file paths/extensions.")

    # 2. Resolve to actual repo paths
    file_paths = []
    for fname in file_names:
        basename = os.path.basename(fname)
        candidates = [p for p in find_repo_file_paths(basename) if p.lower().endswith(fname.lower())]
        if not candidates:
            raise FileNotFoundError(f"File '{fname}' not found in repository")
        file_paths.append(candidates[0])

    # 3. Create feature branch
    main_ref = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
    branch_name = f"api/{uuid.uuid4().hex[:6]}"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    # 4. Update each file
    updated_paths = []
    for repo_path in file_paths:
        content_file = repo.get_contents(repo_path, ref=DEFAULT_BRANCH)
        original = content_file.decoded_content.decode()
        ext = os.path.splitext(repo_path)[1].lstrip('.')
        updated = generate_updated_content(original, analyst_prompt, ext, repo_path)
        repo.update_file(
            path=repo_path,
            message=f"chore: update {repo_path} per request",
            content=updated,
            sha=content_file.sha,
            branch=branch_name
        )
        updated_paths.append(repo_path)

    # 5. Create Pull Request
    pr_title = generate_summary(analyst_prompt)
    pr = repo.create_pull(
        title=pr_title,
        body=(f"Automated changes to {updated_paths} per request:\n> {analyst_prompt}"),
        head=branch_name,
        base=DEFAULT_BRANCH
    )
    return pr.html_url