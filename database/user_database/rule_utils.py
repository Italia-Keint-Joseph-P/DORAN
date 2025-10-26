import json
import os
import logging
from uuid import uuid4

# Main combined files paths
USER_COMBINED_FILE = os.path.join(os.path.dirname(__file__), "all_user_rules.json")
GUEST_COMBINED_FILE = os.path.join(os.path.dirname(__file__), "..", "guest_database", "all_guest_rules.json")

# Category mappings (for reference)
CATEGORIES = ["SOICT", "SOIT", "SOED", "SOBM", "Registrar", "Faculty"]

# Mapping of categories to their user and guest JSON files
CATEGORY_FILES = {
    "soict": {
        "user": os.path.join(os.path.dirname(__file__), "soict_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "..", "guest_database", "soict_guest_rules.json")
    },
    "soit": {
        "user": os.path.join(os.path.dirname(__file__), "soit_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "..", "guest_database", "soit_guest_rules.json")
    },
    "soed": {
        "user": os.path.join(os.path.dirname(__file__), "soed_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "..", "guest_database", "soed_guest_rules.json")
    },
    "sobm": {
        "user": os.path.join(os.path.dirname(__file__), "sobm_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "..", "guest_database", "sobm_guest_rules.json")
    },
    "registrar": {
        "user": os.path.join(os.path.dirname(__file__), "registrar_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "..", "guest_database", "registrar_guest_rules.json")
    },
    "faculty": {
        "user": os.path.join(os.path.dirname(__file__), "faculty_rules.json"),
        "guest": os.path.join(os.path.dirname(__file__), "..", "guest_database", "faculty_staff_guest_rules.json")
    }
}

def load_combined_file(file_path):
    """Load the combined rules file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize with empty categories if file doesn't exist
        return {category: [] for category in CATEGORIES}

def save_combined_file(file_path, data):
    """Save data to the combined rules file"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving rules to {file_path}: {e}")

def add_rule(user_type, category, question, response):
    """
    Add a rule to the appropriate combined file based on user_type and category.
    user_type: "user", "guest", or "both"
    category: one of the categories in CATEGORIES
    question: question string
    response: response string
    Returns the rule ID.
    """
    rule_id = str(uuid4())

    # Create rule object
    rule = {
        "question": question,
        "answer": response,
        "id": rule_id
    }

    # Handle user rules
    if user_type == "user" or user_type == "both":
        file_path = USER_COMBINED_FILE
        data = load_combined_file(file_path)
        if category in data:
            data[category].append(rule)
        else:
            data[category] = [rule]
        save_combined_file(file_path, data)

    # Handle guest rules
    if user_type == "guest" or user_type == "both":
        file_path = GUEST_COMBINED_FILE
        data = load_combined_file(file_path)
        if category in data:
            data[category].append(rule)
        else:
            data[category] = [rule]
        save_combined_file(file_path, data)

    return rule_id

def delete_rule(rule_id, user_type='user', category='SOICT'):
    """
    Delete a rule from the appropriate combined file based on user_type and category.
    user_type: "user" or "guest"
    category: one of the categories in CATEGORIES
    rule_id: the ID of the rule to delete
    Returns True if rule was deleted, False otherwise.
    """
    # Load the appropriate file
    if user_type == "user":
        file_path = USER_COMBINED_FILE
    else:
        file_path = GUEST_COMBINED_FILE

    data = load_combined_file(file_path)

    # Find and remove the rule
    if category in data:
        original_length = len(data[category])
        data[category] = [rule for rule in data[category] if str(rule.get("id", "")) != str(rule_id)]

        if len(data[category]) < original_length:
            # Save the updated file
            save_combined_file(file_path, data)
            return True

    return False

def edit_rule(rule_id, question, response, user_type='user', category='SOICT'):
    """
    Edit a rule in the appropriate combined file based on user_type and category.
    user_type: "user" or "guest"
    category: one of the categories in CATEGORIES
    rule_id: the ID of the rule to edit
    question: new question
    response: new response
    Returns True if rule was edited, False otherwise.
    """
    # Load the appropriate file
    if user_type == "user":
        file_path = USER_COMBINED_FILE
    else:
        file_path = GUEST_COMBINED_FILE

    data = load_combined_file(file_path)

    # Find and edit the rule
    if category in data:
        for rule in data[category]:
            if str(rule.get("id", "")) == str(rule_id):
                rule["question"] = question
                rule["answer"] = response
                # Save the updated file
                save_combined_file(file_path, data)
                return True

    return False

def add_empty_category(category_name, user_type='both'):
    """
    Add an empty category to the appropriate combined file(s) if it doesn't exist.
    user_type: "user", "guest", or "both"
    category_name: the name of the category to add
    Returns True if category was added, False otherwise.
    """
    added = False

    # Handle user rules
    if user_type == "user" or user_type == "both":
        file_path = USER_COMBINED_FILE
        data = load_combined_file(file_path)

        if category_name not in data:
            data[category_name] = []
            save_combined_file(file_path, data)
            added = True

    # Handle guest rules
    if user_type == "guest" or user_type == "both":
        file_path = GUEST_COMBINED_FILE
        data = load_combined_file(file_path)

        if category_name not in data:
            data[category_name] = []
            save_combined_file(file_path, data)
            added = True

    return added

def remove_category(category_name, user_type='both'):
    """
    Remove a category from the appropriate combined file(s).
    user_type: "user", "guest", or "both"
    category_name: the name of the category to remove
    Returns True if category was removed, False otherwise.
    """
    removed = False

    # Handle user rules
    if user_type == "user" or user_type == "both":
        file_path = USER_COMBINED_FILE
        data = load_combined_file(file_path)

        if category_name in data:
            del data[category_name]
            save_combined_file(file_path, data)
            removed = True

    # Handle guest rules
    if user_type == "guest" or user_type == "both":
        file_path = GUEST_COMBINED_FILE
        data = load_combined_file(file_path)

        if category_name in data:
            del data[category_name]
            save_combined_file(file_path, data)
            removed = True

    return removed
