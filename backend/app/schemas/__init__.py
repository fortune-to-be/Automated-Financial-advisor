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
    token_type = fields.Str(default='Bearer')
    expires_in = fields.Int()


class AccountSchema(Schema):
    """Account schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    account_type = fields.Str(required=True, validate=validate.OneOf(['checking', 'savings', 'credit_card', 'investment']))
    balance = fields.Decimal(places=2, dump_only=True)
    currency = fields.Str(default='USD')
    is_active = fields.Bool(default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CategorySchema(Schema):
    """Category schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, unique=True)
    description = fields.Str(allow_none=True)
    color = fields.Str(default='#000000')
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
    period = fields.Str(default='monthly', validate=validate.OneOf(['monthly', 'yearly', 'custom']))
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(allow_none=True)
    is_active = fields.Bool(default=True)
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
    priority = fields.Str(default='medium', validate=validate.OneOf(['low', 'medium', 'high']))
    is_active = fields.Bool(default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class RuleSchema(Schema):
    """Rule schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    condition = fields.Dict(required=True)
    action = fields.Dict(required=True)
    priority = fields.Int(default=0)
    is_active = fields.Bool(default=True)
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
    priority = fields.Int(default=0)
    is_active = fields.Bool(default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class RuleDetailSchema(Schema):
    """Rule schema - detailed view"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    condition = fields.Dict(required=True)
    action = fields.Dict(required=True)
    priority = fields.Int(default=0)
    is_active = fields.Bool(default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
