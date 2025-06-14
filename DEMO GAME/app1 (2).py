from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
from recommender import GameRecommender

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize recommender
recommender = GameRecommender('data/Game_processed_data.csv')
# Add this right after your imports in app.py to debug
def check_db_tables():
    conn = sqlite3.connect('data/recommendations.db')
    c = conn.cursor()
    
    # Check if tables exist
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print("Existing tables:", tables)
    
    # Check interactions table structure
    try:
        c.execute("PRAGMA table_info(interactions)")
        print("Interactions columns:", c.fetchall())
    except sqlite3.Error as e:
        print("Interactions table error:", e)
    
    conn.close()


# Database initialization
def init_db():
    conn = sqlite3.connect('data/recommendations.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  preferences TEXT)''')
    
    # Interactions table
    c.execute('''CREATE TABLE IF NOT EXISTS interactions
                 (user_id INTEGER,
                  game_id TEXT,
                  interaction_type TEXT,   'view', 'rating', 'playtime'
                  value REAL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

init_db()

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('data/recommendations.db')
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
    
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('data/recommendations.db')
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

# Main recommendation page
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    recommendations = recommender.get_recommendations(user_id)
    
    return render_template('index.html', games=recommendations)

# Game details page (track interactions)
@app.route('/game/<game_id>')
def game_detail(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    game = recommender.get_game_details(game_id)
    
    # Track view interaction
    conn = sqlite3.connect('data/recommendations.db')
    c = conn.cursor()
    c.execute("INSERT INTO interactions (user_id, game_id, interaction_type) VALUES (?, ?, 'view')",
              (user_id, game_id))
    conn.commit()
    conn.close()
    
    return render_template('game_detail.html', game=game)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
# Add these new routes to your existing app.py

@app.route('/rate/<game_id>', methods=['POST'])
def rate_game(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    rating = request.form.get('rating')
    
    if rating and rating.isdigit():
        rating = float(rating)
        
        conn = sqlite3.connect('data/recommendations.db')
        c = conn.cursor()
        
        # Check if user already rated this game
        c.execute("SELECT value FROM interactions WHERE user_id = ? AND game_id = ? AND interaction_type = 'rating'",
                  (user_id, game_id))
        existing_rating = c.fetchone()
        
        if existing_rating:
            # Update existing rating
            c.execute("UPDATE interactions SET value = ?, timestamp = CURRENT_TIMESTAMP WHERE user_id = ? AND game_id = ? AND interaction_type = 'rating'",
                      (rating, user_id, game_id))
        else:
            # Insert new rating
            c.execute("INSERT INTO interactions (user_id, game_id, interaction_type, value) VALUES (?, ?, 'rating', ?)",
                      (user_id, game_id, rating))
        
        conn.commit()
        conn.close()
        
        flash('Thanks for your rating!', 'success')
    
    return redirect(url_for('game_detail', game_id=game_id))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's rated games
    conn = sqlite3.connect('data/recommendations.db')
    c = conn.cursor()
    
    c.execute('''SELECT i.game_id, i.value, g.Name, g.Icon URL 
                 FROM interactions i
                 JOIN games g ON i.game_id = g.URL
                 WHERE i.user_id = ? AND i.interaction_type = 'rating'
                 ORDER BY i.timestamp DESC''', (user_id,))
    rated_games = c.fetchall()
    
    conn.close()
    
    return render_template('profile.html', rated_games=rated_games)
# Call this function right before app.run()
if __name__ == '__main__':
    check_db_tables()
    app.run(debug=True)