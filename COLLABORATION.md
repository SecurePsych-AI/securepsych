# Team Collaboration Guide — SecurePsych AI

## 🚀 Quick Start

1. **Clone the repo**
   ```bash
        git clone https://github.com/securepsych-ai/securepsych.git
   cd securepsych
   ```

2. **Set up your environment**
   ```bash
   cp .env.example .env
   # Fill in values — ask for local server config, once we get machine set up and everything ofc
   ```

3. **Install dependencies**
   ```bash
   # Backend (from any service folder)
   poetry install
   # or
   pip install -r requirements.txt

   # Frontend
   cd frontend && npm install
   ```

4. **Read the docs**
   - See `README.md` for architecture overview and stack
   - Ask Natoli or Kai if anything is unclear before diving in

---

## 📋 Workflow Rules

### 📺 Walkthrough

New to the workflow? Watch the setup and PR demo before diving in:
[Git Collaboration Walkthrough →](https://loom.com/link)

```bash
# Always sync before starting new work:
git checkout dev
git pull origin dev

# Create a branch for your work:
git checkout -b feat/your-feature-name

# While working — stay in sync with dev to avoid drift:
git pull --rebase origin dev

# If there are conflicts during rebase, resolve them, then:
git rebase --continue

# Commit as you go:
git add .
git commit -m "feat: short description of what you did"

# Push your branch:
git push origin feat/your-feature-name

# If you've already pushed and just rebased, you'll need to force push:
# Never just git push --force, only --force-with-lease when needed, if consufued contact us:
git push --force-with-lease origin feat/your-feature-name 

# Then open a Pull Request on GitHub: your branch → dev
# Assign Natoli as reviewer.
```

**Two hard rules:**
- Do not commit directly to `main` or `dev`
- Do not merge your own PR

Everything else is flexible.

---

## 🔀 Branch Naming

Keep it short and descriptive. A few examples:

```
feat/rag-query-chain
feat/frontend-file-upload
fix/chunking-overlap
docs/api-reference
infra/docker-compose-setup
```

---

## 💬 Commit Messages

No strict format required — just be descriptive enough that someone else knows what changed:

```bash
git commit -m "feat: add ChromaDB embedding pipeline"
git commit -m "fix: handle token overflow on long documents"
git commit -m "docs: update API endpoint reference"
```

---

## 🔍 PR Review

Assign **Natoli** as reviewer on every PR. If Natoli hasn't responded within **48 hours**, follow up with Natoli and/or **Kai** directly — don't let your work sit blocked.

PRs to `main` are handled by Natoli only, at phase gates and before demos.

---

## 🗂 Repo Structure

```
securepsych/
├── backend/
│   ├── gateway/        ← API gateway, port 8000
│   ├── rag/            ← RAG Q&A service
│   ├── summarizer/     ← Summarization service
│   ├── jargon/         ← Jargon simplification (Phase 3)
│   ├── visualizer/     ← Data visualization (Phase 3)
│   └── task_manager/   ← Task manager (Phase 4)
├── frontend/           ← React + Vite + TailwindCSS
├── infra/              ← Docker, CI/CD configs
├── docs/               ← API docs, guides, troubleshooting
├── .env.example        ← Copy to .env — never commit your .env
└── README.md
```

Everyone can contribute anywhere — backend, frontend, docs, infra. Pick up what needs doing.

---

## 🔧 Code Quality

- Python: follow PEP8, run `black .` before pushing if you have it installed
- Frontend: Prettier formatting preferred
- No hard requirement on linters for now — clean, readable code over perfect style

---

## ⚠️ What Not to Commit — Ever

These rules exist because of FERPA. Non-negotiable:

| Don't commit | Why |
|---|---|
| Student documents, IEPs, any real student data | FERPA — immediate removal required |
| `.env` files | Contains credentials |
| API keys or tokens of any kind | Use `.env` and `.env.example` |
| `chroma/` vector store data | Contains embeddings derived from student files |

When in doubt, check `.gitignore` — if it's listed there, don't force it in.

---

## ⚙️ Git Reminders

- Never `git push --force` on shared branches
- If you have a merge conflict you can't resolve, stop and message Natoli and everyone involved with your branch name — don't guess
- Keep `.gitignore` updated if you're adding new file types or build artifacts

---