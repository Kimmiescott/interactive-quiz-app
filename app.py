from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import time
import datetime
from datetime import timedelta
import os  # Added to read environment variables

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    quizzes = db.relationship('QuizResult', backref='user', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Routes
@app.route('/')
def home():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('home.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('quiz_start_time', None)
    return redirect(url_for('home'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    quiz_duration = timedelta(minutes=15)
    questions = Question.query.all()

    if request.method == 'GET':
        if 'quiz_start_time' not in session:
            session['quiz_start_time'] = time.time()

        elapsed_time = time.time() - session['quiz_start_time']
        remaining_time = max(quiz_duration.total_seconds() - elapsed_time, 0)

        if remaining_time <= 0:
            return redirect(url_for('results'))

        return render_template('quiz.html', questions=questions, remaining_time=remaining_time)

    if request.method == 'POST':
        user_id = session['user_id']
        score = 0
        for question in questions:
            selected_option = request.form.get(f'question_{question.id}')
            if selected_option == question.correct_option:
                score += 1

        new_result = QuizResult(user_id=user_id, score=score)
        db.session.add(new_result)
        db.session.commit()

        session.pop('quiz_start_time', None)
        return redirect(url_for('results'))

@app.route('/results')
def results():
    timeout = request.args.get('timeout', False)
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    results = QuizResult.query.filter_by(user_id=user_id).all()
    return render_template('results.html', results=results, timeout=timeout)

@app.route('/user/<int:user_id>', methods=['GET'])
def user_account(user_id):
    user = User.query.get_or_404(user_id)
    quizzes = QuizResult.query.filter_by(user_id=user_id).all()
    return render_template('user_account.html', user=user, quizzes=quizzes)

@app.route('/add_questions', methods=['GET', 'POST'])
def add_questions():
    if request.method == 'POST':
        question_text = request.form['question_text']
        options = {
            'A': request.form['option_a'],
            'B': request.form['option_b'],
            'C': request.form['option_c'],
            'D': request.form['option_d']
        }
        correct_option = request.form['correct_option']

        new_question = Question(question_text=question_text, options=options, correct_option=correct_option)
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('add_questions'))

    return render_template('add_questions.html')

@app.route('/api/questions', methods=['GET'])
def api_questions():
    questions = Question.query.all()
    question_list = [
        {
            'id': q.id,
            'question_text': q.question_text,
            'options': q.options,
        } for q in questions
    ]
    return jsonify(question_list)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Use the PORT environment variable, or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
