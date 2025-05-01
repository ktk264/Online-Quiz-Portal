from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from utils.db import get_db_connection
from utils.auth import authenticate_user, register_user
from utils.quiz_helpers import get_quiz_questions, calculate_score, get_quiz_analytics
import pymysql
from datetime import datetime
from config import Config as config
import webbrowser
from threading import Timer
import os

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Database configuration
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

browser_opened = False

# Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user['UserID']
            session['username'] = user['Username']
            session['role'] = user['Role']
            return redirect(url_for('home'))
        
        return render_template('auth/login.html', error="Invalid credentials")
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        role = request.form['role']
        
        success, message = register_user(username, password, first_name, last_name, email, role)
        if success:
            return redirect(url_for('login'))
        else:
            return render_template('auth/register.html', error=message)
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Student routes
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Get available quizzes
    cursor.execute("""
        SELECT q.*, c.Name as CategoryName 
        FROM quiz q
        JOIN category c ON q.category = c.CategoryID
        WHERE q.start_time <= %s AND q.end_time >= %s
    """, (datetime.now(), datetime.now()))
    available_quizzes = cursor.fetchall()
    
    # Get completed quizzes
    cursor.execute("""
        SELECT q.QuizID, q.Title, r.Score, q.Passing_Score, r.Date_Taken
        FROM result r
        JOIN quiz q ON r.Quiz = q.QuizID
        WHERE r.AttemptedBy = %s
        ORDER BY r.Date_Taken DESC
    """, (session['user_id'],))
    completed_quizzes = cursor.fetchall()
    
    conn.close()
    
    return render_template('student/dashboard.html', 
                         available_quizzes=available_quizzes,
                         completed_quizzes=completed_quizzes)

@app.route('/student/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    # Check if user is logged in and is a student
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Check if quiz is available
        cursor.execute("""
            SELECT * FROM quiz 
            WHERE QuizID = %s AND start_time <= %s AND end_time >= %s
        """, (quiz_id, datetime.now(), datetime.now()))
        quiz = cursor.fetchone()
        
        if not quiz:
            return redirect(url_for('student_dashboard'))
        
        # Check if already attempted
        cursor.execute("""
            SELECT * FROM result 
            WHERE AttemptedBy = %s AND Quiz = %s
        """, (session['user_id'], quiz_id))
        if cursor.fetchone():
            return redirect(url_for('student_dashboard'))

        if request.method == 'POST':
            # Process quiz submission
            answers = request.form.to_dict()
            start_time = datetime.strptime(answers['start_time'], '%Y-%m-%d %H:%M:%S')
            time_taken = (datetime.now() - start_time).seconds
            
            # Calculate score
            cursor.execute("""
                SELECT q.QuestionID, c.ChoiceID
                FROM question q
                JOIN choice c ON q.QuestionID = c.Question
                WHERE q.Quiz = %s AND c.IsCorrect = 1
            """, (quiz_id,))
            correct_answers = {str(row['QuestionID']): str(row['ChoiceID']) for row in cursor.fetchall()}
            
            total_questions = len(correct_answers)
            correct = 0
            
            for question_id, selected_choice in answers.items():
                if question_id == 'start_time':
                    continue
                if question_id in correct_answers and selected_choice == correct_answers[question_id]:
                    correct += 1
            
            score = round((correct / total_questions) * 100, 2) if total_questions > 0 else 0
            
            # Save result
            cursor.execute("""
                INSERT INTO result (AttemptedBy, Quiz, Score, Date_Taken, Time_Taken)
                VALUES (%s, %s, %s, %s, %s)
            """, (session['user_id'], quiz_id, score, datetime.now(), time_taken))
            conn.commit()
            
            return redirect(url_for('view_results', quiz_id=quiz_id))
        
        # Get quiz questions for GET request
        cursor.execute("""
            SELECT * FROM question 
            WHERE Quiz = %s
            ORDER BY QuestionID
        """, (quiz_id,))
        questions = cursor.fetchall()
        
        # Get choices for each question
        for question in questions:
            cursor.execute("""
                SELECT * FROM choice 
                WHERE Question = %s
                ORDER BY ChoiceID
            """, (question['QuestionID'],))
            question['choices'] = cursor.fetchall()
        
        # Generate start time string in Python
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return render_template('student/quiz.html', 
                            quiz=quiz, 
                            questions=questions,
                            start_time=start_time)
    
    except Exception as e:
        conn.rollback()
        return render_template('error.html', error=str(e))
    
    finally:
        conn.close()

@app.route('/student/results/<int:quiz_id>')
def view_results(quiz_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT r.*, q.Title, q.Passing_Score
        FROM result r
        JOIN quiz q ON r.Quiz = q.QuizID
        WHERE r.AttemptedBy = %s AND r.Quiz = %s
    """, (session['user_id'], quiz_id))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    # Get correct answers for review
    cursor.execute("""
        SELECT q.QuestionID, q.Text as QuestionText, c.Text as CorrectAnswer
        FROM question q
        JOIN choice c ON q.QuestionID = c.Question
        WHERE q.Quiz = %s AND c.IsCorrect = 1
    """, (quiz_id,))
    correct_answers = cursor.fetchall()
    
    conn.close()
    
    return render_template('student/results.html', result=result, correct_answers=correct_answers)

# Teacher routes
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Get quizzes created by this teacher
    cursor.execute("""
        SELECT q.*, c.Name as CategoryName, 
               COUNT(r.Quiz) as Attempts,
               AVG(r.Score) as AvgScore
        FROM quiz q
        JOIN category c ON q.category = c.CategoryID
        LEFT JOIN result r ON q.QuizID = r.Quiz
        WHERE q.createdby = %s
        GROUP BY q.QuizID
        ORDER BY q.Created_Date DESC
    """, (session['user_id'],))
    quizzes = cursor.fetchall()
    
    conn.close()
    
    return render_template('teacher/dashboard.html', quizzes=quizzes)

@app.route('/teacher/quiz/<int:quiz_id>/report')
def quiz_report(quiz_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Get quiz details with category name
        cursor.execute("""
            SELECT q.*, c.Name as category_name 
            FROM quiz q
            JOIN category c ON q.category = c.CategoryID
            WHERE q.QuizID = %s AND q.createdby = %s
        """, (quiz_id, session['user_id']))
        quiz = cursor.fetchone()
        
        if not quiz:
            return redirect(url_for('teacher_dashboard'))
        
        # Get analytics
        analytics = get_quiz_analytics(quiz_id)
        
        # Get student attempts
        cursor.execute("""
            SELECT u.UserID, u.First_Name, u.Last_Name, 
                   r.Score, r.Date_Taken, r.Time_Taken
            FROM result r
            JOIN user u ON r.AttemptedBy = u.UserID
            WHERE r.Quiz = %s
            ORDER BY r.Score DESC
        """, (quiz_id,))
        attempts = cursor.fetchall()
        
        return render_template('teacher/quiz_report.html', 
                             quiz=quiz, 
                             analytics=analytics,
                             attempts=attempts)
    
    except Exception as e:
        print(f"Error in quiz_report: {str(e)}")
        return render_template('error.html', error=str(e))
    finally:
        conn.close()

@app.route('/teacher/quiz/create', methods=['GET', 'POST'])
def create_quiz():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Process quiz creation form
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        passing_score = request.form['passing_score']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insert quiz
            cursor.execute("""
                INSERT INTO quiz (Title, createdby, Description, Created_Date, 
                                 category, start_time, end_time, Passing_Score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, session['user_id'], description, datetime.now(), 
                 category, start_time, end_time, passing_score))
            quiz_id = cursor.lastrowid
            
            # Process questions
            question_count = int(request.form['question_count'])
            for i in range(1, question_count + 1):
                question_text = request.form[f'question_{i}_text']
                question_type = request.form[f'question_{i}_type']
                
                cursor.execute("""
                    INSERT INTO question (Quiz, Text, Type)
                    VALUES (%s, %s, %s)
                """, (quiz_id, question_text, question_type))
                question_id = cursor.lastrowid
                
                # Process choices
                choice_count = int(request.form[f'question_{i}_choice_count'])
                for j in range(1, choice_count + 1):
                    choice_text = request.form[f'question_{i}_choice_{j}_text']
                    is_correct = request.form.get(f'question_{i}_choice_{j}_correct', '0') == '1'
                    
                    cursor.execute("""
                        INSERT INTO choice (Question, Text, IsCorrect)
                        VALUES (%s, %s, %s)
                    """, (question_id, choice_text, is_correct))
            
            conn.commit()
            return redirect(url_for('quiz_report', quiz_id=quiz_id))
        except Exception as e:
            conn.rollback()
            return render_template('teacher/create_quiz.html', 
                                categories=get_categories(),
                                error=str(e))
        finally:
            conn.close()
    
    return render_template('teacher/create_quiz.html', categories=get_categories())

def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM category")
    categories = cursor.fetchall()
    conn.close()
    return categories

def open_browser():
    global browser_opened
    if not browser_opened:
        webbrowser.open_new('http://127.0.0.1:5000/')
        browser_opened = True
    
if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1, open_browser).start()
    app.run(debug=True)