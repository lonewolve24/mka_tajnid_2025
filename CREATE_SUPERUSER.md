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

## Method 2: Railway Web Console (If you can't find it)

**How to find Railway Console:**
1. Go to https://railway.app
2. Click on your project
3. Click on your **service** (the Django app, not PostgreSQL)
4. Look for tabs: **"Deployments"**, **"Metrics"**, **"Settings"**
5. In the **"Deployments"** tab, find your latest deployment
6. Click the **three dots (⋮)** or **"View Logs"** button
7. Look for **"Shell"** or **"Console"** button - click it
8. A terminal will open where you can run commands

**Alternative locations:**
- Sometimes it's in the top right corner as a terminal icon
- Or in the service settings under "Connect" or "Shell"

## Method 3: Railway CLI (Note: Has Limitations)

⚠️ **Important:** `railway run` tries to use Railway's internal database hostname which doesn't work from your local machine. Use Method 1 (Web Console) instead.

If you still want to try CLI:
1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Link: `railway link`
4. **This won't work for database commands** - use web console instead!

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

