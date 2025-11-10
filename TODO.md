# TODO: Optimize Chatbot Response Time

## Completed
- [x] Analyze bottlenecks: TF-IDF fitting per query and spell correction in preprocessing.

## In Progress
- [ ] Disable spell correction in preprocess_text (nlp_utils.py).
- [ ] Implement precompute_tfidf in chatbot.py to precompute TF-IDF matrix for all rules' questions.
- [ ] Modify semantic_similarity to use precomputed matrix when corpus matches precomputed questions.
- [ ] Run test_nlp.py to verify average response time <5 seconds.

## Pending
- [ ] If time not under 5s, explore further optimizations like caching preprocessed texts.
