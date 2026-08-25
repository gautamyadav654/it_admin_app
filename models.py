from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

# Association tables for many-to-many relationships if needed
# For now, keeping it simple with foreign keys

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    designation = db.Column(db.String(50))
    email = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    location = db.Column(db.String(50))
    manager = db.Column(db.String(100))
    joining_date = db.Column(db.Date)
    assigned_asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Pending
    remarks = db.Column(db.Text)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    assigned_asset = db.relationship('Asset', foreign_keys=[assigned_asset_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

class Asset(db.Model):
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(20), unique=True, nullable=False)
    hostname = db.Column(db.String(50))
    asset_type = db.Column(db.String(20))  # Laptop, Desktop, Server, Monitor, Printer, Network Device
    manufacturer = db.Column(db.String(50))  # Dell, HP, Lenovo, Apple, Microsoft, Other
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(50))
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    employee_id = db.Column(db.String(20))  # Denormalized for easier display
    department = db.Column(db.String(50))
    location = db.Column(db.String(50))  # Mumbai, Delhi, Bangalore, etc.
    ip_address = db.Column(db.String(15))
    mac_address = db.Column(db.String(17))  # Format: 00:1A:2B:3C:4D:5E
    operating_system = db.Column(db.String(30))  # Windows 11, Windows 10, macOS, Ubuntu, Other
    ram = db.Column(db.String(20))  # 8GB, 16GB, etc.
    storage = db.Column(db.String(20))  # 256GB, 512GB, etc.
    processor = db.Column(db.String(50))  # Intel i5, Intel i7, AMD Ryzen 5, Apple M1
    purchase_date = db.Column(db.Date)
    warranty_start = db.Column(db.Date)
    warranty_end = db.Column(db.Date)
    amc_info = db.Column(db.String(50))  # AMC-XXXX
    asset_status = db.Column(db.String(20))  # Active, In Stock, Under Repair, Assigned, Returned, Retired, Lost
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    assigned_user = db.relationship('User', foreign_keys=[assigned_user_id])

class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    category = db.Column(db.String(20))  # Hardware, Software, Network, Access, Security, Other
    subcategory = db.Column(db.String(50))  # Installation, Repair, Upgrade, Configuration, Troubleshooting, Request
    priority = db.Column(db.String(10))  # Low, Medium, High, Critical
    issue = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    action_taken = db.Column(db.Text)
    resolution = db.Column(db.Text)
    status = db.Column(db.String(20))  # New, Open, In Progress, Pending, Resolved, Closed
    assigned_to = db.Column(db.String(50))  # Admin, Team Lead, Engineer
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    closed_date = db.Column(db.DateTime)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    asset = db.relationship('Asset', foreign_keys=[asset_id])

class Software(db.Model):
    __tablename__ = 'software'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20))
    license_key = db.Column(db.String(50))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20))  # Active, Inactive, Expired
    install_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])

class NetworkDevice(db.Model):
    __tablename__ = 'network'

    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(15))
    mac_address = db.Column(db.String(17))
    device_type = db.Column(db.String(20))  # Switch, Router, Access Point, Firewall, Modem
    location = db.Column(db.String(50))  # Mumbai, Delhi, Bangalore, etc.
    status = db.Column(db.String(20))  # Active, Inactive, Maintenance
    manufacturer = db.Column(db.String(50))  # Dell, HP, Cisco, Juniper, Other
    model = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MaintenanceRecord(db.Model):
    __tablename__ = 'maintenance'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    asset_name = db.Column(db.String(100))
    maintenance_type = db.Column(db.String(20))  # Preventive, Corrective, Urgent, Scheduled
    date = db.Column(db.Date, nullable=False)
    performed_by = db.Column(db.String(50))  # Admin, Tech Team, Vendor
    status = db.Column(db.String(20))  # Completed, In Progress, Scheduled, Cancelled
    description = db.Column(db.Text)
    cost = db.Column(db.String(20))  # Stored as string to handle currency symbols
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    asset = db.relationship('Asset', foreign_keys=[asset_id])

class ActivityLog(db.Model):
    __tablename__ = 'activity'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    action = db.Column(db.String(100), nullable=False)
    record_type = db.Column(db.String(20))  # Incident, User, Asset, etc.
    record_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    user = db.Column(db.String(50), default='Admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SwitchPort(db.Model):
    __tablename__ = 'switch_ports'

    id = db.Column(db.Integer, primary_key=True)
    switch_id = db.Column(db.Integer, db.ForeignKey('network.id'), nullable=False)
    port_number = db.Column(db.String(20), nullable=False)  # e.g., Gi1/0/1, Eth1/1
    port_name = db.Column(db.String(50))  # Description/label
    status = db.Column(db.String(20))  # Connected, Empty, Down, Error
    connected_device = db.Column(db.String(100))  # Device connected to this port
    connected_device_ip = db.Column(db.String(15))  # IP of connected device
    connected_device_mac = db.Column(db.String(17))  # MAC of connected device
    vlan = db.Column(db.String(20))  # VLAN assignment
    speed = db.Column(db.String(20))  # 1G, 10G, 100M, Auto
    duplex = db.Column(db.String(10))  # Full, Half, Auto
    poe = db.Column(db.Boolean, default=False)  # PoE enabled
    poe_power = db.Column(db.String(20))  # Power drawn (Watts)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    switch = db.relationship('NetworkDevice', foreign_keys=[switch_id], backref='ports')

    def __repr__(self):
        return f'<SwitchPort {self.port_number} on Switch {self.switch_id}>'

class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    admin_password = db.Column(db.String(100), default='admin123')
    # Add other settings as needed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)