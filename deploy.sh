#!/bin/bash

# Production deployment script for backend-metal-gest
# Run this script after git push to production server

set -e  # Exit on any error

echo "🚀 Starting deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

# 1. Backup database (CRITICAL)
print_status "Creating database backup..."
BACKUP_FILE="db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"
cp db.sqlite3 "$BACKUP_FILE"
print_status "Database backed up to: $BACKUP_FILE"

# 2. Pull latest changes
print_status "Pulling latest changes from git..."
git pull origin main

# 3. Install/Update dependencies
print_status "Installing/updating dependencies..."
pip install -r requirements.txt

# 4. Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# 5. Run database migrations
print_status "Running database migrations..."
python manage.py migrate

# 6. Run system checks
print_status "Running system checks..."
python manage.py check --deploy

# 7. Test database connectivity
print_status "Testing database connectivity..."
python manage.py shell -c "from api.models import Client; print(f'Database OK - {Client.objects.count()} clients found')"

# 8. Restart services (uncomment the one you use)
print_status "Restarting services..."

# For systemd services (uncomment as needed):
# sudo systemctl restart gunicorn
# sudo systemctl restart nginx
# sudo systemctl restart apache2

# For manual gunicorn restart:
# pkill -f gunicorn || true
# nohup gunicorn --bind 0.0.0.0:8000 lazercut.wsgi:application &

print_warning "Please manually restart your web server (gunicorn/nginx/apache)"

# 9. Verify deployment
print_status "Verifying deployment..."
python manage.py showmigrations api | tail -5

print_status "🎉 Deployment completed successfully!"
print_warning "Don't forget to:"
echo "  - Restart your web server"
echo "  - Check application logs"
echo "  - Test critical functionality"
