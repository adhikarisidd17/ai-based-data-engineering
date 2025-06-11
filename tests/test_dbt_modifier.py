# tests/test_dbt_modifier.py
from pathlib import Path
from ai_dbt_bot.dbt_modifier import apply_patch

def test_apply_simple_patch(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file.sql").write_text("SELECT 1;\n")
    patch = (
        "diff --git a/file.sql b/file.sql\n"
        "index e69de29..4b825dc 100644\n"
        "--- a/file.sql\n"
        "+++ b/file.sql\n"
        "@@ -1 +1,2 @@\n"
        " SELECT 1;\n"
        "+SELECT 2;\n"
    )
    success, _ = apply_patch(repo, patch)
    assert success
    assert "SELECT 2" in (repo / "file.sql").read_text()
