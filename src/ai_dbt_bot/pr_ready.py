import os
import sys
from github import Github
from github.GithubException import GithubException

# ——— Configuration ———
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Make sure this env var is set
OWNER        = "adhikarisidd17"
REPO         = "ai-based-data-engineering"
PR_NUMBER     = 39  # the PR number you want to mark ready

# ——— Authenticate via PyGithub ———
if not GITHUB_TOKEN:
    sys.exit("❌ Please set the GITHUB_TOKEN environment variable with repo scope.")

gh = Github(GITHUB_TOKEN)

# ——— 1. Authenticate and fetch the PR ———
try:
    repo = gh.get_repo(f"{OWNER}/{REPO}")
    pr   = repo.get_pull(PR_NUMBER)
    if not pr.draft:
        print(f"ℹ️ PR #{PR_NUMBER} is already ready for review.")
        sys.exit(0)
except GithubException as e:
    sys.exit(f"🚨 GitHub error while fetching PR: {e.status} – {e.data}")

# ——— 2. Mark the PR as ready for review ———
try:
    pr.edit(draft=False)
    print(f"✅ PR #{PR_NUMBER} is now ready for review!")
except GithubException as e:
    print("⚠️ Failed to mark PR ready for review:", e)