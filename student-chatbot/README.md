# Student Help Desk: AI Chatbot for Student Service Support

A complete working project: web chat page (frontend), FastAPI server (backend), retrieval + optional
Claude AI (brain), SQLite (data), and security features (login tokens, rate limit, PII masking, escalation).

Built by: Anant Singh | Roll No 2300821540004 | Section J1

---------------------------------------------------------------------
## 1. What you will build

```
Student browser  --->  FastAPI backend  --->  Retriever (TF-IDF over knowledge_base.json)
 (static/index.html)    (app/main.py)    --->  Optional LLM (Claude) writes the final answer
                              |           --->  Student records (app/students.py, demo)
                              +---------->  SQLite (chat logs, tickets, ratings)
Security around everything: JWT login, rate limit, input checks, PII masking, human handover
```

| Part | File | Job |
|---|---|---|
| Frontend | static/index.html | Chat window, quick questions, login box, feedback buttons |
| Backend | app/main.py | API routes, routing logic, handover |
| AI brain | app/retriever.py, app/llm.py | Finds facts, writes the answer |
| Data | data/knowledge_base.json, app/db.py, app/students.py | FAQs, logs, demo records |
| Security | app/security.py | Tokens, rate limit, masking, sensitive-topic detection |
| Tests | tests/test_basic.py, eval/run_eval.py | Checks the system works and measures accuracy |

---------------------------------------------------------------------
## 2. Requirements

- Python 3.10 or newer (check with `python --version`)
- A code editor (VS Code recommended)
- Internet for the first install. An Anthropic API key is OPTIONAL (the bot works offline without it).

---------------------------------------------------------------------
## 3. Step-by-step setup

### Step 1: Open the project folder
```bash
cd student-chatbot
```

### Step 2: Create and activate a virtual environment
Windows (PowerShell):
```bash
python -m venv .venv
.venv\Scripts\activate
```
Mac / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create your settings file
Copy `.env.example` to `.env` (Windows: `copy .env.example .env`, Mac/Linux: `cp .env.example .env`).
Edit `.env` and set SECRET_KEY and ADMIN_KEY to long random strings. Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Run the tests
```bash
python -m pytest -q
python -m eval.run_eval
```
Expected: all tests pass, and the evaluation prints accuracy (it was 10/10 on the sample questions).

### Step 6: Start the server
```bash
uvicorn app.main:app --reload
```
Open http://localhost:8000 in your browser.

### Step 7: Try it
- Click a common question, or type: "How can I pay my fees?"
- Type "What is my attendance?" (it asks you to sign in first)
- Sign in with student ID `2300001`, password `asha123`, then ask again
- Type "I feel depressed" (it escalates to staff and creates a ticket)
- Type "weather on Mars" (no answer found, so it hands over to staff)
- Open http://localhost:8000/docs to see and test all API routes

### Step 8: See the admin statistics
```bash
curl -H "X-Admin-Key: YOUR_ADMIN_KEY" http://localhost:8000/api/stats
```
Shows total chats, handovers, helpful rating %, and the recent questions the bot could not answer.

---------------------------------------------------------------------
## 4. Make it yours (replace the demo content)

1. **Knowledge base** (`data/knowledge_base.json`): replace every entry with your institution's real
   information. Each entry has: `id`, `title`, `question`, `answer`, `keywords`, `source`.
   Rules: one topic per entry, short clear answers, add many keywords (words students really use,
   including slang and common spellings), give each entry an owner and review it every semester.
2. **Greeting and chips**: edit the `topics` array and text in `static/index.html`.
3. **Colours and name**: edit the `:root` variables and `<h1>` in `static/index.html`.
4. **Handover messages**: edit `HANDOVER_TEXT` and `CRISIS_TEXT` in `app/main.py`.
   Add your real counselling centre and helpline details.
5. **Sensitive words**: edit `SENSITIVE_WORDS` in `app/security.py` and add words in your local languages.

---------------------------------------------------------------------
## 5. Turn on the AI brain (Claude writes the answers)

Offline mode returns the best matching knowledge-base answer. With an API key, Claude rewrites it
into a friendly, context-aware reply, but ONLY from the retrieved passages (this is called RAG).

1. Create an API key in the Anthropic Console (console.anthropic.com).
2. Put it in `.env`: `ANTHROPIC_API_KEY=your-key`
3. Restart the server. Answers now come from the model, grounded in your knowledge base.
4. The system prompt in `app/llm.py` forbids guessing and tells the model to hand over when unsure.
   Keep these rules. Test with tricky questions after any change.

Note: the model name is set by `LLM_MODEL` in `.env`. Use a model ID that your account can access.

---------------------------------------------------------------------
## 6. Connect real student data (personalised answers)

`app/students.py` holds demo data. To use real data:
1. Ask your IT team for a read-only API of the student information system (SIS) or ERP.
2. Replace `authenticate()` with a call to your university login (SSO, OAuth 2.0 / OpenID Connect).
3. Replace `get()` with an API call that returns ONLY the logged-in student's fee, attendance, etc.
4. Never send personal data to the AI model. The code already keeps personal answers rule-based.
5. Use HTTPS everywhere, and get written approval from your data protection officer.

---------------------------------------------------------------------
## 7. Security checklist (before real students use it)

- [ ] SECRET_KEY and ADMIN_KEY are long random values, stored only in `.env` or host secrets
- [ ] The site runs on HTTPS only
- [ ] Real password verification through university SSO (not demo users)
- [ ] CORS `ALLOWED_ORIGINS` lists only your real domain
- [ ] Rate limit is on (`RATE_LIMIT_PER_MINUTE`); put a firewall / reverse proxy in front
- [ ] Logs store masked text only (done by `mask_pii`); decide how long to keep logs
- [ ] Students are told they are talking to an AI and can reach a human
- [ ] A person reads the tickets table every day (handover must really work)
- [ ] Database backups, and a plan to delete old data
- [ ] Prompt-injection tests done (see tests) and API vendor data terms reviewed

---------------------------------------------------------------------
## 8. Deploy online

### Option A: Docker
```bash
docker build -t student-chatbot .
docker run -p 8000:8000 --env-file .env student-chatbot
```

### Option B: Render / Railway (simple cloud hosting)
1. Push the project to a private GitHub repository (`.env` is ignored by `.gitignore`).
2. Create a new Web Service on the host and connect the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add the variables from `.env` in the host's Environment settings.
6. For permanent storage use a managed database (PostgreSQL) instead of the local SQLite file,
   because many free hosts erase local files on restart.

### Put it on your college website
Add an iframe: `<iframe src="https://your-domain/" width="100%" height="650" style="border:0"></iframe>`

---------------------------------------------------------------------
## 9. Add more channels (WhatsApp / Telegram)

The `/api/chat` route is the single entry point. A messaging bot only needs to:
1. Receive the user's message through the platform's webhook (WhatsApp Business Cloud API, Telegram Bot API).
2. POST `{"message": text}` to `/api/chat`.
3. Send `answer` back to the user.
Start with Telegram (free, simplest). WhatsApp needs a business account and approved templates.

---------------------------------------------------------------------
## 10. Improve it over time (the learning loop)

1. Every week open `/api/stats` and read `recent_unanswered_questions`.
2. Add or rewrite knowledge-base entries for those questions.
3. Add each new question to `eval/questions.json`, run `python -m eval.run_eval`, keep accuracy high.
4. Look at "Not helpful" ratings and fix those answers.
5. Upgrade path when the knowledge base grows (hundreds of documents):
   - replace TF-IDF in `app/retriever.py` with embeddings (sentence-transformers) + a vector store (FAISS or Chroma);
   - move SQLite to PostgreSQL;
   - add Hindi and other languages (a multilingual embedding model, and tell the LLM to reply in the student's language);
   - add proactive reminders (a scheduled job that messages students before fee and exam deadlines).

---------------------------------------------------------------------
## 11. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Activate the virtual environment, run `pip install -r requirements.txt` |
| `uvicorn` not found | Use `python -m uvicorn app.main:app --reload` |
| Port 8000 busy | Add `--port 8001` and open that port |
| Bot hands over too often | Add keywords to the knowledge base, or lower `MIN_CONFIDENCE` in `.env` (for example 0.08) |
| Bot answers the wrong topic | Raise `MIN_CONFIDENCE`, remove overlapping entries, add precise keywords |
| AI mode is not used | Check `ANTHROPIC_API_KEY` in `.env`, restart, read the terminal for "LLM error" |
| Login fails | Use demo ID `2300001` and password `asha123` |
| Database locked | Stop duplicate servers; delete `chatbot.db` to reset the demo data |

---------------------------------------------------------------------
## 12. Questions your teacher may ask (viva)

- **Why retrieval before generation?** It keeps answers tied to approved documents and reduces made-up answers.
- **Where is the "brain"?** `retriever.py` finds facts and `llm.py` writes the reply. Rules in `main.py` decide routing.
- **How is security handled?** JWT login, hashed passwords, rate limiting, masked logs, input checks, admin key, HTTPS in deployment.
- **What if the bot does not know?** It creates a ticket and tells the student that staff will help.
- **How do you measure success?** Resolution rate, helpful %, handover rate (`/api/stats`) and retrieval accuracy (`eval/run_eval.py`).
- **Limitations?** TF-IDF matches words, not deep meaning; demo data; needs a human team for handovers.
