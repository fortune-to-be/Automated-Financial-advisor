"""Transaction service for CRUD operations and rule engine integration."""

import csv
import io
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from decimal import Decimal

from app.database import db
from app.models import Transaction, Account, User, Rule, AuditLog
from app.services.rule_engine import RuleEngine


class TransactionError(Exception):
    """Raised when transaction operations fail."""


class TransactionService:
    """Service for transaction CRUD operations with rule engine integration."""

    def __init__(self):
        self.rule_engine = RuleEngine()

    def create_transaction(
        self,
        user_id: int,
        account_id: int,
        amount: Decimal,
        type: str,
        description: str = "",
        transaction_date: datetime = None,
        category_id: int = None,
        tags: List[str] = None,
    ) -> Tuple[Dict[str, Any], List[int]]:
        """Create a transaction, apply rules, persist, and return (transaction, applied_rules)."""
        if not user_id or not account_id:
            raise TransactionError("user_id and account_id are required")

        account = Account.query.filter_by(id=account_id, user_id=user_id).first()
        if not account:
            raise TransactionError(f"Account {account_id} not found for user {user_id}")

        # Build a minimal tx dict for rule evaluation
        tx_for_engine = {
            "description": description,
            "amount": float(amount),
            "type": type,
            "transaction_date": transaction_date,
            "category_id": category_id,
            "is_recurring": False,
        }

        # Load user's active rules
        user_rules = (
            Rule.query.filter_by(user_id=user_id, is_active=True)
            .order_by(Rule.priority.desc())
            .all()
        )

        rules_list = [
            {
                "id": r.id,
                "name": r.name,
                "condition": r.condition,
                "action": r.action,
                "priority": r.priority,
                "is_active": r.is_active,
            }
            for r in user_rules
        ]

        modified_tx, rule_trace = self.rule_engine.evaluate_transaction(tx_for_engine, rules_list)

        applied_rules = [rt.get("rule_id") for rt in rule_trace if not rt.get("error")]
        rule_trace_str = [f"Rule '{rt.get('name')}' matched - {rt.get('explanation')}" for rt in rule_trace]

        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=modified_tx.get("category_id"),
            amount=amount,
            type=type,
            description=description,
            transaction_date=transaction_date,
            tags=tags or [],
        )

        db.session.add(transaction)
        db.session.flush()

        audit_log = AuditLog(
            user_id=user_id,
            action="create",
            resource_type="transaction",
            resource_id=transaction.id,
            new_values={
                "amount": float(amount),
                "type": type,
                "category_id": modified_tx.get("category_id"),
                "description": description,
                "applied_rules": applied_rules,
                "rule_trace": rule_trace_str,
            },
        )
        db.session.add(audit_log)
        db.session.commit()

        # Return transaction fields (datetime objects kept as-is for Marshmallow)
        return (
            {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "account_id": transaction.account_id,
                "category_id": transaction.category_id,
                "amount": float(transaction.amount),
                "type": transaction.type,
                "description": transaction.description,
                "transaction_date": transaction.transaction_date,
                "tags": transaction.tags or [],
                "applied_rules": applied_rules,
                "rule_trace": rule_trace_str,
                "created_at": transaction.created_at,
            },
            applied_rules,
        )

    def update_transaction(self, user_id: int, transaction_id: int, **kwargs) -> Tuple[Dict[str, Any], List[int]]:
        """Update a transaction, re-evaluate rules, persist, and return (transaction, applied_rules)."""
        transaction = (
            Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
        )
        if not transaction:
            raise TransactionError(f"Transaction {transaction_id} not found")

        # Keep a snapshot of old values for audit
        old_values = {
            "category_id": transaction.category_id,
            "description": transaction.description,
            "tags": transaction.tags,
            "amount": float(transaction.amount),
        }

        # Allowed updatable fields
        updatable = {"description", "transaction_date", "category_id", "tags", "amount", "type"}
        for k, v in kwargs.items():
            if k in updatable:
                setattr(transaction, k, v)

        # Re-evaluate rules
        tx_for_engine = {
            "description": transaction.description,
            "amount": float(transaction.amount),
            "type": transaction.type,
            "transaction_date": transaction.transaction_date,
            "category_id": transaction.category_id,
            "is_recurring": False,
        }

        user_rules = (
            Rule.query.filter_by(user_id=user_id, is_active=True)
            .order_by(Rule.priority.desc())
            .all()
        )

        rules_list = [
            {
                "id": r.id,
                "name": r.name,
                "condition": r.condition,
                "action": r.action,
                "priority": r.priority,
                "is_active": r.is_active,
            }
            for r in user_rules
        ]

        modified_tx, rule_trace = self.rule_engine.evaluate_transaction(tx_for_engine, rules_list)

        applied_rules = [rt.get("rule_id") for rt in rule_trace if not rt.get("error")]
        rule_trace_str = [f"Rule '{rt.get('name')}' matched - {rt.get('explanation')}" for rt in rule_trace]

        transaction.category_id = modified_tx.get("category_id")
        transaction.updated_at = datetime.now(timezone.utc)

        audit_log = AuditLog(
            user_id=user_id,
            action="update",
            resource_type="transaction",
            resource_id=transaction.id,
            old_values=old_values,
            new_values={
                "category_id": transaction.category_id,
                "description": transaction.description,
                "tags": transaction.tags,
                "applied_rules": applied_rules,
                "rule_trace": rule_trace_str,
            },
        )
        db.session.add(audit_log)
        db.session.commit()

        return (
            {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "account_id": transaction.account_id,
                "category_id": transaction.category_id,
                "amount": float(transaction.amount),
                "type": transaction.type,
                "description": transaction.description,
                "transaction_date": transaction.transaction_date,
                "tags": transaction.tags or [],
                "applied_rules": applied_rules,
                "rule_trace": rule_trace_str,
                "updated_at": transaction.updated_at,
            },
            applied_rules,
        )

    def get_transactions(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        start_date: datetime = None,
        end_date: datetime = None,
        category_id: int = None,
        account_id: int = None,
        include_rule_trace: bool = False,
    ) -> Dict[str, Any]:
        """Return paginated transactions for a user. Datetimes are returned as objects."""
        query = Transaction.query.filter_by(user_id=user_id)

        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        query = query.order_by(Transaction.transaction_date.desc())
        paginated = query.paginate(page=page, per_page=per_page)

        transactions = []
        for tx in paginated.items:
            tx_dict = {
                "id": tx.id,
                "user_id": tx.user_id,
                "account_id": tx.account_id,
                "category_id": tx.category_id,
                "amount": float(tx.amount),
                "type": tx.type,
                "description": tx.description,
                "transaction_date": tx.transaction_date,
                "tags": tx.tags or [],
                "created_at": tx.created_at,
                "updated_at": tx.updated_at,
            }

            if include_rule_trace:
                tx_dict["rule_trace"] = self._get_rule_trace(user_id, tx)

            transactions.append(tx_dict)

        return {
            "data": transactions,
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": per_page,
        }

    def get_transaction(self, user_id: int, transaction_id: int, include_rule_trace: bool = False) -> Dict[str, Any]:
        """Return a single transaction."""
        tx = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
        if not tx:
            raise TransactionError(f"Transaction {transaction_id} not found")

        tx_dict = {
            "id": tx.id,
            "user_id": tx.user_id,
            "account_id": tx.account_id,
            "category_id": tx.category_id,
            "amount": float(tx.amount),
            "type": tx.type,
            "description": tx.description,
            "transaction_date": tx.transaction_date,
            "tags": tx.tags or [],
            "created_at": tx.created_at,
            "updated_at": tx.updated_at,
        }

        if include_rule_trace:
            tx_dict["rule_trace"] = self._get_rule_trace(user_id, tx)

        return tx_dict

    def delete_transaction(self, user_id: int, transaction_id: int) -> None:
        """Delete a transaction and write an audit log."""
        tx = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
        if not tx:
            raise TransactionError(f"Transaction {transaction_id} not found")

        audit_log = AuditLog(
            user_id=user_id,
            action="delete",
            resource_type="transaction",
            resource_id=transaction_id,
            old_values={
                "amount": float(tx.amount),
                "type": tx.type,
                "description": tx.description,
            },
        )
        db.session.add(audit_log)
        db.session.delete(tx)
        db.session.commit()

    def _get_rule_trace(self, user_id: int, transaction: Transaction) -> List[str]:
        """Evaluate rules against a transaction and return human-readable trace lines."""
        tx_for_engine = {
            "description": transaction.description,
            "amount": float(transaction.amount),
            "type": transaction.type,
            "transaction_date": transaction.transaction_date,
            "category_id": transaction.category_id,
            "is_recurring": False,
        }

        user_rules = (
            Rule.query.filter_by(user_id=user_id, is_active=True)
            .order_by(Rule.priority.desc())
            .all()
        )

        rules_list = [
            {
                "id": r.id,
                "name": r.name,
                "condition": r.condition,
                "action": r.action,
                "priority": r.priority,
                "is_active": r.is_active,
            }
            for r in user_rules
        ]

        _, rule_trace = self.rule_engine.evaluate_transaction(tx_for_engine, rules_list)
        return [rt.get("explanation") for rt in rule_trace]


class TransactionImporter:
    """Service for importing transactions from CSV."""

    def __init__(self):
        self.transaction_service = TransactionService()
        self.rule_engine = RuleEngine()

    def preview_csv(self, user_id: int, csv_content: str, max_rows: int = 10) -> Dict[str, Any]:
        """Preview CSV rows with the rule engine applied (does not persist)."""
        user = db.session.get(User, user_id)
        if not user:
            raise TransactionError(f"User {user_id} not found")

        accounts = {acc.id: acc for acc in user.accounts}
        preview_rows = []
        warnings = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            if not reader.fieldnames:
                raise TransactionError("CSV is empty")

            required_fields = ["account_id", "amount", "type", "description", "transaction_date"]
            missing = [f for f in required_fields if f not in reader.fieldnames]
            if missing:
                raise TransactionError(f"Missing required fields: {', '.join(missing)}")

            for idx, row in enumerate(reader):
                if idx >= max_rows:
                    break

                try:
                    account_id = int(row.get("account_id", 0))
                    amount = Decimal(row.get("amount", 0))
                    tx_type = row.get("type", "").strip()
                    description = row.get("description", "").strip()
                    tx_date_str = row.get("transaction_date", "")

                    if account_id not in accounts:
                        warnings.append(f"Row {idx+1}: Account {account_id} not found, skipping")
                        continue

                    if tx_type not in ["income", "expense", "transfer"]:
                        warnings.append(f"Row {idx+1}: Invalid transaction type '{tx_type}'")
                        continue

                    try:
                        tx_date = datetime.fromisoformat(tx_date_str)
                    except Exception:
                        warnings.append(f"Row {idx+1}: Invalid date format '{tx_date_str}'")
                        continue

                    tx_for_engine = {
                        "description": description,
                        "amount": float(amount),
                        "type": tx_type,
                        "transaction_date": tx_date,
                        "category_id": None,
                        "is_recurring": False,
                    }

                    user_rules = (
                        Rule.query.filter_by(user_id=user_id, is_active=True)
                        .order_by(Rule.priority.desc())
                        .all()
                    )

                    rules_list = [
                        {
                            "id": r.id,
                            "name": r.name,
                            "condition": r.condition,
                            "action": r.action,
                            "priority": r.priority,
                            "is_active": r.is_active,
                        }
                        for r in user_rules
                    ]

                    modified_tx, engine_trace = self.rule_engine.evaluate_transaction(tx_for_engine, rules_list)
                    applied_rules = [t.get("rule_id") for t in engine_trace if not t.get("error")]
                    rule_trace = [f"Rule '{t.get('name')}' matched - {t.get('explanation')}" for t in engine_trace]

                    preview_rows.append(
                        {
                            "row_number": idx + 1,
                            "account_id": account_id,
                            "amount": float(amount),
                            "type": tx_type,
                            "description": description,
                            "transaction_date": tx_date,
                            "category_id": modified_tx.get("category_id"),
                            "applied_rules": applied_rules,
                            "rule_trace": rule_trace,
                        }
                    )

                except Exception as e:
                    warnings.append(f"Row {idx+1}: Error processing row: {str(e)}")

        except Exception as e:
            raise TransactionError(f"CSV parsing error: {str(e)}")

        return {"preview_rows": preview_rows, "total_rows_preview": len(preview_rows), "warnings": warnings}

    def commit_import(self, user_id: int, csv_content: str) -> Dict[str, Any]:
        """Persist transactions from CSV. Returns summary with errors."""
        user = db.session.get(User, user_id)
        if not user:
            raise TransactionError(f"User {user_id} not found")

        accounts = {acc.id: acc for acc in user.accounts}
        created = 0
        errors = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            if not reader.fieldnames:
                raise TransactionError("CSV is empty")

            required_fields = ["account_id", "amount", "type", "description", "transaction_date"]
            missing = [f for f in required_fields if f not in reader.fieldnames]
            if missing:
                raise TransactionError(f"Missing required fields: {', '.join(missing)}")

            for idx, row in enumerate(reader):
                try:
                    account_id = int(row.get("account_id", 0))
                    amount = Decimal(row.get("amount", 0))
                    tx_type = row.get("type", "").strip()
                    description = row.get("description", "").strip()
                    tx_date_str = row.get("transaction_date", "")

                    if account_id not in accounts:
                        errors.append(f"Row {idx+1}: Account {account_id} not found")
                        continue

                    if tx_type not in ["income", "expense", "transfer"]:
                        errors.append(f"Row {idx+1}: Invalid transaction type '{tx_type}'")
                        continue

                    try:
                        tx_date = datetime.fromisoformat(tx_date_str)
                    except Exception:
                        errors.append(f"Row {idx+1}: Invalid date format '{tx_date_str}'")
                        continue

                    self.transaction_service.create_transaction(
                        user_id=user_id,
                        account_id=account_id,
                        amount=amount,
                        type=tx_type,
                        description=description,
                        transaction_date=tx_date,
                    )
                    created += 1

                except Exception as e:
                    errors.append(f"Row {idx+1}: {str(e)}")

        except Exception as e:
            raise TransactionError(f"CSV processing error: {str(e)}")

        return {"created_count": created, "total_errors": len(errors), "errors": errors}
        
