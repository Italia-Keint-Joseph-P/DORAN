from app import app
from chatbot import Chatbot

with app.app_context():
    cb = Chatbot()
    print('Testing sample queries...')
    test_queries = [
        'What is the location of the library?',
        'How to contact the dean?',
        'Where is the computer lab?',
        'What are the admission requirements?',
        'Email of the registrar',
        'Contact the library'
    ]

    for q in test_queries:
        print(f'Query: {q}')
        response = cb.get_response(q)
        print(f'Response: {response}')
        print('---')
