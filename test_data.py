from update_chatbot import ChatbotDB

db = ChatbotDB()

print('=== SAMPLE USER RULES ===')
user_rules = db.get_user_rules()[:3]
for rule in user_rules:
    print(f'ID: {rule["id"]}, Question: {rule.get("question", "N/A")}, Answer: {rule.get("answer", "N/A")[:50]}...')

print('\n=== SAMPLE LOCATION RULES ===')
loc_rules = db.get_location_rules()[:3]
for rule in loc_rules:
    print(f'ID: {rule["id"]}, Questions: {rule.get("questions", [])}, Response: {rule.get("response", "N/A")[:50]}...')

print('\n=== SAMPLE FAQS ===')
faqs = db.get_faqs()[:3]
for rule in faqs:
    print(f'Question: {rule.get("question", "N/A")}, Answer: {rule.get("answer", "N/A")[:50]}...')

db.close()
