import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
SQLALCHEMY_DATABASE_URI = (
    'mysql+mysqlconnector://root:a647ec150@localhost:3306/sr_bot_db'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
