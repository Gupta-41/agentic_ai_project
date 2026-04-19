import re
import streamlit as st


def extract_questions_from_text(text):
    """
    tries to pull out individual questions from question paper text
    looks for patterns like Q1, 1., (1), etc.
    """
    questions = []

    # common question patterns in indian university papers
    patterns = [
        r'(?:Q\.?\s*\d+[\.\):]|^\d+[\.\):])\s*(.+?)(?=(?:Q\.?\s*\d+[\.\):]|^\d+[\.\):])|$)',
        r'(?:^|\n)\s*\d+\.\s+(.+?)(?=\n\s*\d+\.|\Z)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        if matches and len(matches) > 2:
            questions = [q.strip() for q in matches if len(q.strip()) > 20]
            break

    # if regex didn't work, just split by newlines and filter
    if not questions:
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) > 30 and any(line.startswith(str(i)) for i in range(1, 30)):
                questions.append(line)

    return questions


def categorize_question(question_text):
    """
    figure out what kind of question this is
    based on keywords - common in VTU/Anna University papers
    """
    q = question_text.lower()

    if any(word in q for word in ["define", "what is", "what are", "list"]):
        return "definition/listing"
    elif any(word in q for word in ["explain", "describe", "discuss", "elaborate"]):
        return "explanation"
    elif any(word in q for word in ["compare", "differentiate", "distinguish", "difference"]):
        return "comparison"
    elif any(word in q for word in ["solve", "calculate", "find", "compute", "evaluate"]):
        return "numerical/problem"
    elif any(word in q for word in ["design", "implement", "write", "code", "draw"]):
        return "implementation"
    else:
        return "general"


def get_question_marks(question_text):
    """extract marks if mentioned in the question"""
    # looks for patterns like (10 marks), [5M], (8), etc.
    patterns = [r'\((\d+)\s*marks?\)', r'\[(\d+)M\]', r'\((\d+)\)$']
    for pattern in patterns:
        match = re.search(pattern, question_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def build_exam_query(question_text, subject=""):
    """
    takes a raw exam question and turns it into a better search query
    """
    # remove question numbers and marks info
    cleaned = re.sub(r'^[Qq]?\.?\s*\d+[\.\):]?\s*', '', question_text)
    cleaned = re.sub(r'\(\d+\s*marks?\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    if subject:
        return f"{subject}: {cleaned}"
    return cleaned


def format_answer_for_marks(answer, marks):
    """
    gives a hint to the LLM about how detailed the answer should be
    based on marks allocated
    """
    if not marks:
        return answer

    if marks <= 2:
        return f"[2-3 line answer expected]\n{answer}"
    elif marks <= 5:
        return f"[Short answer, ~half page expected]\n{answer}"
    elif marks <= 10:
        return f"[Detailed answer, ~1 page expected]\n{answer}"
    else:
        return f"[Very detailed answer with examples, diagrams mentioned]\n{answer}"