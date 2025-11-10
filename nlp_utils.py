import re
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Download NLTK resources if not present
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Initialize tools
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
spell = SpellChecker()
vectorizer = TfidfVectorizer()

def preprocess_text(text):
    """
    Enhanced text preprocessing: lowercase, remove punctuation, lemmatize, remove stop words.
    Handles both strings and lists by joining lists into strings.
    Improved to handle numbers, special chars, contractions, spell correction, and synonym expansion.
    """
    if isinstance(text, list):
        text = ' '.join(str(t) for t in text)
    # Lowercase
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
    # Spell correction disabled for performance
    # tokens = text.split()
    # corrected_tokens = [spell.correction(word) if spell.correction(word) else word for word in tokens]
    # text = ' '.join(corrected_tokens)
    tokens = text.split()
    corrected_tokens = tokens  # No correction
    # Synonym expansion disabled for performance - can re-enable if needed
    # expanded_tokens = []
    # for word in corrected_tokens:
    #     expanded_tokens.append(word)
    #     synsets = wordnet.synsets(word)
    #     if synsets:
    #         synonyms = set()
    #         for syn in synsets[0].lemmas()[:1]:  # Limit to 1 synonym per word
    #             synonyms.add(syn.name().lower())
    #         expanded_tokens.extend(list(synonyms))
    # Lemmatize, remove stop words
    tokens = [lemmatizer.lemmatize(word) for word in corrected_tokens if word not in stop_words and len(word) > 1]
    return ' '.join(tokens)

def semantic_similarity(query, corpus, threshold=0.3, precomputed_matrix=None, precomputed_corpus=None):
    """
    Compute TF-IDF cosine similarity between query and corpus sentences.
    If precomputed_matrix and precomputed_corpus are provided and match corpus, use them to avoid refitting.
    Returns the most similar sentence and similarity score if above threshold.
    """
    if not corpus:
        return None, 0.0

    if precomputed_matrix is not None and precomputed_corpus == corpus:
        # Use precomputed matrix
        processed_query = preprocess_text(query)
        query_vector = vectorizer.transform([processed_query])
        cosine_similarities = cosine_similarity(query_vector, precomputed_matrix).flatten()
    else:
        # Fit new vectorizer
        processed_texts = [preprocess_text(query)] + [preprocess_text(sent) for sent in corpus]
        tfidf_matrix = vectorizer.fit_transform(processed_texts)
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Find best match
    best_idx = np.argmax(cosine_similarities)
    best_score = cosine_similarities[best_idx]

    if best_score >= threshold:
        return corpus[best_idx], best_score
    return None, 0.0

def fuzzy_match(query, corpus, threshold=80):
    """
    Compute fuzzy string similarity between query and corpus.
    Returns the most similar sentence and score if above threshold.
    """
    from fuzzywuzzy import fuzz
    best_match = None
    best_score = 0.0
    for sent in corpus:
        score = fuzz.token_sort_ratio(query.lower(), sent.lower())
        if score > best_score:
            best_score = score
            best_match = sent
    if best_score >= threshold:
        return best_match, best_score / 100.0  # Normalize to 0-1
    return None, 0.0

def classify_intent(query):
    """
    Simple keyword-based intent classification.
    Returns intent: 'location', 'contact', 'faq', 'info', or 'unknown'.
    """
    query_lower = query.lower()
    if any(word in query_lower for word in ['where', 'location', 'find', 'room', 'office', 'building']):
        return 'location'
    elif any(word in query_lower for word in ['email', 'contact', 'mail', 'phone', 'reach', 'call']):
        return 'contact'
    elif any(word in query_lower for word in ['what', 'how', 'tell', 'explain', 'info']):
        return 'info'
    elif any(word in query_lower for word in ['faq', 'question', 'answer']):
        return 'faq'
    return 'unknown'


