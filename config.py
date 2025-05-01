import os

class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Legendary!264'
    MYSQL_DB = 'quiz_portal'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'