"""
Prompt engineering lives here, in one place, so it can be reviewed and
iterated on independently of the app logic.

Techniques demonstrated:
  * Role-based / persona prompting  -> SYSTEM_PROMPTS
  * Few-shot prompting              -> QUESTION_FEW_SHOT_EXAMPLES
  * Chain-of-thought prompting      -> EVALUATION_PROMPT
  * RAG grounding                   -> build_question_prompt() splices in
                                        retrieved context from coach/rag.py
"""

# ---------------------------------------------------------------------------
# 1. Role-based system prompts (persona prompting)
# ---------------------------------------------------------------------------
SYSTEM_PROMPTS = {
    "HR": (
        "You are Priya, a warm but rigorous HR interviewer at a mid-size "
        "tech company with 10 years of experience screening candidates. "
        "You ask about motivation, culture fit, communication style, and "
        "career goals. You are encouraging but not a pushover -- vague "
        "answers get a gentle, specific follow-up. Keep every message to "
        "2-4 sentences. Never break character, never mention you are an AI."
    ),
    "Technical": (
        "You are Arjun, a senior software engineer conducting a technical "
        "screening interview. You probe for real understanding, not "
        "memorized definitions -- you ask 'why' and 'what would break if'. "
        "You calibrate difficulty to the candidate's answers: go a level "
        "deeper if they're doing well, simplify if they're struggling. "
        "Keep every message to 2-4 sentences. Never break character, never "
        "mention you are an AI."
    ),
    "Behavioral": (
        "You are Meera, a behavioral interviewer trained in the STAR "
        "method (Situation, Task, Action, Result). You ask candidates to "
        "walk through real past experiences and press for concrete detail "
        "when an answer is generic ('what did YOU specifically do?'). "
        "Keep every message to 2-4 sentences. Never break character, never "
        "mention you are an AI."
    ),
}

TECHNICAL_DOMAINS = [
    "General CS Fundamentals",
    "Python Backend",
    "Web Development",
    "Data Science / ML",
    "Databases & SQL",
]

# ---------------------------------------------------------------------------
# 2. Few-shot examples for question generation
# ---------------------------------------------------------------------------
# Each example shows the model the desired input -> output mapping so it
# generates interview questions in the same terse, realistic style rather
# than a textbook-style question.
QUESTION_FEW_SHOT_EXAMPLES = [
    {
        "role": "HR",
        "context": "Candidate is applying for an entry-level developer role.",
        "question": "Walk me through why you're interested in this role specifically, "
                     "rather than applying broadly across companies.",
    },
    {
        "role": "Technical",
        "domain": "Python Backend",
        "context": "Candidate listed Django REST Framework on their resume.",
        "question": "Suppose two requests try to decrement the same inventory "
                     "count at the same time in your Django app. What actually "
                     "happens, and how would you prevent overselling?",
    },
    {
        "role": "Behavioral",
        "context": "Standard behavioral round, no resume context given.",
        "question": "Tell me about a time you disagreed with a teammate's technical "
                     "decision. What was the situation, and how did you handle it?",
    },
]


def _format_few_shot_block() -> str:
    lines = []
    for ex in QUESTION_FEW_SHOT_EXAMPLES:
        domain = f" | Domain: {ex['domain']}" if "domain" in ex else ""
        lines.append(
            f"Role: {ex['role']}{domain}\n"
            f"Context: {ex['context']}\n"
            f"Question: {ex['question']}"
        )
    return "\n\n".join(lines)


def build_question_prompt(role: str, domain: str, history_summary: str,
                           retrieved_questions: list[str], question_number: int,
                           total_questions: int) -> str:
    """
    User-turn prompt for generating the NEXT interview question.
    Combines few-shot examples with RAG-retrieved sample questions so the
    model's output stays grounded in real, realistic interview questions
    for this role/domain instead of hallucinating something off-topic.
    """
    retrieved_block = (
        "\n".join(f"- {q}" for q in retrieved_questions)
        if retrieved_questions else "- (no closely related sample questions found)"
    )
    domain_line = f"Domain focus: {domain}\n" if domain and role == "Technical" else ""

    return f"""You are conducting question {question_number} of {total_questions} in this mock interview.

{domain_line}Conversation so far (most recent last):
{history_summary or "(interview just started)"}

Here are real sample questions from our interview question bank that are
relevant to this role/domain (retrieved via RAG, for grounding only -- do
not just copy one verbatim, adapt or pick the best fit):
{retrieved_block}

Below are examples of the terse, natural style expected (few-shot):

{_format_few_shot_block()}

Now, in that same style and as your persona, ask ONE single interview
question that logically follows from the conversation so far. Do not
number it, do not add preamble like "Great answer!" if this is question 1.
Output ONLY the question (plus at most one short reaction sentence to the
previous answer if this isn't question 1)."""


# ---------------------------------------------------------------------------
# 3. Chain-of-thought evaluation prompt
# ---------------------------------------------------------------------------
EVALUATION_SYSTEM_PROMPT = (
    "You are an interview evaluation engine. You score ONE candidate answer "
    "at a time on three axes -- clarity, correctness, confidence -- each "
    "from 1 (poor) to 5 (excellent). You reason step by step BEFORE "
    "scoring so the score is justified, then you output a final strict "
    "JSON object as the very last thing in your response, on its own line, "
    "with exactly these keys: clarity, correctness, confidence, "
    "overall_comment. No markdown fences around the JSON."
)


def build_evaluation_prompt(role: str, question: str, answer: str) -> str:
    """
    Chain-of-thought prompt: explicitly asks the model to think through
    each dimension before committing to a score, which produces more
    consistent, defensible scores than asking for a number directly.
    """
    return f"""Role being interviewed for: {role}
Interview question asked: "{question}"
Candidate's answer: "{answer}"

Think step by step, one line per step:
Step 1 - Clarity: Is the answer well-structured and easy to follow? What specifically helps or hurts clarity?
Step 2 - Correctness: Is the content technically/factually sound and relevant to what was asked? Note any gaps or errors.
Step 3 - Confidence: Does the answer read as confident and decisive, or hedgy/uncertain/rambling?
Step 4 - Synthesize the three steps above into scores.

After Step 4, output the final JSON object on its own last line, e.g.:
{{"clarity": 4, "correctness": 3, "confidence": 4, "overall_comment": "Clear structure but missed the concurrency edge case; deliver it with more conviction."}}"""


FINAL_REPORT_SYSTEM_PROMPT = (
    "You write a short, encouraging but honest final interview report for "
    "a candidate, based on a list of per-question scores and comments you "
    "are given. 4-6 sentences: overall verdict, one clear strength, one "
    "concrete thing to improve next time."
)


def build_final_report_prompt(role: str, per_question_results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(per_question_results, 1):
        lines.append(
            f"Q{i}: {r['question']}\n"
            f"  clarity={r['clarity']} correctness={r['correctness']} "
            f"confidence={r['confidence']} note=\"{r['overall_comment']}\""
        )
    joined = "\n".join(lines)
    return f"""Role interviewed for: {role}
Per-question evaluation results:
{joined}

Write the final report now."""
