from chatbot import Chatbot

print('Testing enrollment query...')
bot = Chatbot()

query = "What is the Enrollment Requirements?"
print(f'Query: "{query}"')

response = bot.get_response(query)
print(f'Response: {response[:300]}...')

# Also test exact match
query2 = "What are the enrollment requirements for freshmen or first year or 1st year?"
print(f'\nQuery: "{query2}"')
response2 = bot.get_response(query2)
print(f'Response: {response2[:300]}...')
