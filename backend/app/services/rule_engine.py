"""Rule engine service for processing financial automation rules"""

import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from decimal import Decimal


class RuleValidationError(Exception):
    """Raised when rule validation fails"""
    pass


class RuleEvaluationError(Exception):
    """Raised when rule evaluation fails"""
    pass


class ConditionEvaluator:
    """Evaluates rule conditions against transactions"""
    
    SUPPORTED_OPERATORS = {
        'any', 'all', 'merchant_contains', 'merchant_regex',
        'amount_gt', 'amount_gte', 'amount_lt', 'amount_lte', 'amount_eq',
        'is_recurring', 'date_range', 'category_id_eq'
    }
    
    @staticmethod
    def validate_condition(condition: Dict[str, Any]) -> None:
        """Validate condition structure and syntax"""
        if not isinstance(condition, dict):
            raise RuleValidationError("Condition must be a dictionary")
        
        if 'operator' not in condition:
            raise RuleValidationError("Condition must have 'operator' field")
        
        operator = condition.get('operator')
        if operator not in ConditionEvaluator.SUPPORTED_OPERATORS:
            raise RuleValidationError(
                f"Unknown operator: {operator}. "
                f"Supported: {', '.join(ConditionEvaluator.SUPPORTED_OPERATORS)}"
            )
        
        # Validate operator-specific fields
        if operator in ['any', 'all']:
            if 'conditions' not in condition:
                raise RuleValidationError(f"'{operator}' operator requires 'conditions' array")
            if not isinstance(condition['conditions'], list):
                raise RuleValidationError(f"'{operator}' conditions must be a list")
            if len(condition['conditions']) == 0:
                raise RuleValidationError(f"'{operator}' conditions cannot be empty")
            
            # Recursively validate nested conditions
            for sub_condition in condition['conditions']:
                ConditionEvaluator.validate_condition(sub_condition)
        
        elif operator == 'merchant_contains':
            if 'value' not in condition:
                raise RuleValidationError("'merchant_contains' requires 'value' field")
            if not isinstance(condition['value'], str):
                raise RuleValidationError("'merchant_contains' value must be a string")
        
        elif operator == 'merchant_regex':
            if 'value' not in condition:
                raise RuleValidationError("'merchant_regex' requires 'value' field")
            if not isinstance(condition['value'], str):
                raise RuleValidationError("'merchant_regex' value must be a string")
            
            # Test regex compilation
            try:
                re.compile(condition['value'])
            except re.error as e:
                raise RuleValidationError(f"Invalid regex pattern: {str(e)}")
        
        elif operator.startswith('amount_'):
            if 'value' not in condition:
                raise RuleValidationError(f"'{operator}' requires 'value' field")
            try:
                float(condition['value'])
            except (ValueError, TypeError):
                raise RuleValidationError(f"'{operator}' value must be numeric")
        
        elif operator == 'is_recurring':
            if 'value' not in condition:
                raise RuleValidationError("'is_recurring' requires 'value' field")
            if not isinstance(condition['value'], bool):
                raise RuleValidationError("'is_recurring' value must be boolean")
        
        elif operator == 'date_range':
            if 'start' not in condition or 'end' not in condition:
                raise RuleValidationError("'date_range' requires 'start' and 'end' fields")
            
            for field in ['start', 'end']:
                try:
                    datetime.fromisoformat(condition[field])
                except (ValueError, TypeError):
                    raise RuleValidationError(f"'{field}' must be ISO format date/datetime")
        
        elif operator == 'category_id_eq':
            if 'value' not in condition:
                raise RuleValidationError("'category_id_eq' requires 'value' field")
            if not isinstance(condition['value'], int):
                raise RuleValidationError("'category_id_eq' value must be an integer")
    
    @staticmethod
    def evaluate(condition: Dict[str, Any], transaction: Dict[str, Any]) -> bool:
        """Evaluate a condition against a transaction"""
        operator = condition.get('operator')
        
        if operator == 'any':
            # At least one condition is true
            return any(
                ConditionEvaluator.evaluate(c, transaction)
                for c in condition.get('conditions', [])
            )
        
        elif operator == 'all':
            # All conditions are true
            return all(
                ConditionEvaluator.evaluate(c, transaction)
                for c in condition.get('conditions', [])
            )
        
        elif operator == 'merchant_contains':
            merchant = transaction.get('description', '').lower()
            value = condition.get('value', '').lower()
            return value in merchant
        
        elif operator == 'merchant_regex':
            merchant = transaction.get('description', '')
            pattern = condition.get('value', '')
            try:
                return bool(re.search(pattern, merchant, re.IGNORECASE))
            except re.error:
                return False
        
        elif operator == 'amount_gt':
            return Decimal(str(transaction.get('amount', 0))) > Decimal(str(condition.get('value', 0)))
        
        elif operator == 'amount_gte':
            return Decimal(str(transaction.get('amount', 0))) >= Decimal(str(condition.get('value', 0)))
        
        elif operator == 'amount_lt':
            return Decimal(str(transaction.get('amount', 0))) < Decimal(str(condition.get('value', 0)))
        
        elif operator == 'amount_lte':
            return Decimal(str(transaction.get('amount', 0))) <= Decimal(str(condition.get('value', 0)))
        
        elif operator == 'amount_eq':
            return Decimal(str(transaction.get('amount', 0))) == Decimal(str(condition.get('value', 0)))
        
        elif operator == 'is_recurring':
            expected = condition.get('value', False)
            actual = transaction.get('is_recurring', False)
            return actual == expected
        
        elif operator == 'date_range':
            tx_date = transaction.get('transaction_date')
            if isinstance(tx_date, str):
                tx_date = datetime.fromisoformat(tx_date)
            
            start = datetime.fromisoformat(condition.get('start', ''))
            end = datetime.fromisoformat(condition.get('end', ''))
            
            return start <= tx_date <= end
        
        elif operator == 'category_id_eq':
            return transaction.get('category_id') == condition.get('value')
        
        return False


class ActionExecutor:
    """Executes rule actions on transactions"""
    
    SUPPORTED_ACTIONS = {
        'set_category', 'set_tags', 'recommend_budget_change',
        'recommend_goal', 'stop_processing'
    }
    
    @staticmethod
    def validate_action(action: Dict[str, Any]) -> None:
        """Validate action structure and syntax"""
        if not isinstance(action, dict):
            raise RuleValidationError("Action must be a dictionary")
        
        if 'type' not in action:
            raise RuleValidationError("Action must have 'type' field")
        
        action_type = action.get('type')
        if action_type not in ActionExecutor.SUPPORTED_ACTIONS:
            raise RuleValidationError(
                f"Unknown action type: {action_type}. "
                f"Supported: {', '.join(ActionExecutor.SUPPORTED_ACTIONS)}"
            )
        
        # Validate action-specific fields
        if action_type == 'set_category':
            if 'category_id' not in action:
                raise RuleValidationError("'set_category' action requires 'category_id'")
            if not isinstance(action['category_id'], int):
                raise RuleValidationError("'set_category' category_id must be an integer")
        
        elif action_type == 'set_tags':
            if 'tags' not in action:
                raise RuleValidationError("'set_tags' action requires 'tags'")
            if not isinstance(action['tags'], list):
                raise RuleValidationError("'set_tags' tags must be a list")
            for tag in action['tags']:
                if not isinstance(tag, str):
                    raise RuleValidationError("Each tag must be a string")
        
        elif action_type == 'recommend_budget_change':
            if 'change_percent' not in action:
                raise RuleValidationError("'recommend_budget_change' requires 'change_percent'")
            try:
                float(action['change_percent'])
            except (ValueError, TypeError):
                raise RuleValidationError("'recommend_budget_change' change_percent must be numeric")
        
        elif action_type == 'recommend_goal':
            if 'goal_name' not in action or 'amount' not in action:
                raise RuleValidationError("'recommend_goal' requires 'goal_name' and 'amount'")
            if not isinstance(action['goal_name'], str):
                raise RuleValidationError("'recommend_goal' goal_name must be a string")
            try:
                float(action['amount'])
            except (ValueError, TypeError):
                raise RuleValidationError("'recommend_goal' amount must be numeric")
        
        elif action_type == 'stop_processing':
            # No additional validation needed
            pass
    
    @staticmethod
    def execute(action: Dict[str, Any], transaction: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Execute an action on a transaction.
        Returns (modified_transaction, explanation).
        """
        action_type = action.get('type')
        tx = transaction.copy()
        explanation = ""
        
        if action_type == 'set_category':
            category_id = action.get('category_id')
            tx['category_id'] = category_id
            explanation = f"Set category to {category_id}"
        
        elif action_type == 'set_tags':
            tags = action.get('tags', [])
            existing_tags = tx.get('tags', [])
            if isinstance(existing_tags, list):
                tx['tags'] = list(set(existing_tags + tags))
            else:
                tx['tags'] = tags
            explanation = f"Added tags: {', '.join(tags)}"
        
        elif action_type == 'recommend_budget_change':
            change_percent = float(action.get('change_percent', 0))
            explanation = f"Recommended budget change: {change_percent:+.1f}%"
        
        elif action_type == 'recommend_goal':
            goal_name = action.get('goal_name')
            amount = action.get('amount')
            explanation = f"Recommended goal '{goal_name}' with amount ${amount}"
        
        elif action_type == 'stop_processing':
            tx['_stop_processing'] = True
            explanation = "Stopped further rule processing"
        
        return tx, explanation


class RuleEngine:
    """Main rule engine for evaluating transactions against rules"""
    
    def __init__(self):
        self.rules_cache: Optional[List[Dict[str, Any]]] = None
    
    def validate_rule(self, rule_dict: Dict[str, Any]) -> None:
        """Validate a complete rule definition"""
        if not isinstance(rule_dict, dict):
            raise RuleValidationError("Rule must be a dictionary")
        
        # Check required fields
        required_fields = ['name', 'condition', 'action']
        for field in required_fields:
            if field not in rule_dict:
                raise RuleValidationError(f"Rule must have '{field}' field")
        
        # Validate condition
        ConditionEvaluator.validate_condition(rule_dict['condition'])
        
        # Validate action
        ActionExecutor.validate_action(rule_dict['action'])
        
        # Validate optional fields
        if 'priority' in rule_dict:
            try:
                int(rule_dict['priority'])
            except (ValueError, TypeError):
                raise RuleValidationError("'priority' must be an integer")
    
    def set_cache(self, rules: List[Dict[str, Any]]) -> None:
        """Set rules cache"""
        self.rules_cache = rules
    
    def invalidate_cache(self) -> None:
        """Invalidate rules cache"""
        self.rules_cache = None
    
    def evaluate_transaction(
        self,
        transaction: Dict[str, Any],
        rules: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Evaluate a transaction against a list of rules.
        
        Returns:
            (modified_transaction, rule_trace) where rule_trace is a list of
            {rule_id, name, explanation} for each rule that matched and was applied.
        """
        modified_tx = transaction.copy()
        rule_trace: List[Dict[str, Any]] = []
        
        # Sort rules by priority (higher first)
        sorted_rules = sorted(
            rules,
            key=lambda r: r.get('priority', 0),
            reverse=True
        )
        
        for rule in sorted_rules:
            # Skip inactive rules
            if not rule.get('is_active', True):
                continue
            
            try:
                # Check if condition matches
                if ConditionEvaluator.evaluate(rule['condition'], modified_tx):
                    # Execute action
                    modified_tx, explanation = ActionExecutor.execute(
                        rule['action'],
                        modified_tx
                    )
                    
                    # Record in trace
                    rule_trace.append({
                        'rule_id': rule.get('id'),
                        'name': rule.get('name'),
                        'explanation': explanation
                    })
                    
                    # Check for stop processing flag
                    if modified_tx.get('_stop_processing'):
                        modified_tx.pop('_stop_processing')
                        break
            
            except Exception as e:
                # Skip rules with evaluation errors
                rule_trace.append({
                    'rule_id': rule.get('id'),
                    'name': rule.get('name'),
                    'explanation': f"Error: {str(e)}",
                    'error': True
                })
        
        return modified_tx, rule_trace


def create_sample_transaction() -> Dict[str, Any]:
    """Create a sample transaction for testing"""
    return {
        'id': 999,
        'amount': Decimal('50.00'),
        'description': 'Trader Joe\'s Grocery Store',
        'transaction_date': datetime.now(),
        'category_id': None,
        'tags': [],
        'is_recurring': False,
        'account_id': 1
    }
