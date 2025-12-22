# Railway Pre-Deploy Command Setup

## ✅ Custom Management Command Created

I've created a custom management command `create_superuser_if_none` that:
- ✅ Checks if a superuser already exists (won't create duplicates)
- ✅ Can run automatically on every deploy
- ✅ Uses environment variables for credentials
- ✅ Safe to run multiple times

## How to Use in Railway

### Option 1: Using railway.json (Already Configured)

The `railway.json` file has been updated to include the command in the start command:
```json
"startCommand": "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py create_superuser_if_none --noinput || true && gunicorn config.wsgi:application"
```

### Option 2: Using Railway Dashboard Pre-Deploy Command

1. Go to your Railway project
2. Click on your **Django service**
3. Go to **"Settings"** tab
4. Find **"Pre-Deploy Command"** or **"Build Command"** section
5. Add this command:
   ```bash
   python manage.py create_superuser_if_none --noinput
   ```

**Note:** The `|| true` in railway.json ensures the app starts even if superuser creation fails (because one already exists).

## Environment Variables to Set in Railway

Go to Railway Dashboard → Your Service → Variables tab and add:

```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password-here
```

## How It Works

1. **First Deploy**: Creates superuser with the credentials from environment variables
2. **Subsequent Deploys**: Skips creation (superuser already exists)
3. **Safe**: Won't create duplicate superusers or fail if one exists

## Manual Usage

You can also run it manually in Railway console:
```bash
python manage.py create_superuser_if_none --noinput
```

Or interactively:
```bash
python manage.py create_superuser_if_none
```

## Command Options

```bash
# Use environment variables (recommended for Railway)
python manage.py create_superuser_if_none --noinput

# Specify credentials directly
python manage.py create_superuser_if_none --username admin --email admin@example.com --password mypassword --noinput

# Interactive mode (will prompt for password)
python manage.py create_superuser_if_none --username admin --email admin@example.com
```

## Benefits

- ✅ Automatic superuser creation on first deploy
- ✅ No manual intervention needed
- ✅ Safe to run multiple times
- ✅ Uses environment variables (secure)
- ✅ Won't break if superuser already exists

