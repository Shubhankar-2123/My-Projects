from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
import os
from recommender import GameRecommender

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize recommender with both data files
# At the top of app.py
recommender = GameRecommender('data/Game_processed_data.csv')
def check_db_tables():
    conn = sqlite3.connect('data/recommendations.db')
    c = conn.cursor()
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print("Existing tables:", tables)
    
    try:
        c.execute("PRAGMA table_info(interactions)")
        print("Interactions columns:", c.fetchall())
    except sqlite3.Error as e:
        print("Interactions table error:", e)
    
    conn.close()

def init_db():
    conn = sqlite3.connect('data/recommendations.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    
    # Interactions table (modified for your data structure)
    c.execute('''CREATE TABLE IF NOT EXISTS interactions
                 (user_id INTEGER,
                  game_url TEXT,
                  interaction_type TEXT,  -- 'view', 'rating', 'like'
                  value REAL,             -- rating value or 1/0 for like
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Create games table from CSV if it doesn't exist
    if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='games'").fetchone():
        games_df = pd.read_csv('data/Game_processed_data.csv')
        games_df.to_sql('games', conn, if_exists='replace', index=False)
        print("Games table created from CSV")
    
    conn.commit()
    conn.close()

init_db()
check_db_tables()

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

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    recommendations = recommender.get_recommendations(user_id, top_n=10)
    
    return render_template('index.html', 
                         games=recommendations,
                         username=session.get('username'))

@app.route('/game/<game_name>')
def game_detail(game_name):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get game details from recommender
    game_details = None
    for game in recommender.games_df.to_dict('records'):
        if game['Name'].lower() == game_name.lower():
            game_details = game
            break
    
    if not game_details:
        flash('Game not found', 'danger')
        return redirect(url_for('index'))
    
    # Track view interaction
    conn = sqlite3.connect('data/recommendations.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO interactions 
                    (user_id, game_url, interaction_type) 
                    VALUES (?, ?, 'view')""",
                    (user_id, game_details['URL']))
        conn.commit()
    except sqlite3.Error as e:
        print("Error logging view:", e)
    finally:
        conn.close()
    
    return render_template('game_detail.html', game=game_details)

@app.route('/rate/<game_name>', methods=['POST'])
def rate_game(game_name):
    if 'user_id' not in session:
        flash('Please log in to rate games', 'danger')
        return redirect(url_for('login'))

    try:
        user_id = session['user_id']
        rating = float(request.form.get('rating', 0))
        
        # Validate rating
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5', 'danger')
            return redirect(url_for('game_detail', game_name=game_name))

        # Get game URL from name
        game = next((g for g in recommender.games_df.to_dict('records') 
                   if g['Name'].lower() == game_name.lower()), None)
        
        if not game:
            flash('Game not found', 'danger')
            return redirect(url_for('index'))

        game_url = game['URL']

        # Database operations
        conn = sqlite3.connect('data/recommendations.db')
        c = conn.cursor()
        
        try:
            # Check for existing rating
            c.execute('''SELECT rowid FROM interactions 
                        WHERE user_id=? AND game_url=? AND interaction_type='rating' ''',
                     (user_id, game_url))
            existing = c.fetchone()

            if existing:
                # Update existing rating
                c.execute('''UPDATE interactions SET value=?, timestamp=CURRENT_TIMESTAMP
                           WHERE rowid=?''',
                         (rating, existing[0]))
            else:
                # Insert new rating
                c.execute('''INSERT INTO interactions 
                           (user_id, game_url, interaction_type, value)
                           VALUES (?, ?, 'rating', ?)''',
                         (user_id, game_url, rating))

            conn.commit()
            flash('Rating saved successfully!', 'success')
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            flash('Failed to save rating due to a database error', 'danger')
            
        finally:
            conn.close()

    except ValueError:
        flash('Invalid rating value', 'danger')
    except Exception as e:
        print(f"Unexpected error: {e}")
        flash('Failed to save rating', 'danger')

    return redirect(url_for('game_detail', game_name=game_name))
# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
# Add these new routes to your existing app.py
# ... (keep your existing register, login, logout routes) ...

if __name__ == '__main__':
    app.run(debug=True)