# Deploying to Railway

## Quick Deploy

1. Push this folder to a GitHub repository
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Select your repository

## Add PostgreSQL

1. In your Railway project → **New** → **Database** → **Add PostgreSQL**
2. Railway automatically sets `DATABASE_URL` in your environment

## Set Environment Variables

In Railway project → **Variables** tab, add:

```
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

`DATABASE_URL` is set automatically by Railway when you add PostgreSQL.

## File Storage (Important)

Railway uses **ephemeral storage** — uploaded files (logos, signatures, stamps) are lost on redeploy.

**Recommended solutions:**
- Use **Cloudflare R2** or **AWS S3** for file storage
- Or use **Railway Volumes** (persistent disk): In Railway → your service → **Volumes** → Mount at `/app/static/uploads`

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (auto-set) | PostgreSQL connection string |
| `SECRET_KEY` | Yes | Flask session secret (random 32+ char string) |
| `PORT` | Auto-set | Port for gunicorn (Railway sets this) |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally with SQLite (no DATABASE_URL needed)
python app.py

# Run locally with PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/ghm python app.py
```

## Database Migration

The app auto-creates all tables on first startup via `init_db()`.
For existing SQLite data, use the backup feature before switching to PostgreSQL.

## Default Login

- Username: `admin`
- Password: `admin123`

**Change immediately after first login.**
