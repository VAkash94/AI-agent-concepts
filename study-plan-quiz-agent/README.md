# 🎓 Personalized Study Plan & Quiz Agent

A **multi-agent AI system** that generates personalized explanations at three learning levels, lets you pick the one that fits you best, then quizzes you on it — all powered by the **OpenAI Agents SDK**.

Built as a practical exploration of agentic patterns:
- Parallel agent fan-out with `asyncio.gather`
- Orchestration by code (Python controls the pipeline)
- `@function_tool` for SQLite progress persistence
- Full observability via `trace()` → [platform.openai.com/traces](https://platform.openai.com/traces)

---

## 🏗 Architecture

```
                     User Input (topic)
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
   │   Beginner    │ │ Intermediate  │ │   Advanced    │
   │    Agent      │ │    Agent      │ │    Agent      │
   │  (ELI5 style) │ │(structured)   │ │(Socratic deep)│
   └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
           └────────────────┬┘                  │
                        (run in parallel via asyncio.gather)
                            │
                   Student picks a level
                            │
                            ▼
                  ┌──────────────────┐
                  │  Assessment      │
                  │  Agent (Quiz)    │
                  └────────┬─────────┘
                           │
                  Student answers quiz
                           │
                           ▼
              ┌────────────────────────┐
              │  save_progress (tool)  │
              │   → SQLite DB          │
              └────────────────────────┘
```

### Agents

| Agent | Style | Purpose |
|---|---|---|
| **Beginner Agent** | ELI5, analogies, no jargon | Explains topics for complete newcomers |
| **Intermediate Agent** | Structured theory + examples | For students with foundational knowledge |
| **Advanced Agent** | Socratic, edge cases, trade-offs | Deep dives for experienced learners |
| **Assessment Agent** | Quiz master | Generates 5 MCQs from the chosen explanation |

### Tools

| Tool | Storage | Purpose |
|---|---|---|
| `save_progress()` | SQLite (`study_progress.db`) | Persist topic, level, score, timestamp |
| `get_history()` | SQLite | Retrieve all past sessions for a student |

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/study-plan-quiz-agent.git
cd study-plan-quiz-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or GOOGLE_API_KEY
```

The agent auto-detects which provider to use:
- If `OPENAI_API_KEY` is set → uses `gpt-4o-mini`
- If only `GOOGLE_API_KEY` is set → uses `gemini-2.0-flash`
- Override with `STUDY_MODEL=openai` or `STUDY_MODEL=gemini`

### 4. Run a study session

```bash
# Interactive mode (prompts for topic)
python main.py

# With a topic pre-set
python main.py --topic "explain how transformers work" --student_id alice

# View past sessions
python history.py --student_id alice
```

---

## 📂 Project Structure

```
study-plan-quiz-agent/
├── main.py            # Entry point — full pipeline orchestration
├── study_agents.py    # Agent definitions (Beginner, Intermediate, Advanced, Assessment)
├── tools.py           # @function_tool definitions + SQLite helpers
├── history.py         # CLI to view past study sessions
├── pyproject.toml     # Dependencies and project metadata
├── .env.example       # Environment variable template
├── .gitignore
└── README.md
```

---

## 🔄 Agentic Patterns Demonstrated

### Pattern 1: Parallel Fan-Out (Orchestration by Code)
```python
results = await asyncio.gather(
    Runner.run(beginner_agent,      prompt),
    Runner.run(intermediate_agent,  prompt),
    Runner.run(advanced_agent,      prompt),
)
```
All 3 curriculum agents run **simultaneously**. Total latency = slowest single agent, not sum of all three.

### Pattern 2: Sequential Pipeline
After the student picks a level, the Assessment Agent runs **sequentially** — it needs the chosen explanation as input before it can generate the quiz.

### Pattern 3: `@function_tool` — Side-Effect Actions
```python
@function_tool
def save_progress_tool(student_id: str, topic: str, level_chosen: str, score: int) -> str:
    ...
```
Wraps a database write as a tool the LLM can call. The JSON schema is auto-generated from type hints and docstrings.

### Pattern 4: `trace()` — Full Observability
Every `Runner.run(...)` call inside a `with trace("...")` block is recorded to OpenAI Traces. You can inspect:
- Which agent ran
- What the model received and returned
- Token counts and latencies
- Tool call inputs/outputs

View at: https://platform.openai.com/traces

---

## 🧪 Example Session

```
🎓 Personalized Study Plan & Quiz Agent
=============================================
What topic would you like to study? > explain backpropagation

──────────────── Generating explanations (all 3 levels in parallel)... ────────────────

──────────────────── 🟢 BEGINNER — ELI5 Style ───────────────────────
Imagine your brain is trying to learn to ride a bike...

──────────────────── 🟡 INTERMEDIATE — Structured Theory ────────────
Backpropagation is an algorithm for computing gradients in neural networks...

──────────────────── 🔴 ADVANCED — Deep Dive ────────────────────────
The computational graph perspective reveals why backprop works through the
chain rule of calculus. Consider the pathological case of vanishing gradients...

📚 Choose your learning level:
  [1] Beginner
  [2] Intermediate
  [3] Advanced

Enter 1, 2, or 3: 2

──────────────────── YOUR QUIZ ──────────────────────────────────────
Q1: What is the primary purpose of backpropagation?
A) To initialize neural network weights
B) To compute gradients for weight updates
C) To normalize input data
D) To apply the activation function
Answer: B
...

──────────────────── ANSWER YOUR QUIZ ──────────────────────────────
Q1: B
  ✅ Correct!
...

✅ Score: 4/5
💾 Progress saved for student 'alice'
```

---

## ⚙️ Configuration Reference

| Env Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GOOGLE_API_KEY` | — | Google Gemini API key |
| `STUDY_MODEL` | `auto` | Model provider: `auto`, `openai`, or `gemini` |
| `STUDY_DB_PATH` | `study_progress.db` | SQLite file path |

---

## 🛠 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Lint
ruff check .

# Format
ruff format .

# Run tests (if added)
pytest
```

---

## 🧩 Extending the Project

Some ideas to take this further:

- **More agents**: Add a `Visual Learner` agent that generates Mermaid diagrams
- **Adaptive difficulty**: Track scores over time and auto-select level based on performance
- **Spaced repetition**: Schedule quiz reminders via email/push (see `2_lab2.ipynb` for SMTP setup)
- **Multi-topic sessions**: Chain multiple topics in one session using `SQLiteSession` for memory
- **Web UI**: Wrap in a FastAPI + Streamlit app for a proper learning dashboard

---

## 📚 Built On

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) (`openai-agents`)
- [OpenAI API](https://platform.openai.com/) or [Google Gemini](https://ai.google.dev/)
- Python `asyncio` for parallel agent execution
- SQLite for lightweight progress persistence

---

## 📄 License

MIT
