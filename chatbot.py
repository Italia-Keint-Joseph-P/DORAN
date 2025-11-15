import logging
import string
import re
from uuid import uuid4
import logging
from nlp_utils import (
    NLUEngine,
    classify_intent,
    preprocess_text
)

def simple_tokenize(text):
    """
    Simple tokenizer that converts text to lowercase and splits on non-alphanumeric characters, but keeps hyphens in words.
    """
    return re.findall(r'\b[\w-]+\b', text.lower())

import database.email_directory as email_directory
import database.user_database.rule_utils as rule_utils

import json
import os

from nlp_utils import NLUEngine
from chatbot_models import Category, Faq, Location, Visual, UserRule, GuestRule
from extensions import db

class Chatbot:
    def __init__(self):
# Initialize NLP Engine FIRST
        self.nlu = NLUEngine(
            min_similarity=0.35,
            fuzzy_threshold=80
        )

        # -----------------------------------------
        # Load all rules with error handling
        # -----------------------------------------

        try:
            self.rules = self.get_rules()
        except Exception as e:
            logging.error(f"Error loading user rules: {e}")
            self.rules = []
        try:
            self.guest_rules = self.get_guest_rules()
        except Exception as e:
            logging.error(f"Error loading guest rules: {e}")
            self.guest_rules = []

        # Load chatbot answer images from MySQL Location table
        try:
            locations_data = Location.query.all()
            self.chatbot_images = []
            for entry in locations_data:
                questions = entry.questions or []
                image_entry = {
                    "id": entry.id,
                    "questions": questions,
                    "url": entry.url,
                    "description": entry.description
                }
                self.chatbot_images.append(image_entry)
        except Exception as e:
            logging.error(f"Error loading chatbot images: {e}")
            self.chatbot_images = []

        # Load location-based rules from MySQL Location table
        try:
            self.location_rules = self.get_location_rules()
        except Exception as e:
            logging.error(f"Error loading location rules: {e}")
            self.location_rules = []

        # Load visual-based rules from MySQL Visual table
        try:
            self.visual_rules = self.get_visual_rules()
        except Exception as e:
            logging.error(f"Error loading visual rules: {e}")
            self.visual_rules = []

        # Email keywords for triggering email search
        self.email_keywords = ["email", "contact", "mail", "reach", "address", "send", "message"]

        # Load FAQs from MySQL Faq table
        try:
            faqs_data = Faq.query.all()
            self.faqs = [{"question": faq.question, "answer": faq.answer, "id": faq.id} for faq in faqs_data]
            self.faq_rules = [{"question": faq["question"], "response": faq["answer"], "category": "faqs", "id": faq["id"]} for faq in self.faqs]
        except Exception as e:
            logging.error(f"Error loading FAQs: {e}")
            self.faqs = []
            self.faq_rules = []

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

        # Initialize response cache for repeated queries
        self.response_cache = {}

        # No longer precomputing TF-IDF for faster performance

        # Cache email directory for faster lookups
        try:
            self.cached_emails = self.cache_emails()
        except Exception as e:
            logging.error(f"Error caching emails: {e}")
            self.cached_emails = []

    def precompute_tfidf(self):
        """
        Precompute TF-IDF matrix for all rules to improve performance.
        Now includes all questions for better accuracy and speed.
        """
        from nlp_utils import preprocess_text, tfidf_vectorizer
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
        # Compute TF-IDF for all questions (no limit for better coverage)
        self.tfidf_matrix = tfidf_vectorizer.fit_transform([preprocess_text(q) for q in all_questions])
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
        # Load and return all user rules from MySQL UserRule table
        try:
            user_rules = UserRule.query.all()
            rules = []
            for rule in user_rules:
                rule_obj = {
                    "category": rule.category,
                    "question": rule.question,  # Using question field
                    "response": rule.answer,
                    "id": rule.id
                }
                rules.append(rule_obj)
            return rules
        except Exception as e:
            logging.error(f"Error loading user rules from MySQL: {e}")
            return []

    def get_guest_rules(self):
        # Load and return all guest rules from MySQL GuestRule table
        try:
            guest_rules = GuestRule.query.all()
            rules = []
            for rule in guest_rules:
                rule_obj = {
                    "category": rule.category,
                    "question": rule.question,  # Using question field
                    "response": rule.answer,
                    "id": rule.id
                }
                rules.append(rule_obj)
            return rules
        except Exception as e:
            logging.error(f"Error loading guest rules from MySQL: {e}")
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
        Load location-based rules from MySQL Location table.
        Converts each location entry to a rule with questions and response containing description and all image URLs.
        """
        try:
            locations_data = Location.query.all()
            location_rules = []
            for entry in locations_data:
                questions = entry.questions or []
                if isinstance(questions, str):
                    questions = [questions]
                flattened_questions = []
                for q in questions:
                    if isinstance(q, str):
                        flattened_questions.append(q)
                    elif isinstance(q, list):
                        flattened_questions.extend(q)
                description = entry.description or ""
                image_urls = entry.urls or []
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
                    "id": entry.id,
                    "questions": flattened_questions,
                    "response": response,
                    "category": "locations",
                    "user_type": entry.user_type or "both"
                }
                location_rules.append(rule)
            return location_rules
        except Exception as e:
            logging.error(f"Error loading location rules from MySQL: {e}")
            return []

    def get_visual_rules(self):
        """
        Load visual-based rules from MySQL Visual table.
        Converts each visual entry to a rule with questions and response containing description and all image URLs.
        Dynamically generates specific questions based on description if questions are generic.
        """
        try:
            visuals_data = Visual.query.all()
            visual_rules = []
            for entry in visuals_data:
                questions = entry.questions or []
                description = entry.description or ""
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
                image_urls = entry.urls or []
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
                    "id": entry.id,
                    "questions": questions,
                    "response": response,
                    "category": "visuals",
                    "user_type": entry.user_type or "user"
                }
                visual_rules.append(rule)
            return visual_rules
        except Exception as e:
            logging.error(f"Error loading visual rules from MySQL: {e}")
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
        dynamic thresholds, and response caching for better accuracy and speed.

        Args:
            user_input (str): The input message from the user.
            user_role (str): The role of the user ('guest' or other).
            session_id (str): Unique session ID for context tracking.

        Returns:
            str: The chatbot's response from rules, info.json, or fallback message.
        """
    def get_response(self, user_input, user_role="guest", session_id=None):

            try:
                # Cache key
                cache_key = f"{user_role}:{user_input.lower().strip()}"
                if cache_key in self.response_cache:
                    return self.append_image_to_response(self.response_cache[cache_key])

                # Detect intent
                intent = classify_intent(user_input)

                # Select rules
                if user_role == "guest":
                    rules_to_use = (
                        self.guest_rules +
                        self.location_rules +
                        self.visual_rules +
                        self.faq_rules
                    )
                else:
                    rules_to_use = (
                        self.rules +
                        self.location_rules +
                        self.visual_rules +
                        self.faq_rules
                    )

                # ---------------------------------------------------
                # NEW NLP ENGINE REPLACEMENT BLOCK STARTS HERE
                # ---------------------------------------------------

                processed_query = self.nlu.preprocess(user_input)

                # Combine all rules for unified search
                all_rules = (
                    self.rules +
                    self.guest_rules +
                    self.location_rules +
                    self.visual_rules +
                    self.faq_rules
                )

                best_rule, score = self.nlu.match_rule(processed_query, all_rules)

                if best_rule:
                    self.consecutive_fallbacks = 0

                    # Determine the response text from rule
                    response = (
                        best_rule.get("response") or
                        best_rule.get("answer") or
                        best_rule.get("description") or
                        "I'm not sure how to answer that, but I found something related."
                    )

                    if session_id:
                        self.update_context(session_id, user_input, response)

                    # Cache
                    self.response_cache[cache_key] = response

                    # If rule has images or visual data, include it
                    return self.append_image_to_response(response, best_rule.get("questions"))

                # ---------------------------------------------------
                # NEW NLP ENGINE BLOCK ENDS HERE
                # ---------------------------------------------------

                # Fallback responses
                logging.info("No matches found, using fallback")
                self.consecutive_fallbacks += 1
                fallback = self.fallback_responses[self.fallback_index]
                self.fallback_index = (self.fallback_index + 1) % len(self.fallback_responses)

                if session_id:
                    self.update_context(session_id, user_input, fallback)

                # Cache fallback
                self.response_cache[cache_key] = fallback
                return self.append_image_to_response(fallback)

            except Exception as e:
                logging.error(f"Error in get_response: {e}", exc_info=True)
                fallback = "I'm sorry, I encountered an error. Please try again."

                if session_id:
                    self.update_context(session_id, user_input, fallback)

                self.response_cache[cache_key] = fallback
                return fallback


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
                        flattened_keywords.append(str(item))
            else:
                flattened_keywords = [str(rule_keywords)]
            # Find an image whose questions contain any of the flattened_keywords
            for image in self.chatbot_images:
                image_questions = image.get("questions", [])
                # Flatten image_questions if nested
                flattened_image_questions = []
                if isinstance(image_questions, list):
                    for item in image_questions:
                        if isinstance(item, list):
                            flattened_image_questions.extend(item)
                        else:
                            flattened_image_questions.append(str(item))
                else:
                    flattened_image_questions = [str(image_questions)]
                # Check if any keyword is in any question
                match = any(any(kw.lower() in q.lower() for kw in flattened_keywords) for q in flattened_image_questions)
                if match:
                    image_url = image.get("url", "")
                    if image_url:
                        if not image_url.startswith("/static/"):
                            image_url = "/static/" + image_url
                        response_text += f"<img src='{image_url}' alt='Chatbot Image' class='message-image'>"
                    break  # Append only one image
        return response_text

    def add_rule(self, question, response, user_type='user', category='soict'):
        try:
            if user_type == 'user':
                new_rule = UserRule(category=category, question=question, answer=response)
                db.session.add(new_rule)
                db.session.commit()
                # Reload rules to update in-memory state
                self.rules = self.get_rules()
                return {"user": new_rule.id}
            elif user_type == 'guest':
                new_rule = GuestRule(category=category, question=question, answer=response)
                db.session.add(new_rule)
                db.session.commit()
                # Reload rules to update in-memory state
                self.guest_rules = self.get_guest_rules()
                return {"guest": new_rule.id}
            else:
                # For both user types
                user_rule = UserRule(category=category, question=question, answer=response)
                guest_rule = GuestRule(category=category, question=question, answer=response)
                db.session.add(user_rule)
                db.session.add(guest_rule)
                db.session.commit()
                # Reload rules to update in-memory state
                self.rules = self.get_rules()
                self.guest_rules = self.get_guest_rules()
                return {"user": user_rule.id, "guest": guest_rule.id}
        except Exception as e:
            logging.error(f"Error adding rule to MySQL: {e}")
            db.session.rollback()
            return None

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
        # Edit rule in MySQL database
        try:
            if user_type == 'user':
                rule = UserRule.query.filter_by(id=rule_id).first()
                if rule:
                    rule.question = question
                    rule.answer = response
                    db.session.commit()
                    self.rules = self.get_rules()
                    return True
            elif user_type == 'guest':
                rule = GuestRule.query.filter_by(id=rule_id).first()
                if rule:
                    rule.question = question
                    rule.answer = response
                    db.session.commit()
                    self.guest_rules = self.get_guest_rules()
                    return True
        except Exception as e:
            logging.error(f"Error editing rule in MySQL: {e}")
            db.session.rollback()
        return False

    def reload_faqs(self):
        """
        Reload FAQs from MySQL Faq table into memory.
        """
        try:
            faqs_data = Faq.query.all()
            self.faqs = [{"question": faq.question, "answer": faq.answer, "id": faq.id} for faq in faqs_data]
            self.faq_rules = [{"question": faq["question"], "response": faq["answer"], "category": "faqs", "id": faq["id"]} for faq in self.faqs]
        except Exception as e:
            logging.error(f"Error reloading FAQs from MySQL: {e}")
            self.faqs = []
            self.faq_rules = []

    def reload_location_rules(self):
        """
        Reload location rules from database/locations/locations.json into memory.
        """
        self.location_rules = self.get_location_rules()

    def reload_visual_rules(self):
        """
        Reload visual rules from MySQL Visual table into memory.
        """
        self.visual_rules = self.get_visual_rules()

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




