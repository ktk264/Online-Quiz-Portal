import pymysql
from datetime import datetime
from utils.db import get_db_connection

def get_quiz_questions(quiz_id):
    """Fetch all questions and choices for a quiz"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Get questions
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
        
        return questions
        
    except Exception as e:
        print(f"Error getting quiz questions: {str(e)}")
        return []
    finally:
        conn.close()

def calculate_score(quiz_id, answers):
    """Calculate score based on submitted answers"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Get correct answers
        cursor.execute("""
            SELECT q.QuestionID, c.ChoiceID
            FROM question q
            JOIN choice c ON q.QuestionID = c.Question
            WHERE q.Quiz = %s AND c.IsCorrect = 1
        """, (quiz_id,))
        correct_answers = {str(row['QuestionID']): str(row['ChoiceID']) for row in cursor.fetchall()}
        
        # Calculate score
        total_questions = len(correct_answers)
        correct = 0
        
        for question_id, selected_choice in answers.items():
            if question_id == 'start_time':
                continue
            if question_id in correct_answers and selected_choice == correct_answers[question_id]:
                correct += 1
        
        score = round((correct / total_questions) * 100, 2) if total_questions > 0 else 0
        time_taken = int((datetime.now() - datetime.strptime(answers.get('start_time'), '%Y-%m-%d %H:%M:%S')).total_seconds())
        
        return score, time_taken
        
    except Exception as e:
        print(f"Error calculating score: {str(e)}")
        return 0, 0
    finally:
        conn.close()

def get_quiz_analytics(quiz_id):
    """Get comprehensive analytics for a quiz"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    analytics = {
        'average_score': 0.0,
        'passed': 0,
        'failed': 0,
        'score_distribution': []
    }
    
    try:
        # Call the stored procedure
        cursor.callproc('get_quiz_analytics', (quiz_id,))
        
        # Process multiple result sets
        # 1. First result set: Average score
        try:
            avg_result = cursor.fetchone()
            if avg_result:
                analytics['average_score'] = float(avg_result.get('AverageScore', 0))
        except pymysql.Error as e:
            print("Error processing average score:", e)
        
        # Move to next result set
        cursor.nextset()
        
        # 2. Second result set: Pass/fail counts
        try:
            pass_fail = cursor.fetchone()
            if pass_fail:
                analytics['passed'] = int(pass_fail.get('Passed', 0))
                analytics['failed'] = int(pass_fail.get('Failed', 0))
        except pymysql.Error as e:
            print("Error processing pass/fail:", e)
        
        # Move to next result set
        cursor.nextset()
        
        # 3. Third result set: Score distribution
        try:
            distribution = cursor.fetchall()
            if distribution:
                analytics['score_distribution'] = [
                    {
                        'ScoreRange': int(item.get('ScoreRange', 0)),
                        'Count': int(item.get('Count', 0))
                    } 
                    for item in distribution
                ]
        except pymysql.Error as e:
            print("Error processing distribution:", e)
        
    except Exception as e:
        print(f"Error in get_quiz_analytics: {str(e)}")
    finally:
        conn.close()
    
    print("FINAL ANALYTICS:", analytics)
    return analytics