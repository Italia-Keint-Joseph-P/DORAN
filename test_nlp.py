from app import app
from chatbot import Chatbot
from sklearn.metrics import precision_score, recall_score
import time

def evaluate_responses(true_responses, predicted_responses):
    """
    Simple evaluation: precision and recall based on whether response is not fallback.
    Assumes non-fallback responses are correct matches.
    """
    y_true = [1 if 'fallback' not in resp.lower() else 0 for resp in true_responses]  # 1 if expected match, 0 if fallback
    y_pred = [1 if 'sorry' not in resp.lower() and 'didn\'t' not in resp.lower() else 0 for resp in predicted_responses]
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    return precision, recall

with app.app_context():
    cb = Chatbot()
    print('Testing sample queries with evaluation...')
    test_queries = [
        ('What is the location of the library?', 'location'),
        ('How to contact the dean?', 'contact'),
        ('Where is the computer lab?', 'location'),
        ('What are the admission requirements?', 'info'),
        ('Email of the registrar', 'contact'),
        ('Contact the library', 'contact'),
        ('Tell me about the uniform', 'info'),
        ('Who is the director?', 'info'),
        ('Where can I find the office?', 'location'),
        ('What is the FAQ?', 'faq')
    ]

    predicted_responses = []
    true_labels = []  # 1 if query should match, 0 if fallback expected

    start_time = time.time()
    for q, intent in test_queries:
        print(f'Query: {q} (Intent: {intent})')
        response = cb.get_response(q, session_id='test_session')
        print(f'Response: {response[:100]}...' if len(response) > 100 else f'Response: {response}')
        predicted_responses.append(response)
        # Assume all queries should match (not fallback) for evaluation
        true_labels.append(1)
        print('---')

    end_time = time.time()
    avg_time = (end_time - start_time) / len(test_queries)
    print(f'Average response time: {avg_time:.3f} seconds per query')

    # Simple evaluation (precision/recall assuming all queries should match)
    precision, recall = evaluate_responses(['match'] * len(test_queries), predicted_responses)
    print(f'Precision: {precision:.3f}')
    print(f'Recall: {recall:.3f}')
    print(f'F1 Score: {2 * precision * recall / (precision + recall) if precision + recall > 0 else 0:.3f}')
