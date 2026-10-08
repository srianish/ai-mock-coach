"""
Runs 10 sample interview turns through the ACTUAL app code paths
(RAG retrieval -> question generation -> candidate answer -> CoT
evaluation) and writes the observed outputs to sample_test_results.md.

This is the "basic testing of at least 10 sample prompts/questions with
observed outputs" deliverable. It uses whatever LLM_PROVIDER is
configured in .env -- if none is configured it automatically uses the
offline mock backend (see coach/config.py), so this script always runs,
with or without an API key.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from coach.interview_engine import InterviewSession  # noqa: E402
from coach.llm_client import get_llm_client  # noqa: E402
from coach.rag import QuestionBankRAG  # noqa: E402
from coach.config import Config  # noqa: E402

SAMPLE_ANSWERS = [
    ("HR", "General", "I want to work here because I've used your product for two years and I "
                       "respect how the team ships fast without breaking things. I also think my "
                       "background in customer-facing support gives me an edge in understanding "
                       "user pain points."),
    ("HR", "General", "Honestly I just need a job right now, any company is fine as long as the "
                       "pay is decent."),
    ("Technical", "Python Backend", "A generator computes values lazily one at a time instead of "
                                     "building the whole list in memory, so for huge or infinite "
                                     "sequences it uses O(1) memory instead of O(n)."),
    ("Technical", "Python Backend", "Generators are like... functions but with yield instead of "
                                     "return I think? Not totally sure how they differ from lists."),
    ("Technical", "Databases & SQL", "An index is basically a sorted lookup structure, usually a "
                                      "B-tree, that lets the DB avoid scanning every row. It speeds "
                                      "up reads but costs extra writes and storage to maintain."),
    ("Technical", "Data Science / ML", "Precision is about how many of your positive predictions "
                                        "were actually correct, recall is about how many actual "
                                        "positives you caught. You'd optimize precision when false "
                                        "positives are costly, like spam filtering."),
    ("Behavioral", "General", "In my last group project a teammate wanted to use a NoSQL database "
                               "for clearly relational data. I proposed we prototype both in an "
                               "afternoon and compare query complexity, which showed SQL was "
                               "simpler for our joins, and he agreed to switch."),
    ("Behavioral", "General", "Once a teammate disagreed with me and eventually we just... did "
                               "what the manager said I guess."),
    ("Technical", "Web Development", "CORS is enforced by the browser to stop a malicious site from "
                                      "making authenticated requests to another origin on your "
                                      "behalf; the server opts in via Access-Control-Allow-Origin "
                                      "headers."),
    ("HR", "General", "Success in 90 days means I've shipped at least one feature end-to-end, "
                       "built relationships with my immediate team, and know our codebase well "
                       "enough to review PRs confidently."),
]


def main():
    print(f"Effective LLM provider: {Config.effective_provider()}")
    rag = QuestionBankRAG()
    print(f"Embedding backend: {rag.mode}")
    llm = get_llm_client()

    lines = [
        "# Sample Test Results\n",
        f"LLM backend used for this run: `{Config.effective_provider()}`  \n"
        f"Embedding backend used for this run: `{rag.mode}`\n",
        "Each entry below was produced by actually running "
        "`coach/rag.py`, `coach/interview_engine.py`, and "
        "`coach/evaluator.py` end to end -- these are real observed "
        "outputs, not hand-written examples.\n",
    ]

    for i, (role, domain, answer) in enumerate(SAMPLE_ANSWERS, 1):
        session = InterviewSession(role=role, domain=domain, llm_client=llm,
                                    rag=rag, total_questions=1)
        question = session.generate_next_question()
        result = session.submit_answer(answer)

        print(f"[{i}/10] {role}/{domain} -> generated + evaluated OK")

        lines.append(f"## Test {i}: {role} ({domain})\n")
        lines.append(f"**Generated question:** {question}\n")
        lines.append(f"**Candidate answer (input):** {answer}\n")
        lines.append(
            f"**Observed evaluation:** clarity={result['clarity']}/5, "
            f"correctness={result['correctness']}/5, "
            f"confidence={result['confidence']}/5\n"
        )
        lines.append(f"**Observed feedback comment:** {result['overall_comment']}\n")
        lines.append("<details><summary>Raw CoT reasoning (observed)</summary>\n\n"
                      f"```\n{result['raw_reasoning']}\n```\n</details>\n")
        lines.append("---\n")

    out_path = os.path.join(os.path.dirname(__file__), "sample_test_results.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
