import io
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models import User, Category, Account


def test_end_to_end_flow():
    """In-process end-to-end smoke test exercising key API flows."""
    app = create_app(TestingConfig)

    with app.app_context():
        # fresh DB
        db.drop_all()
        db.create_all()

        client = app.test_client()

        # Register admin user
        reg = client.post('/api/auth/register', json={
            'email': 'admin@advisor.local',
            'username': 'admin',
            'password': 'admin123'
        })
        assert reg.status_code == 201
        user_id = reg.json['user']['id']

        # Promote to admin
        user = User.query.get(user_id)
        user.role = 'admin'
        db.session.commit()

        # Create a default category and account for the user
        cat = Category(name='Groceries', description='Grocery category')
        db.session.add(cat)
        db.session.flush()

        acct = Account(user_id=user.id, name='Checking', account_type='checking', balance=1000)
        db.session.add(acct)
        db.session.commit()

        # Login to get access token
        login = client.post('/api/auth/login', json={'email': 'admin@advisor.local', 'password': 'admin123'})
        assert login.status_code == 200
        token = login.json['tokens']['access_token']
        auth_headers = {'Authorization': f'Bearer {token}'}

        # Profile should be accessible
        profile = client.get('/api/auth/profile', headers=auth_headers)
        assert profile.status_code == 200
        assert profile.json.get('email') == 'admin@advisor.local'

        # Validate a simple admin rule payload
        rule_payload = {
            'name': 'Grocery rule',
            'condition': {'operator': 'merchant_contains', 'value': 'trader'},
            'action': {'type': 'set_category', 'category_id': cat.id}
        }
        rv = client.post('/api/admin/rules/validate', json=rule_payload, headers=auth_headers)
        assert rv.status_code == 200
        assert rv.json.get('valid') is True

        # Prepare a small CSV for import using account_id and required fields
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        d1 = (now - timedelta(days=1)).isoformat()
        d2 = (now - timedelta(days=5)).isoformat()

        csv_text = (
            "transaction_date,description,amount,account_id,type\n"
            f"{d1},Trader Joe's,23.45,{acct.id},expense\n"
            f"{d2},Rent,150.00,{acct.id},expense\n"
            f"{d2},Salary,3000.00,{acct.id},income\n"
        )
        csv_bytes = csv_text.encode('utf-8')

        # Preview import
        data = {'file': (io.BytesIO(csv_bytes), 'transactions.csv')}
        preview = client.post('/api/transactions/import/preview', headers=auth_headers, data=data)
        if preview.status_code != 200:
            print('PREVIEW_RESPONSE_STATUS:', preview.status_code)
            try:
                print('PREVIEW_RESPONSE_JSON:', preview.json)
            except Exception:
                print('PREVIEW_RESPONSE_TEXT:', preview.get_data(as_text=True))
        assert preview.status_code == 200
        assert 'preview_rows' in preview.json

        # Commit import
        data = {'file': (io.BytesIO(csv_bytes), 'transactions.csv')}
        commit = client.post('/api/transactions/import/commit', headers=auth_headers, data=data)
        assert commit.status_code == 200
        # TransactionImporter returns 'created_count' on success
        assert commit.json.get('created_count', 0) >= 1

        # Create a budget for the category
        bdata = {'category_id': cat.id, 'limit_amount': 200, 'period': 'monthly', 'start_date': '2025-01-01T00:00:00'}
        cb = client.post('/api/budgets/', headers=auth_headers, json=bdata)
        assert cb.status_code == 201

        # Request planner recommendations
        rec = client.post('/api/planner/recommend-budgets', headers=auth_headers, json={'months': 3})
        if rec.status_code != 200:
            print('PLANNER_RESPONSE_STATUS:', rec.status_code)
            try:
                print('PLANNER_RESPONSE_JSON:', rec.json)
            except Exception:
                print('PLANNER_RESPONSE_TEXT:', rec.get_data(as_text=True))
        assert rec.status_code == 200
        assert isinstance(rec.json, dict) or isinstance(rec.json, list)
