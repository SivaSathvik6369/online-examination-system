# Question bank management
questions_bank = [
    {
        "id": 1,
        "question": "What is the primary branch in modern Git repositories?",
        "options": ["master", "main", "trunk", "root"],
        "answer": "main"
    },
    {
        "id": 2,
        "question": "Which command is used to find a bug using binary search?",
        "options": ["git search", "git find", "git bisect", "git blame"],
        "answer": "git bisect"
    },
    {
        "id": 3,
        "question": "What does HTTP status code 200 signify?",
        "options": ["Not Found", "OK", "Unauthorized", "Internal Server Error"],
        "answer": "OK"
    }
]

def get_all_questions():
    return questions_bank

def get_question_by_id(qid):
    for q in questions_bank:
        if q["id"] == qid:
            return q
    return None
