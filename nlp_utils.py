import re
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# -----------------------------
# NLTK setup
# -----------------------------
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# -----------------------------
# Initialize tools
# -----------------------------
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
spell = SpellChecker()

# ✅ Global TF-IDF Vectorizer (restored)
# This ensures compatibility with any imports that expect `vectorizer` from this module.
# It's okay to have it here as long as you fit() it explicitly in the chatbot.
vectorizer = TfidfVectorizer()

# -----------------------------
# Text preprocessing
# -----------------------------
def preprocess_text(text):
    """
    Simplified text preprocessing: lowercase, remove punctuation, lemmatize, remove stop words.
    Handles both strings and lists by joining lists into strings.
    Disabled spell correction and synonym expansion for performance.
    """
    if isinstance(text, list):
        text = ' '.join(str(t) for t in text)

    text = text.lower()

    # Expand contractions
    text = re.sub(r"can't", "cannot", text)
    text = re.sub(r"won't", "will not", text)
    text = re.sub(r"n't", " not", text)
    text = re.sub(r"'re", " are", text)
    text = re.sub(r"'ve", " have", text)
    text = re.sub(r"'ll", " will", text)
    text = re.sub(r"'d", " would", text)
    text = re.sub(r"'m", " am", text)

    # Remove punctuation but keep numbers and hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = text.split()

    # Lemmatize and remove stop words
    tokens = [
        lemmatizer.lemmatize(word)
        for word in tokens
        if word not in stop_words and len(word) > 1
    ]

    return ' '.join(tokens)

# -----------------------------
# Semantic similarity
# -----------------------------
def semantic_similarity(
    query,
    corpus,
    threshold=0.3,
    precomputed_matrix=None,
    precomputed_corpus=None,
    vectorizer=None
):
    """
    Compute TF-IDF cosine similarity between query and corpus sentences.
    If precomputed_matrix, precomputed_corpus, and vectorizer are provided and match the corpus,
    use them to avoid refitting.
    """
    if not corpus:
        return None, 0.0

    if (
        precomputed_matrix is not None
        and precomputed_corpus == corpus
        and vectorizer is not None
    ):
        processed_query = preprocess_text(query)
        query_vector = vectorizer.transform([processed_query])
        cosine_similarities = cosine_similarity(query_vector, precomputed_matrix).flatten()
    else:
        local_vectorizer = TfidfVectorizer()
        processed_texts = [preprocess_text(query)] + [preprocess_text(sent) for sent in corpus]
        tfidf_matrix = local_vectorizer.fit_transform(processed_texts)
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    best_idx = np.argmax(cosine_similarities)
    best_score = cosine_similarities[best_idx]

    if best_score >= threshold:
        return corpus[best_idx], best_score
    return None, 0.0

# -----------------------------
# Fuzzy match
# -----------------------------
def fuzzy_match(query, corpus, threshold=80):
    """
    Compute fuzzy string similarity between query and corpus using multiple methods.
    Returns the most similar sentence and score if above threshold.
    """
    from fuzzywuzzy import fuzz
    best_match = None
    best_score = 0.0
    query_lower = query.lower()

    for sent in corpus:
        sent_lower = sent.lower()
        ratio_score = fuzz.ratio(query_lower, sent_lower)
        token_sort_score = fuzz.token_sort_ratio(query_lower, sent_lower)
        token_set_score = fuzz.token_set_ratio(query_lower, sent_lower)
        score = max(ratio_score, token_sort_score, token_set_score)

        if score > best_score:
            best_score = score
            best_match = sent

    if best_score >= threshold:
        return best_match, best_score / 100.0
    return None, 0.0

# -----------------------------
# Jaccard similarity
# -----------------------------
def jaccard_similarity(query, corpus, threshold=0.3):
    """
    Compute Jaccard similarity between query and corpus sentences.
    """
    def jaccard(set1, set2):
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    query_tokens = set(preprocess_text(query).split())
    best_match = None
    best_score = 0.0

    for sent in corpus:
        sent_tokens = set(preprocess_text(sent).split())
        score = jaccard(query_tokens, sent_tokens)
        if score > best_score:
            best_score = score
            best_match = sent

    if best_score >= threshold:
        return best_match, best_score
    return None, 0.0

# -----------------------------
# Intent classification
# -----------------------------
def classify_intent(query):
    """
    Enhanced keyword-based intent classification with stricter specificity and ordering.
    Prioritizes specific intents and reduces false positives with more precise keywords.
    """
    query_lower = query.lower()

    # Check for FAQ first (most specific)
    if any(word in query_lower for word in ['faq', 'frequently asked', 'question']):
        return 'faq'

    # Check for enrollment-specific queries (more specific)
    if any(word in query_lower for word in [
        'enrollment', 'enrol', 'admission', 'requirements', 'apply', 'tuition',
        'fee', 'cost', 'payment', 'scholarship', 'deadline', 'application'
    ]):
        return 'faq'

    # Check for contact/email queries (expanded and more specific)
    if any(word in query_lower for word in [
        'email', 'contact', 'mail', 'phone', 'reach', 'call', 'address', 'message',
        'send', 'communicate', 'inquire', 'ask', 'speak to', 'talk to'
    ]):
        return 'contact'

    # Check for location queries (more specific keywords, added building/room numbers)
    if any(word in query_lower for word in [
        'where', 'location', 'find', 'room', 'office', 'building', 'lab', 'library',
        'classroom', 'map', 'floor', 'wing', 'hall', 'center', 'department',
        'c13', 'j18', 'e3', 'ict', 'soict', 'faculty', 'auditorium', 'gym'
    ]):
        return 'location'

    # Check for info queries (more specific phrases)
    if any(phrase in query_lower for phrase in [
        'tell me about', 'who is', 'what are', 'what is', 'how to', 'how do',
        'show me', 'explain', 'describe', 'information about', 'details on',
        'about the', 'regarding', 'concerning'
    ]):
        return 'info'

    # Default to unknown for better precision
    return 'unknown'
