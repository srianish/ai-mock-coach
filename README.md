# AI Mock Interview Coach

Team 7 — GENAI Course Project

An LLM-powered assistant that role-plays as an interviewer (HR / Technical /
Behavioral), asks a coherent sequence of interview questions, and gives the
candidate structured feedback on **clarity, correctness, and confidence**
at the end of the session.

---

## 1. Problem Statement

Students preparing for placements need practice answering interview
questions and structured feedback. This app conducts a short mock
interview for a chosen role and domain, then evaluates the candidate's
answers.

## 2. Features / Modules

| Module | File | What it does |
|---|---|---|
| Role Selection | `app.py` sidebar | Pick HR / Technical / Behavioral + a technical domain |
| Question Generator | `coach/interview_engine.py`, `coach/prompts.py` | Generates the next interview question using role-based + few-shot prompting, grounded by RAG-retrieved sample questions |
| RAG question bank | `coach/rag.py`, `data/question_bank.json` | Embeds a curated bank of real interview questions into a vector DB (Chroma) and retrieves the most relevant ones for the chosen role/domain, so questions stay realistic and non-repetitive |
| Answer Evaluator | `coach/evaluator.py` | Chain-of-thought evaluation of each answer → scores for clarity, correctness, confidence |
| Feedback & Scoring | `coach/evaluator.py`, `app.py` | Per-answer feedback + a final aggregated report card at the end of the interview |
| Chat-based flow with memory | `coach/interview_engine.py` | Keeps full conversation history so the interviewer's questions stay coherent turn to turn |

## 3. Concepts from the course used, and where

- **Role-based prompting** — `coach/prompts.py::SYSTEM_PROMPTS` gives the
  model a distinct interviewer persona per role.
- **Few-shot prompting** — `coach/prompts.py::QUESTION_FEW_SHOT_EXAMPLES`,
  used when generating the next interview question.
- **Chain-of-thought prompting** — `coach/prompts.py::EVALUATION_PROMPT`
  explicitly asks the model to reason step by step through clarity →
  correctness → confidence *before* emitting the final structured score,
  so the score is grounded in visible reasoning rather than a guess.
- **RAG (embeddings + vector database)** — `coach/rag.py` embeds
  `data/question_bank.json` into a **Chroma** collection and retrieves the
  top-k most relevant real interview questions for the chosen
  role/domain, which are passed into the question-generation prompt as
  grounding context.
- **Conversation memory** — `coach/interview_engine.py::InterviewSession`
  keeps the running transcript and feeds it back into every LLM call so
  the interview flows coherently rather than asking disconnected
  questions.
- **Prompt evaluation & iteration** — `tests/sample_test_results.md`
  documents 10 sample runs used to iterate on the prompts (see §7).

## 4. Architecture

```
                ┌────────────────────┐
User ────────▶ │   Streamlit UI      │  app.py
                │  (chat + sidebar)   │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐        ┌──────────────────┐
                │ InterviewSession    │◀──────▶│ RAG retriever     │
                │ (memory, state      │        │ (Chroma + embed-  │
                │  machine)           │        │  dings)           │
                └─────────┬──────────┘        └──────────────────┘
                          │
                          ▼
                ┌────────────────────┐
                │   LLMClient         │  coach/llm_client.py
                │ (OpenAI, streaming, │
                │  retries, fallback) │
                └────────────────────┘
```

## 5. Setup

```bash
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste your key:
# OPENAI_API_KEY=sk-...

streamlit run app.py
```

### Running without an API key (offline demo mode)

If `OPENAI_API_KEY` is not set, the app automatically falls back to a
built-in **offline mock LLM and a local TF-IDF embedder** (see
`coach/llm_client.py::MockLLMClient` and
`coach/rag.py::LocalTfidfEmbedder`). This lets you demo the full
question → answer → CoT-evaluation → scoring flow with no internet
connection, and is what was used to produce the sample test transcripts
in `tests/sample_test_results.md`. A yellow banner in the UI tells you
when you're in this mode. Swap in a real `OPENAI_API_KEY` for graded
submission / live demo so the "Core LLM/API integration" criterion is
met with a real API.

Hugging Face Inference API can be used instead of OpenAI by setting
`LLM_PROVIDER=huggingface` and `HF_API_TOKEN` in `.env` — see
`coach/llm_client.py::HFInferenceClient`.

## 6. Environment variables (`.env`, never hard-coded — see `.env.example`)

```
LLM_PROVIDER=openai          # openai | huggingface | mock
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
HF_API_TOKEN=
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

## 7. Testing

`tests/run_sample_tests.py` runs 10 fixed sample prompts/questions
through the app's real code paths (question generation + CoT
evaluation) and writes the observed outputs to
`tests/sample_test_results.md`. Run it yourself with:

```bash
python tests/run_sample_tests.py
```

## 8. Error handling & reliability

- `coach/llm_client.py` wraps every API call in retry-with-backoff logic
  and catches rate-limit, connection, timeout, and empty-response cases,
  surfacing a friendly message in the Streamlit UI instead of crashing.
- Streaming is used for the interviewer's chat replies
  (`st.write_stream` in `app.py`) wherever the provider supports it.

## 9. Deployment

The app is a single-command Streamlit app (`streamlit run app.py`), so it
deploys as-is to Streamlit Community Cloud, a Hugging Face Space, or any
container host — just set the environment variables from §6 as secrets.

## 10. Evaluation split coverage (from the assignment)

| Criterion | Marks | Where it's satisfied |
|---|---|---|
| Prompt design & engineering | 15 | `coach/prompts.py` (role-based, few-shot, CoT) |
| Core LLM/API integration | 25 | `coach/llm_client.py` |
| RAG / embeddings / vector DB | 20 | `coach/rag.py`, `data/question_bank.json` |
| Interface & UX | 15 | `app.py` (Streamlit chat UI, streaming, sidebar controls) |
| Deployment & documentation | 10 | this README, `.env.example`, `requirements.txt` |
| Presentation & demo | 15 | `AI_Mock_Interview_Coach_Presentation.pptx` |
"# ai-mock-coach" 
