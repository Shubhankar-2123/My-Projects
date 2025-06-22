from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    # Get data for charts
    departments = db.users.distinct("department")
    player_counts = [db.users.count_documents({"department": dept}) for dept in departments]
    games = list(db.games.find())
    
    return render_template('dashboard/admin.html', 
                         departments=departments,
                         player_counts=player_counts,
                         games=games)