"""
Test cases for evaluating the MIB RAG Chatbot.

Each test case has:
- question: The user question to ask
- category: The type of test
- expected_behavior: What the system should do
- expected_sources: Document names that should be referenced (if applicable)
"""

TEST_CASES = [
    # --- Category 1: Direct factual questions ---
    {
        "question": "What services does MIB Tech Solutions provide?",
        "category": "direct_factual",
        "expected_behavior": "Should list MIB services from the documentation",
        "should_be_grounded": True,
    },
    {
        "question": "What is the contact information for MIB Tech Solutions?",
        "category": "direct_factual",
        "expected_behavior": "Should provide contact details from the documents",
        "should_be_grounded": True,
    },

    # --- Category 2: Paraphrased questions ---
    {
        "question": "What kind of help can I get from MIB?",
        "category": "paraphrased",
        "expected_behavior": "Should understand this as asking about services/support",
        "should_be_grounded": True,
    },
    {
        "question": "Tell me about what MIB does",
        "category": "paraphrased",
        "expected_behavior": "Should describe MIB's offerings from the documents",
        "should_be_grounded": True,
    },

    # --- Category 3: Multi-chunk questions ---
    {
        "question": "Give me a complete overview of MIB Tech Solutions including their services and support process",
        "category": "multi_chunk",
        "expected_behavior": "Should synthesize information from multiple document sections",
        "should_be_grounded": True,
    },

    # --- Category 4: Follow-up questions (test in sequence) ---
    {
        "question": "What products does MIB offer?",
        "category": "follow_up_initial",
        "expected_behavior": "Should list products — this is the setup for a follow-up",
        "should_be_grounded": True,
    },
    {
        "question": "Tell me more about those",
        "category": "follow_up",
        "expected_behavior": "Should understand 'those' refers to the products just mentioned",
        "should_be_grounded": True,
        "requires_session": True,
    },

    # --- Category 5: Out-of-scope questions ---
    {
        "question": "What is the weather in New York today?",
        "category": "out_of_scope",
        "expected_behavior": "Should clearly state this is not in the MIB documents",
        "should_be_grounded": False,
    },
    {
        "question": "Can you write Python code for a web scraper?",
        "category": "out_of_scope",
        "expected_behavior": "Should decline and state this is outside the MIB knowledge base",
        "should_be_grounded": False,
    },
    {
        "question": "What is Apple's stock price?",
        "category": "out_of_scope",
        "expected_behavior": "Should state this information is not in MIB documents",
        "should_be_grounded": False,
    },

    # --- Category 6: Ambiguous questions ---
    {
        "question": "How much does it cost?",
        "category": "ambiguous",
        "expected_behavior": "Should either ask for clarification or state what pricing info is available",
        "should_be_grounded": True,
    },
    {
        "question": "Is it good?",
        "category": "ambiguous",
        "expected_behavior": "Should ask for clarification about what 'it' refers to",
        "should_be_grounded": False,
    },

    # --- Category 7: Terminology variations ---
    {
        "question": "Do you have a FAQ section?",
        "category": "terminology_variation",
        "expected_behavior": "Should reference FAQ content from the MIB documents",
        "should_be_grounded": True,
    },
    {
        "question": "What's your customer support like?",
        "category": "terminology_variation",
        "expected_behavior": "Should describe support process from the documents",
        "should_be_grounded": True,
    },
]


def get_test_cases_by_category(category: str) -> list[dict]:
    return [tc for tc in TEST_CASES if tc["category"] == category]


def get_all_categories() -> list[str]:
    return list({tc["category"] for tc in TEST_CASES})
