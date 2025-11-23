#!/usr/bin/env python
"""Management script for the application"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Account, Category, Transaction, Budget, Goal, Rule, AuditLog
from app.services import AuthService

app = create_app()

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print("Database initialized")

@app.cli.command()
def seed_db():
    """Seed the database with initial data"""
    # Create admin user
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                email='admin@advisor.local',
                username='admin',
                password_hash=AuthService.hash_password('admin123'),
                first_name='Admin',
                last_name='User',
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.session.rollback()
    
    # Create default categories
    categories_data = [
        {'name': 'Grocery', 'description': 'Grocery and food', 'color': '#4CAF50', 'icon': 'shopping-cart'},
        {'name': 'Utilities', 'description': 'Electricity, water, gas', 'color': '#2196F3', 'icon': 'lightbulb'},
        {'name': 'Transportation', 'description': 'Gas, public transit, car maintenance', 'color': '#FF9800', 'icon': 'car'},
        {'name': 'Entertainment', 'description': 'Movies, games, hobbies', 'color': '#9C27B0', 'icon': 'movie'},
        {'name': 'Healthcare', 'description': 'Medical, pharmacy, fitness', 'color': '#F44336', 'icon': 'heart'},
        {'name': 'Shopping', 'description': 'Clothing, accessories, home goods', 'color': '#E91E63', 'icon': 'shopping-bag'},
        {'name': 'Salary', 'description': 'Regular income', 'color': '#00BCD4', 'icon': 'briefcase'},
    ]
    
    try:
        for cat_data in categories_data:
            existing = Category.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
        db.session.commit()
        print(f"Created {len(categories_data)} categories")
    except Exception as e:
        print(f"Error creating categories: {str(e)}")
        db.session.rollback()
    
    # Create a grocery rule
    try:
        rule = Rule.query.filter_by(name='Auto-categorize Grocery').first()
        if not rule:
            grocery_category = Category.query.filter_by(name='Grocery').first()
            if grocery_category:
                grocery_rule = Rule(
                    user_id=admin.id,
                    name='Auto-categorize Grocery',
                    description='Automatically categorize transactions containing "grocery" in description',
                    condition={
                        'field': 'description',
                        'operator': 'contains',
                        'value': 'grocery'
                    },
                    action={
                        'type': 'categorize',
                        'category_id': grocery_category.id
                    },
                    priority=10,
                    is_active=True
                )
                db.session.add(grocery_rule)
                db.session.commit()
                print("Grocery rule created")
    except Exception as e:
        print(f"Error creating rule: {str(e)}")
        db.session.rollback()
    
    print("Database seeded successfully")

@app.cli.command()
def drop_db():
    """Drop all tables"""
    if input('Are you sure you want to drop all tables? (y/n): ').lower() == 'y':
        db.drop_all()
        print("Database dropped")
    else:
        print("Cancelled")

if __name__ == '__main__':
    app.cli()
