````markdown
# AI-Based Data Engineering Automation

This project helps your team automate common data engineering tasks—like adding new columns or renaming fields in your dbt models—by simply sending a request. You can use it directly (if you know which files to edit) or through a friendly, high-level translator (for non-technical users).

---

## 📖 Overview

1. **PR-Bot Service** (`/requests` endpoint)  
   - Receives a technical request: a list of file names plus a clear instruction for each file.  
   - Uses AI to update your dbt models (SQL/YAML), creates a draft pull request, and lets you iterate until you’re happy.

2. **Translator Service** (`/translate-and-forward/` endpoint)  
   - Designed for non-technical users: accepts layman-style prompts (“Add a KPI for date_of_birth”).  
   - Uses AI to translate that into the technical request format and forwards it to the PR-Bot.

3. **Draft & Confirm Workflow**  
   - The PR starts as a draft. You can send follow-up edits to the same draft.  
   - When you reply with **Confirm** or **Looks good**, the draft is automatically marked *Ready for review*.

---

## ⚙️ Prerequisites

- **Python** 3.10+  
- **GitHub Personal Access Token** with `repo` scope (`GITHUB_TOKEN`)  
- **OpenAI API Key** (`OPENAI_API_KEY`)  
- **(Optional)** Poetry or pip for dependency management

---

## 🔧 Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-org/ai-based-data-engineering.git
   cd ai-based-data-engineering
````

2. **Install dependencies**

   * With **Poetry**:

     ```bash
     poetry install
     ```
   * Or with **pip**:

     ```bash
     pip install -r requirements.txt
     ```

3. **Create a `.env`** file in the project root:

   ```dotenv
   # GitHub settings
   GITHUB_TOKEN=ghp_...
   GITHUB_REPO=your-org/your-repo

   # OpenAI settings
   OPENAI_API_KEY=sk-...

   # Translator service (if used)
   TECH_SERVICE_URL=http://localhost:8000/requests
   TECH_SERVICE_TOKEN=ghp_...
   ```

---

## ▶️ Running the Services

You can run the two services on different ports.

### 1. PR-Bot Service (Technical)

This service edits files and creates pull requests.

```bash
uvicorn ai_dbt_bot.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

* **Endpoint**: `POST http://localhost:8000/requests`
* **Body**:

  ```jsonc
  {
    "session_id": null,         // omit or set to reuse a draft
    "file_names": [
      "models/d_customers.sql",
      "models/d_customers.yml"
    ],
    "analyst_prompt": "Add column date_of_birth as CAST(dob_string AS DATE)"
  }
  ```
* **Response**:

  ```json
  {
    "message": "Draft PR created: https://github.com/your-org/your-repo/pull/123",
    "session_id": "abcdef"
  }
  ```

### 2. Translator Service (High-Level)

This service turns layman requests into technical ones and forwards to PR-Bot.

```bash
uvicorn translator_service:app \
  --reload \
  --host 0.0.0.0 \
  --port 8001
```

* **Endpoint**: `POST http://localhost:8001/translate-and-forward/`
* **Body**:

  ```json
  {
    "business_prompt": "Add a KPI for date_of_birth in customer dimension"
  }
  ```
* **Response**: same JSON as the PR-Bot service, including the `session_id` and PR URL.

---

## 🔄 Iterative Workflow

1. **First request** creates a **draft PR**. You’ll get a `session_id` back.
2. **Make follow-up edits** by re-calling the same endpoint with that `session_id`.
3. **Finalize** by sending:

   ```json
   {
     "session_id": "abcdef",
     "analyst_prompt": "looks good"
   }
   ```

   and the draft flips to *Ready for review*.

---

## 📝 Notes

* The framework uses **AI** (OpenAI) to transform file contents. Keep your prompts clear!
* You can skip the Translator service if you already know the exact files and instructions—just talk directly to `/requests`.
* Feel free to extend the LLM prompts, add validations, or support more file types.

---

