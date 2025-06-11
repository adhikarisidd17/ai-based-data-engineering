# tests/test_llm_engine.py
import re
from ai_dbt_bot.llm_engine import generate_dbt_patch

def test_patch_format():
    # For simplicity, we simulate by monkeypatching openai.ChatCompletion
    patch = generate_dbt_patch("Add foo")
    assert "diff --git" in patch
    assert re.search(r"\+.*foo", patch)
