from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

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
    options = db.Column(db.JSON, nullable=False)  # {'A': 'Option1', 'B': 'Option2', ...}
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
        hashed_password = generate_password_hash(password, method='sha256')

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
            return redirect(url_for('quiz'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        score = 0
        for question in Question.query.all():
            selected_option = request.form.get(f'question_{question.id}')
            if selected_option == question.correct_option:
                score += 1

        new_result = QuizResult(user_id=user_id, score=score)
        db.session.add(new_result)
        db.session.commit()
        return redirect(url_for('results'))

    questions = Question.query.all()
    return render_template('quiz.html', questions=questions)

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    results = QuizResult.query.filter_by(user_id=user_id).all()
    return render_template('results.html', results=results)

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

# REST API for quiz questions
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
        db.create_all()  # Ensure database tables are created
    app.run(debug=True)
