# routes/games.py
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from app import db, socketio
from ..decorators import admin_required, coordinator_required

games_bp = Blueprint('games', __name__)

# ADMIN-ONLY ROUTES
@games_bp.route('/games', methods=['POST'])
@login_required
@admin_required
def create_game():
    """Create a new game (Admin only)"""
    try:
        required_fields = ['name', 'type', 'description']
        if not all(request.form.get(field) for field in required_fields):
            flash('Missing required fields', 'danger')
            return redirect(url_for('admin.dashboard'))

        game_data = {
            "name": request.form.get('name'),
            "type": request.form.get('type'),  # individual/doubles/team
            "description": request.form.get('description'),
            "rules": request.form.get('rules', ''),
            "start_date": request.form.get('start_date'),
            "max_players": int(request.form.get('max_players', 0)),
            "status": "upcoming",
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = db.games.insert_one(game_data)
        
        # Notify all clients
        socketio.emit('game_created', {
            'game_id': str(result.inserted_id),
            'game_name': game_data['name']
        }, broadcast=True)

        flash('Game created successfully!', 'success')
        return redirect(url_for('admin.games_list'))

    except Exception as e:
        flash(f'Error creating game: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

# COORDINATOR ROUTES
@games_bp.route('/games/<game_id>/update', methods=['POST'])
@login_required
@coordinator_required
def update_game(game_id):
    """Update game details (Coordinator only)"""
    try:
        game = db.games.find_one({"_id": ObjectId(game_id)})
        if not game:
            flash('Game not found', 'danger')
            return redirect(url_for('coordinator.dashboard'))

        updates = {
            "description": request.form.get('description', game['description']),
            "rules": request.form.get('rules', game['rules']),
            "status": request.form.get('status', game['status']),
            "updated_at": datetime.utcnow()
        }

        db.games.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": updates}
        )

        socketio.emit('game_updated', {'game_id': game_id}, broadcast=True)
        flash('Game updated successfully!', 'success')
        return redirect(url_for('games.details', game_id=game_id))

    except InvalidId:
        flash('Invalid game ID', 'danger')
        return redirect(url_for('coordinator.dashboard'))
    except Exception as e:
        flash(f'Error updating game: {str(e)}', 'danger')
        return redirect(url_for('games.details', game_id=game_id))

# PUBLIC ROUTES
@games_bp.route('/games/<game_id>')
@login_required
def game_details(game_id):
    """View game details (All authenticated users)"""
    try:
        game = db.games.find_one({"_id": ObjectId(game_id)})
        if not game:
            flash('Game not found', 'danger')
            return redirect(url_for('main.index'))

        # Check if current user is coordinator for this game
        is_coordinator = (str(game.get('coordinator_id'))) == str(current_user.id)
        
        # Get registered players
        participants = list(db.participations.find(
            {"game_id": ObjectId(game_id)},
            {"player_id": 1, "player_name": 1, "department": 1}
        ))

        return render_template('games/details.html',
                           game=game,
                           is_coordinator=is_coordinator,
                           participants=participants)

    except InvalidId:
        flash('Invalid game ID', 'danger')
        return redirect(url_for('main.index'))