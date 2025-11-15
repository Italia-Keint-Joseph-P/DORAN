# TODO: Improve NLP Accuracy for Query Matching

- [x] Enhance fuzzy_match in nlp_utils.py with Dice similarity and n-grams for better handling of typos and variations
- [x] Add optional lemmatization to preprocess_text for improved word normalization
- [x] Increase rule limits in chatbot.py (e.g., from 20/5/50 to 50/20/100) for broader matching scope
- [x] Fine-tune thresholds in get_response based on testing (e.g., lower base_threshold for better matches)
- [x] Improve intent classification in nlp_utils.py with more keywords and patterns
- [x] Reintroduce TF-IDF for semantic similarity in semantic_similarity function
- [x] Fix get_location_rules to load from MySQL Location table instead of JSON
- [x] Fix KeyError for 'person' intent by adding it to threshold dictionary
