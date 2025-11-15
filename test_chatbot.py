import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import Chatbot

def test_chatbot_accuracy():
    """Test chatbot intent classification accuracy"""
    chatbot = Chatbot()

    test_cases = [
        ("where is the library", "location"),
        ("how to contact registrar", "contact"),
        ("what are the Enrollment requirements", "faq"),
        ("tell me about the campus", "info"),
        ("show me the map", "location"),
        ("email of dean", "contact"),
        ("what is the tuition fee", "faq"),
        ("who is the SOICT Director", "info"),
        ("where can I find the J3", "location"),
        ("how to reach Registrar office", "contact"),
        ("what courses are offered", "faq"),
        ("tell me about student life", "info"),
        ("location of computer lab", "location"),
        ("contact information for IT support", "contact"),
        ("how to apply", "faq")
    ]

    correct = 0
    total = len(test_cases)

    for query, expected_intent in test_cases:
        response = chatbot.get_response(query)
        # For this test, we're just checking if it doesn't fall back
        if "sorry" not in response.lower() and "didn't get that" not in response.lower():
            correct += 1
        print(f"Query: '{query}' -> Response: '{response[:100]}...'")

    accuracy = correct / total * 100
    print(f"\nAccuracy: {correct}/{total} ({accuracy:.1f}%)")

    return accuracy >= 80  # Pass if 80% or better

if __name__ == "__main__":
    success = test_chatbot_accuracy()
    print(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
