import json

def generate_questions(keywords, description):
    """
    Generate 3-5 natural language questions based on keywords and description.
    Extract the specific room/building name from the description.
    """
    questions = []

    # Extract location name from description
    location_name = ""
    import re
    # Look for patterns like "E3 room", "J10 room", "ICT office", etc.
    match = re.search(r'(\w+\d*|\w+)\s+(room|office|building)', description, re.IGNORECASE)
    if match:
        location_name = match.group(1).strip()
    else:
        # Fallback: look for capitalized words with numbers
        words = description.split()
        for word in words:
            if any(char.isdigit() for char in word) and word[0].isupper():
                location_name = word
                break
        if not location_name:
            # Use first keyword if available
            if keywords:
                location_name = " ".join(keywords[0]) if isinstance(keywords[0], list) else str(keywords[0])

    # If still no name, default
    if not location_name:
        location_name = "this location"

    # Generate questions based on type
    if "room" in description.lower():
        questions.append(f"Where is the {location_name} room?")
        questions.append(f"How do I get to {location_name} room?")
        questions.append(f"What is the location of {location_name} room?")
        questions.append(f"Can you show me {location_name} room?")
        questions.append(f"Where can I find {location_name} room?")
    elif "office" in description.lower():
        questions.append(f"Where is the {location_name} office?")
        questions.append(f"How do I find {location_name} office?")
        questions.append(f"What is the location of {location_name} office?")
        questions.append(f"Where can I locate {location_name} office?")
    elif "building" in description.lower():
        questions.append(f"Where is the {location_name} building?")
        questions.append(f"How do I get to {location_name} building?")
        questions.append(f"What is the location of {location_name} building?")
    else:
        questions.append(f"Where is {location_name}?")
        questions.append(f"How do I find {location_name}?")
        questions.append(f"What is the location of {location_name}?")
        questions.append(f"Can you show me {location_name}?")

    # Ensure at least 3 questions
    while len(questions) < 3:
        questions.append(f"Where can I find {location_name}?")

    return questions[:5]  # Limit to 5

def convert_locations():
    with open('database/locations/locations.json', 'r') as f:
        data = json.load(f)

    for entry in data:
        keywords = entry.pop('keywords', [])
        description = entry.get('description', '')
        questions = generate_questions(keywords, description)
        entry['questions'] = questions

    with open('database/locations/locations.json', 'w') as f:
        json.dump(data, f, indent=4)

    print("Converted locations.json to use 'questions' instead of 'keywords'")

if __name__ == "__main__":
    convert_locations()
