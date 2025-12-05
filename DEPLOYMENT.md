# AWS EC2 Deployment Guide

Deploy the Hotel Management System to AWS EC2 with Docker Compose, running both the FastAPI application and PostgreSQL database on a single EC2 instance for development/staging purposes.

## Prerequisites & Setup

### 1. AWS Account & EC2 Instance Setup

- **Region**: Choose a region (e.g., `us-east-1`, `ap-south-1`)
- **Instance Type**: `t3.micro` or `t3.small` (eligible for free tier, good for dev/staging)
- **OS**: Ubuntu 22.04 LTS AMI (widely supported, well-documented)
- **Storage**: 20-30 GB (gp3 or gp2)
- **Security Group Rules**:
  - Inbound: SSH (22) from your IP
  - Inbound: HTTP (80) from anywhere (optional, for health checks)
  - Inbound: HTTPS (443) from anywhere (optional, for production-ready setup)
  - Inbound: 8050 from anywhere (app port) - OR use via reverse proxy
  - Outbound: All traffic to anywhere (default)

### 2. Prerequisites on EC2

Install required software:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose-plugin

# Add user to docker group (optional, for convenience)
sudo usermod -aG docker $USER

# Verify Docker installation
docker --version
docker compose version

# Install Git
sudo apt install -y git
```

## Deployment Steps

### Step 1: Clone Repository on EC2

```bash
# SSH into EC2 instance
ssh -i /path/to/key.pem ubuntu@your-ec2-public-ip

# Clone the repository
cd /home/ubuntu
git clone <repository-url> hotel_management_admin
cd hotel_management_admin
```

### Step 2: Prepare Environment Configuration

Create `.env` file with production-safe defaults:

```bash
# Generate secure random key for SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
echo "Generated SECRET_KEY: $SECRET_KEY"

# Generate secure random password for PostgreSQL
PG_PASSWORD=$(openssl rand -hex 16)
echo "Generated PG_PASSWORD: $PG_PASSWORD"

# Create .env file
cat > .env << EOF
# API Configuration
API_V1_STR=/api/v1
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Configuration (Docker Compose will use these)
PG_HOST=db
PG_PORT=5432
PG_USERNAME=postgres
PG_PASSWORD=$PG_PASSWORD
PG_DB=hotel_management
PG_SCHEMA=public
EOF

# Verify .env was created
cat .env
```

**Important**: Never commit `.env` to git. It's already in `.gitignore`.

### Step 3: Update docker-compose.yml for EC2

The current `docker-compose.yml` is production-ready:

**Current Status**: ✓ Already configured
- Port mapping: `8050:8080` ✓
- PORT environment variable: Set ✓
- Health checks: Configured ✓

**Optional Enhancement for EC2** (future):
- Consider using a reverse proxy (Nginx) for:
  - SSL termination (HTTPS)
  - Better port management (app on 8080, Nginx on 80)
  - Better resource efficiency

### Step 4: Build and Start Containers

```bash
# Navigate to project directory
cd ~/hotel_management_admin

# Build images (ensures latest code is included)
docker compose build

# Start services in background
docker compose up -d

# Verify services are running
docker compose ps

# Check logs for any errors
docker compose logs -f web

# Test API endpoint (wait 10 seconds for startup)
sleep 10
curl http://localhost:8050

# Expected response:
# {"message":"Welcome to RS Residency!"}
```

### Step 5: Initial Data Setup (Optional)

If you have initial data to populate:

```bash
# Access PostgreSQL container
docker compose exec db psql -U postgres -d hotel_management

# Or run SQL initialization script
docker compose exec db psql -U postgres -d hotel_management < init-scripts/01-init.sql
```

## Post-Deployment Configuration

### 1. Application Access

**From EC2 Instance**:
```
API: http://localhost:8050
Swagger UI: http://localhost:8050/api/v1/docs
ReDoc: http://localhost:8050/api/v1/redoc
```

**From External Machine**:
```
API: http://<ec2-public-ip>:8050
Swagger UI: http://<ec2-public-ip>:8050/api/v1/docs
ReDoc: http://<ec2-public-ip>:8050/api/v1/redoc
```

### 2. Database Access (Optional)

```bash
# Connect from EC2
docker compose exec db psql -U postgres -d hotel_management

# Or use psql from local machine (if PostgreSQL client installed)
psql -h <ec2-public-ip> -U postgres -d hotel_management
```

### 3. Persistent Storage for Database

Docker Compose creates a named volume `postgres_data`:
- Data persists even if container restarts
- Located at: `/var/lib/docker/volumes/hotel_management_admin_postgres_data/_data`

**For EC2 deployment**:
- Named volumes stored on EC2 instance
- Data persists across container restarts
- If instance terminates, data is lost (add EBS snapshot strategy if needed)

### 4. Monitoring & Logs

```bash
# View all logs
docker compose logs

# View web service logs only
docker compose logs -f web

# View database logs only
docker compose logs -f db

# View last 50 lines
docker compose logs --tail=50

# View logs with timestamps
docker compose logs -f --timestamps
```

## Operational Commands

### Daily Operations

```bash
# Start services
docker compose up -d

# Stop services (keeps data)
docker compose stop

# Restart services
docker compose restart

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Troubleshooting

```bash
# If web service won't start, check database connection
docker compose logs web

# If database won't start
docker compose logs db

# Restart all services
docker compose restart

# Full restart (removes containers, keeps volumes/data)
docker compose down
docker compose up -d

# Full cleanup (removes everything including data)
docker compose down -v
docker compose up -d
```

### Backup & Recovery

```bash
# Backup database (create SQL dump)
docker compose exec db pg_dump -U postgres hotel_management > backup-$(date +%Y%m%d).sql

# Restore database from backup
docker compose exec -T db psql -U postgres hotel_management < backup-20251206.sql

# Backup named volume
docker run --rm -v hotel_management_admin_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-data-backup-$(date +%Y%m%d).tar.gz -C /data .
```

## Security Considerations

### Current Status & Recommendations

✓ **Already Addressed**:
- `.gitignore` excludes `.env` files
- `.dockerignore` is configured
- JWT authentication implemented

⚠️ **Recommended for Production Hardening** (Not required for dev/staging):
1. Use AWS Secrets Manager for SECRET_KEY storage
2. Add SSL/TLS certificates (Let's Encrypt via nginx reverse proxy)
3. Implement AWS VPC for network isolation
4. Use AWS Security Groups more restrictively
5. Enable EC2 instance monitoring via CloudWatch
6. Consider AWS RDS for managed PostgreSQL backups

### For Current Dev/Staging Deployment
- `.env` file stored locally on EC2 (not in git) ✓
- Strong random passwords generated for PG_PASSWORD ✓
- SSH key-based access to EC2 ✓

## Rollback & Recovery

If something goes wrong:

```bash
# Option 1: Restart containers
docker compose restart

# Option 2: Recreate containers (keeps data)
docker compose down
docker compose up -d

# Option 3: Full reset (loses data, fresh start)
docker compose down -v
git pull  # Get latest code
docker compose up -d

# Option 4: Revert to specific git commit
git log --oneline
git checkout <commit-hash>
docker compose build
docker compose up -d
```

## Maintenance Tasks

### Weekly
```bash
# Monitor disk space
df -h

# Check logs for errors
docker compose logs | grep -i error
```

### Monthly
```bash
# Backup database (see Backup & Recovery section)
docker compose exec db pg_dump -U postgres hotel_management > backup-monthly-$(date +%Y%m%d).sql

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker pull postgres:15 && docker pull python:3.11-slim
```

### As-Needed
```bash
# Pull latest code
git pull && docker compose build && docker compose restart

# Check resource usage
docker stats
```

## Key Files to Understand

- `Dockerfile` - Container image definition (Python 3.11, FastAPI setup)
- `docker-compose.yml` - Service orchestration (web + db)
- `app/core/config.py` - Settings/environment configuration
- `app/db/postgres_db.py` - Database connection URI builder
- `.env` - Local environment variables (create during deployment)
- `.gitignore` - Already configured to exclude .env and venv

## Cost Estimation (AWS Free Tier)

For first 12 months (if eligible):
- EC2 t3.micro instance: Free (750 hrs/month)
- Data transfer: First 100 GB free
- EBS storage: Free up to 30 GB

After free tier or with larger instance:
- t3.micro: ~$8/month (us-east-1 pricing)
- t3.small: ~$16/month
- Data transfer: ~$0.01/GB after free tier

## Next Steps (Future Enhancements)

For production-grade deployment:
1. Use AWS RDS instead of EC2-hosted PostgreSQL
2. Implement CI/CD pipeline (GitHub Actions → ECR → Deploy)
3. Use AWS ALB/NLB for load balancing
4. Implement CloudWatch monitoring and alarms
5. Use ECS Fargate for serverless container management
6. Implement automated backups via AWS Backup service

## Summary

This deployment guide enables straightforward EC2 deployment with:
- ✓ Single t3.micro/small instance
- ✓ Docker Compose for orchestration
- ✓ Database on same instance
- ✓ Environment-based configuration
- ✓ Security best practices for dev/staging
- ✓ Simple operational procedures
