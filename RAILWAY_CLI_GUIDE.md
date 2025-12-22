# Railway CLI Guide - Creating Superuser

## ✅ Railway CLI is Installed!

Railway CLI has been installed on your system using npm.

## Step-by-Step: Create Superuser on Railway

### 1. Login to Railway
```bash
railway login
```
This will open your browser to authenticate with Railway.

### 2. Link to Your Project
Navigate to your project directory:
```bash
cd /home/ai/Desktop/mka_tajnid_2025
```

Link to your Railway project:
```bash
railway link
```
- Select your Railway project from the list
- Or provide your project ID if prompted

### 3. Create Superuser
Once linked, run:
```bash
railway run python manage.py createsuperuser
```

You'll be prompted to enter:
- Username
- Email (optional)
- Password
- Password (again)

### 4. Verify It Works
After creating the superuser, you can verify by running:
```bash
railway run python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(f'Superusers: {User.objects.filter(is_superuser=True).count()}')"
```

## Other Useful Railway CLI Commands

### View Logs
```bash
railway logs
```

### Run Django Commands
```bash
railway run python manage.py <command>
```

### Check Environment Variables
```bash
railway variables
```

### Open Railway Dashboard
```bash
railway open
```

## Troubleshooting

### If `railway` command not found:
Add npm global bin to your PATH (if not already):
```bash
export PATH="$PATH:$(npm config get prefix)/bin"
```

Or add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export PATH="$PATH:$(npm config get prefix)/bin"' >> ~/.bashrc
source ~/.bashrc
```

### If login fails:
Make sure you're logged into Railway in your browser first, then try:
```bash
railway login --browserless
```

## Quick Reference

```bash
# Login
railway login

# Link project
railway link

# Create superuser
railway run python manage.py createsuperuser

# View logs
railway logs

# Run migrations
railway run python manage.py migrate
```

