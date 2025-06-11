import os, certifi
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
import openai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Retry up to 5 times, doubling the wait each time (with a max of ~10s),
# but only when a RateLimitError is raised.
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(openai.error.RateLimitError),
)
def safe_chat_completion(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

def generate_dbt_patch(prompt: str) -> str:
    response = safe_chat_completion(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a dbt expert. Output a unified diff patch to modify models/d_customers.sql "
                "and models/schema.yml to add or change columns as requested."
            )},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    try:
        patch = generate_dbt_patch("Add KPI …")
        print(patch)
    except openai.error.RateLimitError:
        print("Still being rate-limited after retries. Try again in a minute.")