import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_dbt_patch(prompt: str) -> str:
    """
    Given an analyst prompt, ask the LLM to produce
    a unified diff patch (or SQL & YAML snippet) that:
      - Adds the new KPI column
      - Updates model .sql and schema.yml accordingly
    """
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a dbt expert. "
                "Output a unified diff patch to modify models/d_customers.sql "
                "and models/schema.yml to add a new column as requested."
            )},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )
    return completion.choices[0].message.content
