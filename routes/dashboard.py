from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import Goal
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


# ─── Dashboard ───────────────────────────────────────────────────────────────
@dashboard_bp.route('/dashboard')
@login_required
def index():
    goals = current_user.goals

    # Summary stats
    stats = {
        'total_goals': current_user.total_goals,
        'active_goals': current_user.active_goals,
        'completed_goals': current_user.completed_goals,
        'on_hold_goals': current_user.on_hold_goals,
        'total_target': current_user.total_target,
        'total_saved': current_user.total_saved,
        'total_remaining': current_user.total_remaining,
        'overall_progress': (
            round((current_user.total_saved / current_user.total_target) * 100, 1)
            if current_user.total_target > 0 else 0
        ),
    }

    # Recent goals (last 5, newest first)
    recent_goals = (Goal.query
                    .filter_by(user_id=current_user.id)
                    .order_by(Goal.updated_at.desc())
                    .limit(5)
                    .all())

    return render_template('dashboard.html', stats=stats, recent_goals=recent_goals)


# ─── Dashboard API (Chart Data) ──────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard-data')
@login_required
def dashboard_data():
    goals = current_user.goals

    # Goal status distribution
    status_counts = {'Active': 0, 'Completed': 0, 'On Hold': 0}
    for g in goals:
        if g.status in status_counts:
            status_counts[g.status] += 1

    # Category distribution
    cat_data = {}
    for g in goals:
        cat = g.category or 'Other'
        cat_data[cat] = cat_data.get(cat, 0) + 1

    # Target vs Saved per goal (top 6 for chart clarity)
    sorted_goals = sorted(goals, key=lambda g: g.target_amount, reverse=True)[:6]
    target_vs_saved = {
        'labels': [g.goal_name for g in sorted_goals],
        'target': [g.target_amount for g in sorted_goals],
        'saved': [g.current_amount for g in sorted_goals],
    }

    # Monthly savings trend (last 6 months aggregated across all goals)
    from datetime import date, timedelta
    from models import SavingsRecord, db
    today = date.today()
    monthly_trend = []
    for i in range(5, -1, -1):
        # approximate month boundaries
        month_offset_days = i * 30
        m_start = today - timedelta(days=month_offset_days + 30)
        m_end = today - timedelta(days=month_offset_days)
        total = (SavingsRecord.query
                 .join(Goal)
                 .filter(Goal.user_id == current_user.id)
                 .filter(SavingsRecord.saving_date >= m_start)
                 .filter(SavingsRecord.saving_date <= m_end)
                 .with_entities(func.sum(SavingsRecord.amount))
                 .scalar()) or 0
        label = m_end.strftime('%b %Y')
        monthly_trend.append({'label': label, 'amount': float(total)})

    return jsonify({
        'status_distribution': status_counts,
        'category_distribution': cat_data,
        'target_vs_saved': target_vs_saved,
        'monthly_trend': monthly_trend,
    })
