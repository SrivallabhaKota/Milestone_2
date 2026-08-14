"""
FinGoal — Smart Goal Planning & Investment Management
Single-file Flask application (no authentication)
"""

import os
import sqlite3
from datetime import datetime, date
from flask import (Flask, render_template, redirect, url_for,
                   flash, request, jsonify, abort, g)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE  = os.path.join(BASE_DIR, 'instance', 'database.db')
SQL_FILE  = os.path.join(BASE_DIR, 'database.sql')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fingoal-dev-secret-key-2026'
app.config['DATABASE']   = DATABASE
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024   # 2 MB

os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static', 'images', 'avatars'), exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    """Open a new database connection if not already in context."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def init_db():
    """Create tables from database.sql if they do not exist."""
    if not os.path.exists(SQL_FILE):
        print("[WARNING] database.sql not found. Skipping initialization.")
        return
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    # Use a direct connection (not app context) so PRAGMA survives executescript
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.commit()
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    print("[OK] Database initialized from database.sql")


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT PROCESSOR — inject profile into all templates
# ═══════════════════════════════════════════════════════════════════════════════

@app.context_processor
def inject_globals():
    try:
        db      = get_db()
        profile = db.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        if profile:
            profile = dict(profile)
        else:
            profile = {'id': 1, 'name': 'My Profile', 'currency': '₹',
                       'monthly_saving_capacity': 0, 'monthly_investment_capacity': 0}
    except Exception:
        profile = {'id': 1, 'name': 'My Profile', 'currency': '₹',
                   'monthly_saving_capacity': 0, 'monthly_investment_capacity': 0}
    return {'profile': profile}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORIES  = ['Education', 'Electronics', 'Travel', 'Emergency',
               'Vehicle', 'Personal', 'Health', 'Other']
PRIORITIES  = ['High', 'Medium', 'Low']
STATUSES    = ['Active', 'Completed', 'On Hold']
INV_TYPES   = ['Stocks', 'Mutual Funds', 'Fixed Deposit', 'Recurring Deposit',
               'Gold', 'Bonds', 'Public Provident Fund', 'Other']
INV_STATUSES = ['Active', 'Matured', 'Withdrawn', 'On Hold']


def _parse_date(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def process_goal(row):
    """Convert a goal DB row → dict with all computed financial fields."""
    g_dict = dict(row)

    target_amount  = float(g_dict.get('target_amount') or 0)
    current_amount = float(g_dict.get('current_amount') or 0)
    start_date_str  = g_dict.get('start_date')
    target_date_str = g_dict.get('target_date')
    today = date.today()

    start_date  = _parse_date(start_date_str)
    target_date = _parse_date(target_date_str)

    # Core amounts
    remaining    = max(target_amount - current_amount, 0)
    progress_pct = min(round((current_amount / target_amount * 100), 1), 100) \
                   if target_amount > 0 else 0

    # Time-based
    days_left = (target_date - today).days if target_date else None
    if target_date and target_date > today:
        months_left = max((target_date - today).days / 30.44, 0)
    else:
        months_left = 0

    required_monthly = round(remaining / months_left, 2) if months_left > 0 else 0
    required_weekly  = round(required_monthly / 4.33, 2) if required_monthly > 0 else 0

    # Smart status
    if current_amount >= target_amount:
        smart_status = 'Completed'
    elif start_date and target_date:
        total_days   = (target_date - start_date).days
        elapsed_days = (today - start_date).days
        if total_days > 0:
            ratio    = max(min(elapsed_days / total_days, 1.0), 0.0)
            expected = target_amount * ratio
            if current_amount >= expected * 0.90:
                smart_status = 'On Track'
            elif current_amount >= expected * 0.70:
                smart_status = 'Needs Attention'
            else:
                smart_status = 'Behind Schedule'
        else:
            smart_status = 'Behind Schedule'
    else:
        smart_status = g_dict.get('status', 'Active')

    smart_cls    = {'On Track': 'success', 'Completed': 'success',
                    'Needs Attention': 'warning', 'Behind Schedule': 'danger'}.get(smart_status, 'secondary')
    priority_cls = {'High': 'danger', 'Medium': 'warning', 'Low': 'success'}.get(g_dict.get('priority', 'Medium'), 'secondary')
    status_cls   = {'Active': 'primary', 'Completed': 'success', 'On Hold': 'secondary'}.get(g_dict.get('status', 'Active'), 'secondary')

    g_dict.update({
        'remaining_amount':       remaining,
        'progress_percentage':    progress_pct,
        'required_monthly_saving': required_monthly,
        'required_weekly_saving':  required_weekly,
        'days_left':              days_left,
        'months_left':            round(months_left, 1),
        'smart_status':           smart_status,
        'smart_status_class':     smart_cls,
        'priority_class':         priority_cls,
        'status_class':           status_cls,
    })
    return g_dict


def process_goal_part(row):
    p = dict(row)
    target = float(p.get('target_amount') or 0)
    saved  = float(p.get('saved_amount') or 0)
    p['remaining_amount']  = max(target - saved, 0)
    p['progress_percentage'] = min(round((saved / target * 100), 1), 100) if target > 0 else 0
    p['status_class'] = {'Completed': 'success', 'In Progress': 'primary',
                         'On Hold': 'warning', 'Pending': 'secondary'}.get(p.get('status', 'Pending'), 'secondary')
    return p


def process_investment(row):
    """Convert an investment DB row → dict with computed profit/loss/return fields."""
    inv = dict(row)
    invested = float(inv.get('invested_amount') or 0)
    current  = float(inv.get('current_value') or 0)
    profit   = current - invested
    ret_pct  = round((profit / invested * 100), 2) if invested > 0 else 0.0

    inv.update({
        'profit_loss':       profit,
        'return_percentage': ret_pct,
        'profit_status':     'Profit' if profit > 0 else ('Loss' if profit < 0 else 'No Change'),
        'profit_class':      'success' if profit > 0 else ('danger' if profit < 0 else 'secondary'),
        'status_class':      {'Active': 'primary', 'Matured': 'success',
                              'Withdrawn': 'secondary', 'On Hold': 'warning'}.get(inv.get('status', 'Active'), 'secondary'),
    })
    return inv


def get_dashboard_stats(db):
    """Return dicts of goal stats and investment stats for the dashboard."""
    # Goal stats
    goals_raw = db.execute("SELECT * FROM goals").fetchall()
    goals = [process_goal(r) for r in goals_raw]

    total_target   = sum(g['target_amount'] for g in goals)
    total_saved    = sum(g['current_amount'] for g in goals)
    total_remaining = sum(g['remaining_amount'] for g in goals)
    overall_progress = round((total_saved / total_target * 100), 1) if total_target > 0 else 0

    goal_stats = {
        'total':           len(goals),
        'active':          sum(1 for g in goals if g['status'] == 'Active'),
        'completed':       sum(1 for g in goals if g['status'] == 'Completed'),
        'on_hold':         sum(1 for g in goals if g['status'] == 'On Hold'),
        'total_target':    total_target,
        'total_saved':     total_saved,
        'total_remaining': total_remaining,
        'overall_progress': overall_progress,
    }

    # Investment stats
    invs_raw = db.execute("SELECT * FROM investments").fetchall()
    invs = [process_investment(r) for r in invs_raw]

    total_invested = sum(i['invested_amount'] for i in invs)
    current_value  = sum(i['current_value'] for i in invs)
    total_pl       = current_value - total_invested
    avg_return     = round(sum(i['return_percentage'] for i in invs) / len(invs), 2) if invs else 0

    inv_stats = {
        'total':          len(invs),
        'total_invested': total_invested,
        'current_value':  current_value,
        'total_pl':       total_pl,
        'avg_return':     avg_return,
    }

    return goal_stats, inv_stats


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    db = get_db()
    goal_stats, inv_stats = get_dashboard_stats(db)

    recent_goals = [process_goal(r) for r in
                    db.execute("SELECT * FROM goals ORDER BY updated_at DESC LIMIT 5").fetchall()]
    recent_invs  = [process_investment(r) for r in
                    db.execute("SELECT * FROM investments ORDER BY created_at DESC LIMIT 4").fetchall()]

    return render_template('dashboard.html',
                           goal_stats=goal_stats, inv_stats=inv_stats,
                           recent_goals=recent_goals, recent_invs=recent_invs)


@app.route('/api/dashboard-data')
def dashboard_data():
    db = get_db()
    goal_stats, inv_stats = get_dashboard_stats(db)

    # Goal status distribution
    goals_raw = db.execute("SELECT status FROM goals").fetchall()
    status_counts = {'Active': 0, 'Completed': 0, 'On Hold': 0}
    for r in goals_raw:
        s = r['status']
        if s in status_counts:
            status_counts[s] += 1

    # Category distribution
    cat_rows = db.execute("SELECT category, COUNT(*) as cnt FROM goals GROUP BY category").fetchall()
    cat_data = {r['category'] or 'Other': r['cnt'] for r in cat_rows}

    # Investment type distribution
    inv_type_rows = db.execute(
        "SELECT investment_type, COUNT(*) as cnt FROM investments GROUP BY investment_type"
    ).fetchall()
    inv_type_data = {r['investment_type']: r['cnt'] for r in inv_type_rows}

    # Target vs Saved (top 6 goals by target)
    top_goals = [process_goal(r) for r in
                 db.execute("SELECT * FROM goals ORDER BY target_amount DESC LIMIT 6").fetchall()]
    target_vs_saved = {
        'labels': [g['goal_name'] for g in top_goals],
        'target': [g['target_amount'] for g in top_goals],
        'saved':  [g['current_amount'] for g in top_goals],
    }

    # Invested vs current value (top 6 investments)
    top_invs = [process_investment(r) for r in
                db.execute("SELECT * FROM investments ORDER BY invested_amount DESC LIMIT 6").fetchall()]
    inv_vs_current = {
        'labels':   [i['investment_name'] for i in top_invs],
        'invested': [i['invested_amount'] for i in top_invs],
        'current':  [i['current_value'] for i in top_invs],
    }

    # Monthly savings trend (last 6 months)
    from datetime import timedelta
    today = date.today()
    monthly_trend = []
    for i in range(5, -1, -1):
        m_start = today - timedelta(days=(i + 1) * 30)
        m_end   = today - timedelta(days=i * 30)
        row = db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM savings "
            "WHERE saving_date >= ? AND saving_date <= ?",
            (m_start.isoformat(), m_end.isoformat())
        ).fetchone()
        monthly_trend.append({'label': m_end.strftime('%b %Y'), 'amount': float(row['total'])})

    return jsonify({
        'status_distribution': status_counts,
        'category_distribution': cat_data,
        'target_vs_saved': target_vs_saved,
        'investment_type_distribution': inv_type_data,
        'inv_vs_current': inv_vs_current,
        'monthly_trend': monthly_trend,
        'inv_stats': inv_stats,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# GOAL PLANNING ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/goal-planning', methods=['GET', 'POST'])
def goal_planning():
    if request.method == 'POST':
        goal_name     = request.form.get('goal_name', '').strip()
        goal_type     = request.form.get('goal_type', '').strip()
        description   = request.form.get('description', '').strip()
        category      = request.form.get('category', 'Personal')
        priority      = request.form.get('priority', 'Medium')
        status        = request.form.get('status', 'Active')
        notes         = request.form.get('notes', '').strip()
        start_date    = request.form.get('start_date', '')
        target_date   = request.form.get('target_date', '')

        try:
            target_amount  = float(request.form.get('target_amount', 0))
            current_amount = float(request.form.get('current_amount', 0))
        except (ValueError, TypeError):
            flash('Invalid amount values.', 'danger')
            return redirect(url_for('goal_planning'))

        # Validation
        errors = []
        if not goal_name:
            errors.append('Goal name is required.')
        if target_amount <= 0:
            errors.append('Target amount must be greater than zero.')
        if current_amount < 0:
            errors.append('Current amount cannot be negative.')
        if current_amount > target_amount:
            errors.append('Current amount cannot exceed target amount.')
        sd = _parse_date(start_date)
        td = _parse_date(target_date)
        if sd and td and td <= sd:
            errors.append('Target date must be after start date.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('goal_planning.html',
                                   categories=CATEGORIES, priorities=PRIORITIES,
                                   statuses=STATUSES, form=request.form,
                                   today=date.today().isoformat())

        # Auto-complete if already reached target
        if current_amount >= target_amount > 0:
            status = 'Completed'

        db = get_db()
        now = datetime.utcnow().isoformat()
        db.execute(
            """INSERT INTO goals (goal_name, goal_type, description, target_amount,
               current_amount, start_date, target_date, category, priority, status,
               notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (goal_name, goal_type, description, target_amount, current_amount,
             start_date or date.today().isoformat(), target_date,
             category, priority, status, notes, now, now)
        )
        db.commit()
        goal_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        flash(f'Goal "{goal_name}" created successfully!', 'success')
        return redirect(url_for('goal_detail', goal_id=goal_id))

    return render_template('goal_planning.html',
                           categories=CATEGORIES, priorities=PRIORITIES,
                           statuses=STATUSES, today=date.today().isoformat())


# ═══════════════════════════════════════════════════════════════════════════════
# GOALS ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/goals')
def goals_list():
    db     = get_db()
    search   = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    status   = request.args.get('status', '')
    priority = request.args.get('priority', '')
    sort     = request.args.get('sort', 'newest')

    query  = "SELECT * FROM goals WHERE 1=1"
    params = []
    if search:
        query += " AND goal_name LIKE ?"
        params.append(f'%{search}%')
    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)

    sort_map = {
        'newest':     'created_at DESC',
        'oldest':     'created_at ASC',
        'deadline':   'target_date ASC',
        'amount_high':'target_amount DESC',
        'amount_low': 'target_amount ASC',
        'progress':   'current_amount DESC',
    }
    query += f" ORDER BY {sort_map.get(sort, 'created_at DESC')}"
    goals = [process_goal(r) for r in db.execute(query, params).fetchall()]

    return render_template('goals.html',
                           goals=goals,
                           categories=CATEGORIES, priorities=PRIORITIES, statuses=STATUSES,
                           search=search, selected_category=category,
                           selected_status=status, selected_priority=priority,
                           selected_sort=sort)


@app.route('/goals/<int:goal_id>')
def goal_detail(goal_id):
    db  = get_db()
    row = db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if not row:
        abort(404)
    goal   = process_goal(row)
    parts  = [process_goal_part(r) for r in
              db.execute("SELECT * FROM goal_parts WHERE goal_id = ? ORDER BY id", (goal_id,)).fetchall()]
    savings = [dict(r) for r in
               db.execute("SELECT * FROM savings WHERE goal_id = ? ORDER BY saving_date DESC", (goal_id,)).fetchall()]

    profile_row = db.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    capacity = float(dict(profile_row).get('monthly_saving_capacity', 0)) if profile_row else 0

    return render_template('goal_details.html', goal=goal, parts=parts,
                           savings=savings, capacity=capacity,
                           today=date.today().isoformat())


@app.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
def edit_goal(goal_id):
    db  = get_db()
    row = db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if not row:
        abort(404)
    goal = process_goal(row)

    if request.method == 'POST':
        goal_name     = request.form.get('goal_name', '').strip()
        goal_type     = request.form.get('goal_type', '').strip()
        description   = request.form.get('description', '').strip()
        category      = request.form.get('category', 'Personal')
        priority      = request.form.get('priority', 'Medium')
        status        = request.form.get('status', 'Active')
        notes         = request.form.get('notes', '').strip()
        start_date    = request.form.get('start_date', '')
        target_date   = request.form.get('target_date', '')

        try:
            target_amount  = float(request.form.get('target_amount', 0))
            current_amount = float(request.form.get('current_amount', 0))
        except (ValueError, TypeError):
            flash('Invalid amount values.', 'danger')
            return redirect(url_for('edit_goal', goal_id=goal_id))

        errors = []
        if not goal_name:
            errors.append('Goal name is required.')
        if target_amount <= 0:
            errors.append('Target amount must be greater than zero.')
        if current_amount < 0:
            errors.append('Current amount cannot be negative.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('goal_planning.html',
                                   goal=goal, edit=True,
                                   categories=CATEGORIES, priorities=PRIORITIES,
                                   statuses=STATUSES, form=request.form,
                                   today=date.today().isoformat())

        if current_amount >= target_amount > 0:
            status = 'Completed'

        db.execute(
            """UPDATE goals SET goal_name=?, goal_type=?, description=?, target_amount=?,
               current_amount=?, start_date=?, target_date=?, category=?, priority=?,
               status=?, notes=?, updated_at=? WHERE id=?""",
            (goal_name, goal_type, description, target_amount, current_amount,
             start_date, target_date, category, priority, status, notes,
             datetime.utcnow().isoformat(), goal_id)
        )
        db.commit()
        flash(f'Goal "{goal_name}" updated successfully!', 'success')
        return redirect(url_for('goal_detail', goal_id=goal_id))

    return render_template('goal_planning.html',
                           goal=goal, edit=True,
                           categories=CATEGORIES, priorities=PRIORITIES,
                           statuses=STATUSES, today=date.today().isoformat())


@app.route('/goals/<int:goal_id>/delete', methods=['POST'])
def delete_goal(goal_id):
    db  = get_db()
    row = db.execute("SELECT goal_name FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if not row:
        abort(404)
    name = row['goal_name']
    db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    db.commit()
    flash(f'Goal "{name}" deleted.', 'info')
    return redirect(url_for('goals_list'))


@app.route('/goals/<int:goal_id>/add-savings', methods=['POST'])
def add_savings(goal_id):
    db  = get_db()
    row = db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if not row:
        abort(404)

    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Invalid saving amount.', 'danger')
        return redirect(url_for('goal_detail', goal_id=goal_id))

    saving_date = request.form.get('saving_date', '') or date.today().isoformat()
    note        = request.form.get('note', '').strip()

    if amount <= 0:
        flash('Saving amount must be greater than zero.', 'danger')
        return redirect(url_for('goal_detail', goal_id=goal_id))

    target_amount  = float(row['target_amount'])
    current_amount = float(row['current_amount'])
    new_amount     = min(current_amount + amount, target_amount)

    db.execute(
        "INSERT INTO savings (goal_id, amount, saving_date, note) VALUES (?,?,?,?)",
        (goal_id, amount, saving_date, note)
    )
    new_status = 'Completed' if new_amount >= target_amount else row['status']
    db.execute(
        "UPDATE goals SET current_amount=?, status=?, updated_at=? WHERE id=?",
        (new_amount, new_status, datetime.utcnow().isoformat(), goal_id)
    )
    db.commit()
    flash(f'₹{amount:,.2f} savings added successfully!', 'success')
    return redirect(url_for('goal_detail', goal_id=goal_id))


@app.route('/goals/<int:goal_id>/add-milestone', methods=['POST'])
def add_milestone(goal_id):
    db  = get_db()
    if not db.execute("SELECT id FROM goals WHERE id = ?", (goal_id,)).fetchone():
        abort(404)

    part_name   = request.form.get('part_name', '').strip()
    due_date    = request.form.get('due_date', '')
    part_status = request.form.get('part_status', 'Pending')

    try:
        target_amount = float(request.form.get('target_amount', 0))
        saved_amount  = float(request.form.get('saved_amount', 0))
    except (ValueError, TypeError):
        flash('Invalid milestone amounts.', 'danger')
        return redirect(url_for('goal_detail', goal_id=goal_id))

    if not part_name:
        flash('Milestone name is required.', 'danger')
        return redirect(url_for('goal_detail', goal_id=goal_id))
    if target_amount <= 0:
        flash('Milestone target amount must be greater than zero.', 'danger')
        return redirect(url_for('goal_detail', goal_id=goal_id))

    db.execute(
        "INSERT INTO goal_parts (goal_id, part_name, target_amount, saved_amount, due_date, status) VALUES (?,?,?,?,?,?)",
        (goal_id, part_name, target_amount, max(saved_amount, 0), due_date, part_status)
    )
    db.commit()
    flash('Milestone added successfully!', 'success')
    return redirect(url_for('goal_detail', goal_id=goal_id))


@app.route('/goals/<int:goal_id>/milestones/<int:mid>/update', methods=['POST'])
def update_milestone(goal_id, mid):
    db = get_db()
    part_row = db.execute("SELECT * FROM goal_parts WHERE id = ? AND goal_id = ?", (mid, goal_id)).fetchone()
    if not part_row:
        abort(404)

    try:
        saved_amount = float(request.form.get('saved_amount', part_row['saved_amount']))
    except (ValueError, TypeError):
        saved_amount = float(part_row['saved_amount'])

    part_status = request.form.get('part_status', part_row['status'])
    saved_amount = min(saved_amount, float(part_row['target_amount']))
    if saved_amount >= float(part_row['target_amount']):
        part_status = 'Completed'

    db.execute("UPDATE goal_parts SET saved_amount=?, status=? WHERE id=?",
               (saved_amount, part_status, mid))
    db.commit()
    flash('Milestone updated successfully!', 'success')
    return redirect(url_for('goal_detail', goal_id=goal_id))


@app.route('/goals/<int:goal_id>/milestones/<int:mid>/delete', methods=['POST'])
def delete_milestone(goal_id, mid):
    db = get_db()
    if not db.execute("SELECT id FROM goal_parts WHERE id = ? AND goal_id = ?", (mid, goal_id)).fetchone():
        abort(404)
    db.execute("DELETE FROM goal_parts WHERE id = ?", (mid,))
    db.commit()
    flash('Milestone deleted.', 'info')
    return redirect(url_for('goal_detail', goal_id=goal_id))


# ═══════════════════════════════════════════════════════════════════════════════
# INVESTMENT ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/investments')
def investments_list():
    db     = get_db()
    search   = request.args.get('search', '').strip()
    inv_type = request.args.get('inv_type', '')
    status   = request.args.get('status', '')
    sort     = request.args.get('sort', 'newest')

    query  = "SELECT * FROM investments WHERE 1=1"
    params = []
    if search:
        query += " AND investment_name LIKE ?"
        params.append(f'%{search}%')
    if inv_type:
        query += " AND investment_type = ?"
        params.append(inv_type)
    if status:
        query += " AND status = ?"
        params.append(status)

    sort_map = {
        'newest':      'created_at DESC',
        'oldest':      'created_at ASC',
        'invested_high': 'invested_amount DESC',
        'invested_low':  'invested_amount ASC',
        'value_high':    'current_value DESC',
        'maturity':      'maturity_date ASC',
    }
    query += f" ORDER BY {sort_map.get(sort, 'created_at DESC')}"
    investments = [process_investment(r) for r in db.execute(query, params).fetchall()]

    # Summary stats
    total_invested = sum(i['invested_amount'] for i in investments)
    current_value  = sum(i['current_value'] for i in investments)
    total_pl       = current_value - total_invested
    avg_return     = round(sum(i['return_percentage'] for i in investments) / len(investments), 2) if investments else 0

    inv_stats = {
        'total': len(investments),
        'total_invested': total_invested,
        'current_value':  current_value,
        'total_pl':       total_pl,
        'avg_return':     avg_return,
    }

    return render_template('investments.html',
                           investments=investments, inv_stats=inv_stats,
                           inv_types=INV_TYPES, inv_statuses=INV_STATUSES,
                           search=search, selected_type=inv_type,
                           selected_status=status, selected_sort=sort,
                           today=date.today().isoformat())


@app.route('/investments/new', methods=['GET', 'POST'])
def investment_new():
    if request.method == 'POST':
        return _save_investment(None)
    return render_template('investment_form.html',
                           inv_types=INV_TYPES, inv_statuses=INV_STATUSES,
                           today=date.today().isoformat(), edit=False)


@app.route('/investments/<int:inv_id>/edit', methods=['GET', 'POST'])
def investment_edit(inv_id):
    db  = get_db()
    row = db.execute("SELECT * FROM investments WHERE id = ?", (inv_id,)).fetchone()
    if not row:
        abort(404)
    inv = process_investment(row)

    if request.method == 'POST':
        return _save_investment(inv_id)
    return render_template('investment_form.html',
                           inv=inv, inv_types=INV_TYPES, inv_statuses=INV_STATUSES,
                           today=date.today().isoformat(), edit=True)


def _save_investment(inv_id):
    """Shared logic for create/update investment."""
    inv_name     = request.form.get('investment_name', '').strip()
    inv_type     = request.form.get('investment_type', 'Other')
    inv_date     = request.form.get('investment_date', '')
    maturity_date= request.form.get('maturity_date', '')
    status       = request.form.get('status', 'Active')
    notes        = request.form.get('notes', '').strip()

    try:
        invested = float(request.form.get('invested_amount', 0))
        current  = float(request.form.get('current_value', 0))
        exp_ret  = float(request.form.get('expected_return_rate', 0) or 0)
    except (ValueError, TypeError):
        flash('Invalid amount values.', 'danger')
        return redirect(request.url)

    errors = []
    if not inv_name:
        errors.append('Investment name is required.')
    if invested <= 0:
        errors.append('Invested amount must be greater than zero.')
    if current < 0:
        errors.append('Current value cannot be negative.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(request.url)

    db  = get_db()
    now = datetime.utcnow().isoformat()
    if inv_id is None:
        db.execute(
            """INSERT INTO investments (investment_name, investment_type, invested_amount,
               current_value, investment_date, maturity_date, expected_return_rate,
               status, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (inv_name, inv_type, invested, current, inv_date, maturity_date,
             exp_ret, status, notes, now, now)
        )
        db.commit()
        new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        flash(f'Investment "{inv_name}" added successfully!', 'success')
        return redirect(url_for('investments_list'))
    else:
        db.execute(
            """UPDATE investments SET investment_name=?, investment_type=?, invested_amount=?,
               current_value=?, investment_date=?, maturity_date=?, expected_return_rate=?,
               status=?, notes=?, updated_at=? WHERE id=?""",
            (inv_name, inv_type, invested, current, inv_date, maturity_date,
             exp_ret, status, notes, now, inv_id)
        )
        db.commit()
        flash(f'Investment "{inv_name}" updated successfully!', 'success')
        return redirect(url_for('investments_list'))


@app.route('/investments/<int:inv_id>/delete', methods=['POST'])
def investment_delete(inv_id):
    db  = get_db()
    row = db.execute("SELECT investment_name FROM investments WHERE id = ?", (inv_id,)).fetchone()
    if not row:
        abort(404)
    name = row['investment_name']
    db.execute("DELETE FROM investments WHERE id = ?", (inv_id,))
    db.commit()
    flash(f'Investment "{name}" deleted.', 'info')
    return redirect(url_for('investments_list'))


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    db = get_db()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip() or 'My Profile'
        email    = request.form.get('email', '').strip()
        phone    = request.form.get('phone', '').strip()
        currency = request.form.get('currency', '₹').strip() or '₹'
        notes    = request.form.get('notes', '').strip()

        try:
            saving_cap = float(request.form.get('monthly_saving_capacity', 0) or 0)
            invest_cap = float(request.form.get('monthly_investment_capacity', 0) or 0)
        except (ValueError, TypeError):
            saving_cap = 0
            invest_cap = 0

        now = datetime.utcnow().isoformat()
        existing = db.execute("SELECT id FROM profile WHERE id = 1").fetchone()
        if existing:
            db.execute(
                """UPDATE profile SET name=?, email=?, phone=?, currency=?,
                   monthly_saving_capacity=?, monthly_investment_capacity=?,
                   notes=?, updated_at=? WHERE id=1""",
                (name, email, phone, currency, saving_cap, invest_cap, notes, now)
            )
        else:
            db.execute(
                """INSERT INTO profile (id, name, email, phone, currency,
                   monthly_saving_capacity, monthly_investment_capacity, notes,
                   created_at, updated_at)
                   VALUES (1,?,?,?,?,?,?,?,?,?)""",
                (name, email, phone, currency, saving_cap, invest_cap, notes, now, now)
            )
        db.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    # Compute stats for profile page
    goal_stats, inv_stats = get_dashboard_stats(db)
    prof = db.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    prof = dict(prof) if prof else {}

    return render_template('profile.html', prof=prof,
                           goal_stats=goal_stats, inv_stats=inv_stats)


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404,
                           message='Page not found.'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500,
                           message='Something went wrong. Please try again.'), 500


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION START
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
