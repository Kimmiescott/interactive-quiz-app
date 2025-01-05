from app import db, Question, app

with app.app_context():
    # Delete all questions
    num_deleted = Question.query.delete()
    db.session.commit()
    print(f"Deleted {num_deleted} questions successfully!")

    # Verify deletion
    remaining_questions = Question.query.count()
    print(f"Remaining questions in the database: {remaining_questions}")
