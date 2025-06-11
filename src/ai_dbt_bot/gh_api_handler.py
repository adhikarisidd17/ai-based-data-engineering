# New file: src/ai_dbt_bot/gh_api_handler.py
import os
import re
import uuid
from github import Github

# Read from environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")  # e.g. "org/ai-based-data-engineering"


def create_pr_via_github_api(analyst_prompt: str) -> str:
    """
    1. Create a new branch off main
    2. Fetch and update two files via GitHub Contents API
    3. Open a PR with those changes
    """
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(REPO_NAME)

    # 1. Create new branch
    main_ref = repo.get_git_ref("heads/main")
    new_branch = f"api/{uuid.uuid4().hex[:8]}"
    repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=main_ref.object.sha)

    # 2a. Update SQL model
    sql_path = "models/d_customers.sql"
    sql_file = repo.get_contents(sql_path, ref="main")
    sql_content = sql_file.decoded_content.decode()
    updated_sql = re.sub(
        r"(years,\s*\n)",
        r"\1    SUM(revenue) / COUNT(years) AS total_lifetime,\n",
        sql_content
    )
    repo.update_file(
        path=sql_path,
        message=f"feat: {analyst_prompt}",
        content=updated_sql,
        sha=sql_file.sha,
        branch=new_branch
    )

    # 2b. Update schema YAML
    yml_path = "models/schema.yml"
    yml_file = repo.get_contents(yml_path, ref="main")
    yml_content = yml_file.decoded_content.decode()
    updated_yml = re.sub(
        r"(name: years[^\n]*\n\s*description:.*\n)",
        r"\1      - name: total_lifetime\n        description: \"Total lifetime value of the customer calculated as sum(revenue) / count(years).\"\n",
        yml_content
    )
    repo.update_file(
        path=yml_path,
        message=f"feat: {analyst_prompt}",
        content=updated_yml,
        sha=yml_file.sha,
        branch=new_branch
    )

    # 3. Open pull request
    pr = repo.create_pull(
        title=f"Automated PR: {analyst_prompt[:50]}…",
        body=f"Automated change per analyst request:\n\n> {analyst_prompt}",
        head=new_branch,
        base="main"
    )
    return pr.html_url