# Docker Deployment Guide for Thrift and Thrive

## Quick Start

### 1. Configure Environment (Optional)
```bash
# Copy and customize environment variables
cp .env.example .env
# Edit .env to set your preferred port and other settings
```

### 2. Build and run with Docker Compose (Recommended)
```bash
# Basic deployment (default port 5000)
docker-compose up -d

# Custom port deployment
HOST_PORT=8080 docker-compose up -d

# With nginx reverse proxy (production)
docker-compose --profile production up -d
```

### 3. Build and run with Docker only
```bash
# Build the image
docker build -t thrift-and-thrive .

# Run the container (default port 5000)
docker run -d \
  --name thrift-and-thrive-app \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/reports:/app/reports \
  -e SECRET_KEY=your_secret_key_here \
  thrift-and-thrive

# Run with custom port (e.g., 8080)
docker run -d \
  --name thrift-and-thrive-app \
  -p 8080:8080 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/reports:/app/reports \
  -e SECRET_KEY=your_secret_key_here \
  -e PORT=8080 \
  thrift-and-thrive
```

## Production Features

### Gunicorn WSGI Server
The application now uses Gunicorn, a production-ready WSGI server with:
- **Multiple worker processes** for better performance
- **Automatic worker recycling** to prevent memory leaks
- **Proper logging** and monitoring
- **Graceful shutdowns** and restarts
- **Better security** and stability

### Configurable Ports
- Set `HOST_PORT` to change the port on your host machine
- Set `CONTAINER_PORT` to change the port inside the container
- Both default to 5000 if not specified

### Performance Tuning
- `GUNICORN_WORKERS`: Number of worker processes (default: 4)
- Recommended: 2 × CPU cores for CPU-bound apps
- For I/O-bound apps: 2-4 × CPU cores

## Production Deployment

### Environment Setup
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file and set production values:
   - Change `SECRET_KEY` to a strong random key
   - Set `FLASK_ENV=production`
   - Configure other security settings

### Database Considerations
- The current setup uses SQLite, which works well for development and small deployments
- For production with multiple instances, consider PostgreSQL:
  1. Add `psycopg2-binary` to requirements.txt
  2. Update `SQLALCHEMY_DATABASE_URI` in app.py to use environment variable
  3. Add PostgreSQL service to docker-compose.yml

### Volume Mounts
The following directories need persistent storage:
- `./instance` - SQLite database
- `./uploads` - User uploaded images
- `./reports` - Generated CSV reports
- `./static/uploads` - Static uploaded files

### Security Recommendations
1. Use strong secret keys
2. Enable SSL/TLS (HTTPS) in production
3. Set up proper firewall rules
4. Regular database backups
5. Monitor logs and set up alerts

### Scaling
- Use docker-compose for single-server deployments
- For multi-server deployments, consider:
  - Kubernetes
  - Docker Swarm
  - Shared storage for uploads (NFS, S3, etc.)
  - External database (PostgreSQL, MySQL)

### Health Checks
The container includes health checks. Monitor with:
```bash
docker ps  # Check health status
docker logs <container_id>  # View logs
```

### Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Common Issues
1. **Permission errors**: Ensure upload directories are writable
2. **Database locked**: Stop all containers before backup/restore
3. **Port conflicts**: Change port mapping in docker-compose.yml
4. **Memory issues**: Increase Docker memory limits if needed

### Logs
```bash
# View application logs
docker-compose logs web

# Follow logs in real-time
docker-compose logs -f web
```

### Backup
```bash
# Backup database and uploads
tar -czf backup-$(date +%Y%m%d).tar.gz instance uploads reports
```
