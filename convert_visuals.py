import json

def generate_questions(keywords, description):
    """
    Generate 3-5 natural language questions based on keywords and description.
    """
    questions = []

    # Flatten keywords if nested
    flat_keywords = []
    for kw in keywords:
        if isinstance(kw, list):
            flat_keywords.extend(kw)
        else:
            flat_keywords.append(kw)

    # Use keywords to form questions
    keyword_str = " ".join(flat_keywords).lower()

    # Generate questions
    questions.append(f"What is {keyword_str}?")
    questions.append(f"Can you show me {keyword_str}?")
    questions.append(f"Where can I find information about {keyword_str}?")
    questions.append(f"Tell me about {keyword_str}.")
    questions.append(f"What are the details on {keyword_str}?")

    # If description has specific info, add more
    if "faculty" in description.lower() or "teacher" in description.lower():
        questions.append(f"Who are the {keyword_str}?")
    elif "uniform" in description.lower():
        questions.append(f"What does the {keyword_str} look like?")
    elif "officer" in description.lower() or "representative" in description.lower():
        questions.append(f"Who is the {keyword_str}?")

    return questions[:5]  # Limit to 5

def convert_visuals():
    with open('database/visuals/visuals.json', 'r') as f:
        data = json.load(f)

    for entry in data:
        keywords = entry.pop('keywords', [])
        description = entry.get('description', '')
        questions = generate_questions(keywords, description)
        entry['questions'] = questions

    with open('database/visuals/visuals.json', 'w') as f:
        json.dump(data, f, indent=4)

    print("Converted visuals.json to use 'questions' instead of 'keywords'")

if __name__ == "__main__":
    convert_visuals()
