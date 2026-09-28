"""
RAG Evaluation Runner.

Runs test cases against the RAG pipeline and produces an evaluation report.

Usage:
    cd backend
    python -m app.evaluation.evaluator
"""
import sys
import os
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.evaluation.test_cases import TEST_CASES
from app.rag.pipeline import RAGPipeline

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def evaluate_single(pipeline: RAGPipeline, test_case: dict, session_id: str | None = None) -> dict:
    """Run a single test case and produce an evaluation result."""
    question = test_case["question"]
    try:
        result = pipeline.query(question=question, session_id=session_id)
        return {
            "question": question,
            "category": test_case["category"],
            "expected_behavior": test_case["expected_behavior"],
            "expected_grounded": test_case.get("should_be_grounded", True),
            "actual_grounded": result.grounded,
            "grounding_match": result.grounded == test_case.get("should_be_grounded", True),
            "answer": result.answer,
            "sources_count": len(result.sources),
            "sources": [s["document_name"] for s in result.sources],
            "session_id": result.session_id,
            "status": "success",
        }
    except Exception as e:
        return {
            "question": question,
            "category": test_case["category"],
            "status": "error",
            "error": str(e),
        }


def run_evaluation() -> dict:
    """Run all test cases and produce a summary report."""
    pipeline = RAGPipeline.get_instance()
    results = []
    session_id = None

    print(f"\n{'=' * 70}")
    print("MIB RAG Chatbot — Evaluation Report")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] {test_case['category']}: {test_case['question'][:60]}...")

        # Use session continuity for follow-up tests
        use_session = test_case.get("requires_session", False)
        current_session = session_id if use_session else None

        result = evaluate_single(pipeline, test_case, session_id=current_session)
        results.append(result)

        # Capture session_id for follow-up chain
        if test_case["category"] == "follow_up_initial":
            session_id = result.get("session_id")

        if result["status"] == "success":
            match = "[PASS]" if result["grounding_match"] else "[MISMATCH]"
            print(f"  {match} Grounded: {result['actual_grounded']} "
                  f"(expected: {result['expected_grounded']}) | "
                  f"Sources: {result['sources_count']}")
            # Print first 150 chars of answer
            preview = result["answer"][:150].replace("\n", " ")
            print(f"  -> {preview}...")
        else:
            print(f"  [ERROR] Error: {result['error']}")
        print()

    # Summary
    successful = [r for r in results if r["status"] == "success"]
    grounding_matches = sum(1 for r in successful if r.get("grounding_match", False))

    print(f"{'=' * 70}")
    print(f"SUMMARY")
    print(f"  Total test cases: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Errors: {len(results) - len(successful)}")
    print(f"  Grounding accuracy: {grounding_matches}/{len(successful)} "
          f"({100 * grounding_matches / len(successful):.0f}%)" if successful else "  N/A")
    print(f"{'=' * 70}\n")

    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "successful": len(successful),
        "errors": len(results) - len(successful),
        "grounding_accuracy": grounding_matches / len(successful) if successful else 0,
        "results": results,
    }


if __name__ == "__main__":
    report = run_evaluation()
