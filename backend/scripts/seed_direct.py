from app import create_app
from app.database import db
from app.services import AuthService
from app.models import User, Category, Rule

app = create_app()

with app.app_context():
    db.create_all()
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
        print('Admin user created')
    else:
        print('Admin already exists')

    # create Grocery category if missing
    grocery = Category.query.filter_by(name='Grocery').first()
    if not grocery:
        grocery = Category(name='Grocery', description='Grocery and food')
        db.session.add(grocery)
        db.session.commit()
        print('Grocery category created')

    # create a simple rule
    rule = Rule.query.filter_by(name='Auto-categorize Grocery').first()
    if not rule:
        rule = Rule(
            user_id=admin.id,
            name='Auto-categorize Grocery',
            description='Categorize by grocery',
            condition={'operator': 'merchant_contains', 'value': 'trader'},
            action={'type': 'set_category', 'category_id': grocery.id},
            priority=10,
            is_active=True
        )
        db.session.add(rule)
        db.session.commit()
        print('Grocery rule created')

    print('Seeding complete')
