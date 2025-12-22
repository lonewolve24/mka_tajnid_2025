# How to Create Superuser on Railway

## ⚠️ Important
**DO NOT create superuser locally** - it won't work because Railway uses a different database!

## Method 1: Railway Console (Easiest)

1. Deploy your app to Railway
2. Go to your Railway project dashboard
3. Click on your service
4. Click **"View Logs"** or find **"Console"** / **"Shell"** button
5. Click to open the console/terminal
6. Run:
   ```bash
   python manage.py createsuperuser
   ```
7. Enter:
   - Username: (choose a username)
   - Email: (your email - optional)
   - Password: (choose a strong password)
   - Password (again): (confirm password)

## Method 2: Railway CLI

1. Install Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Link to your project:
   ```bash
   railway link
   ```

4. Create superuser:
   ```bash
   railway run python manage.py createsuperuser
   ```

## Method 3: One-Time Auto-Creation (Advanced)

If you want to auto-create superuser on first deploy, you can temporarily modify `railway.json`:

1. Set environment variable in Railway:
   ```
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_EMAIL=admin@example.com
   DJANGO_SUPERUSER_PASSWORD=your-secure-password
   ```

2. Temporarily modify `railway.json` start command:
   ```json
   "startCommand": "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py createsuperuser --noinput || true && gunicorn config.wsgi:application"
   ```

3. **IMPORTANT:** After first deployment, remove this and use Method 1 for future superusers!

## ✅ After Creating Superuser

1. Go to: `https://your-app.railway.app/admin/`
2. Login with your superuser credentials
3. You can now manage users, registrations, and vitals from the admin panel

