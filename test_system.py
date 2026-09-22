# Automated system test suite
from questions import get_all_questions
from scoring import calculate_score

def test_scoring_system():
    questions = get_all_questions()
    perfect_submission = {1: "main", 2: "git bisect", 3: "OK"}
    score, passed = calculate_score(perfect_submission, questions)
    assert score == 100.0, f"Expected 100.0, got {score}"
    assert passed is True, "Expected pass to be True"

    partial_submission = {1: "main", 2: "wrong", 3: "wrong"}
    score, passed = calculate_score(partial_submission, questions)
    assert round(score, 2) == 33.33, f"Expected 33.33, got {score}"
    assert passed is False, "Expected pass to be False"
    print("All tests passed successfully!")

if __name__ == "__main__":
    test_scoring_system()
