import logging
import string
import re
from uuid import uuid4

def simple_tokenize(text):
    """
    Simple tokenizer that converts text to lowercase and splits on non-alphanumeric characters, but keeps hyphens in words.
    """
    return re.findall(r'\b[\w-]+\b', text.lower())

import database.email_directory as email_directory
import database.user_database.rule_utils as rule_utils

import json
import os

from nlp_utils import semantic_similarity, preprocess_text, fuzzy_match, classify_intent

class Chatbot:
    def __init__(self):
        # Keep all other initialization code unchanged

        # Initialize rules attributes
        self.rules = self.get_rules()
        self.guest_rules = self.get_guest_rules()

        # Load chatbot answer images from locations.json
        locations_path = os.path.join("database", "locations", "locations.json")
        try:
            with open(locations_path, "r", encoding="utf-8") as f:
                locations_data = json.load(f)
                self.chatbot_images = []
                for entry in locations_data:
                    questions = entry.get("questions", [])
                    image_entry = {
                        "id": entry.get("id", ""),
                        "questions": questions,
                        "url": entry.get("url", ""),
                        "description": entry.get("description", "")
                    }
                    self.chatbot_images.append(image_entry)
        except Exception:
            self.chatbot_images = []

        # Load location-based rules from locations.json
        self.location_rules = self.get_location_rules()

        # Load visual-based rules from visuals.json
        visuals_path = os.path.join("database", "visuals", "visuals.json")
        self.visual_rules = self.get_visual_rules()
        self.visual_rules_mtime = os.path.getmtime(visuals_path)

        # Email keywords for triggering email search
        self.email_keywords = ["email", "contact", "mail", "reach", "address", "send", "message"]

        # Load FAQs
        with open('database/faqs.json', 'r', encoding='utf-8') as f:
            self.faqs = json.load(f)

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
        """
        from nlp_utils import preprocess_text, vectorizer
        all_questions = []
        for rule in self.rules + self.guest_rules + self.location_rules + self.visual_rules:
            questions = rule.get('questions', []) or rule.get('question', '')
            if isinstance(questions, str):
                questions = [questions]
            flattened_questions = []
            for q in questions:
                if isinstance(q, str):
                    flattened_questions.append(q)
                elif isinstance(q, list):
                    flattened_questions.extend(q)
            all_questions.extend(flattened_questions)
        # Preprocess all questions
        processed_questions = [preprocess_text(q) for q in all_questions]
        # Fit vectorizer on all processed questions
        self.tfidf_matrix = vectorizer.fit_transform(processed_questions)
        self.tfidf_corpus = all_questions

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
        # Load and return all user rules from the combined all_user_rules.json file
        import json
        import os
        rules = []
        user_rules_path = os.path.join("database", "user_database", "all_user_rules.json")
        rules_updated = False

        try:
            with open(user_rules_path, "r", encoding="utf-8") as f:
                rules_data = json.load(f)
                # Handle new categorized structure
                if isinstance(rules_data, dict):
                    # New categorized structure
                    for category, category_rules in rules_data.items():
                        for rule in category_rules:
                            # Use question as the matching text, not keywords
                            # Preserve existing ID or generate new one if missing
                            if 'id' not in rule:
                                rule['id'] = str(uuid4())
                                rules_updated = True
                            rule_id = rule.get("id")
                            rule_obj = {
                                "category": category,
                                "question": rule.get("question", ""),
                                "response": rule.get("answer", ""),
                                "id": rule_id
                            }
                            rules.append(rule_obj)
                else:
                    # Legacy flat array structure (fallback)
                    for rule in rules_data:
                        # Preserve existing ID or generate new one if missing
                        if 'id' not in rule:
                            rule['id'] = str(uuid4())
                            rules_updated = True
                        rule_id = rule.get("id")
                        rule_obj = {
                            "category": "combined_user",
                            "question": rule.get("question", ""),
                            "response": rule.get("answer", ""),
                            "id": rule_id
                        }
                        rules.append(rule_obj)

            # Save updated rules back to file if any IDs were added
            if rules_updated:
                with open(user_rules_path, "w", encoding="utf-8") as f:
                    json.dump(rules_data, f, indent=4, ensure_ascii=False)

        except Exception:
            # Fallback to original method if combined file not found
            rules = []
            user_db_path = os.path.join("database", "user_database")
            try:
                for filename in os.listdir(user_db_path):
                    if filename.endswith("_rules.json") and filename != "locations_rules.json":
                        category = filename.replace("_rules.json", "")
                        filepath = os.path.join(user_db_path, filename)
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                rules_data = json.load(f)
                                for rule in rules_data:
                                    rule['category'] = category
                                    rule['question'] = rule.get('question', '')
                                    rule['response'] = rule.get('answer', '')
                                    if 'id' not in rule:
                                        rule['id'] = str(uuid4())
                                    rules.append(rule)
                        except Exception:
                            continue
            except Exception:
                category_files = {
                    "soict": "database/user_database/soict_rules.json",
                    "soed": "database/user_database/soed_rules.json",
                    "sobm": "database/user_database/sobm_rules.json",
                    "soit": "database/user_database/soit_rules.json",
                    "faculty_staff": "database/user_database/faculty_staff_rules.json"
                }
                for category, filepath in category_files.items():
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            rules_data = json.load(f)
                            for rule in rules_data:
                                rule['category'] = category
                                rule['question'] = rule.get('question', '')
                                rule['response'] = rule.get('answer', '')
                                if 'id' not in rule:
                                    rule['id'] = str(uuid4())
                                rules.append(rule)
                    except Exception:
                        continue



        return rules

    def get_guest_rules(self):
        # Load and return all guest rules from the combined all_guest_rules.json file
        import json
        import os
        rules = []
        guest_rules_path = os.path.join("database", "guest_database", "all_guest_rules.json")
        rules_updated = False

        try:
            with open(guest_rules_path, "r", encoding="utf-8") as f:
                rules_data = json.load(f)
                # Handle new categorized structure
                if isinstance(rules_data, dict):
                    # New categorized structure
                    for category, category_rules in rules_data.items():
                        for rule in category_rules:
                            # Use question as the matching text, not keywords
                            # Preserve existing ID or generate new one if missing
                            if 'id' not in rule:
                                rule['id'] = str(uuid4())
                                rules_updated = True
                            rule_id = rule.get("id")
                            rule_obj = {
                                "category": category,
                                "question": rule.get("question", ""),
                                "response": rule.get("answer", ""),
                                "id": rule_id
                            }
                            rules.append(rule_obj)
                else:
                    # Legacy flat array structure (fallback)
                    for rule in rules_data:
                        # Preserve existing ID or generate new one if missing
                        if 'id' not in rule:
                            rule['id'] = str(uuid4())
                            rules_updated = True
                        rule_id = rule.get("id")
                        rule_obj = {
                            "category": "combined_guest",
                            "question": rule.get("question", ""),
                            "response": rule.get("answer", ""),
                            "id": rule_id
                        }
                        rules.append(rule_obj)

            # Save updated rules back to file if any IDs were added
            if rules_updated:
                with open(guest_rules_path, "w", encoding="utf-8") as f:
                    json.dump(rules_data, f, indent=4, ensure_ascii=False)

        except Exception:
            rules = []
            guest_db_path = os.path.join("database", "guest_database")
            try:
                for filename in os.listdir(guest_db_path):
                    if filename.endswith("_guest_rules.json"):
                        category = filename.replace("_guest_rules.json", "")
                        filepath = os.path.join(guest_db_path, filename)
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                rules_data = json.load(f)
                                for rule in rules_data:
                                    rule['category'] = category
                                    rule['question'] = rule.get('question', '')
                                    rule['response'] = rule.get('answer', '')
                                    if 'id' not in rule or not rule['id']:
                                        rule['id'] = str(uuid4())
                                    rules.append(rule)
                        except Exception:
                            continue
            except Exception:
                category_files = {
                    "soict": "database/guest_database/soict_guest_rules.json",
                    "soed": "database/guest_database/soed_guest_rules.json",
                    "sobm": "database/guest_database/sobm_guest_rules.json",
                    "soit": "database/guest_database/soit_guest_rules.json",
                    "faculty_staff": "database/guest_database/faculty_staff_guest_rules.json"
                }
                for category, filepath in category_files.items():
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            rules_data = json.load(f)
                            for rule in rules_data:
                                rule['category'] = category
                                rule['question'] = rule.get('question', '')
                                rule['response'] = rule.get('answer', '')
                                if 'id' not in rule or not rule['id']:
                                    rule['id'] = str(uuid4())
                                rules.append(rule)
                    except Exception:
                        continue
        return rules

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
        Load location-based rules from database/locations/locations.json
        Converts each image entry to a rule with keywords and response containing description and all image URLs.
        """
        locations_path = os.path.join("database", "locations", "locations.json")
        try:
            with open(locations_path, "r", encoding="utf-8") as f:
                locations_data = json.load(f)
                location_rules = []
                for entry in locations_data:
                    questions = entry.get("questions", [])
                    if isinstance(questions, str):
                        questions = [questions]
                    flattened_questions = []
                    for q in questions:
                        if isinstance(q, str):
                            flattened_questions.append(q)
                        elif isinstance(q, list):
                            flattened_questions.extend(q)
                    # Include description in questions for NLP matching
                    description = entry.get("description", "")
                    flattened_questions.append(description)
                    keywords = [word for q in flattened_questions for word in q.lower().split()]
                    image_urls = entry.get("urls", [])
                    # Compose response with description and all image HTML tags
                    images_html = ""
                    if len(image_urls) > 2:
                        # Show first image with overlay for additional images
                        static_img_url = image_urls[0]
                        if not static_img_url.startswith("/static/"):
                            static_img_url = "/static/" + static_img_url
                        additional_count = len(image_urls) - 1
                        prefixed_urls = ["/static/" + url if not url.startswith("/static/") else url for url in image_urls]
                        images_html = f"""
                        <div class="image-gallery" data-images='{",".join(prefixed_urls)}'>
                            <img src='{static_img_url}' alt='Location Image' class='message-image'>
                            <div class="image-overlay">+{additional_count} more</div>
                        </div>
                        """
                    else:
                        # Show all images if 2 or fewer
                        for img_url in image_urls:
                            static_img_url = img_url
                            if not img_url.startswith("/static/"):
                                static_img_url = "/static/" + img_url
                            prefixed_urls = ["/static/" + url if not url.startswith("/static/") else url for url in image_urls]
                            images_html += f"<img src='{static_img_url}' alt='Location Image' class='message-image' data-images='{','.join(prefixed_urls)}'>"
                    response = f"{description}<br>{images_html}"
                    rule = {
                        "id": entry.get("id", ""),
                        "questions": flattened_questions,
                        "response": response,
                        "category": "locations",
                        "user_type": entry.get("user_type", "both")
                    }
                    location_rules.append(rule)
                return location_rules
        except Exception:
            return []

    def get_visual_rules(self):
        """
        Load visual-based rules from database/visuals/visuals.json
        Converts each image entry to a rule with questions and response containing description and all image URLs.
        Dynamically generates specific questions based on description if questions are generic.
        """
        visuals_path = os.path.join("database", "visuals", "visuals.json")
        try:
            with open(visuals_path, "r", encoding="utf-8") as f:
                visuals_data = json.load(f)
                visual_rules = []
                for entry in visuals_data:
                    questions = entry.get("questions", [])
                    description = entry.get("description", "")
                    # Check if questions are generic and generate specific ones based on description
                    if questions == ["What is ?", "Can you show me ?", "Where can I find information about ?", "Tell me about .", "What are the details on ?"]:
                        desc_lower = description.lower()
                        if 'uniform' in desc_lower:
                            school = desc_lower.split('uniform')[0].strip().title()
                            questions = [
                                f"What is the uniform for {school}?",
                                "Can you show me the uniform?",
                                "Tell me about the uniform.",
                                "What are the details on the uniform?",
                                "Where can I find information about the uniform?"
                            ]
                        elif 'student council' in desc_lower or 'council' in desc_lower:
                            council_type = 'ICT Student Council' if 'ict' in desc_lower else 'Student Council'
                            questions = [
                                f"Who are the {council_type} members?",
                                f"Can you show me the {council_type}?",
                                f"Tell me about the {council_type}.",
                                f"What are the details on the {council_type}?",
                                f"Where can I find information about the {council_type}?"
                            ]
                        elif 'ictzen' in desc_lower:
                            # Extract role
                            if 'is the' in desc_lower:
                                role = desc_lower.split('is the')[1].split('a.y')[0].strip().title()
                            else:
                                role = 'ICTzen staff'
                            questions = [
                                f"Who is the {role}?",
                                f"Can you show me the {role}?",
                                f"Tell me about the {role}.",
                                f"What is the {role}'s role?",
                                f"Where can I find information about the {role}?"
                            ]
                        elif 'research coordinator' in desc_lower or 'program head' in desc_lower or 'director' in desc_lower or 'adviser' in desc_lower or 'professor' in desc_lower or 'instructor' in desc_lower or 'lecturer' in desc_lower or 'aide' in desc_lower:
                            # Person entry
                            if ',' in description:
                                name = description.split(',')[0].strip()
                            else:
                                name = description.split(' is ')[0].strip()
                            questions = [
                                f"Who is {name}?",
                                f"Can you show me {name}?",
                                f"Tell me about {name}.",
                                f"What is {name}'s role?",
                                f"Where can I find information about {name}?"
                            ]
                        else:
                            # Default
                            questions = [
                                "What is this?",
                                "Can you show me this?",
                                "Tell me about this.",
                                "What are the details on this?",
                                "Where can I find information about this?"
                            ]
                    image_urls = entry.get("urls", [])
                    # Compose response with description and all image HTML tags
                    images_html = ""
                    if len(image_urls) > 2:
                        # Show first image with overlay for additional images
                        static_img_url = image_urls[0]
                        if not static_img_url.startswith("/static/"):
                            static_img_url = "/static/" + static_img_url
                        additional_count = len(image_urls) - 1
                        prefixed_urls = ["/static/" + url if not url.startswith("/static/") else url for url in image_urls]
                        images_html = f"""
                        <div class="image-gallery" data-images='{",".join(prefixed_urls)}'>
                            <img src='{static_img_url}' alt='Visual Image' class='message-image'>
                            <div class="image-overlay">+{additional_count} more</div>
                        </div>
                        """
                    else:
                        # Show all images if 2 or fewer
                        for img_url in image_urls:
                            static_img_url = img_url
                            if not img_url.startswith("/static/"):
                                static_img_url = "/static/" + img_url
                            prefixed_urls = ["/static/" + url if not url.startswith("/static/") else url for url in image_urls]
                            images_html += f"<img src='{static_img_url}' alt='Visual Image' class='message-image' data-images='{','.join(prefixed_urls)}'>"
                    response = f"{description}<br>{images_html}"
                    rule = {
                        "id": entry.get("id", ""),
                        "questions": questions,
                        "response": response,
                        "category": "visuals",
                        "user_type": entry.get("user_type", "user")
                    }
                    visual_rules.append(rule)
                return visual_rules
        except Exception:
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

        # Classify intent for dynamic thresholds
        intent = classify_intent(user_input)
        base_threshold = {'location': 0.25, 'contact': 0.3, 'faq': 0.35, 'info': 0.3, 'unknown': 0.4}[intent]

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

        # Check if visuals.json has been modified and reload if necessary
        visuals_path = os.path.join("database", "visuals", "visuals.json")
        try:
            current_mtime = os.path.getmtime(visuals_path)
            if current_mtime > self.visual_rules_mtime:
                self.reload_visual_rules()
        except Exception as e:
            logging.error(f"Error checking visuals.json modification time: {e}")

        # Collect all potential matches with their scores
        candidates = []  # List of (rule, combined_score, match_type)

        # Determine rules to use based on user role
        if user_role == 'guest':
            rules_to_use = self.guest_rules + self.location_rules + self.visual_rules
        else:
            rules_to_use = self.rules + self.guest_rules + self.location_rules + self.visual_rules

        # TF-IDF cosine similarity for all rules using precomputed matrix
        for r in rules_to_use[:100]:  # Limit to first 100 rules to avoid memory issues
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
                _, tfidf_score = semantic_similarity(user_input, flattened_questions, threshold=0.0, precomputed_matrix=self.tfidf_matrix, precomputed_corpus=self.tfidf_corpus)
                if tfidf_score >= base_threshold:
                    # Boost for intent match
                    if r.get('category') == intent or (intent == 'location' and r.get('category') in ['locations', 'visuals']):
                        tfidf_score += 0.1
                    candidates.append((r, tfidf_score, 'tfidf'))

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

        # FAQs TF-IDF similarity
        faq_questions = [item['question'] for item in self.faqs]
        faq_answers = [item['answer'] for item in self.faqs]
        if faq_questions:
            best_faq, faq_similarity_score = semantic_similarity(user_input, faq_questions, threshold=base_threshold)
            if best_faq:
                index = faq_questions.index(best_faq)
                faq_rule = {'response': faq_answers[index], 'category': 'faqs'}
                candidates.append((faq_rule, faq_similarity_score, 'faq'))

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
            # Use the centralized add_rule function from rule_utils to add and save rules
            # This will update the "all" files correctly without creating unnecessary category files
            added_id = rule_utils.add_rule(user_type, category, question, response)

            # Reload rules to update in-memory state without double-saving
            if user_type == 'user' or user_type == 'both':
                self.rules = self.get_rules()
            if user_type == 'guest' or user_type == 'both':
                self.guest_rules = self.get_guest_rules()
            # Recompute embeddings after adding rules
            self.recompute_embeddings()
            return {"user": added_id} if user_type == "user" else {"guest": added_id}

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

    def save_visual_rules(self):
        """
        Save the current visual rules to database/visuals/visuals.json.
        """
        import json
        visuals_path = os.path.join("database", "visuals", "visuals.json")
        try:
            # Convert visual_rules to the format expected in visuals.json
            visuals_data = []
            for rule in self.visual_rules:
                # Extract image URLs from response HTML
                import re
                img_matches = re.findall(r"<img src='([^']+)'", rule.get("response", ""))
                urls = []
                for img_url in img_matches:
                    if img_url.startswith("/static/"):
                        img_url = img_url[len("/static/"):]
                    urls.append(img_url)
                # Primary url
                url = urls[0] if urls else ""
                # Extract description (text before <br>)
                description = rule.get("response", "").split("<br>")[0]
                visuals_data.append({
                    "id": rule.get("id", ""),
                    "questions": rule.get("questions", []),
                    "url": url,
                    "urls": urls,
                    "description": description
                })
            with open(visuals_path, "w", encoding="utf-8") as f:
                logging.info("Saving visual rules to %s", visuals_path)
                json.dump(visuals_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            import logging
            logging.error(f"Error saving visual rules to {visuals_path}: {e}")

    def delete_rule(self, rule_id, user_type=None):
        import logging
        logging.debug(f"Deleting rule with id: {rule_id}, user_type: {user_type}")
        deleted = False

        if user_type == 'guest':
            # Check guest rules first
            for i in reversed(range(len(self.guest_rules))):
                rule = self.guest_rules[i]
                logging.debug(f"Checking guest rule id: {rule.get('id')}")
                if str(rule.get("id")) == str(rule_id):
                    category = rule.get("category", "SOICT")
                    del self.guest_rules[i]
                    # Remove from JSON file using rule_utils
                    from database.user_database import rule_utils
                    deleted = rule_utils.delete_rule(rule_id, user_type='guest', category=category)
                    self.guest_rules = self.get_guest_rules()
                    logging.debug(f"Rule with id {rule_id} deleted from guest rules.")
                    return deleted

            # Then check user rules
            for i, rule in enumerate(self.rules):
                logging.debug(f"Checking user rule id: {rule.get('id')}")
                if str(rule.get("id")) == str(rule_id):
                    category = rule.get("category", "SOICT")
                    # Remove from in-memory list
                    del self.rules[i]
                    # Remove from JSON file using rule_utils
                    from database.user_database import rule_utils
                    deleted = rule_utils.delete_rule(rule_id, user_type='user', category=category)
                    # Reload rules
                    self.rules = self.get_rules()
                    # Recompute embeddings after deleting rules
                    self.recompute_embeddings()
                    logging.debug(f"Rule with id {rule_id} deleted from user rules.")
                    return deleted
        else:
            # Check user rules first (default)
            for i, rule in enumerate(self.rules):
                logging.debug(f"Checking user rule id: {rule.get('id')}")
                if str(rule.get("id")) == str(rule_id):
                    category = rule.get("category", "SOICT")
                    # Remove from in-memory list
                    del self.rules[i]
                    # Remove from JSON file using rule_utils
                    from database.user_database import rule_utils
                    deleted = rule_utils.delete_rule(rule_id, user_type='user', category=category)
                    # Reload rules
                    self.rules = self.get_rules()
                    logging.debug(f"Rule with id {rule_id} deleted from user rules.")
                    return deleted

            # Then check guest rules
            for i in reversed(range(len(self.guest_rules))):
                rule = self.guest_rules[i]
                logging.debug(f"Checking guest rule id: {rule.get('id')}")
                if str(rule.get("id")) == str(rule_id):
                    category = rule.get("category", "SOICT")
                    del self.guest_rules[i]
                    # Remove from JSON file using rule_utils
                    from database.user_database import rule_utils
                    deleted = rule_utils.delete_rule(rule_id, user_type='guest', category=category)
                    self.guest_rules = self.get_guest_rules()
                    # Recompute embeddings after deleting rules
                    self.recompute_embeddings()
                    logging.debug(f"Rule with id {rule_id} deleted from guest rules.")
                    return deleted

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
        return deleted

    def edit_rule(self, rule_id, question, response, user_type='user'):
        # Edit rule in user, guest, or location rules
        edited = False

        # Choose the appropriate rules list based on user_type
        if user_type == 'user':
            rules_list = self.rules
        elif user_type == 'guest':
            rules_list = self.guest_rules
        else:
            # Try user rules first, then guest rules
            rules_list = self.rules

        # Edit rules in the selected list
        for rule in rules_list:
            if str(rule.get("id")) == str(rule_id):
                category = rule.get("category", "SOICT")
                # Use rule_utils to edit the rule
                from database.user_database import rule_utils
                edited = rule_utils.edit_rule(rule_id, question, response, user_type=user_type, category=category)
                # Update in-memory rule
                rule["question"] = question
                rule["response"] = response
                # Recompute embeddings after editing rules
                self.recompute_embeddings()
                break

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
        return edited

    def reload_faqs(self):
        """
        Reload FAQs from database/faqs.json into memory.
        """
        try:
            with open('database/faqs.json', 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)
        except Exception as e:
            logging.error(f"Error reloading FAQs: {e}")
            self.faqs = []

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




