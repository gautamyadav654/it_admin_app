# IT Admin Manager

A comprehensive IT Asset Management System built with Flask, SQLAlchemy, and Bootstrap 5.

## Features

- **Dashboard** - Real-time stats, charts, recent activity
- **User Management** - CRUD operations with search/filter
- **Asset Tracking** - Hardware inventory with warranty monitoring
- **Incident/Ticket System** - Priority, SLA, status tracking
- **Software License Management** - Expiry alerts, compliance
- **Network Device Management** - IP/MAC tracking, switch port mapping
- **Maintenance Records** - Cost tracking, scheduling
- **Activity Log** - Full audit trail
- **Switch Port Manager** - Visual port layout, VLAN/PoE tracking

## Local Development

```bash
# Clone and navigate
cd it_admin_app

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
# or use the batch file
start.bat
```

Access at: http://127.0.0.1:5000
Default password: `admin123`

## Deployment Options

### Option 1: Vercel (Serverless) ⚠️ Limited

**Limitations:**
- SQLite doesn't work on Vercel (ephemeral filesystem)
- Requires external PostgreSQL database (Neon, Supabase, Vercel Postgres)
- 30s function timeout
- No WebSocket support

**Setup for Vercel:**

1. Create a PostgreSQL database (recommended: [Neon](https://neon.tech) or [Supabase](https://supabase.com))
2. Get the connection string
3. Deploy to Vercel:

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

4. Set Environment Variables in Vercel Dashboard:
   - `DATABASE_URL` = your PostgreSQL connection string
   - `SECRET_KEY` = generate a secure random string

**vercel.json** is configured for Flask deployment.

---

### Option 2: Railway (Recommended) 🚂

Best for Flask apps with databases.

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

- Automatic PostgreSQL provisioning
- Persistent storage
- Custom domains
- $5/month hobby plan

---

### Option 3: Render 🎨

```bash
# Connect GitHub repo to Render
# Create Web Service
# Build Command: pip install -r requirements.txt
# Start Command: gunicorn app:app
# Add PostgreSQL database
```

- Free tier available
- Automatic SSL
- Persistent disks

---

### Option 4: Fly.io 🪰

```bash
# Install flyctl
# fly auth signup
# fly launch
# fly deploy
```

- Free allowance
- Global deployment
- SQLite with LiteFS for replication

---

### Option 5: Docker (Any VPS)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t it-admin .
docker run -d -p 5000:5000 -v $(pwd)/data:/app/instance it-admin
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key (generate with `secrets.token_hex(32)`) |
| `DATABASE_URL` | Yes | Database connection string |
| `FLASK_ENV` | No | `production` or `development` |

## Database Support

| Database | Connection String Format |
|----------|-------------------------|
| SQLite (dev) | `sqlite:///it_admin.db` |
| PostgreSQL | `postgresql://user:pass@host:port/db` |
| MySQL | `mysql+pymysql://user:pass@host:port/db` |

## Project Structure

```
it_admin_app/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy models
├── database.py         # DB initialization
├── import_data.py      # Excel data importer
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
├── api/index.py        # Vercel entry point
├── start.bat           # Windows startup script
├── templates/          # Jinja2 templates
│   ├── base.html
│   ├── dashboard.html
│   ├── users.html
│   ├── assets.html
│   ├── incidents.html
│   ├── software.html
│   ├── network.html
│   ├── switch_ports.html
│   └── ...
└── Latest Data/        # Source Excel files (not deployed)
```

## Data Import

To import data from Excel files:

```bash
python import_data.py
```

Imports from `../Latest Data/`:
- Asset details (desktops, AIOs)
- Network inventory (switches, routers, APs)
- Switch port mappings

## Switch Port Management

1. Go to **Network** page
2. Click the **blue diagram icon** on any switch
3. View visual port layout with color-coded status
4. Add/edit ports with VLAN, PoE, connected device tracking

## Security Notes

- Change default password in Settings
- Use strong `SECRET_KEY` in production
- Enable HTTPS in production
- Consider adding authentication (Flask-Login)
- Regular database backups

## License

MIT License - Feel free to use and modify.