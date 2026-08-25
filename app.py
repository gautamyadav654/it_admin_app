from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Asset, Incident, Software, NetworkDevice, MaintenanceRecord, ActivityLog, Settings, SwitchPort
from database import init_app
from datetime import datetime
import json
import os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///it_admin.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Handle PostgreSQL URL format for Vercel/Neon/Supabase
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

    # Add datetime to template globals
    from datetime import datetime
    app.jinja_env.globals['datetime'] = datetime

    # Initialize database
    db = init_app(app)

    # Create tables
    with app.app_context():
        db.create_all()

        # Create default settings if not exists
        if not Settings.query.first():
            default_settings = Settings(password='admin123')
            db.session.add(default_settings)
            db.session.commit()

    # Helper function to log activity
    def log_activity(action, record_type, record_id=None, details=''):
        activity = ActivityLog(
            action=action,
            record_type=record_type,
            record_id=record_id,
            details=details,
            user=current_user.name if current_user.is_authenticated else 'Admin'
        )
        db.session.add(activity)
        db.session.commit()

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create default admin user
    with app.app_context():
        db.create_all()

        # Create default settings if not exists
        if not Settings.query.first():
            default_settings = Settings(password='admin123')
            db.session.add(default_settings)
            db.session.commit()

        # Create default admin user
        admin_user = User.query.filter_by(employee_id='ADMIN').first()
        if not admin_user:
            admin_user = User(
                employee_id='ADMIN',
                name='Admin',
                email='admin@company.com',
                department='IT',
                designation='System Administrator',
                status='Active',
                is_admin=True
            )
            admin_user.set_password('Admin@123')
            db.session.add(admin_user)
            db.session.commit()

    # Routes

    # Protect all routes except login, logout, static
    @app.before_request
    def require_login():
        allowed_routes = ['login', 'logout', 'static']
        if request.endpoint and request.endpoint not in allowed_routes:
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))

    @app.route('/')
    def index():
        # Dashboard stats
        stats = {
            'users': User.query.count(),
            'assets': Asset.query.count(),
            'open_incidents': Incident.query.filter(Incident.status.notin_(['Closed', 'Resolved'])).count(),
            'pending_requests': Incident.query.filter(Incident.status.in_(['Pending', 'New'])).count(),
            'closed_incidents': Incident.query.filter(Incident.status.in_(['Closed', 'Resolved'])).count(),
            'warranty': Asset.query.filter(Asset.warranty_end > datetime.now().date()).count() if Asset.query.first() else 0
        }

        # Recent activity
        recent_activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(8).all()

        # Recent records (mixed)
        recent_incidents = Incident.query.order_by(Incident.created_date.desc()).limit(3).all()
        recent_users = User.query.order_by(User.created_at.desc()).limit(3).all()
        recent_assets = Asset.query.order_by(Asset.created_at.desc()).limit(3).all()

        # Combine and sort by date
        recent_records = []
        for inc in recent_incidents:
            recent_records.append({
                'type': 'Incident',
                'title': inc.ticket_number,
                'date': inc.created_date.strftime('%Y-%m-%d') if inc.created_date else '',
                'status': inc.status
            })
        for user in recent_users:
            recent_records.append({
                'type': 'User',
                'title': user.name,
                'date': user.joining_date.strftime('%Y-%m-%d') if user.joining_date else '',
                'status': user.status
            })
        for asset in recent_assets:
            recent_records.append({
                'type': 'Asset',
                'title': f"{asset.asset_id} ({asset.hostname})",
                'date': asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else '',
                'status': asset.asset_status
            })

        recent_records.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)
        recent_records = recent_records[:8]

        # Chart data for incidents (last 12 months)
        from sqlalchemy import extract
        incident_chart_data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'data': [0] * 12
        }

        current_year = datetime.now().year
        for i in range(12):
            month = i + 1
            count = Incident.query.filter(
                extract('month', Incident.date) == month,
                extract('year', Incident.date) == current_year
            ).count()
            incident_chart_data['data'][i] = count

        return render_template('dashboard.html',
                             stats=stats,
                             recent_activity=recent_activity,
                             recent_records=recent_records,
                             incident_chart_data=incident_chart_data)

    # Users routes
    @app.route('/users')
    def users():
        search = request.args.get('search', '')
        dept_filter = request.args.get('dept', '')

        query = User.query

        if search:
            query = query.filter(
                db.or_(
                    User.name.contains(search),
                    User.employee_id.contains(search),
                    User.email.contains(search)
                )
            )

        if dept_filter:
            query = query.filter(User.department == dept_filter)

        users_list = query.all()

        # Get unique departments for filter dropdown
        departments = db.session.query(User.department.distinct()).filter(User.department.isnot(None)).all()
        departments = [d[0] for d in departments if d[0]]

        return render_template('users.html', users=users_list, search=search, dept_filter=dept_filter, departments=departments)

    @app.route('/users/add', methods=['GET', 'POST'])
    def add_user():
        if request.method == 'POST':
            # Get form data
            employee_id = request.form.get('employee_id')
            name = request.form.get('name')
            department = request.form.get('department')
            designation = request.form.get('designation')
            email = request.form.get('email')
            contact = request.form.get('contact')
            location = request.form.get('location')
            manager = request.form.get('manager')
            joining_date = request.form.get('joining_date')
            status = request.form.get('status')
            remarks = request.form.get('remarks')

            # Validate required fields
            if not employee_id or not name:
                flash('Employee ID and Name are required!', 'error')
                return redirect(url_for('add_user'))

            # Check if employee_id already exists
            if User.query.filter_by(employee_id=employee_id).first():
                flash('Employee ID already exists!', 'error')
                return redirect(url_for('add_user'))

            # Create new user
            user = User(
                employee_id=employee_id,
                name=name,
                department=department if department else None,
                designation=designation if designation else None,
                email=email if email else None,
                contact=contact if contact else None,
                location=location if location else None,
                manager=manager if manager else None,
                joining_date=datetime.strptime(joining_date, '%Y-%m-%d').date() if joining_date else None,
                status=status if status else 'Active',
                remarks=remarks if remarks else None
            )

            db.session.add(user)
            db.session.commit()

            # Log activity
            log_activity('Added user', 'User', user.id, f'User {name} added')

            flash('User added successfully!', 'success')
            return redirect(url_for('users'))

        # GET request - show form
        # Get unique values for dropdowns from existing data
        departments = db.session.query(User.department.distinct()).filter(User.department.isnot(None)).all()
        departments = [d[0] for d in departments if d[0]]

        locations = db.session.query(User.location.distinct()).filter(User.location.isnot(None)).all()
        locations = [l[0] for l in locations if l[0]]

        designations = db.session.query(User.designation.distinct()).filter(User.designation.isnot(None)).all()
        designations = [d[0] for d in designations if d[0]]

        return render_template('add_user.html',
                             departments=departments or ['IT', 'HR', 'Finance', 'Marketing', 'Sales', 'Operations', 'R&D'],
                             locations=locations or ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune'],
                             designations=designations or ['Engineer', 'Analyst', 'Manager', 'Executive', 'Specialist', 'Lead'])

    @app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
    def edit_user(id):
        user = User.query.get_or_404(id)

        if request.method == 'POST':
            # Update user fields
            user.employee_id = request.form.get('employee_id')
            user.name = request.form.get('name')
            user.department = request.form.get('department') if request.form.get('department') else None
            user.designation = request.form.get('designation') if request.form.get('designation') else None
            user.email = request.form.get('email') if request.form.get('email') else None
            user.contact = request.form.get('contact') if request.form.get('contact') else None
            user.location = request.form.get('location') if request.form.get('location') else None
            user.manager = request.form.get('manager') if request.form.get('manager') else None
            joining_date = request.form.get('joining_date')
            user.joining_date = datetime.strptime(joining_date, '%Y-%m-%d').date() if joining_date else None
            user.status = request.form.get('status') if request.form.get('status') else 'Active'
            user.remarks = request.form.get('remarks') if request.form.get('remarks') else None

            db.session.commit()

            # Log activity
            log_activity('Updated user', 'User', user.id, f'User {user.name} updated')

            flash('User updated successfully!', 'success')
            return redirect(url_for('users'))

        # GET request - show form with current data
        # Get unique values for dropdowns
        departments = db.session.query(User.department.distinct()).filter(User.department.isnot(None)).all()
        departments = [d[0] for d in departments if d[0]]

        locations = db.session.query(User.location.distinct()).filter(User.location.isnot(None)).all()
        locations = [l[0] for l in locations if l[0]]

        designations = db.session.query(User.designation.distinct()).filter(User.designation.isnot(None)).all()
        designations = [d[0] for d in designations if d[0]]

        return render_template('edit_user.html',
                             user=user,
                             departments=departments or ['IT', 'HR', 'Finance', 'Marketing', 'Sales', 'Operations', 'R&D'],
                             locations=locations or ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune'],
                             designations=designations or ['Engineer', 'Analyst', 'Manager', 'Executive', 'Specialist', 'Lead'])

    @app.route('/users/delete/<int:id>')
    def delete_user(id):
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()

        # Log activity
        log_activity('Deleted user', 'User', id, f'User {user.name} deleted')

        flash('User deleted successfully!', 'success')
        return redirect(url_for('users'))

    # Assets routes
    @app.route('/assets')
    def assets():
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')

        query = Asset.query

        if search:
            query = query.filter(
                db.or_(
                    Asset.asset_id.contains(search),
                    Asset.hostname.contains(search),
                    Asset.model.contains(search),
                    Asset.assigned_user.contains(search)
                )
            )

        if status_filter:
            query = query.filter(Asset.asset_status == status_filter)

        assets_list = query.all()

        # Get unique statuses for filter dropdown
        statuses = db.session.query(Asset.asset_status.distinct()).filter(Asset.asset_status.isnot(None)).all()
        statuses = [s[0] for s in statuses if s[0]]

        return render_template('assets.html', assets=assets_list, search=search, status_filter=status_filter, statuses=statuses)

    @app.route('/assets/add', methods=['GET', 'POST'])
    def add_asset():
        if request.method == 'POST':
            # Get form data
            asset_id = request.form.get('asset_id')
            hostname = request.form.get('hostname')
            asset_type = request.form.get('asset_type')
            manufacturer = request.form.get('manufacturer')
            model = request.form.get('model')
            serial_number = request.form.get('serial_number')
            assigned_user = request.form.get('assigned_user')
            employee_id = request.form.get('employee_id')
            department = request.form.get('department')
            location = request.form.get('location')
            ip_address = request.form.get('ip_address')
            mac_address = request.form.get('mac_address')
            operating_system = request.form.get('operating_system')
            ram = request.form.get('ram')
            storage = request.form.get('storage')
            processor = request.form.get('processor')
            purchase_date = request.form.get('purchase_date')
            warranty_start = request.form.get('warranty_start')
            warranty_end = request.form.get('warranty_end')
            amc_info = request.form.get('amc_info')
            asset_status = request.form.get('asset_status')
            remarks = request.form.get('remarks')

            # Validate required fields
            if not asset_id or not hostname:
                flash('Asset ID and Hostname are required!', 'error')
                return redirect(url_for('add_asset'))

            # Check if asset_id already exists
            if Asset.query.filter_by(asset_id=asset_id).first():
                flash('Asset ID already exists!', 'error')
                return redirect(url_for('add_asset'))

            # Create new asset
            asset = Asset(
                asset_id=asset_id,
                hostname=hostname,
                asset_type=asset_type if asset_type else None,
                manufacturer=manufacturer if manufacturer else None,
                model=model if model else None,
                serial_number=serial_number if serial_number else None,
                assigned_user=assigned_user if assigned_user else None,
                employee_id=employee_id if employee_id else None,
                department=department if department else None,
                location=location if location else None,
                ip_address=ip_address if ip_address else None,
                mac_address=mac_address if mac_address else None,
                operating_system=operating_system if operating_system else None,
                ram=ram if ram else None,
                storage=storage if storage else None,
                processor=processor if processor else None,
                purchase_date=datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None,
                warranty_start=datetime.strptime(warranty_start, '%Y-%m-%d').date() if warranty_start else None,
                warranty_end=datetime.strptime(warranty_end, '%Y-%m-%d').date() if warranty_end else None,
                amc_info=amc_info if amc_info else None,
                asset_status=asset_status if asset_status else 'In Stock',
                remarks=remarks if remarks else None
            )

            db.session.add(asset)
            db.session.commit()

            # Log activity
            log_activity('Added asset', 'Asset', asset.id, f'Asset {asset_id} added')

            flash('Asset added successfully!', 'success')
            return redirect(url_for('assets'))

        # GET request - show form
        # Get unique values for dropdowns from existing data
        asset_types = ['Laptop', 'Desktop', 'Server', 'Monitor', 'Printer', 'Network Device']
        manufacturers = ['Dell', 'HP', 'Lenovo', 'Apple', 'Microsoft', 'Other']
        operating_systems = ['Windows 11', 'Windows 10', 'macOS', 'Ubuntu', 'Other']
        departments = db.session.query(User.department.distinct()).filter(User.department.isnot(None)).all()
        departments = [d[0] for d in departments if d[0]]
        locations = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune']
        asset_statuses = ['Active', 'In Stock', 'Under Repair', 'Assigned', 'Returned', 'Retired', 'Lost']

        # Get users for assigned user dropdown
        users = User.query.all()

        return render_template('add_asset.html',
                             asset_types=asset_types,
                             manufacturers=manufacturers,
                             operating_systems=operating_systems,
                             departments=departments or ['IT', 'HR', 'Finance', 'Marketing', 'Sales', 'Operations', 'R&D'],
                             locations=locations,
                             asset_statuses=asset_statuses,
                             users=users)

    # Incidents routes
    @app.route('/incidents')
    def incidents():
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')

        query = Incident.query

        if search:
            query = query.filter(
                db.or_(
                    Incident.ticket_number.contains(search),
                    Incident.user.contains(search),
                    Incident.issue.contains(search)
                )
            )

        if status_filter:
            query = query.filter(Incident.status == status_filter)

        if priority_filter:
            query = query.filter(Incident.priority == priority_filter)

        incidents_list = query.order_by(Incident.created_date.desc()).all()

        # Get unique statuses and priorities for filter dropdowns
        statuses = db.session.query(Incident.status.distinct()).filter(Incident.status.isnot(None)).all()
        statuses = [s[0] for s in statuses if s[0]]

        priorities = db.session.query(Incident.priority.distinct()).filter(Incident.priority.isnot(None)).all()
        priorities = [p[0] for p in priorities if p[0]]

        return render_template('incidents.html',
                             incidents=incidents_list,
                             search=search,
                             status_filter=status_filter,
                             priority_filter=priority_filter,
                             statuses=statuses,
                             priorities=priorities)

    @app.route('/incidents/add', methods=['GET', 'POST'])
    def add_incident():
        if request.method == 'POST':
            # Get form data
            ticket_number = request.form.get('ticket_number')
            date = request.form.get('date')
            user = request.form.get('user')
            asset = request.form.get('asset')
            category = request.form.get('category')
            subcategory = request.form.get('subcategory')
            priority = request.form.get('priority')
            issue = request.form.get('issue')
            description = request.form.get('description')
            action_taken = request.form.get('action_taken')
            resolution = request.form.get('resolution')
            status = request.form.get('status')
            assigned_to = request.form.get('assigned_to')
            resolution_date = request.form.get('resolution_date')
            sla_target = request.form.get('sla_target')
            remarks = request.form.get('remarks')

            # Validate required fields
            if not ticket_number or not date or not issue:
                flash('Ticket Number, Date, and Issue are required!', 'error')
                return redirect(url_for('add_incident'))

            # Check if ticket_number already exists
            if Incident.query.filter_by(ticket_number=ticket_number).first():
                flash('Ticket Number already exists!', 'error')
                return redirect(url_for('add_incident'))

            # Create new incident
            incident = Incident(
                ticket_number=ticket_number,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                user=user if user else None,
                asset=asset if asset else None,
                category=category if category else None,
                subcategory=subcategory if subcategory else None,
                priority=priority if priority else 'Medium',
                issue=issue,
                description=description if description else None,
                action_taken=action_taken if action_taken else None,
                resolution=resolution if resolution else None,
                status=status if status else 'New',
                assigned_to=assigned_to if assigned_to else None,
                resolution_date=datetime.strptime(resolution_date, '%Y-%m-%d').date() if resolution_date else None,
                closed_date=datetime.strptime(resolution_date, '%Y-%m-%d').date() if resolution_date and status in ['Closed', 'Resolved'] else None,
                remarks=remarks if remarks else None
            )

            db.session.add(incident)
            db.session.commit()

            # Log activity
            log_activity('Added incident', 'Incident', incident.id, f'Incident {ticket_number} added')

            flash('Incident added successfully!', 'success')
            return redirect(url_for('incidents'))

        # GET request - show form
        # Get unique values for dropdowns
        categories = ['Hardware', 'Software', 'Network', 'Access', 'Security', 'Other']
        priorities = ['Low', 'Medium', 'High', 'Critical']
        statuses = ['New', 'Open', 'In Progress', 'Pending', 'Resolved', 'Closed']
        assigned_to_options = ['Admin', 'Team Lead', 'Engineer']

        # Get users and assets for dropdowns
        users = User.query.all()
        assets = Asset.query.all()

        return render_template('add_incident.html',
                             categories=categories,
                             priorities=priorities,
                             statuses=statuses,
                             assigned_to_options=assigned_to_options,
                             users=users,
                             assets=assets)

    # Software routes
    @app.route('/software')
    def software():
        search = request.args.get('search', '')

        query = Software.query

        if search:
            query = query.filter(
                db.or_(
                    Software.name.contains(search),
                    Software.license_key.contains(search),
                    Software.assigned_to.contains(search)
                )
            )

        software_list = query.all()

        return render_template('software.html', software=software_list, search=search)

    @app.route('/software/add', methods=['GET', 'POST'])
    def add_software():
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name')
            version = request.form.get('version')
            license_key = request.form.get('license_key')
            assigned_to = request.form.get('assigned_to')
            status = request.form.get('status')
            install_date = request.form.get('install_date')
            expiry_date = request.form.get('expiry_date')
            remarks = request.form.get('remarks')

            # Validate required fields
            if not name:
                flash('Software Name is required!', 'error')
                return redirect(url_for('add_software'))

            # Create new software
            software = Software(
                name=name,
                version=version if version else None,
                license_key=license_key if license_key else None,
                assigned_to=assigned_to if assigned_to else None,
                status=status if status else 'Active',
                install_date=datetime.strptime(install_date, '%Y-%m-%d').date() if install_date else None,
                expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
                remarks=remarks if remarks else None
            )

            db.session.add(software)
            db.session.commit()

            # Log activity
            log_activity('Added software', 'Software', software.id, f'Software {name} added')

            flash('Software added successfully!', 'success')
            return redirect(url_for('software'))

        # GET request - show form
        # Get unique values for dropdowns
        statuses = ['Active', 'Inactive', 'Expired']

        # Get users for assigned to dropdown
        users = User.query.all()

        return render_template('add_software.html',
                             statuses=statuses,
                             users=users)

    # Network routes
    @app.route('/network')
    def network():
        search = request.args.get('search', '')

        query = NetworkDevice.query

        if search:
            query = query.filter(
                db.or_(
                    NetworkDevice.device_name.contains(search),
                    NetworkDevice.ip_address.contains(search),
                    NetworkDevice.type.contains(search)
                )
            )

        network_list = query.all()

        return render_template('network.html', network=network_list, search=search)

    @app.route('/network/add', methods=['GET', 'POST'])
    def add_network():
        if request.method == 'POST':
            # Get form data
            device_name = request.form.get('device_name')
            ip_address = request.form.get('ip_address')
            mac_address = request.form.get('mac_address')
            device_type = request.form.get('device_type')
            location = request.form.get('location')
            status = request.form.get('status')
            manufacturer = request.form.get('manufacturer')
            model = request.form.get('model')
            remarks = request.form.get('remarks')

            # Validate required fields
            if not device_name:
                flash('Device Name is required!', 'error')
                return redirect(url_for('add_network'))

            # Create new network device
            network_device = NetworkDevice(
                device_name=device_name,
                ip_address=ip_address if ip_address else None,
                mac_address=mac_address if mac_address else None,
                device_type=device_type if device_type else None,
                location=location if location else None,
                status=status if status else 'Active',
                manufacturer=manufacturer if manufacturer else None,
                model=model if model else None,
                remarks=remarks if remarks else None
            )

            db.session.add(network_device)
            db.session.commit()

            # Log activity
            log_activity('Added network device', 'Network', network_device.id, f'Network device {device_name} added')

            flash('Network device added successfully!', 'success')
            return redirect(url_for('network'))

        # GET request - show form
        # Get unique values for dropdowns
        device_types = ['Switch', 'Router', 'Access Point', 'Firewall', 'Modem']
        locations = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune']
        statuses = ['Active', 'Inactive', 'Maintenance']
        manufacturers = ['Dell', 'HP', 'Cisco', 'Juniper', 'Other']

        return render_template('add_network.html',
                             device_types=device_types,
                             locations=locations,
                             statuses=statuses,
                             manufacturers=manufacturers)

    # Switch Port routes
    @app.route('/network/switch/<int:id>')
    def switch_ports(id):
        switch = NetworkDevice.query.get_or_404(id)
        ports = SwitchPort.query.filter_by(switch_id=id).order_by(SwitchPort.port_number).all()
        
        # Get connected assets for dropdown
        assets = Asset.query.filter(Asset.ip_address.isnot(None)).all()
        
        return render_template('switch_ports.html', switch=switch, ports=ports, assets=assets)

    @app.route('/network/switch/<int:id>/port/add', methods=['GET', 'POST'])
    def add_switch_port(id):
        switch = NetworkDevice.query.get_or_404(id)
        
        if request.method == 'POST':
            port = SwitchPort(
                switch_id=id,
                port_number=request.form.get('port_number'),
                port_name=request.form.get('port_name'),
                status=request.form.get('status'),
                connected_device=request.form.get('connected_device'),
                connected_device_ip=request.form.get('connected_device_ip'),
                connected_device_mac=request.form.get('connected_device_mac'),
                vlan=request.form.get('vlan'),
                speed=request.form.get('speed'),
                duplex=request.form.get('duplex'),
                poe=bool(request.form.get('poe')),
                poe_power=request.form.get('poe_power'),
                remarks=request.form.get('remarks')
            )
            db.session.add(port)
            db.session.commit()
            
            log_activity('Added switch port', 'SwitchPort', port.id, f'Port {port.port_number} added to {switch.device_name}')
            flash('Port added successfully!', 'success')
            return redirect(url_for('switch_ports', id=id))
        
        assets = Asset.query.filter(Asset.ip_address.isnot(None)).all()
        return render_template('add_switch_port.html', switch=switch, assets=assets)

    @app.route('/network/switch/<int:switch_id>/port/<int:port_id>/edit', methods=['GET', 'POST'])
    def edit_switch_port(switch_id, port_id):
        port = SwitchPort.query.get_or_404(port_id)
        switch = NetworkDevice.query.get_or_404(switch_id)
        
        if request.method == 'POST':
            port.port_number = request.form.get('port_number')
            port.port_name = request.form.get('port_name')
            port.status = request.form.get('status')
            port.connected_device = request.form.get('connected_device')
            port.connected_device_ip = request.form.get('connected_device_ip')
            port.connected_device_mac = request.form.get('connected_device_mac')
            port.vlan = request.form.get('vlan')
            port.speed = request.form.get('speed')
            port.duplex = request.form.get('duplex')
            port.poe = bool(request.form.get('poe'))
            port.poe_power = request.form.get('poe_power')
            port.remarks = request.form.get('remarks')
            
            db.session.commit()
            
            log_activity('Updated switch port', 'SwitchPort', port.id, f'Port {port.port_number} updated on {switch.device_name}')
            flash('Port updated successfully!', 'success')
            return redirect(url_for('switch_ports', id=switch_id))
        
        assets = Asset.query.filter(Asset.ip_address.isnot(None)).all()
        return render_template('edit_switch_port.html', switch=switch, port=port, assets=assets)

    @app.route('/network/switch/<int:switch_id>/port/<int:port_id>/delete')
    def delete_switch_port(switch_id, port_id):
        port = SwitchPort.query.get_or_404(port_id)
        port_info = f'{port.port_number} on {port.switch.device_name}'
        db.session.delete(port)
        db.session.commit()
        
        log_activity('Deleted switch port', 'SwitchPort', port_id, f'Port {port_info} deleted')
        flash('Port deleted successfully!', 'success')
        return redirect(url_for('switch_ports', id=switch_id))

    # Maintenance routes
    @app.route('/maintenance')
    def maintenance():
        search = request.args.get('search', '')

        query = MaintenanceRecord.query

        if search:
            query = query.filter(
                db.or_(
                    MaintenanceRecord.asset_id.contains(search),
                    MaintenanceRecord.asset_name.contains(search),
                    MaintenanceRecord.type.contains(search)
                )
            )

        maintenance_list = query.all()

        return render_template('maintenance.html', maintenance=maintenance_list, search=search)

    @app.route('/maintenance/add', methods=['GET', 'POST'])
    def add_maintenance():
        if request.method == 'POST':
            # Get form data
            asset_id = request.form.get('asset_id')
            asset_name = request.form.get('asset_name')
            maintenance_type = request.form.get('type')
            date = request.form.get('date')
            performed_by = request.form.get('performed_by')
            status = request.form.get('status')
            description = request.form.get('description')
            cost = request.form.get('cost')
            remarks = request.form.get('remarks')

            # Validate required fields
            if not asset_id or not date:
                flash('Asset ID and Date are required!', 'error')
                return redirect(url_for('add_maintenance'))

            # Create new maintenance record
            maintenance_record = MaintenanceRecord(
                asset_id=asset_id,
                asset_name=asset_name if asset_name else None,
                maintenance_type=maintenance_type if maintenance_type else None,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                performed_by=performed_by if performed_by else None,
                status=status if status else 'Completed',
                description=description if description else None,
                cost=cost if cost else None,
                remarks=remarks if remarks else None
            )

            db.session.add(maintenance_record)
            db.session.commit()

            # Log activity
            log_activity('Added maintenance record', 'Maintenance', maintenance_record.id, f'Maintenance record for asset {asset_id} added')

            flash('Maintenance record added successfully!', 'success')
            return redirect(url_for('maintenance'))

        # GET request - show form
        # Get unique values for dropdowns
        maintenance_types = ['Preventive', 'Corrective', 'Urgent', 'Scheduled']
        statuses = ['Completed', 'In Progress', 'Scheduled', 'Cancelled']

        # Get assets for dropdown
        assets = Asset.query.all()

        return render_template('add_maintenance.html',
                             maintenance_types=maintenance_types,
                             statuses=statuses,
                             assets=assets)

    # Activity Log routes
    @app.route('/activity')
    def activity():
        search = request.args.get('search', '')

        query = ActivityLog.query

        if search:
            query = query.filter(
                db.or_(
                    ActivityLog.action.contains(search),
                    ActivityLog.record_type.contains(search),
                    ActivityLog.details.contains(search)
                )
            )

        activity_list = query.order_by(ActivityLog.timestamp.desc()).all()

        return render_template('activity.html', activity=activity_list, search=search)

    @app.route('/activity/clear', methods=['POST'])
    def clear_activity():
        ActivityLog.query.delete()
        db.session.commit()

        # Log activity
        log_activity('Cleared activity log', 'Activity', 0, 'Activity log cleared')

        flash('Activity log cleared successfully!', 'success')
        return redirect(url_for('activity'))

    # Reports routes (simplified)
    @app.route('/reports')
    def reports():
        # In a real app, this would generate various reports
        # For now, just show a placeholder
        return render_template('reports.html')

    # Settings routes
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        settings = Settings.query.first()

        if request.method == 'POST':
            new_password = request.form.get('new_password')
            if new_password:
                settings.password = new_password
                db.session.commit()

                # Log activity
                log_activity('Updated settings', 'Settings', settings.id, 'Password changed')

                flash('Settings updated successfully!', 'success')
                return redirect(url_for('settings'))

        return render_template('settings.html', settings=settings)

    @app.route('/settings/backup')
    def backup_db():
        # In a real app, this would export the database
        flash('Database backup functionality would be implemented here', 'info')
        return redirect(url_for('settings'))

    @app.route('/settings/load-sample')
    def load_sample_data():
        # In a real app, this would load sample data
        flash('Sample data loading functionality would be implemented here', 'info')
        return redirect(url_for('settings'))

    @app.route('/settings/clear-all', methods=['POST'])
    def clear_all_data():
        # Clear all tables except settings
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            if table.name != 'settings':
                db.session.execute(table.delete())
        db.session.commit()

        # Log activity
        log_activity('Cleared all data', 'System', 0, 'All data cleared except settings')

        flash('All data cleared successfully!', 'success')
        return redirect(url_for('settings'))

    # API endpoints for AJAX requests (if needed)
    @app.route('/api/stats')
    def api_stats():
        stats = {
            'users': User.query.count(),
            'assets': Asset.query.count(),
            'open_incidents': Incident.query.filter(Incident.status.notin_(['Closed', 'Resolved'])).count(),
            'pending_requests': Incident.query.filter(Incident.status.in_(['Pending', 'New'])).count(),
            'closed_incidents': Incident.query.filter(Incident.status.in_(['Closed', 'Resolved'])).count(),
            'warranty': Asset.query.filter(Asset.warranty_end > datetime.now().date()).count() if Asset.query.first() else 0
        }
        return jsonify(stats)

    # Auth routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            employee_id = request.form.get('employee_id')
            password = request.form.get('password')
            remember = bool(request.form.get('remember'))
            
            user = User.query.filter_by(employee_id=employee_id).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                log_activity('User login', 'User', user.id, f'User {user.name} logged in')
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Invalid employee ID or password', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        log_activity('User logout', 'User', current_user.id, f'User {current_user.name} logged out')
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)