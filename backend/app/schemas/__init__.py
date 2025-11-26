from marshmallow import Schema, fields, validate, validates, ValidationError

class UserSchema(Schema):
    """User schema for serialization"""
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class RegisterSchema(Schema):
    """User registration schema"""
    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)


class LoginSchema(Schema):
    """User login schema"""
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class RefreshTokenSchema(Schema):
    """Refresh token schema"""
    refresh_token = fields.Str(required=True, load_only=True)


class TokenResponseSchema(Schema):
    """Token response schema"""
    access_token = fields.Str()
    refresh_token = fields.Str()
    token_type = fields.Str(dump_default='Bearer')
    expires_in = fields.Int()


class AccountSchema(Schema):
    """Account schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    account_type = fields.Str(required=True, validate=validate.OneOf(['checking', 'savings', 'credit_card', 'investment']))
    balance = fields.Decimal(places=2, dump_only=True)
    currency = fields.Str(dump_default='USD')
    is_active = fields.Bool(dump_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CategorySchema(Schema):
    """Category schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, metadata={"unique": True})
    description = fields.Str(allow_none=True)
    color = fields.Str(dump_default='#000000')
    icon = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class TransactionSchema(Schema):
    """Transaction schema"""
    id = fields.Int(dump_only=True)
    account_id = fields.Int(required=True)
    category_id = fields.Int(allow_none=True)
    amount = fields.Decimal(places=2, required=True)
    type = fields.Str(required=True, validate=validate.OneOf(['income', 'expense', 'transfer']))
    description = fields.Str(allow_none=True)
    transaction_date = fields.DateTime(required=True)
    tags = fields.List(fields.Str(), allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class BudgetSchema(Schema):
    """Budget schema"""
    id = fields.Int(dump_only=True)
    category_id = fields.Int(allow_none=True)
    limit_amount = fields.Decimal(places=2, required=True)
    period = fields.Str(dump_default='monthly', validate=validate.OneOf(['monthly', 'yearly', 'custom']))
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(allow_none=True)
    is_active = fields.Bool(dump_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class GoalSchema(Schema):
    """Goal schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    target_amount = fields.Decimal(places=2, required=True)
    current_amount = fields.Decimal(places=2, dump_only=True)
    target_date = fields.DateTime(required=True)
    category = fields.Str(allow_none=True)
    priority = fields.Str(dump_default='medium', validate=validate.OneOf(['low', 'medium', 'high']))
    is_active = fields.Bool(dump_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class RuleSchema(Schema):
    """Rule schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    condition = fields.Dict(required=True)
    action = fields.Dict(required=True)
    priority = fields.Int(dump_default=0)
    is_active = fields.Bool(dump_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AuditLogSchema(Schema):
    """Audit log schema"""
    id = fields.Int(dump_only=True)
    action = fields.Str()
    resource_type = fields.Str()
    resource_id = fields.Int(allow_none=True)
    old_values = fields.Dict(allow_none=True)
    new_values = fields.Dict(allow_none=True)
    ip_address = fields.Str(allow_none=True)
    user_agent = fields.Str(allow_none=True)
    created_at = fields.DateTime()


class RuleSchema(Schema):
    """Rule schema - list view"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    priority = fields.Int(dump_default=0)
    is_active = fields.Bool(dump_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class RuleDetailSchema(Schema):
    """Rule schema - detailed view"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    condition = fields.Dict(required=True)
    action = fields.Dict(required=True)
    priority = fields.Int(dump_default=0)
    is_active = fields.Bool(dump_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class BudgetRecommendationSchema(Schema):
    """Schema for budget recommendation responses"""
    user_id = fields.Int()
    recommended_budgets = fields.List(fields.Dict())
    monthly_income = fields.Decimal(places=2)
    debt_ratio = fields.Float()
    rule_trace = fields.List(fields.Str())
    generated_at = fields.DateTime()


class GoalScheduleSchema(Schema):
    """Schema for computed goal schedule"""
    goal_id = fields.Int()
    name = fields.Str()
    target_amount = fields.Decimal(places=2)
    current_amount = fields.Decimal(places=2)
    remaining_amount = fields.Decimal(places=2)
    months_remaining = fields.Int()
    monthly_required = fields.Decimal(places=2)
    is_feasible = fields.Bool()
    feasibility_reason = fields.Str()
    monthly_schedule = fields.List(fields.Dict())
    alternative_plans = fields.List(fields.Dict())
    rule_trace = fields.List(fields.Str())


class CashflowForecastSchema(Schema):
    """Schema for cashflow forecast responses"""
    user_id = fields.Int()
    forecast_months = fields.Int()
    starting_balance = fields.Decimal(places=2)
    monthly_forecasts = fields.List(fields.Dict())
    negative_balance_months = fields.List(fields.Int())
    warnings = fields.List(fields.Str())
    rule_trace = fields.List(fields.Str())


class PortfolioAllocationSchema(Schema):
    """Schema for portfolio allocation responses"""
    risk_profile = fields.Str()
    age = fields.Int()
    horizon = fields.Int()
    allocation = fields.Dict()
    explanation = fields.Str()
    expected_return = fields.Float()
    volatility = fields.Float()
    rule_trace = fields.List(fields.Str())


class TransactionCreateSchema(Schema):
    """Schema for creating a transaction"""
    account_id = fields.Int(required=True)
    amount = fields.Decimal(places=2, required=True)
    type = fields.Str(required=True, validate=validate.OneOf(['income', 'expense', 'transfer']))
    description = fields.Str(required=True)
    transaction_date = fields.DateTime(allow_none=True)
    category_id = fields.Int(allow_none=True)
    tags = fields.List(fields.Str(), allow_none=True)


class TransactionUpdateSchema(Schema):
    """Schema for updating a transaction"""
    description = fields.Str(allow_none=True)
    category_id = fields.Int(allow_none=True)
    tags = fields.List(fields.Str(), allow_none=True)
    transaction_date = fields.DateTime(allow_none=True)


class TransactionResponseSchema(Schema):
    """Schema for transaction responses"""
    id = fields.Int()
    user_id = fields.Int()
    account_id = fields.Int()
    category_id = fields.Int(allow_none=True)
    amount = fields.Decimal(places=2)
    type = fields.Str()
    description = fields.Str()
    transaction_date = fields.DateTime()
    tags = fields.List(fields.Str())
    applied_rules = fields.List(fields.Int())
    rule_trace = fields.List(fields.Str())
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class TransactionListSchema(Schema):
    """Schema for transaction list with pagination"""
    data = fields.List(fields.Nested(TransactionResponseSchema))
    total = fields.Int()
    pages = fields.Int()
    current_page = fields.Int()
    per_page = fields.Int()


class CSVImportPreviewSchema(Schema):
    """Schema for CSV import preview"""
    row_number = fields.Int()
    account_id = fields.Int()
    amount = fields.Decimal(places=2)
    type = fields.Str()
    description = fields.Str()
    transaction_date = fields.Str()
    category_id = fields.Int(allow_none=True)
    applied_rules = fields.List(fields.Int())
    rule_trace = fields.List(fields.Str())


class CSVImportPreviewResponseSchema(Schema):
    """Schema for CSV import preview response"""
    preview_rows = fields.List(fields.Nested(CSVImportPreviewSchema))
    total_rows_preview = fields.Int()
    warnings = fields.List(fields.Str())


class CSVImportCommitResponseSchema(Schema):
    """Schema for CSV import commit response"""
    created_count = fields.Int()
    total_errors = fields.Int()
    errors = fields.List(fields.Str())

