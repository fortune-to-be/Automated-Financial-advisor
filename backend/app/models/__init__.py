from datetime import datetime, timezone
from app.database import db
from sqlalchemy.dialects.postgresql import JSON

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    role = db.Column(db.String(50), default='user')  # admin, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')
    rules = db.relationship('Rule', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Account(db.Model):
    """Account model - checking, savings, etc."""
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # checking, savings, credit_card, investment
    balance = db.Column(db.Numeric(15, 2), default=0.0)
    currency = db.Column(db.String(3), default='USD')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Account {self.name}>'


class Category(db.Model):
    """Transaction category model"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#000000')  # Hex color
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Transaction(db.Model):
    """Transaction model - income, expense, transfer"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # income, expense, transfer
    description = db.Column(db.Text)
    transaction_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    tags = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<Transaction {self.type} ${self.amount}>'


class Budget(db.Model):
    """Budget model - spending limits per category"""
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    limit_amount = db.Column(db.Numeric(15, 2), nullable=False)
    period = db.Column(db.String(50), default='monthly')  # monthly, yearly, custom
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<Budget {self.limit_amount}>'


class Goal(db.Model):
    """Financial goal model"""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    target_amount = db.Column(db.Numeric(15, 2), nullable=False)
    current_amount = db.Column(db.Numeric(15, 2), default=0.0)
    target_date = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(100))  # savings, debt_payoff, purchase, education, etc.
    priority = db.Column(db.String(50), default='medium')  # low, medium, high
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<Goal {self.name}>'


class Rule(db.Model):
    """Automated rule model - automation for categorization and actions"""
    __tablename__ = 'rules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    condition = db.Column(JSON, nullable=False)  # e.g., {"field": "description", "operator": "contains", "value": "grocery"}
    action = db.Column(JSON, nullable=False)  # e.g., {"type": "categorize", "category_id": 5}
    priority = db.Column(db.Integer, default=0)  # Higher number = higher priority
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<Rule {self.name}>'
    
    def apply_to_transaction(self, transaction_dict):
        """
        Apply this rule to a transaction dictionary.
        Returns (modified_tx, explanation) tuple.
        """
        from app.services.rule_engine import ConditionEvaluator, ActionExecutor
        
        if not ConditionEvaluator.evaluate(self.condition, transaction_dict):
            return transaction_dict, None
        
        modified_tx, explanation = ActionExecutor.execute(self.action, transaction_dict)
        return modified_tx, explanation


class AuditLog(db.Model):
    """Audit log model - track user actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)  # create, update, delete, login, etc.
    resource_type = db.Column(db.String(100))  # User, Transaction, Budget, etc.
    resource_id = db.Column(db.Integer)
    old_values = db.Column(JSON)
    new_values = db.Column(JSON)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'
