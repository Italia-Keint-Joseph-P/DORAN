"""
optimized_nlp_utils.py
Lightweight, Railway-friendly NLP utilities for rule-based chatbots.

Features
- Precompute & cache TF-IDF vectors at startup (no per-request retrain)
- Consistent preprocessing (lemmatization) using NLTK
- Spell correction used only as a fallback
- Hierarchical matching pipeline: keyword rules -> TF-IDF -> spell-corrected TF-IDF -> fuzzy fallback
- Small memory footprint; compatible with packages you listed (NLTK, scikit-learn, spellchecker, pandas)
- Optional helpers to load corpus from SQLAlchemy-style sessions or plain lists

API (short):
- NLU = NLUEngine()
- NLU.init_from_list(corpus_list)  # corpus_list: list of dicts or tuples (id, question, answer) or strings
- reply = NLU.get_reply(query, user_meta=None)

"""

from typing import List, Tuple, Optional, Dict, Any
import re
import os
import pickle
import math
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher

# Ensure essential NLTK data
for resource in ("stopwords", "wordnet", "omw-1.4", "punkt"):
    try:
        nltk.data.find(f"corpora/{resource}")
    except LookupError:
        nltk.download(resource)

STOP_WORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()
SPELL = SpellChecker()

# Defaults
DEFAULT_TFIDF_PARAMS = {
    "ngram_range": (1, 2),
    "min_df": 1,
    "max_df": 0.95,
}
DEFAULT_SIMILARITY_THRESHOLD = 0.38
DEFAULT_KEYWORD_THRESHOLD = 0.5


def _simple_tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())


def preprocess_text(text: str, remove_stopwords: bool = True) -> str:
    """Lowercase -> tokenize -> lemmatize -> remove stopwords -> join"""
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    tokens = _simple_tokenize(text)
    processed = []
    for t in tokens:
        if remove_stopwords and t in STOP_WORDS:
            continue
        if len(t) <= 1:
            continue
        lemma = LEMMATIZER.lemmatize(t)
        processed.append(lemma)
    return " ".join(processed)


# -------------------------------------------------------------------------
# ⭐ ADDED FUNCTION: classify_intent (required by chatbot.py)
# -------------------------------------------------------------------------
def classify_intent(text: str) -> str:
    text = text.lower()

    # Location-related messages
    if any(w in text for w in [
        "where", "location", "locate", "map", "room", "floor", "building"
    ]):
        return "location"

    # Contact / email / phone
    if any(w in text for w in [
        "email", "gmail", "contact", "phone", "number", "call"
    ]):
        return "contact"

    # Hours / time / schedule
    if any(w in text for w in [
        "open", "close", "time", "hours", "schedule"
    ]):
        return "hours"

    # People / names / staff
    if any(w in text for w in [
        "who", "person", "teacher", "staff", "professor"
    ]):
        return "person"

    # FAQ-style What/How queries
    if any(w in text for w in [
        "what", "how", "when", "why"
    ]):
        return "faq"

    return "unknown"


class NLUEngine:
    """Encapsulates an optimized lightweight pipeline."""

    def __init__(self, min_similarity=0.38, fuzzy_threshold=0.45):
        self.min_similarity = min_similarity
        self.fuzzy_threshold = fuzzy_threshold
        self.corpus: List[Dict[str, Any]] = []
        self.processed_questions: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.keyword_rules: Dict[str, str] = {}

        self.intent_patterns = {
            "location": ["where", "location", "map", "directions", "room", "floor"],
            "contact": ["email", "phone", "call", "contact", "reach"],
            "hours": ["open", "close", "hours", "time"],
        }

    # -------------------- corpus loading --------------------
    def init_from_list(self, items: List[Any]):
        normalized = []
        for i, x in enumerate(items):
            if isinstance(x, str):
                normalized.append({"id": i, "question": x, "answer": x, "meta": {}})
            elif isinstance(x, (list, tuple)) and len(x) >= 2:
                normalized.append({"id": i, "question": x[0], "answer": x[1], "meta": {}})
            elif isinstance(x, dict):
                q = x.get("question") or x.get("q") or x.get("text")
                a = x.get("answer") or x.get("a") or x.get("reply") or ""
                normalized.append({"id": x.get("id", i), "question": q, "answer": a, "meta": x.get("meta", {})})
            else:
                normalized.append({"id": i, "question": str(x), "answer": str(x), "meta": {}})

        self.corpus = normalized
        self._prepare_vectorizer()

    def init_from_sqlalchemy(self, db_session, table_query_fn):
        items = []
        for row in table_query_fn(db_session):
            q = getattr(row, "question", None) or getattr(row, "q", None) or getattr(row, "text", None)
            a = getattr(row, "answer", None) or getattr(row, "a", None) or getattr(row, "reply", None) or ""
            rid = getattr(row, "id", None) or getattr(row, "pk", None) or None
            items.append({"id": rid, "question": q, "answer": a, "meta": {}})
        self.init_from_list(items)

    # -------------------- vectorizer --------------------
    def _prepare_vectorizer(self, tfidf_params: Dict = None):
        if tfidf_params is None:
            tfidf_params = DEFAULT_TFIDF_PARAMS
        self.processed_questions = [preprocess_text(q["question"]) for q in self.corpus]
        self.vectorizer = TfidfVectorizer(**tfidf_params)
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.processed_questions)
        except ValueError:
            self.tfidf_matrix = None

    # -------------------- matching --------------------
    def _keyword_lookup(self, query: str) -> Optional[str]:
        q = query.lower()
        for k, v in self.keyword_rules.items():
            if k in q:
                return v
        for intent, patterns in self.intent_patterns.items():
            if any(p in q for p in patterns):
                pass
        return None

    def _tfidf_match(self, processed_query: str, top_k: int = 1) -> Tuple[Optional[int], float]:
        if self.vectorizer is None or self.tfidf_matrix is None:
            return None, 0.0
        q_vec = self.vectorizer.transform([processed_query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        if sims.size == 0:
            return None, 0.0
        best_idx = int(sims.argmax())
        best_score = float(sims[best_idx])
        return best_idx, best_score

    def _spell_correct_query(self, query: str) -> str:
        tokens = _simple_tokenize(query)
        corpus_vocab = set()
        for s in self.processed_questions:
            corpus_vocab.update(s.split())

        corrected = []
        for t in tokens:
            if len(t) <= 2:
                corrected.append(t)
                continue
            if t in corpus_vocab:
                corrected.append(t)
                continue
            cand = SPELL.correction(t)
            if not cand or cand == t:
                corrected.append(t)
                continue
            ratio = SequenceMatcher(None, t, cand).ratio()
            if ratio < 0.6:
                corrected.append(t)
            else:
                corrected.append(cand)
        return " ".join(corrected)

    def _fuzzy_fallback(self, query: str) -> Tuple[Optional[int], float]:
        qproc = preprocess_text(query)
        best_idx = None
        best_score = 0.0
        for i, p in enumerate(self.processed_questions):
            r = SequenceMatcher(None, qproc, p).ratio()
            if r > best_score:
                best_score = r
                best_idx = i
        return best_idx, best_score

    # -------------------- main reply --------------------
    def get_reply(self, query: str, top_k: int = 1, return_confidence: bool = False) -> Any:
        if not query or not query.strip():
            return ("", 0.0) if return_confidence else ""

        kw = self._keyword_lookup(query)
        if kw:
            return (kw, 1.0) if return_confidence else kw

        pquery = preprocess_text(query)
        idx, score = self._tfidf_match(pquery)
        if idx is not None and score >= self.min_similarity:
            reply = self.corpus[idx]["answer"]
            return (reply, score) if return_confidence else reply

        corrected = self._spell_correct_query(query)
        if corrected != query:
            pquery2 = preprocess_text(corrected)
            idx2, score2 = self._tfidf_match(pquery2)
            if idx2 is not None and score2 >= self.min_similarity:
                reply = self.corpus[idx2]["answer"]
                return (reply, score2) if return_confidence else reply

        fidx, fscore = self._fuzzy_fallback(query)
        if fidx is not None and fscore >= self.fuzzy_threshold:
            reply = self.corpus[fidx]["answer"]
            conf = max(0.0, min(1.0, (fscore - self.fuzzy_threshold) / (1 - self.fuzzy_threshold)))
            return (reply, conf) if return_confidence else reply

        unknown_msg = "Sorry, I didn't understand. Can you rephrase or ask differently?"
        return (unknown_msg, 0.0) if return_confidence else unknown_msg

    def preprocess(self, text: str) -> str:
        return preprocess_text(text)

    def match_rule(self, processed_query: str, rules: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], float]:
        # Temporarily set corpus to rules for matching, flattening multiple questions
        original_corpus = self.corpus[:]
        corpus = []
        rule_index = []
        for i, r in enumerate(rules):
            questions = r.get("questions") or [r.get("question") or r.get("q") or ""]
            if isinstance(questions, str):
                questions = [questions]
            for q in questions:
                corpus.append({"id": r.get("id"), "question": q, "answer": r.get("response", r.get("answer", "")), "meta": {}})
                rule_index.append(i)
        self.corpus = corpus
        self._prepare_vectorizer()

        idx, score = self._tfidf_match(processed_query)
        if idx is not None and score >= self.min_similarity:
            rule = rules[rule_index[idx]]
            # Restore original corpus
            self.corpus = original_corpus
            self._prepare_vectorizer()
            return rule, score

        # Spell correction
        corrected = self._spell_correct_query(processed_query)
        if corrected != processed_query:
            pquery2 = preprocess_text(corrected)
            idx2, score2 = self._tfidf_match(pquery2)
            if idx2 is not None and score2 >= self.min_similarity:
                rule = rules[rule_index[idx2]]
                self.corpus = original_corpus
                self._prepare_vectorizer()
                return rule, score2

        # Fuzzy fallback
        fidx, fscore = self._fuzzy_fallback(processed_query)
        if fidx is not None and fscore >= self.fuzzy_threshold:
            rule = rules[rule_index[fidx]]
            self.corpus = original_corpus
            self._prepare_vectorizer()
            return rule, fscore

        # Restore original corpus
        self.corpus = original_corpus
        self._prepare_vectorizer()
        return None, 0.0

    def add_keyword_rule(self, keyword: str, reply: str):
        self.keyword_rules[keyword.lower()] = reply


USAGE = '''
from optimized_nlp_utils import NLUEngine
corpus = [
    ("Where is the registrar office?", "The registrar is in Building A, 2nd floor."),
    ("What's the email for admissions?", "admissions@example.edu"),
]
nlu = NLUEngine()
nlu.init_from_list(corpus)
print(nlu.get_reply("where is registrar"))
print(nlu.get_reply("what's admission email"))
'''
