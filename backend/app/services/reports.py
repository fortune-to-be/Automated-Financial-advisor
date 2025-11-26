"""Reports service: CSV export and PDF/summary generation"""
from io import StringIO, BytesIO
import csv
from datetime import datetime
from decimal import Decimal

from app.database import db
from app.models import Transaction, Category, Budget, User

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet
    HAVE_REPORTLAB = True
except Exception:
    HAVE_REPORTLAB = False

try:
    import matplotlib.pyplot as plt
    HAVE_MATPLOTLIB = True
except Exception:
    HAVE_MATPLOTLIB = False


class ReportsService:
    def stream_expenses_csv(self, user_id, start_date=None, end_date=None):
        """Yield CSV lines for user's transactions between dates."""
        si = StringIO()
        writer = csv.writer(si)
        # header
        writer.writerow(['id', 'account_id', 'category', 'type', 'amount', 'description', 'transaction_date'])
        yield si.getvalue()
        si.seek(0)
        si.truncate(0)

        query = Transaction.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        for tx in query.order_by(Transaction.transaction_date.asc()).all():
            row = [
                tx.id,
                tx.account_id,
                tx.category.name if tx.category else None,
                tx.type,
                str(tx.amount),
                tx.description or '',
                tx.transaction_date.isoformat() if tx.transaction_date else ''
            ]
            writer.writerow(row)
            yield si.getvalue()
            si.seek(0)
            si.truncate(0)

    def get_summary(self, user_id, start_date=None, end_date=None):
        """Return a JSON-serializable summary of activity for the period."""
        query = Transaction.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        transactions = query.all()

        total_income = Decimal('0.00')
        total_expense = Decimal('0.00')
        by_category = {}

        for tx in transactions:
            amt = Decimal(tx.amount)
            if tx.type == 'income':
                total_income += amt
            else:
                total_expense += amt

            cat_name = tx.category.name if tx.category else 'Uncategorized'
            by_category.setdefault(cat_name, Decimal('0.00'))
            by_category[cat_name] += amt

        # budgets: sum active budgets per category overlapping the requested period
        budgets = {}
        b_list = Budget.query.filter_by(user_id=user_id, is_active=True).all()
        for b in b_list:
            # determine overlap: if budget has start/end date, check intersection with requested window
            if start_date and b.end_date and b.end_date < start_date:
                continue
            if end_date and b.start_date and b.start_date > end_date:
                continue

            # resolve category name safely (Budget has category_id)
            cat_name = 'Uncategorized'
            if getattr(b, 'category_id', None):
                from app.models import Category as _Category
                c = db.session.get(_Category, b.category_id)
                if c:
                    cat_name = c.name

            budgets.setdefault(cat_name, Decimal('0.00'))
            try:
                budgets[cat_name] += Decimal(b.limit_amount)
            except Exception:
                # fallback if limit_amount is already numeric
                budgets[cat_name] += Decimal(str(getattr(b, 'limit_amount', 0)))

        # Format results
        by_category_out = {k: float(v) for k, v in by_category.items()}
        budgets_out = {k: float(v) for k, v in budgets.items()}

        return {
            'user_id': user_id,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'by_category': by_category_out,
            'budgets': budgets_out,
        }

    def generate_summary_pdf(self, summary, user_id=None):
        """Generate a PDF bytes for the provided summary. Uses reportlab; optionally include charts via matplotlib."""
        if not HAVE_REPORTLAB:
            raise RuntimeError('reportlab is required to generate PDFs')

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elems = []

        title = Paragraph(f"Summary Report for User {user_id}", styles['Title'])
        elems.append(title)
        elems.append(Spacer(1, 12))

        meta = Paragraph(f"Period: {summary.get('start_date')} — {summary.get('end_date')}", styles['Normal'])
        elems.append(meta)
        elems.append(Spacer(1, 12))

        income_p = Paragraph(f"Total Income: {summary.get('total_income')}", styles['Normal'])
        expense_p = Paragraph(f"Total Expense: {summary.get('total_expense')}", styles['Normal'])
        elems.extend([income_p, expense_p, Spacer(1, 12)])

        # Add a simple category table or list
        elems.append(Paragraph('By Category:', styles['Heading2']))
        for cat, amt in summary.get('by_category', {}).items():
            elems.append(Paragraph(f"{cat}: {amt}", styles['Normal']))

        elems.append(Spacer(1, 12))

        # Generate a chart image if matplotlib is available
        if HAVE_MATPLOTLIB and summary.get('by_category'):
            try:
                fig, ax = plt.subplots(figsize=(6, 3))
                cats = list(summary['by_category'].keys())
                vals = list(summary['by_category'].values())
                ax.bar(cats, vals)
                ax.set_ylabel('Amount')
                ax.set_title('Spending by Category')
                plt.xticks(rotation=45, ha='right')
                imgbuf = BytesIO()
                plt.tight_layout()
                fig.savefig(imgbuf, format='png')
                plt.close(fig)
                imgbuf.seek(0)
                elems.append(Image(imgbuf, width=400, height=200))
            except Exception:
                pass

        doc.build(elems)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
