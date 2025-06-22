from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.email = user_data["email"]
        self.role = user_data["role"]

def get_user_by_email(email):
    return db.users.find_one({"email": email})