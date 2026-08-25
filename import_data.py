"""
Import data from Excel files into IT Admin Manager database
"""
import pandas as pd
from datetime import datetime
from app import create_app
from models import db, Asset, NetworkDevice, User

def clean_val(val):
    """Clean pandas NaN values"""
    if pd.isna(val):
        return None
    return str(val).strip()

def parse_date(val):
    """Parse date from various formats"""
    if pd.isna(val):
        return None
    try:
        if isinstance(val, (int, float)):
            # Excel serial date
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=val)
        return pd.to_datetime(val).date()
    except:
        return None

def import_assets():
    """Import assets from Collection of Assets Details"""
    df = pd.read_excel(r'..\Latest Data\Collection of Assets Details -Rajkot Location.xlsx', header=1)
    df.columns = ['SI_No', 'Zone_Refinery', 'Location_Code', 'Location_Name', 'Desktop_Model', 
                  'Procurement_Year', 'Working_Status', 'Serial_Number', 'ERP_Asset_Tag', 
                  'User_Emp_No', 'User_Name', 'User_Department', 'Non_Emp_User_Name', 
                  'Non_Emp_Reporting_Officer_Emp_No', 'Non_Emp_Reporting_Officer_Name', 
                  'Non_Emp_Reporting_Officer_Dept_Name']
    # Skip first row (it's the header repeated)
    df = df.iloc[1:].reset_index(drop=True)
    print(f"Importing {len(df)} assets...")
    
    count = 0
    for _, row in df.iterrows():
        serial = clean_val(row.get('Serial_Number'))
        if not serial or serial == 'nan':
            continue
            
        asset = Asset(
            asset_id=clean_val(row.get('ERP_Asset_Tag')) or f"AST-{serial[-6:]}",
            hostname=clean_val(row.get('Desktop_Model')),
            asset_type='Desktop',
            manufacturer='HP',
            model=clean_val(row.get('Desktop_Model')),
            serial_number=serial,
            employee_id=clean_val(row.get('User_Emp_No')),
            department=clean_val(row.get('User_Department')),
            location=clean_val(row.get('Location_Name')),
            asset_status='Active' if clean_val(row.get('Working_Status')) == 'Y' else 'Inactive',
            purchase_date=parse_date(row.get('Procurement_Year')),
            remarks=f"Zone: {clean_val(row.get('Zone_Refinery'))}, Location Code: {clean_val(row.get('Location_Code'))}, User: {clean_val(row.get('User_Name'))}"
        )
        db.session.add(asset)
        count += 1
    
    db.session.commit()
    print(f"Imported {count} assets")

def import_network_inventory():
    """Import network devices from Network_Inventory_Rajkot"""
    df = pd.read_excel(r'..\Latest Data\Network_Inventory_Rajkot 08052026.xlsx')
    print(f"Importing {len(df)} network devices...")
    
    count = 0
    for _, row in df.iterrows():
        if pd.isna(row.get('Asset Model')):
            continue
            
        device = NetworkDevice(
            device_name=f"{clean_val(row.get('Asset Type'))} - {clean_val(row.get('Asset Model'))}",
            ip_address=clean_val(row.get('IP Address')),
            mac_address=clean_val(row.get('Mac Address')),
            device_type=clean_val(row.get('Asset Type')),
            location=clean_val(row.get('Location')),
            status=clean_val(row.get('Status')),
            manufacturer=clean_val(row.get('OEM')),
            model=clean_val(row.get('Asset Model')),
            remarks=f"Zone: {clean_val(row.get('Zone'))}, State: {clean_val(row.get('State'))}, RE: {clean_val(row.get('RE Name'))}, Email: {clean_val(row.get('Email ID'))}, Mobile: {clean_val(row.get('Mobile No.'))}, LAN IP: {clean_val(row.get('Location LAN IP'))}"
        )
        db.session.add(device)
        count += 1
    
    db.session.commit()
    print(f"Imported {count} network devices")

def import_aio_desktops():
    """Import new AIO desktops"""
    df = pd.read_excel(r'..\Latest Data\New AIO Desktop Serial Number 2025.xlsx')
    print(f"Importing {len(df)} AIO desktops...")
    
    count = 0
    for _, row in df.iterrows():
        serial = clean_val(row.get('Serial Number'))
        if not serial or serial == 'nan':
            continue
            
        asset = Asset(
            asset_id=f"AIO-{serial[-6:]}",
            hostname=clean_val(row.get('Make & Model')),
            asset_type='All-in-One',
            manufacturer='HP',
            model=clean_val(row.get('Make & Model')),
            serial_number=serial,
            location=clean_val(row.get('Location Name')),
            asset_status='Active',
            remarks=f"State: {clean_val(row.get('State'))}, Mouse SN: {clean_val(row.get('Mouse SN'))}, Keyboard SN: {clean_val(row.get('Keyboard SN'))}, {clean_val(row.get('Remarks'))}"
        )
        db.session.add(asset)
        count += 1
    
    db.session.commit()
    print(f"Imported {count} AIO desktops")

def import_network_sites():
    """Import network site info from the three NETWORK files"""
    files = [
        (r'..\Latest Data\NETWORK ESSAR VADINAR (11449).xlsx', 'ESSAR VADINAR', '10.2.113.1'),
        (r'..\Latest Data\NETWORK RAJKOT RO (11360).xlsx', 'RAJKOT RO', '10.2.73.1'),
        (r'..\Latest Data\NETWORK RELIANCE JAMNAGAR TOP (11541).xlsx', 'JAMNAGAR TOP', '10.2.41.1'),
    ]
    
    for f, site_name, site_ip in files:
        device = NetworkDevice(
            device_name=f"{site_name} - Main Router",
            ip_address=site_ip,
            device_type='Router',
            location=site_name.split(' ')[0],
            status='Active',
            manufacturer='CISCO',
            remarks=f"Site: {site_name}, Main Gateway IP"
        )
        db.session.add(device)
        print(f"Added site router: {site_name} ({site_ip})")
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Starting data import...")
        print("=" * 50)
        
        # Clear existing data (optional - comment out to keep existing)
        # db.session.query(Asset).delete()
        # db.session.query(NetworkDevice).delete()
        # db.session.commit()
        
        import_assets()
        import_network_inventory()
        import_aio_desktops()
        import_network_sites()
        
        print("=" * 50)
        print("Import complete!")
        print(f"Total Assets: {Asset.query.count()}")
        print(f"Total Network Devices: {NetworkDevice.query.count()}")