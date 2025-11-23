"""Tests for rule engine and admin endpoints"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.rule_engine import (
    ConditionEvaluator, ActionExecutor, RuleEngine,
    RuleValidationError, create_sample_transaction
)


class TestConditionEvaluator:
    """Test condition evaluation"""
    
    def test_validate_any_operator(self):
        """Test any operator validation"""
        # Valid
        condition = {
            'operator': 'any',
            'conditions': [
                {'operator': 'amount_gt', 'value': 100}
            ]
        }
        ConditionEvaluator.validate_condition(condition)
        
        # Invalid - missing conditions
        with pytest.raises(RuleValidationError, match="requires 'conditions'"):
            ConditionEvaluator.validate_condition({
                'operator': 'any'
            })
        
        # Invalid - empty conditions
        with pytest.raises(RuleValidationError, match="cannot be empty"):
            ConditionEvaluator.validate_condition({
                'operator': 'any',
                'conditions': []
            })
    
    def test_validate_merchant_contains(self):
        """Test merchant_contains validation"""
        # Valid
        condition = {
            'operator': 'merchant_contains',
            'value': 'grocery'
        }
        ConditionEvaluator.validate_condition(condition)
        
        # Invalid - missing value
        with pytest.raises(RuleValidationError, match="requires 'value'"):
            ConditionEvaluator.validate_condition({
                'operator': 'merchant_contains'
            })
    
    def test_validate_merchant_regex(self):
        """Test merchant_regex validation"""
        # Valid regex
        condition = {
            'operator': 'merchant_regex',
            'value': r'^Trader Joe.*'
        }
        ConditionEvaluator.validate_condition(condition)
        
        # Invalid regex
        with pytest.raises(RuleValidationError, match="Invalid regex"):
            ConditionEvaluator.validate_condition({
                'operator': 'merchant_regex',
                'value': '[invalid('
            })
    
    def test_validate_amount_operators(self):
        """Test amount operator validation"""
        for op in ['amount_gt', 'amount_gte', 'amount_lt', 'amount_lte', 'amount_eq']:
            # Valid
            condition = {'operator': op, 'value': 50.0}
            ConditionEvaluator.validate_condition(condition)
            
            # Invalid - non-numeric value
            with pytest.raises(RuleValidationError, match="must be numeric"):
                ConditionEvaluator.validate_condition({
                    'operator': op,
                    'value': 'not-a-number'
                })
    
    def test_validate_is_recurring(self):
        """Test is_recurring validation"""
        # Valid
        condition = {'operator': 'is_recurring', 'value': True}
        ConditionEvaluator.validate_condition(condition)
        
        # Invalid - non-boolean
        with pytest.raises(RuleValidationError, match="must be boolean"):
            ConditionEvaluator.validate_condition({
                'operator': 'is_recurring',
                'value': 'yes'
            })
    
    def test_validate_date_range(self):
        """Test date_range validation"""
        # Valid
        condition = {
            'operator': 'date_range',
            'start': '2025-01-01T00:00:00',
            'end': '2025-12-31T23:59:59'
        }
        ConditionEvaluator.validate_condition(condition)
        
        # Invalid - bad date format
        with pytest.raises(RuleValidationError, match="must be ISO format"):
            ConditionEvaluator.validate_condition({
                'operator': 'date_range',
                'start': '01/01/2025',
                'end': '12/31/2025'
            })
    
    def test_validate_unknown_operator(self):
        """Test unknown operator rejection"""
        with pytest.raises(RuleValidationError, match="Unknown operator"):
            ConditionEvaluator.validate_condition({
                'operator': 'unknown_op'
            })
    
    def test_evaluate_merchant_contains(self):
        """Test merchant_contains evaluation"""
        tx = {'description': 'Trader Joe\'s Grocery'}
        
        # Match
        condition = {'operator': 'merchant_contains', 'value': 'trader'}
        assert ConditionEvaluator.evaluate(condition, tx) is True
        
        # No match
        condition = {'operator': 'merchant_contains', 'value': 'walmart'}
        assert ConditionEvaluator.evaluate(condition, tx) is False
    
    def test_evaluate_amount_operators(self):
        """Test amount operator evaluation"""
        tx = {'amount': Decimal('100.00')}
        
        assert ConditionEvaluator.evaluate({'operator': 'amount_gt', 'value': 50}, tx) is True
        assert ConditionEvaluator.evaluate({'operator': 'amount_gt', 'value': 100}, tx) is False
        assert ConditionEvaluator.evaluate({'operator': 'amount_gte', 'value': 100}, tx) is True
        assert ConditionEvaluator.evaluate({'operator': 'amount_lt', 'value': 150}, tx) is True
        assert ConditionEvaluator.evaluate({'operator': 'amount_lte', 'value': 100}, tx) is True
        assert ConditionEvaluator.evaluate({'operator': 'amount_eq', 'value': 100}, tx) is True
    
    def test_evaluate_any_operator(self):
        """Test any operator evaluation"""
        tx = {'amount': Decimal('50.00'), 'description': 'Store'}
        
        # Any matches
        condition = {
            'operator': 'any',
            'conditions': [
                {'operator': 'amount_gt', 'value': 100},
                {'operator': 'merchant_contains', 'value': 'store'}
            ]
        }
        assert ConditionEvaluator.evaluate(condition, tx) is True
        
        # None match
        condition = {
            'operator': 'any',
            'conditions': [
                {'operator': 'amount_gt', 'value': 100},
                {'operator': 'merchant_contains', 'value': 'walmart'}
            ]
        }
        assert ConditionEvaluator.evaluate(condition, tx) is False
    
    def test_evaluate_all_operator(self):
        """Test all operator evaluation"""
        tx = {'amount': Decimal('50.00'), 'description': 'Store'}
        
        # All match
        condition = {
            'operator': 'all',
            'conditions': [
                {'operator': 'amount_lt', 'value': 100},
                {'operator': 'merchant_contains', 'value': 'store'}
            ]
        }
        assert ConditionEvaluator.evaluate(condition, tx) is True
        
        # Not all match
        condition = {
            'operator': 'all',
            'conditions': [
                {'operator': 'amount_gt', 'value': 100},
                {'operator': 'merchant_contains', 'value': 'store'}
            ]
        }
        assert ConditionEvaluator.evaluate(condition, tx) is False


class TestActionExecutor:
    """Test action execution"""
    
    def test_validate_set_category(self):
        """Test set_category validation"""
        # Valid
        action = {'type': 'set_category', 'category_id': 5}
        ActionExecutor.validate_action(action)
        
        # Missing category_id
        with pytest.raises(RuleValidationError, match="requires 'category_id'"):
            ActionExecutor.validate_action({'type': 'set_category'})
        
        # Non-integer category_id
        with pytest.raises(RuleValidationError, match="must be an integer"):
            ActionExecutor.validate_action({
                'type': 'set_category',
                'category_id': 'five'
            })
    
    def test_validate_set_tags(self):
        """Test set_tags validation"""
        # Valid
        action = {'type': 'set_tags', 'tags': ['tag1', 'tag2']}
        ActionExecutor.validate_action(action)
        
        # Non-list tags
        with pytest.raises(RuleValidationError, match="must be a list"):
            ActionExecutor.validate_action({
                'type': 'set_tags',
                'tags': 'tag1'
            })
        
        # Non-string tag
        with pytest.raises(RuleValidationError, match="Each tag must be a string"):
            ActionExecutor.validate_action({
                'type': 'set_tags',
                'tags': ['tag1', 123]
            })
    
    def test_validate_recommend_budget_change(self):
        """Test recommend_budget_change validation"""
        # Valid
        action = {'type': 'recommend_budget_change', 'change_percent': 10.5}
        ActionExecutor.validate_action(action)
        
        # Non-numeric change_percent
        with pytest.raises(RuleValidationError, match="must be numeric"):
            ActionExecutor.validate_action({
                'type': 'recommend_budget_change',
                'change_percent': 'ten'
            })
    
    def test_validate_recommend_goal(self):
        """Test recommend_goal validation"""
        # Valid
        action = {
            'type': 'recommend_goal',
            'goal_name': 'Emergency Fund',
            'amount': 5000
        }
        ActionExecutor.validate_action(action)
        
        # Missing fields
        with pytest.raises(RuleValidationError, match="requires 'goal_name'"):
            ActionExecutor.validate_action({
                'type': 'recommend_goal',
                'amount': 5000
            })
    
    def test_validate_unknown_action(self):
        """Test unknown action rejection"""
        with pytest.raises(RuleValidationError, match="Unknown action type"):
            ActionExecutor.validate_action({
                'type': 'unknown_action'
            })
    
    def test_execute_set_category(self):
        """Test set_category execution"""
        tx = {'category_id': None}
        action = {'type': 'set_category', 'category_id': 5}
        
        modified_tx, explanation = ActionExecutor.execute(action, tx)
        assert modified_tx['category_id'] == 5
        assert 'Set category to 5' in explanation
    
    def test_execute_set_tags(self):
        """Test set_tags execution"""
        tx = {'tags': ['existing']}
        action = {'type': 'set_tags', 'tags': ['new', 'tags']}
        
        modified_tx, explanation = ActionExecutor.execute(action, tx)
        assert 'new' in modified_tx['tags']
        assert 'tags' in modified_tx['tags']
        assert 'existing' in modified_tx['tags']
    
    def test_execute_stop_processing(self):
        """Test stop_processing execution"""
        tx = {}
        action = {'type': 'stop_processing'}
        
        modified_tx, explanation = ActionExecutor.execute(action, tx)
        assert modified_tx['_stop_processing'] is True
        assert 'Stopped' in explanation


class TestRuleEngine:
    """Test rule engine"""
    
    def test_validate_rule_complete(self):
        """Test complete rule validation"""
        rule = {
            'name': 'Test Rule',
            'condition': {
                'operator': 'merchant_contains',
                'value': 'grocery'
            },
            'action': {
                'type': 'set_category',
                'category_id': 5
            }
        }
        
        engine = RuleEngine()
        engine.validate_rule(rule)  # Should not raise
    
    def test_validate_rule_missing_fields(self):
        """Test rule validation with missing fields"""
        engine = RuleEngine()
        
        with pytest.raises(RuleValidationError, match="'name'"):
            engine.validate_rule({
                'condition': {},
                'action': {}
            })
    
    def test_evaluate_single_matching_rule(self):
        """Test evaluating transaction against matching rule"""
        engine = RuleEngine()
        
        rule = {
            'id': 1,
            'name': 'Grocery Rule',
            'condition': {
                'operator': 'merchant_contains',
                'value': 'trader'
            },
            'action': {
                'type': 'set_category',
                'category_id': 5
            },
            'is_active': True,
            'priority': 0
        }
        
        tx = {
            'description': 'Trader Joe\'s',
            'amount': Decimal('50.00'),
            'category_id': None
        }
        
        modified_tx, trace = engine.evaluate_transaction(tx, [rule])
        
        assert modified_tx['category_id'] == 5
        assert len(trace) == 1
        assert trace[0]['name'] == 'Grocery Rule'
    
    def test_evaluate_non_matching_rule(self):
        """Test evaluating transaction against non-matching rule"""
        engine = RuleEngine()
        
        rule = {
            'id': 1,
            'name': 'Grocery Rule',
            'condition': {
                'operator': 'merchant_contains',
                'value': 'trader'
            },
            'action': {
                'type': 'set_category',
                'category_id': 5
            },
            'is_active': True,
            'priority': 0
        }
        
        tx = {
            'description': 'Walmart',
            'amount': Decimal('50.00'),
            'category_id': None
        }
        
        modified_tx, trace = engine.evaluate_transaction(tx, [rule])
        
        assert modified_tx['category_id'] is None
        assert len(trace) == 0
    
    def test_evaluate_multiple_rules_priority(self):
        """Test rule priority ordering"""
        engine = RuleEngine()
        
        rules = [
            {
                'id': 1,
                'name': 'Low Priority',
                'condition': {'operator': 'amount_gt', 'value': 0},
                'action': {'type': 'set_tags', 'tags': ['low']},
                'is_active': True,
                'priority': 1
            },
            {
                'id': 2,
                'name': 'High Priority',
                'condition': {'operator': 'amount_gt', 'value': 0},
                'action': {'type': 'set_tags', 'tags': ['high']},
                'is_active': True,
                'priority': 10
            }
        ]
        
        tx = {'amount': Decimal('50.00'), 'tags': []}
        
        modified_tx, trace = engine.evaluate_transaction(tx, rules)
        
        # High priority should be applied first
        assert trace[0]['name'] == 'High Priority'
        assert trace[1]['name'] == 'Low Priority'
    
    def test_evaluate_stop_processing(self):
        """Test stop_processing flag"""
        engine = RuleEngine()
        
        rules = [
            {
                'id': 1,
                'name': 'Stop Rule',
                'condition': {'operator': 'amount_gt', 'value': 0},
                'action': {'type': 'stop_processing'},
                'is_active': True,
                'priority': 10
            },
            {
                'id': 2,
                'name': 'Second Rule',
                'condition': {'operator': 'amount_gt', 'value': 0},
                'action': {'type': 'set_tags', 'tags': ['should-not-apply']},
                'is_active': True,
                'priority': 1
            }
        ]
        
        tx = {'amount': Decimal('50.00'), 'tags': []}
        
        modified_tx, trace = engine.evaluate_transaction(tx, rules)
        
        # Only first rule should be in trace
        assert len(trace) == 1
        assert trace[0]['name'] == 'Stop Rule'
        assert '_stop_processing' not in modified_tx
    
    def test_evaluate_inactive_rule(self):
        """Test that inactive rules are skipped"""
        engine = RuleEngine()
        
        rule = {
            'id': 1,
            'name': 'Inactive Rule',
            'condition': {'operator': 'amount_gt', 'value': 0},
            'action': {'type': 'set_tags', 'tags': ['inactive']},
            'is_active': False,
            'priority': 0
        }
        
        tx = {'amount': Decimal('50.00'), 'tags': []}
        
        modified_tx, trace = engine.evaluate_transaction(tx, [rule])
        
        assert len(trace) == 0
        assert 'inactive' not in modified_tx.get('tags', [])
    
    def test_cache_operations(self):
        """Test cache set and invalidate"""
        engine = RuleEngine()
        
        rules = [{'id': 1, 'name': 'Rule'}]
        
        assert engine.rules_cache is None
        
        engine.set_cache(rules)
        assert engine.rules_cache is not None
        
        engine.invalidate_cache()
        assert engine.rules_cache is None
