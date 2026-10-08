"""
Wraps whichever LLM backend is configured behind one simple interface:

    client = get_llm_client()
    text = client.complete(system_prompt, user_prompt)
    for chunk in client.stream(system_prompt, user_prompt):
        ...

Handles:
  * API failures (connection errors, timeouts)
  * Rate limits (exponential backoff retry, then a clear user-facing error)
  * Empty / malformed responses
  * Streaming, where the provider supports it
"""
import random
import time
from typing import Generator

from coach.config import Config


class LLMError(Exception):
    """Raised when the LLM backend fails after retries, with a message
    that is safe to show directly to the user."""


# ---------------------------------------------------------------------------
# Real backend: OpenAI
# ---------------------------------------------------------------------------
class OpenAIClient:
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self._model = Config.OPENAI_MODEL

    def complete(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        from openai import APIConnectionError, APIStatusError, RateLimitError, APITimeoutError

        last_err = None
        for attempt in range(max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                )
                content = resp.choices[0].message.content if resp.choices else None
                if not content or not content.strip():
                    raise LLMError("The model returned an empty response. Please try again.")
                return content.strip()

            except RateLimitError as e:
                last_err = e
                time.sleep((2 ** attempt) + random.random())
            except (APIConnectionError, APITimeoutError) as e:
                last_err = e
                time.sleep((2 ** attempt) * 0.5 + random.random())
            except APIStatusError as e:
                # 4xx/5xx that isn't a rate limit -- don't blindly retry auth
                # errors or bad requests, surface them immediately.
                raise LLMError(f"The interview service returned an error ({e.status_code}). "
                                f"Please check your API key/quota and try again.") from e

        raise LLMError(
            "The interview service is rate-limited or unreachable right now "
            f"after {max_retries} attempts. Please wait a moment and try again."
        ) from last_err

    def stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        from openai import APIConnectionError, APIStatusError, RateLimitError, APITimeoutError
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                stream=True,
            )
            got_any = False
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    got_any = True
                    yield delta
            if not got_any:
                raise LLMError("The model returned an empty streamed response.")
        except RateLimitError as e:
            raise LLMError("Rate limit hit while streaming. Please wait and retry.") from e
        except (APIConnectionError, APITimeoutError) as e:
            raise LLMError("Lost connection to the interview service mid-response.") from e
        except APIStatusError as e:
            raise LLMError(f"Interview service error ({e.status_code}) while streaming.") from e


# ---------------------------------------------------------------------------
# Real backend: Hugging Face Inference API
# ---------------------------------------------------------------------------
class HFInferenceClient:
    def __init__(self):
        self._token = Config.HF_API_TOKEN
        self._model = Config.HF_MODEL
        self._url = f"https://api-inference.huggingface.co/models/{self._model}"

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        import requests
        headers = {"Authorization": f"Bearer {self._token}"}
        prompt = f"<system>\n{system_prompt}\n</system>\n<user>\n{user_prompt}\n</user>"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 400, "temperature": 0.7}}

        for attempt in range(3):
            try:
                r = requests.post(self._url, headers=headers, json=payload, timeout=30)
            except requests.RequestException as e:
                if attempt == 2:
                    raise LLMError("Could not reach the Hugging Face Inference API.") from e
                time.sleep((2 ** attempt) * 0.5)
                continue

            if r.status_code == 429:
                time.sleep((2 ** attempt) + random.random())
                continue
            if r.status_code >= 400:
                raise LLMError(f"Hugging Face Inference API error ({r.status_code}).")

            data = r.json()
            text = data[0].get("generated_text", "") if isinstance(data, list) and data else ""
            if not text.strip():
                raise LLMError("The model returned an empty response.")
            return text.strip()

        raise LLMError("Hugging Face Inference API is rate-limited. Please try again shortly.")

    def complete(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        return self._call(system_prompt, user_prompt)

    def stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        # The free Inference API used here doesn't support token streaming,
        # so we simulate incremental display from the full completion.
        text = self._call(system_prompt, user_prompt)
        for word in text.split(" "):
            yield word + " "


# ---------------------------------------------------------------------------
# Offline fallback: used automatically with no API key, and by the test
# harness, so the full app flow can be demoed/tested without network access.
# ---------------------------------------------------------------------------
class MockLLMClient:
    _QUESTION_BANK = {
        "HR": [
            "What draws you to this specific role, beyond just needing a job?",
            "How do you handle a week where three things are all 'urgent'?",
            "Tell me what a great manager looks like to you.",
        ],
        "Technical": [
            "What actually happens in memory when you append to a Python list past its allocated capacity?",
            "If two users hit 'submit' on the same form at the same instant, what breaks first in your design?",
            "How would you explain an index to someone who's never touched a database?",
        ],
        "Behavioral": [
            "Tell me about a time a plan you owned fell apart. What did you do next?",
            "Describe a disagreement with a teammate that you're proud of how you handled.",
            "When have you had to learn something fast with no one around to ask?",
        ],
    }

    def __init__(self):
        self._counters = {"HR": 0, "Technical": 0, "Behavioral": 0}

    def complete(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        if "final interview report" in system_prompt.lower():
            return (
                "Overall, this was a solid mock interview. You communicated your "
                "points clearly and structured most answers well. Your strongest "
                "moment was backing claims with a concrete example instead of "
                "staying abstract. Going forward, work on stating your conclusion "
                "up front (answer first, details second) and trimming filler "
                "phrases to sound more decisive. Keep practicing under a timer -- "
                "you're close to interview-ready."
            )
        if "evaluation engine" in system_prompt.lower():
            clarity = random.randint(3, 5)
            correctness = random.randint(2, 5)
            confidence = random.randint(3, 5)
            return (
                "Step 1 - Clarity: The answer follows a logical order and stays on topic.\n"
                "Step 2 - Correctness: Covers the core idea, though it could go one level deeper.\n"
                "Step 3 - Confidence: Reads as reasonably decisive, few hedging words.\n"
                "Step 4 - Combining the above into scores.\n"
                f'{{"clarity": {clarity}, "correctness": {correctness}, '
                f'"confidence": {confidence}, "overall_comment": '
                f'"Good structure and mostly accurate; add one more layer of detail '
                f'and drop the hedging to sound more confident."}}'
            )
        # question generation
        for role, bank in self._QUESTION_BANK.items():
            if role in system_prompt:
                q = bank[self._counters[role] % len(bank)]
                self._counters[role] += 1
                return q
        return "Tell me a bit more about your background."

    def stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        text = self.complete(system_prompt, user_prompt)
        for word in text.split(" "):
            time.sleep(0.01)
            yield word + " "


def get_llm_client():
    provider = Config.effective_provider()
    if provider == "openai":
        return OpenAIClient()
    if provider == "huggingface":
        return HFInferenceClient()
    return MockLLMClient()
