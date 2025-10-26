import json

with open('database/visuals/visuals.json', 'r') as f:
    data = json.load(f)

for item in data:
    desc = item['description'].lower()
    if item['questions'] == ["What is ?", "Can you show me ?", "Where can I find information about ?", "Tell me about .", "What are the details on ?"]:
        # Generate new questions based on description
        if 'uniform' in desc:
            school = desc.split('uniform')[0].strip().title()
            item['questions'] = [
                f"What is the uniform for {school}?",
                "Can you show me the uniform?",
                "Tell me about the uniform.",
                "What are the details on the uniform?",
                "Where can I find information about the uniform?"
            ]
        elif 'student council' in desc or 'council' in desc:
            council_type = 'ICT Student Council' if 'ict' in desc else 'Student Council'
            item['questions'] = [
                f"Who are the {council_type} members?",
                f"Can you show me the {council_type}?",
                f"Tell me about the {council_type}.",
                f"What are the details on the {council_type}?",
                f"Where can I find information about the {council_type}?"
            ]
        elif 'ictzen' in desc:
            # Extract role
            if 'is the' in desc:
                role = desc.split('is the')[1].split('a.y')[0].strip().title()
            else:
                role = 'ICTzen staff'
            item['questions'] = [
                f"Who is the {role}?",
                f"Can you show me the {role}?",
                f"Tell me about the {role}.",
                f"What is the {role}'s role?",
                f"Where can I find information about the {role}?"
            ]
        elif 'research coordinator' in desc or 'program head' in desc or 'director' in desc or 'adviser' in desc or 'professor' in desc or 'instructor' in desc or 'lecturer' in desc or 'aide' in desc:
            # Person entry
            if ',' in item['description']:
                name = item['description'].split(',')[0].strip()
            else:
                name = item['description'].split(' is ')[0].strip()
            item['questions'] = [
                f"Who is {name}?",
                f"Can you show me {name}?",
                f"Tell me about {name}.",
                f"What is {name}'s role?",
                f"Where can I find information about {name}?"
            ]
        else:
            # Default
            item['questions'] = [
                "What is this?",
                "Can you show me this?",
                "Tell me about this.",
                "What are the details on this?",
                "Where can I find information about this?"
            ]

with open('database/visuals/visuals.json', 'w') as f:
    json.dump(data, f, indent=4)
