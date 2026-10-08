# Sample Test Results

LLM backend used for this run: `mock`  
Embedding backend used for this run: `local-tfidf`

Each entry below was produced by actually running `coach/rag.py`, `coach/interview_engine.py`, and `coach/evaluator.py` end to end -- these are real observed outputs, not hand-written examples.

## Test 1: HR (General)

**Generated question:** What draws you to this specific role, beyond just needing a job?

**Candidate answer (input):** I want to work here because I've used your product for two years and I respect how the team ships fast without breaking things. I also think my background in customer-facing support gives me an edge in understanding user pain points.

**Observed evaluation:** clarity=3/5, correctness=4/5, confidence=5/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 3, "correctness": 4, "confidence": 5, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 2: HR (General)

**Generated question:** How do you handle a week where three things are all 'urgent'?

**Candidate answer (input):** Honestly I just need a job right now, any company is fine as long as the pay is decent.

**Observed evaluation:** clarity=5/5, correctness=4/5, confidence=3/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 5, "correctness": 4, "confidence": 3, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 3: Technical (Python Backend)

**Generated question:** Tell me a bit more about your background.

**Candidate answer (input):** A generator computes values lazily one at a time instead of building the whole list in memory, so for huge or infinite sequences it uses O(1) memory instead of O(n).

**Observed evaluation:** clarity=4/5, correctness=5/5, confidence=4/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 4, "correctness": 5, "confidence": 4, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 4: Technical (Python Backend)

**Generated question:** Tell me a bit more about your background.

**Candidate answer (input):** Generators are like... functions but with yield instead of return I think? Not totally sure how they differ from lists.

**Observed evaluation:** clarity=4/5, correctness=5/5, confidence=5/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 4, "correctness": 5, "confidence": 5, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 5: Technical (Databases & SQL)

**Generated question:** Tell me a bit more about your background.

**Candidate answer (input):** An index is basically a sorted lookup structure, usually a B-tree, that lets the DB avoid scanning every row. It speeds up reads but costs extra writes and storage to maintain.

**Observed evaluation:** clarity=4/5, correctness=4/5, confidence=5/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 4, "correctness": 4, "confidence": 5, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 6: Technical (Data Science / ML)

**Generated question:** Tell me a bit more about your background.

**Candidate answer (input):** Precision is about how many of your positive predictions were actually correct, recall is about how many actual positives you caught. You'd optimize precision when false positives are costly, like spam filtering.

**Observed evaluation:** clarity=4/5, correctness=3/5, confidence=3/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 4, "correctness": 3, "confidence": 3, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 7: Behavioral (General)

**Generated question:** Tell me a bit more about your background.

**Candidate answer (input):** In my last group project a teammate wanted to use a NoSQL database for clearly relational data. I proposed we prototype both in an afternoon and compare query complexity, which showed SQL was simpler for our joins, and he agreed to switch.

**Observed evaluation:** clarity=3/5, correctness=2/5, confidence=4/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 3, "correctness": 2, "confidence": 4, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 8: Behavioral (General)

**Generated question:** Tell me a bit more about your background.

**Candidate answer (input):** Once a teammate disagreed with me and eventually we just... did what the manager said I guess.

**Observed evaluation:** clarity=5/5, correctness=4/5, confidence=4/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 5, "correctness": 4, "confidence": 4, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 9: Technical (Web Development)

**Generated question:** Tell me a bit more about your background.

**Candidate answer (input):** CORS is enforced by the browser to stop a malicious site from making authenticated requests to another origin on your behalf; the server opts in via Access-Control-Allow-Origin headers.

**Observed evaluation:** clarity=4/5, correctness=2/5, confidence=5/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 4, "correctness": 2, "confidence": 5, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---

## Test 10: HR (General)

**Generated question:** Tell me what a great manager looks like to you.

**Candidate answer (input):** Success in 90 days means I've shipped at least one feature end-to-end, built relationships with my immediate team, and know our codebase well enough to review PRs confidently.

**Observed evaluation:** clarity=3/5, correctness=2/5, confidence=4/5

**Observed feedback comment:** Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident.

<details><summary>Raw CoT reasoning (observed)</summary>

```
Step 1 - Clarity: The answer follows a logical order and stays on topic.
Step 2 - Correctness: Covers the core idea, though it could go one level deeper.
Step 3 - Confidence: Reads as reasonably decisive, few hedging words.
Step 4 - Combining the above into scores.
{"clarity": 3, "correctness": 2, "confidence": 4, "overall_comment": "Good structure and mostly accurate; add one more layer of detail and drop the hedging to sound more confident."}
```
</details>

---
