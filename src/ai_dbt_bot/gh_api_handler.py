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
    with open(os.path.join(os.path.dirname(__file__), "system_message.txt"), "r", encoding="utf-8") as f:
        static_message = f.read().strip()
    system_message = (
        f"{static_message} User request: '{prompt}'. Provide the full updated content of this file."
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


def create_or_update_pr(session_id: str, analyst_prompt: str, file_names    : list[str] | None = None) -> str:
    sid = session_id or str(uuid.uuid4())
    pr = None
    branch_name = None

    # Load or create session
    if sid in session_pr_map:
        info = session_pr_map[sid]
        branch_name = info['branch']
        pr = repo.get_pull(info['pr_number'])
        original_prompt = info['prompt']
        # Confirmation
        if analyst_prompt.strip().lower() in CONFIRM_KEYWORDS:
            clean = re.sub(r'[^\w\s]', '', analyst_prompt).strip().lower()
            if clean in CONFIRM_KEYWORDS:
                new_title = generate_summary(original_prompt) or pr.title
                pr.edit(title=new_title)
                ready_url = mark_pr_ready(pr)
                session_pr_map.pop(sid)
                return f"PR #{pr.number} marked ready: {ready_url}"
    else:
        branch_name = f"api/{uuid.uuid4().hex[:6]}"
        main_ref    = repo.get_git_ref(f"heads/{DEFAULT_BRANCH}")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    # If the caller gave us explicit filenames, use those; otherwise fall back to regex
    if file_names:
        file_names = [os.path.basename(f) for f in file_names]
    else:
        raw_files = re.findall(
            r"\b[\w/\-\.]\.(?:sql|yml|yaml|md|py|json|csv)\b",
            analyst_prompt,
            flags=re.IGNORECASE
        )
        file_names = [os.path.basename(f) for f in raw_files]
    if not file_names:
        raise ValueError("No target files found; include file names with extensions.")

    # Available files under models/
    sql_pool = [p for p in find_repo_file_paths('.sql') if p.startswith('models/')]
    yml_pool = [p for p in find_repo_file_paths('.yml')] + [p for p in find_repo_file_paths('.yaml')]
    yml_pool = [p for p in yml_pool if p.startswith('models/')]

    # Update each file
    for base in file_names:
        stem, ext = os.path.splitext(base)
        pool = sql_pool if ext.lower()=='.sql' else yml_pool
        # exact match
        candidates = [p for p in pool if os.path.basename(p).lower()==base.lower()]
        # suffix match
        if not candidates:
            candidates = [p for p in pool if p.lower().endswith('/'+base.lower())]
        # fuzzy match
        if not candidates:
            stems = [os.path.splitext(os.path.basename(p))[0] for p in pool]
            match = difflib.get_close_matches(stem, stems, n=1)
            if match:
                candidates = [pool[stems.index(match[0])]]
        if not candidates:
            raise FileNotFoundError(f"File '{base}' not found in models/ or via fuzzy match.")
        path = candidates[0]

        content_file = repo.get_contents(path, ref=branch_name)
        original     = content_file.decoded_content.decode()
        updated      = generate_updated_content(original, analyst_prompt, ext.lstrip('.'), path)
        repo.update_file(
            path=path,
            message=f"chore: update {path} per request",
            content=updated,
            sha=content_file.sha,
            branch=branch_name
        )

    # Create draft PR if first commit
    if pr is None:
        pr = repo.create_pull(
            title="(Draft) Pending changes…",
            body ="Draft PR; reply 'confirm' to finalize.",
            head =branch_name,
            base =DEFAULT_BRANCH,
            draft=True
        )
        session_pr_map[sid] = {'branch':branch_name,'pr_number':pr.number,'prompt':analyst_prompt}
        return f"Draft PR created: {pr.html_url} (session_id={sid})"

    return f"Draft PR updated: {pr.html_url} (session_id={sid})"