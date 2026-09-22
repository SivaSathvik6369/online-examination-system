# Scoring and grading logic
from config import PASSING_PERCENTAGE

def calculate_score(submissions, questions):
    """
    submissions: dict of question_id -> student_answer
    questions: list of question dicts
    returns: (score_percentage, passed)
    """
    if not questions:
        return 0.0, False

    correct_count = 0
    total = len(questions)

    for q in questions:
        qid = q["id"]
        if submissions.get(qid) == q["answer"]:
            correct_count += 1

    percentage = (correct_count / total) * 100.0
    passed = percentage >= PASSING_PERCENTAGE
    return percentage, passed
