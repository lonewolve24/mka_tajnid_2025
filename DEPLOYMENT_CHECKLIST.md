# Railway Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Environment Variables to Set in Railway Dashboard

Go to your Railway project → Variables tab and add:

```
DEBUG=False
SECRET_KEY=your-secret-key-here (generate a new one for production)
ALLOWED_HOSTS=your-app-name.railway.app,*.railway.app

# Database (Railway will auto-provide these if you add PostgreSQL service)
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=(auto-provided by Railway)
DB_HOST=(auto-provided by Railway)
DB_PORT=5432
```

### 2. Generate a New Secret Key

Run this command locally to generate a secure secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Database Setup

1. Add a PostgreSQL service in Railway
2. Railway will automatically provide database connection details
3. Set the environment variables in Railway dashboard

### 4. Static Files

- WhiteNoise middleware is configured ✅
- Static files will be collected during deployment ✅

### 5. Files Ready

- ✅ `requirements.txt` - All dependencies listed
- ✅ `railway.json` - Deployment configuration
- ✅ `config/settings.py` - Production-ready settings
- ✅ `config/wsgi.py` - WSGI application configured

## 🚀 Deployment Steps

1. Push your code to GitHub/GitLab
2. Connect your repository to Railway
3. Add PostgreSQL service in Railway
4. Set all environment variables in Railway dashboard
5. Deploy!

## 👤 Creating Superuser on Railway

**Important:** Don't create superuser locally - it won't work on Railway (different databases).

### Option 1: Using Railway Console (Recommended)

1. After deployment, go to your Railway project
2. Click on your service → **View Logs** or **Deployments**
3. Click **"Open Shell"** or **"Console"** button
4. Run:
   ```bash
   python manage.py createsuperuser
   ```
5. Follow the prompts to enter username, email, and password

### Option 2: Using Railway CLI

1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Link project: `railway link`
4. Run: `railway run python manage.py createsuperuser`

### Option 3: Add to Start Command (One-time)

You can temporarily modify `railway.json` start command to create superuser automatically:

```json
"startCommand": "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py createsuperuser --noinput --username admin --email admin@example.com || true && gunicorn config.wsgi:application"
```

**Note:** This requires setting `DJANGO_SUPERUSER_PASSWORD` environment variable. Remove this after first deployment!

## 📝 Notes

- The app will automatically run migrations on deploy
- Static files will be collected automatically
- Make sure DEBUG=False in production
- Set a strong SECRET_KEY for production
- Create superuser AFTER first successful deployment

