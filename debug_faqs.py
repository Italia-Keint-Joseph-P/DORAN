from update_chatbot import ChatbotDB

db = ChatbotDB()

print('=== ALL FAQS IN DATABASE ===')
faqs = db.get_faqs()
for i, faq in enumerate(faqs):
    print(f'{i+1}. Question: {faq.get("question", "N/A")}')
    print(f'   Answer: {faq.get("answer", "N/A")[:100]}...')
    print()

db.close()
