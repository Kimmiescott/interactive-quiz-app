from app import db, Question, app

# Sample Questions
questions = [
    {
        "question_text": "What is the capital of France?",
        "options": {"A": "Paris", "B": "London", "C": "Berlin", "D": "Madrid"},
        "correct_option": "A",
    },
    {
        "question_text": "Which programming language is known as the backbone of web development?",
        "options": {"A": "Python", "B": "JavaScript", "C": "Ruby", "D": "C++"},
        "correct_option": "B",
    },
    {
        "question_text": "What is 5 + 7?",
        "options": {"A": "10", "B": "11", "C": "12", "D": "13"},
        "correct_option": "C",
    },
]

# Insert Questions into the Database
with app.app_context():  # Explicitly set the app context
    db.create_all()  # Ensure tables exist
    for q in questions:
        question = Question(
            question_text=q["question_text"],
            options=q["options"],
            correct_option=q["correct_option"],
        )
        db.session.add(question)
    db.session.commit()

print("Questions added to the database!")
