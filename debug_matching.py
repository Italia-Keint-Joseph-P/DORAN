from update_chatbot import ChatbotDB

db = ChatbotDB()

print('=== SEARCHING FOR ENROLLMENT-RELATED RULES ===')

# Check user rules
user_rules = db.get_user_rules()
print(f'\nUser rules containing "enrollment": {len([r for r in user_rules if "enrollment" in r.get("question", "").lower() or "enrollment" in r.get("answer", "").lower()])}')

# Check guest rules
guest_rules = db.get_guest_rules()
print(f'Guest rules containing "enrollment": {len([r for r in guest_rules if "enrollment" in r.get("question", "").lower() or "enrollment" in r.get("answer", "").lower()])}')

# Check locations
locations = db.get_location_rules()
print(f'Location rules containing "enrollment": {len([r for r in locations if "enrollment" in r.get("question", "").lower() or "enrollment" in r.get("response", "").lower()])}')

# Check visuals
visuals = db.get_visual_rules()
print(f'Visual rules containing "enrollment": {len([r for r in visuals if "enrollment" in r.get("question", "").lower() or "enrollment" in r.get("response", "").lower()])}')

# Check FAQs
faqs = db.get_faqs()
enrollment_faqs = [faq for faq in faqs if "enrollment" in faq.get("question", "").lower()]
print(f'FAQ rules containing "enrollment": {len(enrollment_faqs)}')

for faq in enrollment_faqs:
    print(f'  FAQ: {faq.get("question", "")}')
    print(f'  Answer: {faq.get("answer", "")[:100]}...')

print('\n=== CHECKING FOR "ICTzen" CONTENT ===')
ictzen_rules = []
for rule in user_rules + guest_rules + locations + visuals:
    if "ictzen" in rule.get("question", "").lower() or "ictzen" in rule.get("answer", "").lower() or "ictzen" in rule.get("response", "").lower():
        ictzen_rules.append(rule)

print(f'Rules containing "ICTzen": {len(ictzen_rules)}')
for rule in ictzen_rules[:3]:  # Show first 3
    print(f'  Rule: {rule.get("question", rule.get("answer", rule.get("response", "")))[:100]}...')

db.close()
