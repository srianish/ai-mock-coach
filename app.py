"""
AI Mock Interview Coach -- Streamlit interface.

Run with:  streamlit run app.py
"""
import streamlit as st

from coach.config import Config
from coach.interview_engine import InterviewSession
from coach.llm_client import LLMError, get_llm_client
from coach.prompts import SYSTEM_PROMPTS, TECHNICAL_DOMAINS
from coach.rag import QuestionBankRAG

st.set_page_config(page_title="AI Mock Interview Coach", page_icon="🎤", layout="centered")


@st.cache_resource(show_spinner="Loading interview question bank into the vector store...")
def _load_rag() -> QuestionBankRAG:
    return QuestionBankRAG()


@st.cache_resource(show_spinner=False)
def _load_llm_client():
    return get_llm_client()


def _new_session(role: str, domain: str, length: int) -> InterviewSession:
    return InterviewSession(
        role=role,
        domain=domain,
        llm_client=_load_llm_client(),
        rag=_load_rag(),
        total_questions=length,
    )


def _render_score_badge(label: str, value) -> str:
    return f"**{label}:** {value}/5"


def main():
    st.title("🎤 AI Mock Interview Coach")
    st.caption("Practice HR, Technical, or Behavioral interviews and get structured, scored feedback.")

    if not Config.has_real_credentials():
        st.warning(
            "⚠️ Running in **offline demo mode** (no `OPENAI_API_KEY`/`HF_API_TOKEN` found in "
            "`.env`). Using a local mock LLM and a TF-IDF fallback embedder so you can still try "
            "the full flow. Add a real key to `.env` for the graded run / live demo.",
            icon="⚠️",
        )

    if "session" not in st.session_state:
        st.session_state.session = None
        st.session_state.awaiting_answer = False
        st.session_state.show_report = False

    with st.sidebar:
        st.header("Interview Setup")
        role = st.selectbox("Interview type", list(SYSTEM_PROMPTS.keys()))
        domain = st.selectbox("Technical domain", TECHNICAL_DOMAINS) if role == "Technical" else "General"
        length = st.slider("Number of questions", min_value=3, max_value=8, value=Config.INTERVIEW_LENGTH)

        if st.button("🔄 Start new interview", type="primary", use_container_width=True):
            st.session_state.session = _new_session(role, domain, length)
            st.session_state.awaiting_answer = False
            st.session_state.show_report = False
            st.rerun()

        st.divider()
        st.caption(f"LLM backend: `{Config.effective_provider()}`")
        st.caption(f"Embedding backend: `{_load_rag().mode}`")

    session: InterviewSession = st.session_state.session
    if session is None:
        st.info("Pick a role in the sidebar and click **Start new interview** to begin.")
        return

    # --- render transcript so far ---
    for turn in session.transcript:
        speaker = "assistant" if turn["speaker"] == "interviewer" else "user"
        with st.chat_message(speaker):
            st.write(turn["text"])

    # render per-answer evaluation badges under the transcript
    if session.results:
        with st.expander("📊 Per-question scores so far", expanded=False):
            for i, r in enumerate(session.results, 1):
                st.markdown(
                    f"**Q{i}.** {r['question']}\n\n"
                    f"{_render_score_badge('Clarity', r['clarity'])} · "
                    f"{_render_score_badge('Correctness', r['correctness'])} · "
                    f"{_render_score_badge('Confidence', r['confidence'])}\n\n"
                    f"_{r['overall_comment']}_"
                )
                st.divider()

    try:
        # --- ask the next question if none is open and interview isn't done ---
        if not session.current_question and not session.finished:
            system, prompt = session.build_next_question_prompt()
            with st.chat_message("assistant"):
                full_text = st.write_stream(session.llm_client.stream(system, prompt))
            session.commit_question(full_text)

        # --- collect the candidate's answer ---
        if session.current_question and not session.finished:
            answer = st.chat_input("Type your answer...")
            if answer:
                with st.chat_message("user"):
                    st.write(answer)
                with st.spinner("Evaluating your answer..."):
                    session.submit_answer(answer)
                st.rerun()

        # --- wrap up ---
        if session.finished and not st.session_state.show_report:
            with st.spinner("Preparing your final report..."):
                narrative, scores = session.final_report()
            st.session_state.show_report = True
            st.session_state.final_narrative = narrative
            st.session_state.final_scores = scores

        if st.session_state.show_report:
            st.subheader("📋 Final Interview Report")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Clarity", st.session_state.final_scores["clarity"])
            c2.metric("Correctness", st.session_state.final_scores["correctness"])
            c3.metric("Confidence", st.session_state.final_scores["confidence"])
            c4.metric("Overall", st.session_state.final_scores["overall"])
            st.write(st.session_state.final_narrative)

    except LLMError as e:
        st.error(f"Something went wrong talking to the interview service: {e}")
        st.info("You can try again, or switch `LLM_PROVIDER` in `.env` to `mock` to keep demoing offline.")


if __name__ == "__main__":
    main()
