import os
import re
import uuid
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


def extract_file_paths(prompt: str) -> list:
    """
    Extracts candidate file names with extensions from the prompt.
    E.g. specs: ['models/d_customers.sql', 'models/schema.yml', 'README.md']
    """
    # regex for words ending in common extensions
    exts = ['sql', 'yml', 'yaml', 'md', 'py', 'json', 'csv']
    pattern = r"\b[\w\/\-\.]+\.({})\b".format("|".join(exts))
    return re.findall(pattern, prompt, flags=re.IGNORECASE) and re.findall(pattern, prompt, flags=re.IGNORECASE)


def generate_updated_content(original: str, prompt: str, file_type: str) -> str:
    """
    Uses LLM to return full updated file content for any file type.
    Instructs LLM not to wrap with triple backticks.
    """
    sys_msg = (
        "You are a coding assistant. "
        "Don't add ``` lines before start and end of the file. "
        f"The user requests to modify this {file_type} file as follows: '{prompt}'.\n"
        f"Here is the original content:"
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
    return resp.choices[0].message.content.strip()


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
    2. Locate paths in repo
    3. Create feature branch off default
    4. For each file, fetch original, regenerate content via LLM, update via API
    5. Create PR with a summary title
    """
    # 1. Extract file names
    file_names = re.findall(r"\b[\w\/\-\.]+\.(?:sql|yml|yaml|md|py|json|csv)\b", analyst_prompt, flags=re.IGNORECASE)
    if not file_names:
        raise ValueError("No target file names found in prompt. Include file paths/extensions explicitly.")

    # 2. Locate full paths
    file_paths = []
    for fname in file_names:
        matches = [p for p in find_repo_file_paths(os.path.basename(fname)) if p.lower().endswith(fname.lower())]
        if not matches:
            raise FileNotFoundError(f"File '{fname}' not found in repo")
        # take first match
        file_paths.append(matches[0])

    # 3. Create branch
    main_ref = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
    branch_name = f"api/{uuid.uuid4().hex[:6]}"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    # 4. Update each file
    updated_paths = []
    for path in file_paths:
        content_file = repo.get_contents(path, ref=DEFAULT_BRANCH)
        original = content_file.decoded_content.decode()
        ext = os.path.splitext(path)[1].lstrip('.')
        updated = generate_updated_content(original, analyst_prompt, ext)
        repo.update_file(
            path=path,
            message=f"chore: update {path} per analyst request",
            content=updated,
            sha=content_file.sha,
            branch=branch_name
        )
        updated_paths.append(path)

    # 5. Open PR
    title = generate_summary(analyst_prompt) or f"Update files: {', '.join(updated_paths)}"
    pr = repo.create_pull(
        title=title,
        body=(f"Automated change to files {updated_paths} per request:\n> {analyst_prompt}"),
        head=branch_name,
        base=DEFAULT_BRANCH
    )
    return pr.html_url