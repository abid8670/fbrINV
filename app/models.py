from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Roles: admin, manager, operator, viewer
    role = db.Column(db.String(20), default='operator')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Granular Permissions
    can_manage_invoices = db.Column(db.Boolean, default=True)
    can_submit_fbr = db.Column(db.Boolean, default=True)
    can_manage_items = db.Column(db.Boolean, default=True)
    can_manage_customers = db.Column(db.Boolean, default=True)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_edit_settings = db.Column(db.Boolean, default=False)
    can_export_data = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_perm(self, perm_name):
        """Checks if user has a specific granular permission."""
        if not self.is_active:
            return False
        if self.role == 'admin':
            return True
        if self.role == 'viewer':
            # Viewer has read-only access
            return perm_name in ['can_export_data', 'can_view']
        return bool(getattr(self, perm_name, False))

    def apply_role_preset(self, role_name):
        """Sets default permission flags based on selected role."""
        self.role = role_name
        if role_name == 'admin':
            self.can_manage_invoices = True
            self.can_submit_fbr = True
            self.can_manage_items = True
            self.can_manage_customers = True
            self.can_manage_users = True
            self.can_edit_settings = True
            self.can_export_data = True
        elif role_name == 'manager':
            self.can_manage_invoices = True
            self.can_submit_fbr = True
            self.can_manage_items = True
            self.can_manage_customers = True
            self.can_manage_users = False
            self.can_edit_settings = False
            self.can_export_data = True
        elif role_name == 'operator':
            self.can_manage_invoices = True
            self.can_submit_fbr = True
            self.can_manage_items = True
            self.can_manage_customers = True
            self.can_manage_users = False
            self.can_edit_settings = False
            self.can_export_data = False
        elif role_name == 'viewer':
            self.can_manage_invoices = False
            self.can_submit_fbr = False
            self.can_manage_items = False
            self.can_manage_customers = False
            self.can_manage_users = False
            self.can_edit_settings = False
            self.can_export_data = True

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activities', lazy=True)


class CompanySetting(db.Model):
    __tablename__ = 'company_settings'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False, default="My Business (Pvt) Ltd")
    ntn = db.Column(db.String(20), nullable=False, default="1234567-8")
    strn = db.Column(db.String(20), nullable=False, default="1234567890123")
    business_address = db.Column(db.String(255), default="Suite 101, Business Avenue, Main Boulevard, Lahore")
    city = db.Column(db.String(50), default="Lahore")
    province = db.Column(db.String(50), default="Punjab")
    phone = db.Column(db.String(50), default="+92 42 31234567")
    email = db.Column(db.String(100), default="info@mybusiness.com.pk")
    pos_id = db.Column(db.String(50), default="POS-001")
    branch_code = db.Column(db.String(50), default="BR-01")
    
    # FBR Digital Invoicing Configuration
    fbr_environment = db.Column(db.String(20), default="mock")  # mock, sandbox, production
    fbr_api_url = db.Column(db.String(255), default="https://staging-di.pral.com.pk/api/v1/di/postinvoicedata")
    fbr_bearer_token = db.Column(db.Text, default="")
    fbr_token_valid_until = db.Column(db.String(50), default="2031-12-31")
    default_tax_rate = db.Column(db.Float, default=18.0)
    default_further_tax_rate = db.Column(db.Float, default=4.0)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_settings(cls):
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    buyer_type = db.Column(db.String(20), default='Registered')  # Registered, Unregistered
    ntn = db.Column(db.String(20), default='')
    cnic = db.Column(db.String(20), default='')
    strn = db.Column(db.String(20), default='')
    address = db.Column(db.String(255), default='')
    city = db.Column(db.String(50), default='')
    province = db.Column(db.String(50), default='Punjab')
    phone = db.Column(db.String(50), default='')
    email = db.Column(db.String(100), default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    hs_code = db.Column(db.String(20), nullable=False, default='8471.3010')  # Pakistan Customs HS Code
    uom = db.Column(db.String(20), nullable=False, default='NOS')  # NOS, KG, LTR, MTR, etc.
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    sales_tax_rate = db.Column(db.Float, default=18.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Item {self.item_code} - {self.name}>'


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    invoice_type = db.Column(db.String(30), default='Sales Invoice')  # Sales Invoice, Debit Note, Credit Note
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Status: Draft, FBR_Submitted, Failed, Cancelled
    status = db.Column(db.String(30), default='Draft')
    
    # Financial Totals
    total_value_of_supply = db.Column(db.Float, default=0.0)
    total_sales_tax = db.Column(db.Float, default=0.0)
    total_further_tax = db.Column(db.Float, default=0.0)
    total_extra_tax = db.Column(db.Float, default=0.0)
    total_discount = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, default=0.0)
    
    payment_mode = db.Column(db.String(30), default='Cash')
    remarks = db.Column(db.Text, default='')

    # Credit Note / Debit Note Referencing
    original_fbr_invoice_number = db.Column(db.String(100), default='')
    original_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    reason_for_issuance = db.Column(db.String(255), default='')

    # FBR Integration specifics
    fbr_invoice_number = db.Column(db.String(100), default='')
    fbr_status_code = db.Column(db.String(20), default='')
    fbr_response_message = db.Column(db.Text, default='')
    fbr_qr_code_data = db.Column(db.Text, default='')
    fbr_qr_image_base64 = db.Column(db.Text, default='')
    fbr_submitted_at = db.Column(db.DateTime, nullable=True)
    fbr_request_payload = db.Column(db.Text, default='')
    fbr_response_payload = db.Column(db.Text, default='')

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', backref='invoices')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan', lazy=True)
    credit_notes = db.relationship('Invoice', backref=db.backref('original_invoice', remote_side=[id]), lazy=True)

    def calculate_totals(self):
        self.total_value_of_supply = sum(item.value_of_supply for item in self.items)
        self.total_sales_tax = sum(item.sales_tax_amount for item in self.items)
        self.total_further_tax = sum(item.further_tax_amount for item in self.items)
        self.total_discount = sum(item.discount_amount for item in self.items)
        self.grand_total = round(self.total_value_of_supply + self.total_sales_tax + self.total_further_tax + self.total_extra_tax - self.total_discount, 2)


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)
    
    item_code = db.Column(db.String(50), default='')
    description = db.Column(db.String(255), nullable=False)
    hs_code = db.Column(db.String(20), nullable=False)
    uom = db.Column(db.String(20), default='NOS')
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, default=0.0)
    value_of_supply = db.Column(db.Float, default=0.0)
    
    sales_tax_rate = db.Column(db.Float, default=18.0)
    sales_tax_amount = db.Column(db.Float, default=0.0)
    further_tax_rate = db.Column(db.Float, default=0.0)
    further_tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)

    item = db.relationship('Item', backref='invoice_items')
