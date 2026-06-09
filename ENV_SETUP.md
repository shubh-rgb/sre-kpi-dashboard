# Environment Variables Setup Guide

This guide explains how to configure your environment variables for the SRE KPI Dashboard.

## Quick Start

### 1. Create your `.env` file
```bash
cp .env.example .env
```

### 2. Edit `.env` with your credentials
```bash
# Edit with your favorite editor
nano .env
# or
vim .env
```

### 3. Load environment variables (local development)
```bash
export $(cat .env | xargs)
```

### 4. Run the application
```bash
# With Docker
docker-compose up

# Or locally
python3 pipeline/check_api.py
```

---

## Environment Variables Reference

### Freshservice API Configuration

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `FRESHSERVICE_API_KEY` | ✅ Yes | `` | Your Freshservice API key (keep secret!) |
| `FRESHSERVICE_DOMAIN` | ✅ Yes | `ttnmssupport` | Your Freshservice subdomain |

**How to get your API Key:**
1. Log in to Freshservice
2. Go to **Admin** → **API & Webhooks** → **API Keys**
3. Copy your API key (keep it secret!)

---

### PostgreSQL Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | Database hostname (use `postgres` in Docker) |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `governance` | Database name |
| `DB_USER` | `admin` | Database username |
| `DB_PASSWORD` | `admin` | Database password (change in production!) |
| `DB_SCHEMA` | `public` | Database schema |

**For Docker Compose:** Use `postgres` as `DB_HOST`  
**For local PostgreSQL:** Use `localhost`  
**For AWS RDS:** Use your RDS endpoint (e.g., `mydb.xxxxx.us-east-1.rds.amazonaws.com`)

---

### ETL Pipeline Configuration

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `TABLE_NAME` | `sre_kpis` | Any table name | Default table for SRE KPI data |
| `LOAD_RETAIL_DATA` | `true` | `true` / `false` | Load retail database sample data |
| `LOAD_FRESHSERVICE_DATA` | `false` | `true` / `false` | Fetch data from Freshservice API |
| `AUTO_GENERATE_DASHBOARDS` | `true` | `true` / `false` | Auto-generate Grafana dashboards |

---

## Security Best Practices

### ⚠️ DO NOT commit `.env` to Git
Your `.env` file contains secrets and is already in `.gitignore`.

### 🔐 Rotate your API keys regularly
```bash
# If your .env is exposed:
1. Go to Freshservice Admin → API & Webhooks
2. Disable the exposed API key
3. Generate a new one
4. Update .env
```

### 🔒 Production Setup
For AWS/production environments:
1. Use **AWS Secrets Manager** instead of `.env`
2. Or use **AWS Systems Manager Parameter Store**
3. Never hardcode secrets in code

**Example with AWS Secrets Manager:**
```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='freshservice-api')
api_key = secret['SecretString']
```

---

## Usage Examples

### Running locally with `.env`
```bash
# Load environment variables
export $(cat .env | xargs)

# Test Freshservice connection
python3 pipeline/check_api.py

# Run ETL pipeline
python3 pipeline/etl_enhanced.py
```

### Running with Docker Compose
```bash
# Docker automatically loads .env
docker-compose up

# See logs
docker-compose logs -f pipeline
```

### Running with custom variables
```bash
# Override .env with CLI arguments
FRESHSERVICE_API_KEY=your_key docker-compose up

# Or use a different .env file
env $(cat custom.env | xargs) python3 pipeline/check_api.py
```

---

## Troubleshooting

### "Error: FRESHSERVICE_API_KEY not set"
```bash
# Make sure .env exists
ls -la .env

# Make sure variables are loaded
echo $FRESHSERVICE_API_KEY

# Load them if empty
export $(cat .env | xargs)
```

### "Connection refused: localhost:5432"
- **Docker:** Make sure PostgreSQL service is running: `docker-compose up postgres`
- **Local:** Install PostgreSQL and verify: `pg_isready -h localhost`
- **AWS RDS:** Check security group allows your IP

### "401 Unauthorized: Freshservice API"
- ✅ Verify API key is correct in `.env`
- ✅ Check API key hasn't been revoked in Freshservice
- ✅ Confirm `FRESHSERVICE_DOMAIN` matches your subdomain

### "Database error: FATAL: database does not exist"
```bash
# Create the database
createdb -U admin governance

# Or let Docker create it on first run
docker-compose up postgres
```

---

## Migration to AWS

When moving to AWS Glue + RDS:

```env
# Change these for RDS
DB_HOST=your-database.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=your-secure-password

# Store secrets in AWS Secrets Manager instead of .env
# See production setup section above
```

---

## Variables by Environment

### Development (Local)
```env
FRESHSERVICE_API_KEY=pRZTtmEWbZvE2K68kOND
FRESHSERVICE_DOMAIN=ttnmssupport
DB_HOST=localhost
DB_PORT=5432
LOAD_FRESHSERVICE_DATA=false
```

### Testing (Docker)
```env
FRESHSERVICE_API_KEY=pRZTtmEWbZvE2K68kOND
FRESHSERVICE_DOMAIN=ttnmssupport
DB_HOST=postgres
DB_PORT=5432
LOAD_FRESHSERVICE_DATA=true
```

### Production (AWS)
```env
# Use AWS Secrets Manager - do NOT use .env
FRESHSERVICE_API_KEY=${aws:secrets-manager:freshservice-key}
FRESHSERVICE_DOMAIN=ttnmssupport
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_USER=${aws:secrets-manager:db-user}
DB_PASSWORD=${aws:secrets-manager:db-password}
LOAD_FRESHSERVICE_DATA=true
```

---

## Need Help?

- 📖 [Freshservice API Docs](https://api.freshservice.com/)
- 🐘 [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html)
- ☁️ [AWS RDS Setup Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.PostgreSQL.html)
- 🔐 [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
