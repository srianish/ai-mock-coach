"""
Retrieval-Augmented Generation over the curated interview question bank.

Pipeline:
  data/question_bank.json --(embed)--> Chroma vector collection
  user query (role/domain/context) --(embed)--> nearest-neighbour search
  --> top-k real sample questions returned as grounding context for the
      question-generation prompt (see coach/prompts.build_question_prompt)

Two embedding backends are supported so the RAG pipeline works both with
a real API key (production) and fully offline (demo/testing):
  * OpenAIEmbedder    - text-embedding-3-small via the OpenAI API
  * LocalTfidfEmbedder - scikit-learn TF-IDF fitted on the question bank,
                         used automatically when no API key is configured
"""
import json
import os
from typing import List

import chromadb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from coach.config import Config

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "question_bank.json")


class OpenAIEmbedder:
    """Embeds text using the OpenAI embeddings API."""

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self._model = Config.OPENAI_EMBED_MODEL

    def embed(self, texts: List[str]) -> List[List[float]]:
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]


class LocalTfidfEmbedder:
    """
    Fully offline fallback embedder. Fits a TF-IDF vectorizer over the
    question bank corpus once, then projects any query into the same
    space. Good enough for nearest-neighbour retrieval in demo mode
    without any network access or model download.
    """

    def __init__(self, corpus: List[str]):
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._corpus_matrix = self._vectorizer.fit_transform(corpus)

    def embed(self, texts: List[str]) -> List[List[float]]:
        matrix = self._vectorizer.transform(texts)
        return matrix.toarray().tolist()


class QuestionBankRAG:
    """Wraps a Chroma collection holding the embedded question bank."""

    def __init__(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            self.questions = json.load(f)

        corpus = [q["question"] for q in self.questions]

        if Config.has_real_credentials() and Config.effective_provider() == "openai":
            self.embedder = OpenAIEmbedder()
            self.mode = "openai"
        else:
            self.embedder = LocalTfidfEmbedder(corpus)
            self.mode = "local-tfidf"

        self._client = chromadb.EphemeralClient()
        # embedding_function=None: we always supply our own vectors below,
        # so Chroma never tries to download a default embedding model.
        self._collection = self._client.get_or_create_collection(
            name="interview_questions", embedding_function=None
        )
        self._index_corpus(corpus)

    def _index_corpus(self, corpus: List[str]) -> None:
        embeddings = self.embedder.embed(corpus)
        ids = [q["id"] for q in self.questions]
        metadatas = [{"role": q["role"], "domain": q["domain"]} for q in self.questions]
        self._collection.add(
            ids=ids, embeddings=embeddings, documents=corpus, metadatas=metadatas
        )

    def retrieve(self, role: str, domain: str, context: str, top_k: int = 3) -> List[str]:
        """
        Return the top_k most relevant sample questions for this
        role/domain/context, used to ground question generation.
        """
        query = f"Role: {role}. Domain: {domain}. Context: {context}"
        query_embedding = self.embedder.embed([query])[0]

        where = {"role": role} if role else None
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, len(self.questions)),
            where=where,
        )
        docs = result.get("documents", [[]])[0]
        return docs
