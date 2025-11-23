# Rule Engine Documentation

## Overview

The Financial Advisor Rule Engine is a flexible, JSON-based DSL (Domain Specific Language) that automates financial transaction processing. It enables administrators to define rules that automatically categorize transactions, tag them, recommend budget changes, and more.

## Architecture

### Components

1. **ConditionEvaluator**: Evaluates transaction conditions using a declarative JSON format
2. **ActionExecutor**: Applies actions to transactions based on matching rules
3. **RuleEngine**: Orchestrates condition evaluation and action execution with caching
4. **Admin Routes**: RESTful endpoints for rule CRUD operations and validation

### Rule Model

```python
class Rule(db.Model):
    id              : Primary Key
    user_id         : Foreign Key (User)
    name            : String (255) - Human-readable rule name
    description     : Text - Optional description
    condition       : JSON - Condition DSL
    action          : JSON - Action DSL
    priority        : Integer (0-1000) - Higher priority evaluated first
    is_active       : Boolean - Enable/disable without deletion
    created_at      : DateTime
    updated_at      : DateTime
```

## JSON DSL

### Condition Operators

#### 1. **merchant_contains**
Matches transactions where merchant name contains a substring (case-insensitive).

```json
{
    "operator": "merchant_contains",
    "value": "grocery"
}
```

#### 2. **merchant_regex**
Matches transactions where merchant name matches a regex pattern.

```json
{
    "operator": "merchant_regex",
    "value": "^(walmart|target|costco)$"
}
```

#### 3. **amount_gt** (Greater Than)
Matches transactions with amount strictly greater than value.

```json
{
    "operator": "amount_gt",
    "value": 100
}
```

#### 4. **amount_gte** (Greater Than or Equal)
Matches transactions with amount >= value.

```json
{
    "operator": "amount_gte",
    "value": 50
}
```

#### 5. **amount_lt** (Less Than)
Matches transactions with amount < value.

```json
{
    "operator": "amount_lt",
    "value": 25
}
```

#### 6. **amount_lte** (Less Than or Equal)
Matches transactions with amount <= value.

```json
{
    "operator": "amount_lte",
    "value": 100
}
```

#### 7. **amount_eq** (Equal)
Matches transactions with amount exactly equal to value.

```json
{
    "operator": "amount_eq",
    "value": 75
}
```

#### 8. **is_recurring**
Matches recurring transactions (where `is_recurring` flag is true).

```json
{
    "operator": "is_recurring",
    "value": true
}
```

#### 9. **date_range**
Matches transactions within a date range.

```json
{
    "operator": "date_range",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
}
```

#### 10. **category_id_eq**
Matches transactions with a specific category ID.

```json
{
    "operator": "category_id_eq",
    "value": 5
}
```

#### 11. **any** (Logical OR)
Matches if ANY sub-condition matches.

```json
{
    "operator": "any",
    "conditions": [
        {"operator": "merchant_contains", "value": "gas"},
        {"operator": "merchant_contains", "value": "fuel"}
    ]
}
```

#### 12. **all** (Logical AND)
Matches if ALL sub-conditions match.

```json
{
    "operator": "all",
    "conditions": [
        {"operator": "amount_gt", "value": 100},
        {"operator": "merchant_contains", "value": "travel"}
    ]
}
```

### Actions

#### 1. **set_category**
Automatically categorize the transaction.

```json
{
    "type": "set_category",
    "category_id": 3
}
```

#### 2. **set_tags**
Add tags to the transaction.

```json
{
    "type": "set_tags",
    "tags": ["business", "deductible"]
}
```

#### 3. **recommend_budget_change**
Recommend a budget adjustment.

```json
{
    "type": "recommend_budget_change",
    "category_id": 2,
    "recommended_amount": 500,
    "reason": "Based on recent spending pattern"
}
```

#### 4. **recommend_goal**
Recommend creating a financial goal.

```json
{
    "type": "recommend_goal",
    "name": "Vacation Fund",
    "target_amount": 2000,
    "reason": "Travel expenses detected"
}
```

#### 5. **stop_processing**
Stop evaluating remaining rules (exit early).

```json
{
    "type": "stop_processing"
}
```

## Example Rules

### Rule 1: Auto-categorize Grocery Purchases

```json
{
    "name": "Auto-Categorize Groceries",
    "description": "Automatically tag grocery store transactions",
    "condition": {
        "operator": "merchant_regex",
        "value": "(whole foods|trader joe|kroger|safeway)"
    },
    "action": {
        "type": "set_category",
        "category_id": 12
    },
    "priority": 10,
    "is_active": true
}
```

### Rule 2: Flag Large Expenses

```json
{
    "name": "Flag Large Expenses",
    "description": "Tag and recommend review for large expenses",
    "condition": {
        "operator": "amount_gt",
        "value": 500
    },
    "action": {
        "type": "set_tags",
        "tags": ["large_expense", "needs_review"]
    },
    "priority": 5,
    "is_active": true
}
```

### Rule 3: Complex Gas Station Rule

```json
{
    "name": "Smart Gas Station Detection",
    "description": "Detect gas stations and categorize appropriately",
    "condition": {
        "operator": "all",
        "conditions": [
            {"operator": "merchant_regex", "value": "(chevron|shell|bp|exxon|sunoco)"},
            {"operator": "amount_lte", "value": 150},
            {"operator": "amount_gt", "value": 10}
        ]
    },
    "action": {
        "type": "set_category",
        "category_id": 8
    },
    "priority": 15,
    "is_active": true
}
```

### Rule 4: Business Expense Detection

```json
{
    "name": "Business Meals",
    "description": "Flag potential business meal expenses",
    "condition": {
        "operator": "any",
        "conditions": [
            {"operator": "merchant_contains", "value": "restaurant"},
            {"operator": "merchant_contains", "value": "cafe"},
            {"operator": "merchant_regex", "value": ".*bistro.*"}
        ]
    },
    "action": {
        "type": "set_tags",
        "tags": ["business_meal", "deductible"]
    },
    "priority": 8,
    "is_active": true
}
```

## API Endpoints

### List Rules
```
GET /api/admin/rules
Authorization: Bearer <token>
Query Parameters:
  - page: int (default: 1)
  - per_page: int (default: 20)
  - is_active: bool (optional filter)
```

Response:
```json
{
    "data": [
        {
            "id": 1,
            "name": "Auto-Categorize Groceries",
            "priority": 10,
            "is_active": true,
            ...
        }
    ],
    "total": 42,
    "page": 1,
    "per_page": 20
}
```

### Get Single Rule
```
GET /api/admin/rules/<id>
Authorization: Bearer <token>
```

### Create Rule
```
POST /api/admin/rules
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Rule Name",
    "description": "Optional description",
    "condition": {...},
    "action": {...},
    "priority": 5,
    "is_active": true
}
```

### Update Rule
```
PUT /api/admin/rules/<id>
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Updated Name",
    "priority": 10,
    ...
}
```

### Delete Rule
```
DELETE /api/admin/rules/<id>
Authorization: Bearer <token>
```

### Toggle Rule Active Status
```
POST /api/admin/rules/<id>/toggle
Authorization: Bearer <token>
```

Response:
```json
{
    "id": 1,
    "name": "Rule Name",
    "is_active": false,
    ...
}
```

### Validate Rule
```
POST /api/admin/rules/validate
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Test Rule",
    "condition": {...},
    "action": {...}
}
```

Response:
```json
{
    "valid": true,
    "message": "Rule is valid"
}
```

Or on error:
```json
{
    "valid": false,
    "error": "Invalid regex pattern: [invalid("
}
```

## Execution Flow

### Rule Evaluation Process

1. **Authentication Check**: Verify user is admin
2. **Rule Loading**: Load all active rules for the user
3. **Priority Sorting**: Sort rules by priority (higher first)
4. **Condition Evaluation**: For each rule:
   - Evaluate condition against transaction
   - If condition matches → execute action
   - Check for stop_processing flag
   - If set → exit evaluation loop
5. **Result Generation**: Return modified transaction + audit trail

### Rule Trace

Each transaction returns a trace of applied rules:

```json
{
    "transaction": {...},
    "rule_trace": [
        {
            "rule_id": 1,
            "rule_name": "Auto-Categorize Groceries",
            "explanation": "Merchant 'Whole Foods' matched merchant_regex"
        },
        {
            "rule_id": 5,
            "rule_name": "Flag Large Expenses",
            "explanation": "Amount 125.50 matched amount_gt with threshold 100"
        }
    ]
}
```

## Validation

### Condition Validation

- **Unknown Operator**: Error with list of supported operators
- **Invalid Regex**: Error with regex syntax details
- **Missing Fields**: Error with required field names
- **Type Mismatch**: Error with expected vs. actual types
- **Invalid Date**: Error with date format requirements

### Action Validation

- **Unknown Action Type**: Error with list of supported actions
- **Missing Action Fields**: Error with required field names
- **Invalid Category/Goal ID**: Error if referenced resource doesn't exist
- **Invalid Tag Format**: Error with tag format requirements

## Performance Considerations

### Caching

Rules are cached in memory to avoid repeated database queries during transaction processing. Cache is automatically invalidated when:
- New rule created
- Rule updated
- Rule deleted
- Admin manually triggers invalidation

### Optimization Tips

1. **Priority Ordering**: Place frequently-matching rules at higher priority
2. **Condition Specificity**: Use specific conditions to reduce false positives
3. **Regex Complexity**: Simple regex patterns perform better than complex ones
4. **Use stop_processing**: Exit early if no more rules should apply

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|-----------|
| `Unknown operator` | Typo in operator name | Check operator name against list |
| `Invalid regex pattern` | Invalid regex syntax | Use regex tester tool |
| `Password cannot be longer than 72 bytes` | Bcrypt limitation | Keep passwords under 72 bytes |
| `NOT NULL constraint failed` | Missing required fields | Provide all required fields |
| `Unauthorized (403)` | User is not admin | Only admins can manage rules |

### Debugging

Enable detailed logging in Flask app:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

### Run Tests

```bash
# Rule engine tests only
python -m pytest test_rule_engine.py -v

# Admin endpoint tests only
python -m pytest test_admin_rules.py -v

# All tests
python -m pytest test_rule_engine.py test_admin_rules.py -v

# With environment variables
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///:memory:
python -m pytest test_rule_engine.py test_admin_rules.py -v
```

### Test Coverage

- **ConditionEvaluator**: 11 tests covering all operators and validation
- **ActionExecutor**: 6 tests covering all action types
- **RuleEngine**: 10 tests covering complete workflow
- **Admin Routes**: 18 tests covering all CRUD operations and role protection

**Total: 45+ tests**

## Future Enhancements

1. **More Operators**:
   - `location_contains`: Geographic-based rules
   - `payment_method`: Card type-based rules
   - `time_of_day`: Time-based rules
   - `day_of_week`: Weekday/weekend differentiation

2. **Advanced Actions**:
   - `send_notification`: Alert user via email/SMS
   - `auto_split`: Split transactions across categories
   - `schedule_payment`: Auto-pay detected bills

3. **Machine Learning**:
   - Learn rules from user behavior
   - Suggest optimal rule creation
   - Detect anomalies

4. **Rule Templates**:
   - Pre-built rule library
   - Community-shared rules
   - Industry-specific templates

5. **Rule Scheduling**:
   - Time-based activation
   - Temporary rules
   - Seasonal rules

## References

- See `app/services/rule_engine.py` for implementation
- See `app/routes/admin.py` for endpoint details
- See `test_rule_engine.py` and `test_admin_rules.py` for usage examples
