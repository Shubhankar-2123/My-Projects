from flask import Flask
from pymongo import MongoClient
import os
from dotenv import load_dotenv
# from app.sockets import rankings  # This imports and registers the handlers
from flask_socketio import SocketIO

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable CORS if needed

# MongoDB Atlas Connection
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.college_sports


from app.routes.auth import auth_bp
app.register_blueprint(auth_bp)