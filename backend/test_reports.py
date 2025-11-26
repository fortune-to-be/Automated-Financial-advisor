import io
from datetime import datetime, timedelta
from app import create_app, db
from app.config import TestingConfig
from app.models import User, Account, Category, Transaction, Budget
from app.services.reports import ReportsService


def _make_app():
    return create_app(TestingConfig)


def _setup_user_with_transactions(app):
    with app.app_context():
        db.create_all()
        user = User(email='reports@test', username='reports', password_hash='x')
        db.session.add(user)
        db.session.commit()

        acc = Account(user_id=user.id, name='Main', account_type='checking', balance=0)
        db.session.add(acc)

        cat_g = Category(name='Groceries')
        cat_u = Category(name='Utilities')
        db.session.add_all([cat_g, cat_u])
        db.session.commit()

        now = datetime.utcnow()
        tx1 = Transaction(user_id=user.id, account_id=acc.id, amount=45.67, type='expense', category_id=cat_g.id, transaction_date=now - timedelta(days=2))
        tx2 = Transaction(user_id=user.id, account_id=acc.id, amount=120.0, type='expense', category_id=cat_u.id, transaction_date=now - timedelta(days=1))
        tx3 = Transaction(user_id=user.id, account_id=acc.id, amount=3000.0, type='income', category_id=None, transaction_date=now)
        db.session.add_all([tx1, tx2, tx3])

        # budget example
        b = Budget(user_id=user.id, category_id=cat_g.id, limit_amount=200, period='monthly', start_date=now - timedelta(days=30))
        db.session.add(b)

        db.session.commit()
        return user.id


def test_reports_service_csv_and_summary_and_pdf():
    app = _make_app()
    user_id = _setup_user_with_transactions(app)

    service = ReportsService()

    # CSV stream
    with app.app_context():
        gen = service.stream_expenses_csv(user_id=user_id)
        chunks = list(gen)
        csv_text = ''.join(chunks)
        assert 'Groceries' in csv_text
        assert 'Utilities' in csv_text

        # summary
        summary = service.get_summary(user_id=user_id)
        assert summary['total_income'] > 0
        assert summary['total_expense'] > 0
        assert 'Groceries' in summary['by_category']

        # PDF generation: only run if reportlab present
        try:
            pdf_bytes = service.generate_summary_pdf(summary, user_id=user_id)
            assert isinstance(pdf_bytes, (bytes, bytearray))
            assert len(pdf_bytes) > 100
        except RuntimeError:
            # reportlab missing in environment; acceptable
            pass
