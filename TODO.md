# TODO: Improve Chatbot NLP Accuracy

## Overview
This plan upgrades the chatbot's NLP to use TF-IDF cosine similarity, enhanced preprocessing, fuzzy matching, intent classification, context awareness, and better scoring/thresholds. All changes are lightweight for Railway free tier compatibility.

## Steps
- [x] Update requirements.txt: Add scikit-learn, fuzzywuzzy, pyspellchecker
- [x] Enhance nlp_utils.py: Replace Jaccard with TF-IDF cosine similarity, add spell correction and synonym expansion to preprocess_text
- [x] Update chatbot.py: Integrate new similarity, add fuzzy matching, implement keyword-based intent classification, add context tracking, improve thresholds/scoring
- [x] Expand test_nlp.py: Add evaluation metrics (precision, recall) and more diverse test queries
- [x] Install dependencies and test locally
- [x] Run tests to compare old vs. new accuracy
- [ ] Deploy and monitor on Railway (check RAM/storage usage)
- [ ] Optimize if needed (e.g., reduce TF-IDF vector size for performance)
