import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download NLTK resources if not present
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Initialize NLTK tools
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    """
    Enhanced text preprocessing: lowercase, remove punctuation, lemmatize, remove stop words.
    Handles both strings and lists by joining lists into strings.
    Improved to handle numbers, special chars, and contractions.
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
    # Tokenize, lemmatize, remove stop words
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and len(word) > 1]
    return ' '.join(tokens)

def semantic_similarity(query, corpus, threshold=0.6):
    """
    Compute Jaccard similarity between query and a list of corpus sentences.
    Returns the most similar sentence and similarity score if above threshold.
    """
    processed_query = preprocess_text(query)
    query_tokens = set(processed_query.split())

    best_match = None
    best_score = 0.0

    for sent in corpus:
        processed_sent = preprocess_text(sent)
        sent_tokens = set(processed_sent.split())
        intersection = query_tokens.intersection(sent_tokens)
        union = query_tokens.union(sent_tokens)
        if union:
            score = len(intersection) / len(union)
        else:
            score = 0.0
        if score > best_score:
            best_score = score
            best_match = sent

    if best_score >= threshold:
        return best_match, best_score
    return None, 0.0


