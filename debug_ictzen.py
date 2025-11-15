from update_chatbot import ChatbotDB

db = ChatbotDB()

print('=== ICTZEN RULES THAT MIGHT BE MATCHING ===')

all_rules = db.get_user_rules() + db.get_guest_rules() + db.get_location_rules() + db.get_visual_rules()

ictzen_rules = []
for rule in all_rules:
    text = rule.get('question', '') + ' ' + rule.get('answer', '') + ' ' + rule.get('response', '')
    if 'ictzen' in text.lower():
        ictzen_rules.append(rule)

print(f'Found {len(ictzen_rules)} ICTzen rules')

for i, rule in enumerate(ictzen_rules[:5]):  # Show first 5
    print(f'\n{i+1}. ID: {rule.get("id")}')
    print(f'   Question: {rule.get("question", "")}')
    print(f'   Answer/Response: {(rule.get("answer", "") or rule.get("response", ""))[:150]}...')

# Check if any enrollment-related rules exist
print('\n=== CHECKING ENROLLMENT FAQ MATCHING ===')
faqs = db.get_faqs()
enrollment_faqs = [faq for faq in faqs if 'enrollment requirements' in faq.get('question', '').lower()]

print(f'Enrollment requirement FAQs: {len(enrollment_faqs)}')
for faq in enrollment_faqs[:3]:
    print(f'  Question: {faq.get("question")}')
    print(f'  Answer: {faq.get("answer")[:100]}...')

db.close()
