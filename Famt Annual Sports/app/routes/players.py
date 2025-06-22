from flask import Blueprint, render_template
from flask_login import login_required
from app import db

player_bp = Blueprint('player', __name__)

@player_bp.route('/player')
@login_required
def dashboard():
    games = list(db.games.find({"status": "upcoming"}))
    registered_games = list(db.participations.find({"player_id": current_user.id}))
    
    return render_template('dashboard/player.html',
                         games=games,
                         registered_games=registered_games)