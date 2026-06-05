#!/usr/bin/env python3
"""
Test script for the new Intent Router.

Demonstrates how the router handles different scenarios.
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(
    0,
    str(Path(__file__).parent / "backend")
)


def test_router_logic():
    """
    Test router decision logic without requiring actual PDFs.
    """
    
    print("=" * 70)
    print("INTENT ROUTER TEST SCENARIOS")
    print("=" * 70)
    
    # Mock router responses for demonstration
    test_cases = [
        {
            "name": "Resume with CAD mention - General Question",
            "query": "Describe this document",
            "preview_contains": ["resume", "pdf", "software engineer", "cad projects"],
            "expected": "rag_search",
            "expected_confidence": 0.95,
        },
        {
            "name": "Resume with CAD mention - Review Request",
            "query": "Review this resume for me",
            "preview_contains": ["resume", "pdf", "software engineer", "cad projects"],
            "expected": "rag_search",
            "expected_confidence": 0.92,
        },
        {
            "name": "CAD Drawing - Summary Request",
            "query": "Summarize this drawing",
            "preview_contains": ["title block", "drawing number", "scale", "revision"],
            "expected": "rag_search",
            "expected_confidence": 0.90,
        },
        {
            "name": "CAD Drawing - Validation Request",
            "query": "Review this drawing for errors and check array layout",
            "preview_contains": ["title block", "array layout", "drawing number", "scale"],
            "expected": "cad_review",
            "expected_confidence": 0.95,
        },
        {
            "name": "Article on CAD - General Question",
            "query": "What is this document about?",
            "preview_contains": ["cad software", "features", "tutorial", "guide"],
            "expected": "rag_search",
            "expected_confidence": 0.85,
        },
        {
            "name": "Solar Panel Drawing - QA Request",
            "query": "Validate this drawing - check for mismatches",
            "preview_contains": ["roof area", "array layout", "key plan", "drawing"],
            "expected": "cad_review",
            "expected_confidence": 0.98,
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print()
        print(f"Test {i}: {test_case['name']}")
        print("-" * 70)
        print(f"Query: {test_case['query']}")
        print(f"Preview mentions: {', '.join(test_case['preview_contains'])}")
        print()
        print(f"Expected tool: {test_case['expected']}")
        print(f"Expected confidence: {test_case['expected_confidence']}")
        print()


def show_router_prompt():
    """
    Show the actual router prompt used by the LLM.
    """
    
    print("=" * 70)
    print("ROUTER LLM PROMPT")
    print("=" * 70)
    print("""
You are an AI Router for document processing.

Your job is to decide which tool should 
answer the user's request based on:

1. The user's explicit intent (what they want to do)
2. The document preview (what type of content)

Tools available:

cad_review - ONLY use when:
  AND user explicitly asks for: review, validate, check, 
      QA, error checking, mismatch detection
  AND document contains CAD/engineering content: 
      drawing, schematic, blueprint, array layout, roof area, etc.

rag_search - use for EVERYTHING ELSE:
  - summarize, explain, answer questions
  - resume, invoice, legal, academic content
  - general document analysis
  - even if document mentions CAD but user isn't asking for QA

Return ONLY valid JSON (no markdown, no code fence):

{
    "tool": "cad_review" or "rag_search",
    "confidence": 0.0 to 1.0,
    "reason": "brief explanation"
}
    """)


def show_safety_layer():
    """
    Show the CAD marker safety layer logic.
    """
    
    print("=" * 70)
    print("SAFETY LAYER: CAD MARKER VERIFICATION")
    print("=" * 70)
    print("""
After LLM decision, if tool == "cad_review":

CAD_MARKERS = [
    "roof area",
    "array layout", 
    "key plan",
    "engineer's stamp",
    "sheet sm.",
    "title block",
    "drawing number",
    "revision",
    "scale",
    "grid reference",
    "electrical diagram",
    "wiring diagram",
    "schematic",
    "blueprint",
    # ... 20+ markers total
]

score = count markers in document preview

If score >= 3:
    ✓ Document is verified as CAD
    → Run expensive OCR
    
If score < 3:
    ✗ Document is NOT a CAD drawing
    → Downgrade to rag_search
    → Update confidence score
    → Return new decision with reason

Example:
    LLM says: cad_review (confidence: 0.65)
    Markers found: 1 ("cad")
    Score: 1 < 3
    → Final decision: rag_search (confidence: 0.39)
    → Reason: "Document lacks CAD markers. Using general RAG instead."
    """)


def show_decision_examples():
    """
    Show real JSON decision examples.
    """
    
    print("=" * 70)
    print("ROUTER DECISION EXAMPLES")
    print("=" * 70)
    
    examples = [
        {
            "name": "Resume (General Question)",
            "decision": {
                "tool": "rag_search",
                "confidence": 0.97,
                "reason": "Document is a resume. While it mentions CAD projects, user is requesting general description, not CAD validation."
            }
        },
        {
            "name": "CAD Drawing (Validation Request)",
            "decision": {
                "tool": "cad_review",
                "confidence": 0.98,
                "reason": "User explicitly requesting review and error checking. Document is an engineering drawing."
            }
        },
        {
            "name": "Article on CAD (Safety Layer Downgrade)",
            "decision": {
                "tool": "rag_search",
                "confidence": 0.39,
                "reason": "Document lacks CAD markers. Using general RAG instead."
            }
        },
        {
            "name": "Solar Drawing (High Confidence)",
            "decision": {
                "tool": "cad_review",
                "confidence": 0.95,
                "reason": "User explicitly requested validation. Document contains array layout, roof area, and drawing markers."
            }
        },
    ]
    
    for example in examples:
        print()
        print(f"Scenario: {example['name']}")
        print("-" * 70)
        print(json.dumps(example['decision'], indent=2))


def show_benefits():
    """
    Show key benefits of the new architecture.
    """
    
    print("=" * 70)
    print("BENEFITS OF INTENT-BASED ROUTING")
    print("=" * 70)
    print("""
✓ Flexible Intent Matching
  Handles edge cases where content is ambiguous (resume with CAD, etc.)

✓ Cost Reduction  
  Safety layer prevents expensive OCR on non-CAD documents

✓ Scalable
  Easy to add new tools: invoice_agent, resume_agent, legal_agent

✓ Explainable
  Router provides reasoning for each decision via JSON

✓ Verifiable
  Confidence scores help identify uncertain decisions

✓ Avoids Brittle Rules
  No more keyword-based classification that fails on real-world data

✓ User Intent Focused
  What matters is what users want to do, not document type
    """)


if __name__ == "__main__":
    
    print("\n")
    show_router_prompt()
    
    print("\n")
    show_safety_layer()
    
    print("\n")
    show_decision_examples()
    
    print("\n")
    test_router_logic()
    
    print("\n")
    show_benefits()
    
    print("\n" + "=" * 70)
    print("To test with actual PDFs, run ask_question() with sample queries")
    print("=" * 70 + "\n")
