from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────────
# User Model
# ─────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True, default=None)
    monthly_saving_capacity = db.Column(db.Float, nullable=True, default=0.0)
    currency = db.Column(db.String(10), nullable=False, default='₹')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def total_goals(self):
        return len(self.goals)

    @property
    def active_goals(self):
        return sum(1 for g in self.goals if g.status == 'Active')

    @property
    def completed_goals(self):
        return sum(1 for g in self.goals if g.status == 'Completed')

    @property
    def on_hold_goals(self):
        return sum(1 for g in self.goals if g.status == 'On Hold')

    @property
    def total_target(self):
        return sum(g.target_amount for g in self.goals)

    @property
    def total_saved(self):
        return sum(g.current_amount for g in self.goals)

    @property
    def total_remaining(self):
        return self.total_target - self.total_saved

    def __repr__(self):
        return f'<User {self.email}>'


# ─────────────────────────────────────────────
# Goal Model
# ─────────────────────────────────────────────
class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_name = db.Column(db.String(200), nullable=False)
    goal_type = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    target_amount = db.Column(db.Float, nullable=False, default=0.0)
    current_amount = db.Column(db.Float, nullable=False, default=0.0)
    start_date = db.Column(db.Date, nullable=True)
    target_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(100), nullable=True, default='Personal')
    priority = db.Column(db.String(20), nullable=True, default='Medium')
    status = db.Column(db.String(30), nullable=False, default='Active')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parts = db.relationship('GoalPart', backref='goal', lazy=True, cascade='all, delete-orphan')
    savings = db.relationship('SavingsRecord', backref='goal', lazy=True, cascade='all, delete-orphan', order_by='SavingsRecord.saving_date.desc()')

    # ── Computed Properties ──────────────────────────────────
    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, 0)

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0
        return min(round((self.current_amount / self.target_amount) * 100, 1), 100)

    @property
    def months_left(self):
        if not self.target_date:
            return None
        today = date.today()
        if self.target_date <= today:
            return 0
        delta_days = (self.target_date - today).days
        return max(delta_days / 30.44, 0)

    @property
    def required_monthly_saving(self):
        ml = self.months_left
        if ml is None or ml <= 0:
            return 0
        return round(self.remaining_amount / ml, 2)

    @property
    def required_weekly_saving(self):
        rms = self.required_monthly_saving
        return round(rms / 4.33, 2) if rms else 0

    @property
    def smart_status(self):
        """Intelligently determine goal condition based on time vs savings progress."""
        if self.current_amount >= self.target_amount:
            return 'Completed'
        if not self.start_date or not self.target_date:
            return self.status

        today = date.today()
        total_days = (self.target_date - self.start_date).days
        elapsed_days = (today - self.start_date).days

        if total_days <= 0:
            return 'Behind Schedule' if self.current_amount < self.target_amount else 'Completed'

        elapsed_ratio = max(min(elapsed_days / total_days, 1.0), 0.0)
        expected_saved = self.target_amount * elapsed_ratio

        if self.current_amount >= expected_saved * 0.90:
            return 'On Track'
        elif self.current_amount >= expected_saved * 0.70:
            return 'Needs Attention'
        else:
            return 'Behind Schedule'

    @property
    def smart_status_class(self):
        mapping = {
            'On Track': 'success',
            'Completed': 'success',
            'Needs Attention': 'warning',
            'Behind Schedule': 'danger',
        }
        return mapping.get(self.smart_status, 'secondary')

    @property
    def priority_class(self):
        mapping = {'High': 'danger', 'Medium': 'warning', 'Low': 'success'}
        return mapping.get(self.priority, 'secondary')

    @property
    def status_class(self):
        mapping = {'Active': 'primary', 'Completed': 'success', 'On Hold': 'secondary'}
        return mapping.get(self.status, 'secondary')

    @property
    def days_left(self):
        if not self.target_date:
            return None
        return (self.target_date - date.today()).days

    def __repr__(self):
        return f'<Goal {self.goal_name}>'


# ─────────────────────────────────────────────
# Goal Part (Milestone)
# ─────────────────────────────────────────────
class GoalPart(db.Model):
    __tablename__ = 'goal_parts'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    part_name = db.Column(db.String(200), nullable=False)
    target_amount = db.Column(db.Float, nullable=False, default=0.0)
    saved_amount = db.Column(db.Float, nullable=False, default=0.0)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0
        return min(round((self.saved_amount / self.target_amount) * 100, 1), 100)

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.saved_amount, 0)

    def __repr__(self):
        return f'<GoalPart {self.part_name}>'


# ─────────────────────────────────────────────
# Savings Record
# ─────────────────────────────────────────────
class SavingsRecord(db.Model):
    __tablename__ = 'savings'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    saving_date = db.Column(db.Date, nullable=False, default=date.today)
    note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SavingsRecord ₹{self.amount} on {self.saving_date}>'
