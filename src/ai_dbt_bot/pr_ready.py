import os
import sys
from github import Github
from github.GithubException import GithubException
import requests

# ——— Configuration ———
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Make sure this env var is set
OWNER        = "adhikarisidd17"
REPO         = "ai-based-data-engineering"
PR_NUMBER  = 39  # the PR number you want to mark ready

# ——— Authenticate via PyGithub ———
if not GITHUB_TOKEN:
    sys.exit("❌ Please set the GITHUB_TOKEN environment variable with repo scope.")

gh = Github(GITHUB_TOKEN,verify=False)

# ——— Authenticate ———
if not GITHUB_TOKEN:
    sys.exit("❌ Please set the GITHUB_TOKEN environment variable.")

gh = Github(GITHUB_TOKEN)

# ——— 1. Authenticate and fetch the PR node ID ———
try:
    gh   = Github(GITHUB_TOKEN)
    repo = gh.get_repo(f"{OWNER}/{REPO}")
    pr   = repo.get_pull(PR_NUMBER)
    if not pr.draft:
        print(f"ℹ️ PR #{PR_NUMBER} is already ready for review.")
        sys.exit(0)
    pr_node_id = pr.node_id
except GithubException as e:
    sys.exit(f"🚨 GitHub error while fetching PR: {e.status} – {e.data}")

# ——— 2. Prepare and send the GraphQL mutation ———
mutation = """
mutation($prId: ID!) {
  markPullRequestReadyForReview(input: { pullRequestId: $prId }) {
    pullRequest {
      number
      isDraft
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}"
}

payload = {
    "query":     mutation,
    "variables": {"prId": pr_node_id}
}

resp = requests.post("https://api.github.com/graphql", json=payload, headers=headers)

# Handle HTTP errors
try:
    resp.raise_for_status()
except requests.HTTPError as e:
    print("🚨 HTTP error:", e, resp.text)
    sys.exit(1)

result = resp.json()

# Handle GraphQL errors
if "errors" in result:
    print("🚨 GraphQL errors:")
    for err in result["errors"]:
        print(" •", err.get("message"))
    sys.exit(1)

# Ensure we have the expected payload
payload = result.get("data", {}).get("markPullRequestReadyForReview")
if not payload or "pullRequest" not in payload:
    print("🚨 Unexpected response shape:", result)
    sys.exit(1)

pr_data = payload["pullRequest"]

# ——— 3. Check the result ———
if pr_data.get("isDraft") is False:
    print(f"✅ PR #{pr_data['number']} is now ready for review!")
else:
    print("⚠️ Failed to mark PR ready for review:", pr_data)