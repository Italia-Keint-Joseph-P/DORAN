from chatbot import Chatbot
import time

# Initialize chatbot
print('Initializing chatbot...')
start_time = time.time()
bot = Chatbot()
init_time = time.time() - start_time
print('.2f')

# Test some queries
test_queries = [
    'What student organizations are available in SOIT?',
    'Where is the C13 room?',
    'What is DORAN?',
    'Where is the education faculty room?'
]

print('\n=== TESTING RESPONSES ===')
for query in test_queries:
    print(f'\nQuery: \"{query}\"')
    response = bot.get_response(query)
    print(f'Response: {response[:100]}...')
