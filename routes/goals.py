from datetime import date
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, abort)
from flask_login import login_required, current_user
from models import db, Goal, GoalPart, SavingsRecord

goals_bp = Blueprint('goals', __name__)

CATEGORIES = ['Education', 'Electronics', 'Travel', 'Emergency',
              'Vehicle', 'Personal', 'Health', 'Other']
PRIORITIES = ['High', 'Medium', 'Low']
STATUSES = ['Active', 'Completed', 'On Hold']


# ─── Helper ──────────────────────────────────────────────────────────────────
def _get_goal_or_404(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        abort(404)
    return goal


def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


# ─── Goal Planning (Create) ──────────────────────────────────────────────────
@goals_bp.route('/goal-planning', methods=['GET', 'POST'])
@login_required
def goal_planning():
    if request.method == 'POST':
        goal_name = request.form.get('goal_name', '').strip()
        goal_type = request.form.get('goal_type', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Personal')
        priority = request.form.get('priority', 'Medium')
        status = request.form.get('status', 'Active')
        notes = request.form.get('notes', '').strip()

        try:
            target_amount = float(request.form.get('target_amount', 0))
            current_amount = float(request.form.get('current_amount', 0))
        except ValueError:
            flash('Invalid amount values.', 'danger')
            return redirect(url_for('goals.goal_planning'))

        start_date = _parse_date(request.form.get('start_date'))
        target_date = _parse_date(request.form.get('target_date'))

        # Validation
        errors = []
        if not goal_name:
            errors.append('Goal name is required.')
        if target_amount <= 0:
            errors.append('Target amount must be greater than zero.')
        if current_amount < 0:
            errors.append('Current amount cannot be negative.')
        if current_amount > target_amount:
            errors.append('Current amount cannot exceed the target amount.')
        if target_date and start_date and target_date <= start_date:
            errors.append('Target date must be after start date.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('goal_planning.html',
                                   categories=CATEGORIES, priorities=PRIORITIES,
                                   statuses=STATUSES, form=request.form)

        goal = Goal(
            user_id=current_user.id,
            goal_name=goal_name,
            goal_type=goal_type,
            description=description,
            category=category,
            priority=priority,
            status=status,
            notes=notes,
            target_amount=target_amount,
            current_amount=current_amount,
            start_date=start_date or date.today(),
            target_date=target_date,
        )
        db.session.add(goal)
        db.session.commit()

        # If current amount already reaches target, auto-complete
        if goal.current_amount >= goal.target_amount:
            goal.status = 'Completed'
            db.session.commit()

        flash(f'Goal "{goal_name}" created successfully!', 'success')
        return redirect(url_for('goals.goal_detail', goal_id=goal.id))

    return render_template('goal_planning.html',
                           categories=CATEGORIES, priorities=PRIORITIES,
                           statuses=STATUSES, today=date.today().isoformat())


# ─── All Goals ───────────────────────────────────────────────────────────────
@goals_bp.route('/goals')
@login_required
def goals_list():
    query = Goal.query.filter_by(user_id=current_user.id)

    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    sort = request.args.get('sort', 'newest')

    if search:
        query = query.filter(Goal.goal_name.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)

    sort_map = {
        'newest': Goal.created_at.desc(),
        'oldest': Goal.created_at.asc(),
        'deadline': Goal.target_date.asc(),
        'amount_high': Goal.target_amount.desc(),
        'amount_low': Goal.target_amount.asc(),
        'progress': Goal.current_amount.desc(),
    }
    query = query.order_by(sort_map.get(sort, Goal.created_at.desc()))
    goals = query.all()

    return render_template('goals.html',
                           goals=goals,
                           categories=CATEGORIES,
                           priorities=PRIORITIES,
                           statuses=STATUSES,
                           search=search,
                           selected_category=category,
                           selected_status=status,
                           selected_priority=priority,
                           selected_sort=sort)


# ─── Goal Detail ─────────────────────────────────────────────────────────────
@goals_bp.route('/goals/<int:goal_id>')
@login_required
def goal_detail(goal_id):
    goal = _get_goal_or_404(goal_id)
    capacity = current_user.monthly_saving_capacity or 0
    return render_template('goal_details.html', goal=goal, capacity=capacity, today=date.today().isoformat())


# ─── Edit Goal ───────────────────────────────────────────────────────────────
@goals_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    goal = _get_goal_or_404(goal_id)

    if request.method == 'POST':
        goal_name = request.form.get('goal_name', '').strip()
        goal_type = request.form.get('goal_type', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Personal')
        priority = request.form.get('priority', 'Medium')
        status = request.form.get('status', 'Active')
        notes = request.form.get('notes', '').strip()

        try:
            target_amount = float(request.form.get('target_amount', 0))
            current_amount = float(request.form.get('current_amount', 0))
        except ValueError:
            flash('Invalid amount values.', 'danger')
            return redirect(url_for('goals.edit_goal', goal_id=goal_id))

        start_date = _parse_date(request.form.get('start_date'))
        target_date = _parse_date(request.form.get('target_date'))

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
                                   statuses=STATUSES, form=request.form)

        goal.goal_name = goal_name
        goal.goal_type = goal_type
        goal.description = description
        goal.category = category
        goal.priority = priority
        goal.status = status
        goal.notes = notes
        goal.target_amount = target_amount
        goal.current_amount = current_amount
        if start_date:
            goal.start_date = start_date
        if target_date:
            goal.target_date = target_date

        # Auto-complete check
        if goal.current_amount >= goal.target_amount:
            goal.status = 'Completed'

        from datetime import datetime
        goal.updated_at = datetime.utcnow()
        db.session.commit()

        flash(f'Goal "{goal_name}" updated successfully!', 'success')
        return redirect(url_for('goals.goal_detail', goal_id=goal_id))

    return render_template('goal_planning.html',
                           goal=goal, edit=True,
                           categories=CATEGORIES, priorities=PRIORITIES,
                           statuses=STATUSES, today=date.today().isoformat())


# ─── Delete Goal ─────────────────────────────────────────────────────────────
@goals_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = _get_goal_or_404(goal_id)
    name = goal.goal_name
    db.session.delete(goal)
    db.session.commit()
    flash(f'Goal "{name}" has been deleted.', 'info')
    return redirect(url_for('goals.goals_list'))


# ─── Add Savings ─────────────────────────────────────────────────────────────
@goals_bp.route('/goals/<int:goal_id>/add-savings', methods=['POST'])
@login_required
def add_savings(goal_id):
    goal = _get_goal_or_404(goal_id)

    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('Invalid saving amount.', 'danger')
        return redirect(url_for('goals.goal_detail', goal_id=goal_id))

    saving_date_str = request.form.get('saving_date', '')
    note = request.form.get('note', '').strip()
    saving_date = _parse_date(saving_date_str) or date.today()

    if amount <= 0:
        flash('Saving amount must be greater than zero.', 'danger')
        return redirect(url_for('goals.goal_detail', goal_id=goal_id))

    # Create savings record
    record = SavingsRecord(
        goal_id=goal_id,
        amount=amount,
        saving_date=saving_date,
        note=note,
    )
    db.session.add(record)

    # Update goal's current amount
    goal.current_amount = min(goal.current_amount + amount, goal.target_amount)

    # Auto-complete if reached target
    if goal.current_amount >= goal.target_amount:
        goal.status = 'Completed'

    from datetime import datetime
    goal.updated_at = datetime.utcnow()
    db.session.commit()

    flash(f'₹{amount:,.2f} savings added successfully!', 'success')
    return redirect(url_for('goals.goal_detail', goal_id=goal_id))


# ─── Add Milestone ───────────────────────────────────────────────────────────
@goals_bp.route('/goals/<int:goal_id>/add-milestone', methods=['POST'])
@login_required
def add_milestone(goal_id):
    goal = _get_goal_or_404(goal_id)

    part_name = request.form.get('part_name', '').strip()
    due_date = _parse_date(request.form.get('due_date', ''))
    status = request.form.get('part_status', 'Pending')

    try:
        target_amount = float(request.form.get('target_amount', 0))
        saved_amount = float(request.form.get('saved_amount', 0))
    except ValueError:
        flash('Invalid milestone amounts.', 'danger')
        return redirect(url_for('goals.goal_detail', goal_id=goal_id))

    if not part_name:
        flash('Milestone name is required.', 'danger')
        return redirect(url_for('goals.goal_detail', goal_id=goal_id))
    if target_amount <= 0:
        flash('Milestone target amount must be greater than zero.', 'danger')
        return redirect(url_for('goals.goal_detail', goal_id=goal_id))

    part = GoalPart(
        goal_id=goal_id,
        part_name=part_name,
        target_amount=target_amount,
        saved_amount=max(saved_amount, 0),
        due_date=due_date,
        status=status,
    )
    db.session.add(part)
    db.session.commit()

    flash('Milestone added successfully!', 'success')
    return redirect(url_for('goals.goal_detail', goal_id=goal_id))


# ─── Update Milestone ────────────────────────────────────────────────────────
@goals_bp.route('/goals/<int:goal_id>/milestones/<int:mid>/update', methods=['POST'])
@login_required
def update_milestone(goal_id, mid):
    goal = _get_goal_or_404(goal_id)
    part = GoalPart.query.filter_by(id=mid, goal_id=goal_id).first_or_404()

    try:
        saved_amount = float(request.form.get('saved_amount', part.saved_amount))
    except ValueError:
        saved_amount = part.saved_amount

    part.saved_amount = min(saved_amount, part.target_amount)
    part.status = request.form.get('part_status', part.status)
    if part.saved_amount >= part.target_amount:
        part.status = 'Completed'

    db.session.commit()
    flash('Milestone updated successfully!', 'success')
    return redirect(url_for('goals.goal_detail', goal_id=goal_id))


# ─── Delete Milestone ────────────────────────────────────────────────────────
@goals_bp.route('/goals/<int:goal_id>/milestones/<int:mid>/delete', methods=['POST'])
@login_required
def delete_milestone(goal_id, mid):
    goal = _get_goal_or_404(goal_id)
    part = GoalPart.query.filter_by(id=mid, goal_id=goal_id).first_or_404()
    db.session.delete(part)
    db.session.commit()
    flash('Milestone deleted.', 'info')
    return redirect(url_for('goals.goal_detail', goal_id=goal_id))
