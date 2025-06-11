from github import Github
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME   = os.getenv("GITHUB_REPO")  # e.g. "org/ai-dbt-bot"

def open_pr(branch: str, title: str, body: str) -> str:
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(REPO_NAME)
    pr = repo.create_pull(
        title=title,
        body=body,
        head=branch,
        base="main"
    )
    return pr.html_url
