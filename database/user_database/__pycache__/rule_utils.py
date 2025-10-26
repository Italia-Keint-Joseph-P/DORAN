import json
import os
import logging

# Mapping of categories to their user and guest JSON files
CATEGORY_FILES = {
    "sobm": {
        "user": os.path.join(os.path.dirname(__file__), "user_database", "sobm_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "guest_database", "sobm_guest_rules.json"),
    },
    "soict": {
        "user": os.path.join(os.path.dirname(__file__),"user_database", "soict_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "guest_database", "soict_guest_rules.json"),
    },
    "soit": {
        "user": os.path.join(os.path.dirname(__file__),"user_database", "soit_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "guest_database", "soit_guest_rules.json"),
    },
    "soed": {
        "user": os.path.join(os.path.dirname(__file__),"user_database", "soed_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "guest_database", "soed_guest_rules.json"),
    },
    "faculty_staff": {
        "user": os.path.join(os.path.dirname(__file__),"user_database", "faculty_staff_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "guest_database", "faculty_staff_guest_rules.json"),
    },
}

def load_rules(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_rules(file_path, rules):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving rules to {file_path}: {e}")

def add_rule_to_file(file_path, rule):
    rules = load_rules(file_path)
    rules.append(rule)
    save_rules(file_path, rules)
    return len(rules) - 1

def add_rule(user_type, category, keywords, response):
    """
    Add a rule to the appropriate JSON files based on user_type and category.
    user_type: "user", "guest", or "both"
    category: one of the keys in CATEGORY_FILES
    keywords: list of keywords
    response: response string
    Returns a dict with added rule IDs for each file.
    """
    rule = {
        "keywords": keywords,
        "response": response,
        "user_type": user_type,
        "category": category
    }
    added_ids = {}
    if user_type == "user" or user_type == "both":
        user_file = CATEGORY_FILES[category]["user"]
        added_ids["user"] = add_rule_to_file(user_file, rule)
    if user_type == "guest" or user_type == "both":
        guest_file = CATEGORY_FILES[category]["guest"]
        added_ids["guest"] = add_rule_to_file(guest_file, rule)
    return added_ids
