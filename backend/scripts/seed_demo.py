"""Seed demo user and transactions from sample-data CSV files.

Run with:
  python backend/scripts/seed_demo.py

This script expects to run in the project root so it can find
`sample-data/demo-user.csv` and `sample-data/transactions_6mo.csv`.
"""
import csv
import os
from decimal import Decimal
from datetime import datetime, timezone

from app import create_app
from app.database import db
from app.models import User, Account, Category, Transaction


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
DEMO_USER_CSV = os.path.join(ROOT, 'sample-data', 'demo-user.csv')
DEMO_TX_CSV = os.path.join(ROOT, 'sample-data', 'transactions_6mo.csv')


def parse_date(s):
    # Accept ISO-like dates
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.strptime(s, '%Y-%m-%d')


def seed():
    app = create_app()
    with app.app_context():
        print('Creating fresh DB (drop/create)...')
        db.drop_all()
        db.create_all()

        # Read demo user
        with open(DEMO_USER_CSV, newline='') as f:
            r = csv.DictReader(f)
            user_row = next(r)

        user = User(
            email=user_row['email'],
            username=user_row.get('username') or 'demo',
            password_hash=user_row.get('password') or 'demo',
            first_name=user_row.get('first_name', ''),
            last_name=user_row.get('last_name', ''),
        )
        # If your AuthService expects hashing, use provided helper; fallback to manual
        try:
            from app.services import AuthService
            AuthService().create_user(email=user.email, username=user.username, password=user_row['password'])
            user = User.query.filter_by(email=user.email).first()
        except Exception:
            # direct insert (password_hash placeholder)
            user.password_hash = user_row.get('password')
            db.session.add(user)
            db.session.commit()

        # Create a primary checking account
        acct = Account(user_id=user.id, name='Checking', account_type='checking', balance=0)
        db.session.add(acct)
        db.session.commit()

        # Read transactions and categories
        cats = {}
        with open(DEMO_TX_CSV, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure category
                cat_name = row.get('category_name') or 'Uncategorized'
                if cat_name not in cats:
                    c = Category(name=cat_name, description='Demo')
                    db.session.add(c)
                    db.session.flush()
                    cats[cat_name] = c

                tx_date = parse_date(row['transaction_date'])
                tx = Transaction(
                    user_id=user.id,
                    account_id=acct.id,
                    amount=Decimal(row['amount']),
                    type=row.get('type', 'expense'),
                    description=row.get('description', ''),
                    transaction_date=tx_date.replace(tzinfo=timezone.utc) if tx_date.tzinfo is None else tx_date,
                    category_id=cats[cat_name].id,
                )
                db.session.add(tx)

        db.session.commit()
        print('Seeding complete. Demo user:', user.email)
        print('Login with email and password from sample-data/demo-user.csv')


if __name__ == '__main__':
    seed()
