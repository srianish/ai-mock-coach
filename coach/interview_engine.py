"""
Orchestrates one mock-interview session: keeps conversation memory,
decides when to ask a question vs. evaluate an answer vs. wrap up, and
calls into rag.py / prompts.py / evaluator.py to do so.
"""
from dataclasses import dataclass, field

from coach.config import Config
from coach.evaluator import aggregate_scores, evaluate_answer
from coach.prompts import (
    FINAL_REPORT_SYSTEM_PROMPT,
    SYSTEM_PROMPTS,
    build_final_report_prompt,
    build_question_prompt,
)
from coach.rag import QuestionBankRAG


@dataclass
class InterviewSession:
    role: str
    domain: str
    llm_client: object
    rag: QuestionBankRAG
    total_questions: int = field(default_factory=lambda: Config.INTERVIEW_LENGTH)

    transcript: list = field(default_factory=list)   # [{"speaker": "interviewer"/"candidate", "text": ...}]
    results: list = field(default_factory=list)       # evaluate_answer() outputs, one per answered question
    current_question: str = ""
    finished: bool = False

    def _history_summary(self, max_turns: int = 6) -> str:
        recent = self.transcript[-max_turns:]
        return "\n".join(f"{t['speaker']}: {t['text']}" for t in recent)

    def system_prompt(self) -> str:
        return SYSTEM_PROMPTS[self.role]

    def questions_asked(self) -> int:
        return len(self.results) + (1 if self.current_question else 0)

    def build_next_question_prompt(self) -> tuple[str, str]:
        """
        Retrieve grounding context via RAG and build the (system, user)
        prompt pair for the next question, WITHOUT calling the LLM. Split
        out like this so app.py can stream the response with
        llm_client.stream(...) directly, rather than this method blocking
        on a non-streaming complete() call.
        """
        context = self._history_summary(max_turns=2) or f"Start of a {self.role} interview."
        retrieved = self.rag.retrieve(
            role=self.role, domain=self.domain, context=context, top_k=Config.RAG_TOP_K
        )
        prompt = build_question_prompt(
            role=self.role,
            domain=self.domain,
            history_summary=self._history_summary(),
            retrieved_questions=retrieved,
            question_number=len(self.results) + 1,
            total_questions=self.total_questions,
        )
        return self.system_prompt(), prompt

    def generate_next_question(self) -> str:
        """Non-streaming convenience wrapper (used by the test harness)."""
        system, prompt = self.build_next_question_prompt()
        question = self.llm_client.complete(system, prompt)
        self.commit_question(question)
        return question

    def commit_question(self, question: str) -> None:
        """Record a (possibly streamed) generated question into state."""
        self.current_question = question.strip()
        self.transcript.append({"speaker": "interviewer", "text": self.current_question})

    def submit_answer(self, answer: str) -> dict:
        """Evaluate the candidate's answer to the current question, store it, advance state."""
        if not self.current_question:
            raise ValueError("No open question to answer.")

        self.transcript.append({"speaker": "candidate", "text": answer})
        result = evaluate_answer(self.llm_client, self.role, self.current_question, answer)
        self.results.append(result)
        self.current_question = ""

        if len(self.results) >= self.total_questions:
            self.finished = True
        return result

    def final_report(self) -> tuple[str, dict]:
        """Returns (narrative_report_text, aggregated_scores)."""
        prompt = build_final_report_prompt(self.role, self.results)
        narrative = self.llm_client.complete(FINAL_REPORT_SYSTEM_PROMPT, prompt)
        scores = aggregate_scores(self.results)
        return narrative, scores
