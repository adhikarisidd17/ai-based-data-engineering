import os
import re
import uuid
from dotenv import load_dotenv
from github import Github
import openai
load_dotenv()
# Load environment\ nload_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure GitHub Credentials
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME   = os.getenv("GITHUB_REPO")
if not GITHUB_TOKEN or not REPO_NAME:
    raise EnvironmentError("GITHUB_TOKEN and GITHUB_REPO must be set in environment")

# Initialize GitHub client and get repo
gh = Github(GITHUB_TOKEN, verify=False)
repo = gh.get_repo(REPO_NAME)
# Determine default branch dynamically
DEFAULT_BRANCH = repo.default_branch


def find_repo_file_paths(suffix: str) -> list:
    """
    Returns a list of file paths in the repo tree ending with the given suffix.
    Uses the default branch.
    """
    tree = repo.get_git_tree(DEFAULT_BRANCH, recursive=True).tree
    return [item.path for item in tree if item.path.lower().endswith(suffix.lower())]


def extract_model_name(prompt: str) -> str:
    """
    Determines the target dbt model name based on the analyst prompt.
    Strategy:
      1. Check for backtick-wrapped names: `model_name`
      2. Check for any existing model filenames appearing in prompt text
      3. Regex fallback for 'in MODEL' or 'on MODEL'
    """
    # 1. backticks
    names = re.findall(r"`([^`]+)`", prompt)
    if names:
        return names[0]

    # 2. scan available models
    sql_files = find_repo_file_paths('.sql')
    models = [os.path.splitext(os.path.basename(p))[0] for p in sql_files]
    lower_prompt = prompt.lower()
    for m in models:
        if m.lower() in lower_prompt:
            return m

    # 3. fallback regex
    m = re.search(r"(?:in|on|for|to)\s+(\w+)", prompt, re.IGNORECASE)
    if m:
        return m.group(1)

    raise ValueError("Could not determine model name from prompt; please include the model name explicitly.")


def generate_updated_content(original: str, prompt: str, file_type: str) -> str:
    """
    Uses LLM to return full updated file content for SQL or YAML.
    """
    sys_msg = (
        f"You are a dbt expert. "
        "Don't add ``` lines before start and end of the models since they are .sql files. "
        f"The user requests: '{prompt}'.\n"
        f"Below is the original {file_type} file. Return the entire updated {file_type} content, applying only needed changes."
    )
    user_msg = f"```\n{original}\n```"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user",   "content": user_msg}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def generate_summary(prompt: str) -> str:
    """
    Uses LLM to generate a concise PR title (max 60 chars) summarizing the prompt.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a helpful assistant that creates concise PR titles "
                "(no more than 60 characters) summarizing the user's request."
            )},
            {"role": "user",   "content": prompt}
        ],
        temperature=0,
        max_tokens=20
    )
    title = response.choices[0].message.content.strip().strip('"')
    return title

def create_pr_for_prompt(analyst_prompt: str) -> str:
    """
    1. Determine model name
    2. Locate SQL/YML files dynamically
    3. Create branch off default branch
    4. Update files via LLM and GitHub API
    5. Open PR
    """
    # 1. Model name
    model = extract_model_name(analyst_prompt)

    # 2a. Locate SQL file
    sql_candidates = find_repo_file_paths(f"{model}.sql")
    if not sql_candidates:
        raise FileNotFoundError(f"Model SQL file for '{model}' not found in repo")
    sql_path = sql_candidates[0]

    # 2b. Locate YML file; prefer per-model, else fallback to models/schema.yml
    yml_candidates = find_repo_file_paths(f"{model}.yml")
    if yml_candidates:
        yml_path = yml_candidates[0]
    else:
        fallback = [p for p in find_repo_file_paths(".yml") if p.startswith("models/")]
        if not fallback:
            raise FileNotFoundError("No YAML schema file found under models/")
        yml_path = "models/schema.yml" if "models/schema.yml" in fallback else fallback[0]

    # 3. Create branch
    main_ref = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
    branch_name = f"api/{model}-{uuid.uuid4().hex[:6]}"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    # 4a. Update SQL content
    sql_file = repo.get_contents(sql_path, ref=DEFAULT_BRANCH)
    original_sql = sql_file.decoded_content.decode()
    updated_sql = generate_updated_content(original_sql, analyst_prompt, "sql")
    repo.update_file(sql_path,
                     message=f"feat({model}): {analyst_prompt}",
                     content=updated_sql,
                     sha=sql_file.sha,
                     branch=branch_name)

    # 4b. Update YML content
    yml_file = repo.get_contents(yml_path, ref=DEFAULT_BRANCH)
    original_yml = yml_file.decoded_content.decode()
    updated_yml = generate_updated_content(original_yml, analyst_prompt, "yml")
    repo.update_file(yml_path,
                     message=f"docs({model}): schema per request",
                     content=updated_yml,
                     sha=yml_file.sha,
                     branch=branch_name)

    # 5. Summary title and PR
    pr_title = generate_summary(analyst_prompt)
    if not pr_title:
        pr_title = f"Update {model} model"
    pr = repo.create_pull(
        title=pr_title,
        body=f"Automated change for model `{model}` per request:\n> {analyst_prompt}",
        head=branch_name,
        base=DEFAULT_BRANCH
    )
    return pr.html_url