# TODO: Optimize Chatbot Response Time

## Completed
- [x] Add missing JSON editor routes (/admin/load_json, /admin/save_json, /admin/upload_json) to app.py for admin JSON editing functionality.

## In Progress
- [ ] Disable spell correction in preprocess_text (nlp_utils.py).
- [ ] Implement precompute_tfidf in chatbot.py to precompute TF-IDF matrix for all rules' questions.
- [ ] Modify semantic_similarity to use precomputed matrix when corpus matches precomputed questions.
- [ ] Run test_nlp.py to verify average response time <5 seconds.

## Pending
- [ ] If time not under 5s, explore further optimizations like caching preprocessed texts.
- [ ] Set up Railway persistent volume for JSON file persistence on Railway (read-only file system workaround).

## Remove JSON Editor
- [x] Remove JSON editor routes from app.py (/admin/json_editor, /admin/load_json, /admin/save_json, /admin/upload_json)
- [x] Remove JSON Editor card from admin_dashboard.html
- [x] Delete htdocs/admin_json_editor.html
- [ ] Update TODO.md to remove JSON editor task
