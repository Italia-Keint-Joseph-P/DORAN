import logging
import re
from uuid import uuid4
import mysql.connector
import json
import os

def simple_tokenize(text):
    """
    Simple tokenizer that converts text to lowercase and splits on non-alphanumeric characters, but keeps hyphens in words.
    """
    return re.findall(r'\b[\w-]+\b', text.lower())

import database.email_directory as email_directory
import database.user_database.rule_utils as rule_utils

# ✅ FIXED imports (no more vectorizer import from nlp_utils)
from nlp_utils import semantic_similarity, preprocess_text, fuzzy_match, classify_intent, vectorizer, cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from update_chatbot import ChatbotDB


class Chatbot:
    def __init__(self):
        # Initialize database connection (may fail, but continue with local files)
        try:
            self.db = ChatbotDB()
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            self.db = None

        # Initialize rules attributes from database
        self.rules = self.get_rules()
        self.guest_rules = self.get_guest_rules()
        self.location_rules = self.get_location_rules()
        self.visual_rules = self.get_visual_rules()
        self.faqs = self.get_faqs()

        # Load chatbot answer images from locations (for backward compatibility)
        self.chatbot_images = []
        for rule in self.location_rules:
            if rule.get('questions'):
                image_entry = {
                    "id": rule.get("id", ""),
                    "questions": rule.get("questions", []),
                    "url": rule.get("url", ""),
                    "description": rule.get("description", "")
                }
                self.chatbot_images.append(image_entry)

        # Email keywords for triggering email search
        self.email_keywords = ["email", "contact", "mail", "reach", "address", "send", "message"]

        # Initialize fallback tracking attributes
        self.consecutive_fallbacks = 0
        self.fallback_index = 0
        self.fallback_responses = [
            "I'm sorry, I didn't quite get that. Could you please rephrase?",
            "Hmm, I'm not sure I understand. Can you try asking differently?",
            "Apologies, I couldn't find an answer. Could you ask something else?"
        ]

        # Initialize context tracking for conversation history
        self.conversation_history = {}

        # Precompute TF-IDF for performance
        self.precompute_tfidf()

        # Cache email directory for faster lookups
        self.cached_emails = self.cache_emails()

    def precompute_tfidf(self):
        """
        Precompute TF-IDF vectors for all rules to improve performance.
        Now includes proper handling of all data sources including locations and visuals.
        """
        from nlp_utils import preprocess_text, vectorizer
        all_questions = []
        
        # Collect questions from all rule sources
        all_rule_sources = self.rules + self.guest_rules + self.location_rules + self.visual_rules
        
        for rule in all_rule_sources:
            # Handle different question formats
            questions = rule.get('questions', []) or rule.get('question', '')
            
            if isinstance(questions, str):
                if questions.strip():  # Only add non-empty strings
                    questions = [questions]
                else:
                    questions = []
            
            flattened_questions = []
            for q in questions:
                if isinstance(q, str) and q.strip():
                    flattened_questions.append(q)
                elif isinstance(q, list):
                    flattened_questions.extend([item for item in q if isinstance(item, str) and item.strip()])
            
            all_questions.extend(flattened_questions)
        
        # Add FAQ questions
        for faq in self.faqs:
            question = faq.get('question', '')
            if question and question.strip():
                all_questions.append(question)
        
        # Preprocess all questions
        processed_questions = [preprocess_text(q) for q in all_questions if q]
        
        # Fit vectorizer on all processed questions
        if processed_questions:
            self.tfidf_matrix = vectorizer.fit_transform(processed_questions)
            self.tfidf_corpus = all_questions
        else:
            self.tfidf_matrix = None
            self.tfidf_corpus = []
        
        logging.info(f"Precomputed TF-IDF for {len(all_questions)} questions from all data sources")

    def cache_emails(self):
        """
        Cache the email directory for faster lookups.
        """
        try:
            return email_directory.get_all_emails()
        except Exception as e:
            logging.error(f"Error caching emails: {e}")
            return []

    def recompute_embeddings(self):
        """
        No longer needed with NLTK-based similarity.
        """
        pass

    def search_emails(self, user_input):
        """
        Search the email directory for entries matching the user input.
        Returns a response string if matches are found, else None.
        """
        tokens = simple_tokenize(user_input.lower())
        has_email_keyword = any(keyword in tokens for keyword in self.email_keywords)

        # Special case for "registrar data" to return full directory
        if "registrar" in tokens and "data" in tokens:
            try:
                all_emails = email_directory.get_all_emails()
            except Exception as e:
                logging.error(f"Error fetching emails: {e}")
                return None
            if not all_emails:
                return None
            response = "Here is the full email directory:\n"
            for entry in all_emails:
                response += f"- {entry['school']}: {entry['email']}\n"
            return response.strip()

        # Get all emails
        try:
            all_emails = email_directory.get_all_emails()
        except Exception as e:
            logging.error(f"Error fetching emails: {e}")
            return None

        # Special case for registrar email
        if "registrar" in tokens:
            for entry in all_emails:
                if 'registrar' in entry['school'].lower():
                    return entry['email']
            return None

        # Find matching schools/positions
        matches = []
        for entry in all_emails:
            school_lower = entry['school'].lower()
            if any(token in school_lower for token in tokens):
                matches.append(entry)

        if not matches:
            return None

        # Format response
        response = "Here are the relevant email contacts:\n"
        for match in matches:
            if match['school'].lower() == 'registrar':
                response += f"- Registrar: {match['email']}\n"
            else:
                response += f"- {match['school']}: {match['email']}\n"
        return response.strip()

    def get_rules(self):
        # Load user rules from MySQL database
        try:
            db_rules = self.db.get_user_rules()
            rules = []
            for rule in db_rules:
                rule_obj = {
                    "category": rule.get("category", ""),
                    "question": rule.get("question", ""),
                    "response": rule.get("answer", ""),
                    "id": rule.get("id", "")
                }
                rules.append(rule_obj)
            return rules
        except Exception as e:
            logging.error(f"Error loading user rules from DB: {e}")
            return []

    def get_guest_rules(self):
        # Load guest rules from MySQL database
        try:
            db_rules = self.db.get_guest_rules()
            rules = []
            for rule in db_rules:
                rule_obj = {
                    "category": rule.get("category", ""),
                    "question": rule.get("question", ""),
                    "response": rule.get("answer", ""),
                    "id": rule.get("id", "")
                }
                rules.append(rule_obj)
            return rules
        except Exception as e:
            logging.error(f"Error loading guest rules from DB: {e}")
            return []

    def normalize_keywords(self, keywords):
        """
        Normalize keywords to lowercase, handling both flat lists and nested lists.
        Converts all keywords to strings first to handle mixed types.
        """
        if isinstance(keywords, list):
            if keywords and isinstance(keywords[0], list):
                # Nested: list of keyword sets
                return [[str(k).lower() for k in sublist] for sublist in keywords]
            else:
                # Flat: single list
                return [str(k).lower() for k in keywords]
        return []

    def get_location_rules(self):
        """
        Load location rules from MySQL database.
        The database layer now handles JSON parsing and HTML response construction.
        """
        try:
            # The database layer returns properly formatted location rules
            rules = self.db.get_location_rules()
            return rules
        except Exception as e:
            logging.error(f"Error loading location rules from DB: {e}")
            return []

    def get_visual_rules(self):
        """
        Load visual rules from MySQL database.
        The database layer now handles JSON parsing and HTML response construction.
        """
        try:
            # The database layer returns properly formatted visual rules
            rules = self.db.get_visual_rules()
            return rules
        except Exception as e:
            logging.error(f"Error loading visual rules from DB: {e}")
            return []

    def get_faqs(self):
        # Load FAQs from MySQL database
        try:
            db_faqs = self.db.get_faqs()
            faqs = []
            for faq in db_faqs:
                faq_obj = {
                    "question": faq.get("question", ""),
                    "answer": faq.get("answer", "")
                }
                faqs.append(faq_obj)
            return faqs
        except Exception as e:
            logging.error(f"Error loading FAQs from DB: {e}")
            return []

    def update_context(self, session_id, user_input, response):
        """
        Update conversation history for context awareness.
        """
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append({'query': user_input, 'response': response})
        # Keep only last 10 exchanges to avoid memory bloat
        if len(self.conversation_history[session_id]) > 10:
            self.conversation_history[session_id] = self.conversation_history[session_id][-10:]

    def get_response(self, user_input, user_role=None, session_id=None):
        """
        Generate a response by collecting all matches above threshold and selecting the best overall match.
        Improved with TF-IDF cosine similarity, fuzzy matching, intent classification, context awareness,
        and dynamic thresholds for better accuracy.

        Args:
            user_input (str): The input message from the user.
            user_role (str): The role of the user ('guest' or other).
            session_id (str): Unique session ID for context tracking.

        Returns:
            str: The chatbot's response from rules, info.json, or fallback message.
        """
        if not user_input.strip():
            return "Please type a message to chat with DORAN."

        # Classify intent for dynamic thresholds (increased for better precision)
        intent = classify_intent(user_input)
        base_threshold = {'location': 0.7, 'contact': 0.75, 'faq': 0.8, 'info': 0.75, 'unknown': 0.85}[intent]

        # Preprocess user input
        processed_input = preprocess_text(user_input)
        user_tokens = simple_tokenize(processed_input)

        # Check for email queries first to prioritize over rules
        has_email_keyword = any(keyword in user_tokens for keyword in self.email_keywords)
        if has_email_keyword:
            email_response = self.search_emails(user_input)
            if email_response:
                self.consecutive_fallbacks = 0
                if session_id:
                    self.update_context(session_id, user_input, email_response)
                return self.append_image_to_response(email_response)



        # Collect all potential matches with their scores
        candidates = []  # List of (rule, combined_score, match_type)

        # Determine rules to use based on user role
        if user_role == 'guest':
            rules_to_use = self.guest_rules + self.location_rules + self.visual_rules
        else:
            rules_to_use = self.rules + self.guest_rules + self.location_rules + self.visual_rules

        # TF-IDF cosine similarity for all rules using global precomputed matrix
        if self.tfidf_matrix is not None and len(self.tfidf_corpus) > 0:
            processed_query = preprocess_text(user_input)
            query_vector = vectorizer.transform([processed_query])
            cosine_similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            corpus_idx = 0
            for r in rules_to_use:
                rule_user_type = r.get('user_type', 'both')
                if user_role == 'guest' and rule_user_type == 'user':
                    # Skip user-only rules for guests, but still advance corpus index
                    questions = r.get('questions', []) or r.get('question', '')
                    if isinstance(questions, str):
                        questions = [questions] if questions.strip() else []
                    flattened_questions = []
                    for q in questions:
                        if isinstance(q, str) and q.strip():
                            flattened_questions.append(q)
                        elif isinstance(q, list):
                            flattened_questions.extend([item for item in q if isinstance(item, str) and item.strip()])
                    corpus_idx += len(flattened_questions)
                    continue
                elif user_role != 'guest' and rule_user_type == 'guest':
                    # Skip guest-only rules for users, but still advance corpus index
                    questions = r.get('questions', []) or r.get('question', '')
                    if isinstance(questions, str):
                        questions = [questions] if questions.strip() else []
                    flattened_questions = []
                    for q in questions:
                        if isinstance(q, str) and q.strip():
                            flattened_questions.append(q)
                        elif isinstance(q, list):
                            flattened_questions.extend([item for item in q if isinstance(item, str) and item.strip()])
                    corpus_idx += len(flattened_questions)
                    continue
                
                questions = r.get('questions', []) or r.get('question', '')
                if isinstance(questions, str):
                    questions = [questions] if questions.strip() else []
                
                flattened_questions = []
                for q in questions:
                    if isinstance(q, str) and q.strip():
                        flattened_questions.append(q)
                    elif isinstance(q, list):
                        flattened_questions.extend([item for item in q if isinstance(item, str) and item.strip()])
                
                if flattened_questions:
                    # Get scores for this rule's questions
                    rule_end_idx = corpus_idx + len(flattened_questions)
                    if rule_end_idx <= len(cosine_similarities):
                        tfidf_score = max(cosine_similarities[corpus_idx:rule_end_idx])
                        if tfidf_score >= base_threshold:
                            # Boost for intent match
                            if r.get('category') == intent or (intent == 'location' and r.get('category') in ['locations', 'visuals']):
                                tfidf_score += 0.1
                            # Boost for exact keyword matches - stricter criteria
                            exact_match_boost = 0.0
                            user_words = set(simple_tokenize(user_input.lower()))
                            for q in flattened_questions:
                                q_words = set(simple_tokenize(q.lower()))
                                common_words = user_words.intersection(q_words)
                                # Boost if at least 3 common words or 60% overlap
                                if len(common_words) >= 3 or (len(common_words) / max(len(user_words), len(q_words))) >= 0.6:
                                    exact_match_boost = 0.15  # Increased boost
                                    break
                            tfidf_score += exact_match_boost
                            candidates.append((r, tfidf_score, 'tfidf'))
                    
                    corpus_idx = rule_end_idx
                else:
                    # No questions for this rule, don't advance index
                    pass

        # Jaccard similarity for additional matching
        for r in rules_to_use:
            rule_user_type = r.get('user_type', 'both')
            if user_role == 'guest' and rule_user_type == 'user':
                continue
            elif user_role != 'guest' and rule_user_type == 'guest':
                continue
            questions = r.get('questions', []) or r.get('question', '')
            if isinstance(questions, str):
                questions = [questions]
            flattened_questions = []
            for q in questions:
                if isinstance(q, str):
                    flattened_questions.append(q)
                elif isinstance(q, list):
                    flattened_questions.extend(q)
            if flattened_questions:
                from nlp_utils import jaccard_similarity
                _, jaccard_score = jaccard_similarity(user_input, flattened_questions, threshold=0.0)
                if jaccard_score >= base_threshold:
                    # Boost for intent match
                    if r.get('category') == intent or (intent == 'location' and r.get('category') in ['locations', 'visuals']):
                        jaccard_score += 0.1
                    # Boost for exact keyword matches
                    exact_match_boost = 0.0
                    user_words = set(simple_tokenize(user_input.lower()))
                    for q in flattened_questions:
                        q_words = set(simple_tokenize(q.lower()))
                        common_words = user_words.intersection(q_words)
                        if len(common_words) >= 3 or (len(common_words) / max(len(user_words), len(q_words))) >= 0.6:
                            exact_match_boost = 0.15  # Increased boost
                            break
                    jaccard_score += exact_match_boost
                    candidates.append((r, jaccard_score, 'jaccard'))

        # Fuzzy matching as fallback for typos
        if not candidates:
            for r in rules_to_use:
                questions = r.get('questions', []) or r.get('question', '')
                if isinstance(questions, str):
                    questions = [questions]
                flattened_questions = []
                for q in questions:
                    if isinstance(q, str):
                        flattened_questions.append(q)
                    elif isinstance(q, list):
                        flattened_questions.extend(q)
                if flattened_questions:
                    _, fuzzy_score = fuzzy_match(user_input, flattened_questions, threshold=70)
                    if fuzzy_score >= 0.7:  # Normalized threshold
                        candidates.append((r, fuzzy_score, 'fuzzy'))

        # FAQs TF-IDF similarity - using precomputed matrix for consistency
        if self.faqs and self.tfidf_matrix is not None and len(self.tfidf_corpus) > 0:
            faq_questions = [item['question'] for item in self.faqs]
            faq_answers = [item['answer'] for item in self.faqs]

            # Find FAQ questions in the precomputed corpus and get their scores
            faq_candidates = []
            for idx, corpus_question in enumerate(self.tfidf_corpus):
                if corpus_question in faq_questions:
                    faq_idx = faq_questions.index(corpus_question)
                    # Get the score for this FAQ question from the precomputed matrix
                    processed_query = preprocess_text(user_input)
                    query_vector = vectorizer.transform([processed_query])
                    faq_score = cosine_similarity(query_vector, self.tfidf_matrix[idx:idx+1])[0][0]

                    if faq_score >= base_threshold:
                        faq_candidates.append((faq_idx, faq_score))

            # Sort FAQ candidates by score and take the best one
            if faq_candidates:
                faq_candidates.sort(key=lambda x: x[1], reverse=True)
                best_faq_idx, best_faq_score = faq_candidates[0]
                faq_rule = {'response': faq_answers[best_faq_idx], 'category': 'faqs'}
                candidates.append((faq_rule, best_faq_score, 'faq'))

        # Context-aware matching (check previous queries in session)
        if session_id and session_id in self.conversation_history:
            prev_queries = [entry['query'] for entry in self.conversation_history[session_id][-3:]]  # Last 3
            for prev_q in prev_queries:
                # Boost matches related to previous topics
                for r in rules_to_use:
                    questions = r.get('questions', []) or r.get('question', '')
                    if isinstance(questions, str):
                        questions = [questions]
                    flattened_questions = []
                    for q in questions:
                        if isinstance(q, str):
                            flattened_questions.append(q)
                        elif isinstance(q, list):
                            flattened_questions.extend(q)
                    if flattened_questions:
                        _, context_score = semantic_similarity(prev_q, flattened_questions, threshold=0.0)
                        if context_score >= 0.5:  # High threshold for context
                            candidates.append((r, context_score * 0.8, 'context'))  # Slight boost

        # Select the best match across all candidates
        if candidates:
            best_candidate = max(candidates, key=lambda x: x[1])
            best_rule, best_score, match_type = best_candidate
            logging.info(f"Best match: {match_type} with score {best_score:.3f} for rule category {best_rule.get('category', 'unknown')}")
            self.consecutive_fallbacks = 0
            response = best_rule['response']
            if session_id:
                self.update_context(session_id, user_input, response)
            return self.append_image_to_response(response)

        # Fallback responses
        self.consecutive_fallbacks += 1
        fallback = self.fallback_responses[self.fallback_index]
        self.fallback_index = (self.fallback_index + 1) % len(self.fallback_responses)
        if session_id:
            self.update_context(session_id, user_input, fallback)
        return self.append_image_to_response(fallback)

    def append_image_to_response(self, response_text, rule_keywords=None):
        """
        Append a chatbot image as an HTML <img> tag to the response text if available and keywords match.
        Only append the chatbot image if keywords match chatbot image questions.
        Do not append chatbot image as a fallback for all responses.
        """
        if self.chatbot_images and rule_keywords:
            # Flatten rule_keywords if nested
            flattened_keywords = []
            if isinstance(rule_keywords, list):
                for item in rule_keywords:
                    if isinstance(item, list):
                        flattened_keywords.extend(item)
                    else:
                        flattened_keywords.append(item)
            else:
                flattened_keywords = rule_keywords
            # Find an image whose questions contain any of the flattened_keywords
            for image in self.chatbot_images:
                image_questions = image.get("questions", [])
                # Check if any keyword is in any question
                match = any(any(kw.lower() in q.lower() for kw in flattened_keywords) for q in image_questions)
                if match:
                    image_url = image.get("url", "")
                    if image_url:
                        if not image_url.startswith("/static/"):
                            image_url = "/static/" + image_url
                        response_text += f"<img src='{image_url}' alt='Chatbot Image' class='message-image'>"
                    break  # Append only one image
        return response_text

    def add_rule(self, question, response, user_type='user', category='soict'):
        from uuid import uuid4
        if category == "locations":
            # Add location rule directly to location_rules list
            new_rule = {
                "id": str(uuid4()),
                "questions": [question],  # Store as questions instead of keywords
                "response": response,
                "category": category
            }
            self.location_rules.append(new_rule)
            self.save_location_rules()
            return {"location": new_rule["id"]}
        elif category == "visuals":
            # Add visual rule directly to visual_rules list
            new_rule = {
                "id": str(uuid4()),
                "questions": [question],  # Store as questions instead of keywords
                "response": response,
                "category": category
            }
            self.visual_rules.append(new_rule)
            self.save_visual_rules()
            return {"visual": new_rule["id"]}
        else:
            # Use MySQL database for user/guest rules
            rule_data = {
                'id': str(uuid4()),
                'category': category,
                'question': question,
                'answer': response
            }

            if user_type == 'user' or user_type == 'both':
                self.db.add_rule('user', rule_data)
                self.rules = self.get_rules()
            if user_type == 'guest' or user_type == 'both':
                self.db.add_rule('guest', rule_data)
                self.guest_rules = self.get_guest_rules()

            # Recompute embeddings after adding rules
            self.recompute_embeddings()
            return {"user": rule_data['id']} if user_type == "user" else {"guest": rule_data['id']}

    def save_location_rules(self):
        """
        Save the current location rules to database/locations/locations.json.
        """
        import json
        locations_path = os.path.join("database", "locations", "locations.json")
        try:
            # Convert location_rules to the format expected in locations.json
            locations_data = []
            for rule in self.location_rules:
                # Extract image URL from response HTML if possible
                import re
                url_match = re.search(r"<img src='([^']+)'", rule.get("response", ""))
                url = url_match.group(1) if url_match else ""
                # Remove /static/ prefix if present
                if url.startswith("/static/"):
                    url = url[len("/static/"):]
                # Extract description (text before <br>)
                description = rule.get("response", "").split("<br>")[0]
                # Extract URLs from HTML
                img_matches = re.findall(r"<img src='([^']+)'", rule.get("response", ""))
                urls = []
                for img_url in img_matches:
                    if img_url.startswith("/static/"):
                        img_url = img_url[len("/static/"):]
                    urls.append(img_url)
                locations_data.append({
                    "id": rule.get("id", ""),
                    "questions": rule.get("questions", []),
                    "url": url,
                    "urls": urls,
                    "description": description,
                    "user_type": rule.get("user_type", "both")
                })
            with open(locations_path, "w", encoding="utf-8") as f:
                logging.info("Saving location rules to %s", locations_path)
                json.dump(locations_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            import logging
            logging.error(f"Error saving location rules to {locations_path}: {e}")

    def add_location(self, location_data):
        """
        Add a new location to the database.
        """
        return self.db.add_location(location_data)

    def edit_location(self, location_id, location_data):
        """
        Edit an existing location in the database.
        """
        return self.db.edit_location(location_id, location_data)

    def delete_location(self, location_id):
        """
        Delete a location from the database.
        """
        return self.db.delete_location(location_id)

    def add_visual(self, visual_data):
        """
        Add a new visual to the database.
        """
        return self.db.add_visual(visual_data)

    def edit_visual(self, visual_id, visual_data):
        """
        Edit an existing visual in the database.
        """
        return self.db.edit_visual(visual_id, visual_data)

    def delete_visual(self, visual_id):
        """
        Delete a visual from the database.
        """
        return self.db.delete_visual(visual_id)

    def add_faq(self, faq_data):
        """
        Add a new FAQ to the database.
        """
        return self.db.add_faq(faq_data)

    def edit_faq(self, faq_id, faq_data):
        """
        Edit an existing FAQ in the database.
        """
        return self.db.edit_faq(faq_id, faq_data)

    def delete_faq(self, faq_id):
        """
        Delete an FAQ from the database.
        """
        return self.db.delete_faq(faq_id)

    def delete_rule(self, rule_id, user_type=None):
        import logging
        logging.debug(f"Deleting rule with id: {rule_id}, user_type: {user_type}")
        deleted = False

        # Determine user_type if not specified
        if user_type is None:
            # Try to find the rule in user rules first
            for rule in self.rules:
                if str(rule.get("id")) == str(rule_id):
                    user_type = 'user'
                    break
            if user_type is None:
                for rule in self.guest_rules:
                    if str(rule.get("id")) == str(rule_id):
                        user_type = 'guest'
                        break

        if user_type == 'user':
            # Delete from user rules in MySQL
            deleted = self.db.delete_rule('user', rule_id)
            if deleted:
                self.rules = self.get_rules()
                logging.debug(f"Rule with id {rule_id} deleted from user rules.")
        elif user_type == 'guest':
            # Delete from guest rules in MySQL
            deleted = self.db.delete_rule('guest', rule_id)
            if deleted:
                self.guest_rules = self.get_guest_rules()
                logging.debug(f"Rule with id {rule_id} deleted from guest rules.")

        if not deleted:
            # Check location rules
            for i, rule in enumerate(self.location_rules):
                logging.debug(f"Checking location rule id: {rule.get('id')}")
                if str(rule.get("id")) == str(rule_id):
                    del self.location_rules[i]
                    self.save_location_rules()
                    self.location_rules = self.get_location_rules()
                    logging.debug(f"Rule with id {rule_id} deleted from location rules.")
                    deleted = True
                    break

        if not deleted:
            # Check visual rules
            for i, rule in enumerate(self.visual_rules):
                logging.debug(f"Checking visual rule id: {rule.get('id')}")
                if str(rule.get("id")) == str(rule_id):
                    del self.visual_rules[i]
                    self.save_visual_rules()
                    self.visual_rules = self.get_visual_rules()
                    logging.debug(f"Rule with id {rule_id} deleted from visual rules.")
                    deleted = True
                    break

        # Recompute embeddings after deleting rules
        if deleted:
            self.recompute_embeddings()

        return deleted

    def edit_rule(self, rule_id, question, response, user_type='user'):
        # Edit rule in user, guest, or location rules
        edited = False

        # Determine user_type if not specified
        if user_type is None:
            # Try to find the rule in user rules first
            for rule in self.rules:
                if str(rule.get("id")) == str(rule_id):
                    user_type = 'user'
                    break
            if user_type is None:
                for rule in self.guest_rules:
                    if str(rule.get("id")) == str(rule_id):
                        user_type = 'guest'
                        break

        if user_type == 'user':
            # Edit user rule in MySQL
            edited = self.db.edit_rule('user', rule_id, {'question': question, 'answer': response})
            if edited:
                self.rules = self.get_rules()
        elif user_type == 'guest':
            # Edit guest rule in MySQL
            edited = self.db.edit_rule('guest', rule_id, {'question': question, 'answer': response})
            if edited:
                self.guest_rules = self.get_guest_rules()

        if not edited:
            # Edit location rules (if not found in user/guest rules)
            for rule in self.location_rules:
                if str(rule.get("id")) == str(rule_id):
                    rule["questions"] = [question]  # Store as questions instead of keywords
                    rule["response"] = response
                    self.save_location_rules()
                    edited = True
                    break

        if not edited:
            # Edit visual rules (if not found in user/guest rules)
            for rule in self.visual_rules:
                if str(rule.get("id")) == str(rule_id):
                    rule["questions"] = [question]  # Store as questions instead of keywords
                    rule["response"] = response
                    self.save_visual_rules()
                    edited = True
                    break

        # Recompute embeddings after editing rules
        if edited:
            self.recompute_embeddings()

        return edited

    def reload_faqs(self):
        """
        Reload FAQs from database into memory.
        """
        self.faqs = self.get_faqs()

    def reload_location_rules(self):
        """
        Reload location rules from database/locations/locations.json into memory.
        """
        self.location_rules = self.get_location_rules()

    def reload_visual_rules(self):
        """
        Reload visual rules from database/visuals/visuals.json into memory.
        """
        visuals_path = os.path.join("database", "visuals", "visuals.json")
        self.visual_rules = self.get_visual_rules()
        self.visual_rules_mtime = os.path.getmtime(visuals_path)

    def create_category_files(self, category):
        """
        Create JSON files for a new category in both user and guest databases.
        """
        import json
        import os

        # Define paths
        user_file = os.path.join("database", "user_database", f"{category}_rules.json")
        guest_file = os.path.join("database", "guest_database", f"{category}_guest_rules.json")

        # Create empty category files if they don't exist
        for file_path in [user_file, guest_file]:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump([], f, indent=4)
                except Exception as e:
                    logging.error(f"Error creating category file {file_path}: {e}")

        # Update CATEGORY_FILES in rule_utils if needed
        try:
            from database.user_database import rule_utils
            if category not in rule_utils.CATEGORY_FILES:
                rule_utils.CATEGORY_FILES[category] = {
                    "user": user_file,
                    "guest": guest_file
                }
        except Exception as e:
            logging.error(f"Error updating CATEGORY_FILES: {e}")




