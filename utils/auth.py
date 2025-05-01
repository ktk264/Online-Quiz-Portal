from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import pymysql

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT * FROM user WHERE Username = %s", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user['Password'] == password:
        return user
    return None

def register_user(username, password, first_name, last_name, email, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username exists
        cursor.execute("SELECT * FROM user WHERE Username = %s", (username,))
        if cursor.fetchone():
            return False, "Username already exists"
        
        # Check if email exists
        cursor.execute("SELECT * FROM user WHERE EmailID = %s", (email,))
        if cursor.fetchone():
            return False, "Email already exists"
        
        # Insert new user
        cursor.execute("""
            INSERT INTO user (Username, First_Name, Last_Name, EmailID, Role, Password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, first_name, last_name, email, role, password))
        
        conn.commit()
        return True, "Registration successful"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()