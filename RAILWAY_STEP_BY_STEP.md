# Geometry Home Invoice System — Railway Deployment Guide
## Complete Step-by-Step Instructions

---

## OVERVIEW

You will:
1. Create a GitHub account and upload the project
2. Create a Railway account and connect it to GitHub
3. Add a PostgreSQL database
4. Set environment variables
5. Add persistent storage for uploaded files
6. Go live

**Estimated time: 20–30 minutes**

---

## PART 1 — PREPARE GITHUB

### Step 1 — Create a GitHub Account (if you don't have one)

1. Go to **https://github.com**
2. Click **Sign up**
3. Enter your email, create a password, choose a username
4. Verify your email address

---

### Step 2 — Install Git on Windows

1. Go to **https://git-scm.com/download/win**
2. Download and run the installer
3. Accept all defaults and click **Next** until done
4. Open **Command Prompt** and verify: `git --version`
   - You should see something like: `git version 2.44.0`

---

### Step 3 — Create a New GitHub Repository

1. Go to **https://github.com** and log in
2. Click the **+** icon (top right) → **New repository**
3. Fill in:
   - **Repository name:** `gh-invoice-system` (or any name you like)
   - **Visibility:** Select **Private** (recommended — keeps your business data safe)
   - Leave everything else as default
4. Click **Create repository**
5. **Copy the repository URL** shown on the page — it looks like:
   `https://github.com/YOUR-USERNAME/gh-invoice-system.git`

---

### Step 4 — Upload the Project to GitHub

1. Extract the ZIP file you downloaded to a folder, e.g.:
   `C:\Users\Denil Joseph\Desktop\GeometryHome_InvoiceSystem\`

2. Open **Command Prompt** (search "cmd" in Windows search)

3. Navigate to the project folder:
   ```
   cd "C:\Users\Denil Joseph\Desktop\GeometryHome_InvoiceSystem"
   ```

4. Initialize Git and push to GitHub:
   ```
   git init
   git add .
   git commit -m "Initial commit - GH Invoice System"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/gh-invoice-system.git
   git push -u origin main
   ```
   - Replace `YOUR-USERNAME` with your actual GitHub username
   - When asked, enter your GitHub username and password
   - **Note:** GitHub may ask you to use a Personal Access Token instead of password.
     If so, go to GitHub → Settings → Developer Settings → Personal Access Tokens →
     Tokens (classic) → Generate new token → Check "repo" → Generate → Copy the token
     and use it as your password

5. Refresh your GitHub repository page — you should see all project files uploaded

---

## PART 2 — SET UP RAILWAY

### Step 5 — Create a Railway Account

1. Go to **https://railway.app**
2. Click **Login** → **Login with GitHub**
3. Authorize Railway to access your GitHub account
4. Railway will create your account automatically

---

### Step 6 — Create a New Project on Railway

1. After logging in, click **New Project**
2. Select **Deploy from GitHub repo**
3. If prompted, click **Configure GitHub App** and authorize Railway to access your repositories
4. Find and select your **gh-invoice-system** repository
5. Click **Deploy Now**

Railway will start building your app. You will see build logs appear — this takes about 2–3 minutes.

> **Note:** The first deploy will FAIL because PostgreSQL is not connected yet. That is OK — continue to the next step.

---

### Step 7 — Add PostgreSQL Database

1. In your Railway project, click **+ New**
2. Select **Database**
3. Select **Add PostgreSQL**
4. Wait about 30 seconds for the database to be created
5. Railway automatically sets the `DATABASE_URL` environment variable — **you don't need to do anything**

---

### Step 8 — Add Persistent Storage (Volume) for Uploaded Files

> **Why?** Railway resets the file system on every deploy. Without a volume, uploaded logos, signatures, and stamps will be lost when you redeploy.

1. In your Railway project, click on your **app service** (not the PostgreSQL service)
2. Click the **Volumes** tab
3. Click **Add Volume**
4. Set:
   - **Mount Path:** `/app/static/uploads`
   - **Size:** 1 GB (free tier) or more
5. Click **Create Volume**
6. Railway will redeploy your app with persistent storage

---

### Step 9 — Set Environment Variables

1. Click on your **app service** in Railway
2. Click the **Variables** tab
3. Click **New Variable** and add the following:

**Variable 1 — Secret Key (required)**
- Name: `SECRET_KEY`
- Value: Generate a random value by running this in Command Prompt:
  ```
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Copy the output and paste it as the value.
  Example: `a3f8c2d1e4b7a9f0c3d6e2b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5`

**Variable 2 — Port (optional, Railway sets this automatically)**
- Railway automatically sets `PORT` — you don't need to add this manually.

4. After adding variables, click **Deploy** (or Railway redeploys automatically)

---

### Step 10 — Trigger a Redeploy

1. Click on your **app service**
2. Click the **Deployments** tab
3. Click **Deploy** or wait for the automatic redeploy to finish
4. Watch the deployment logs — look for:
   ```
   Booting worker with pid: ...
   ```
   This means the app is running.

---

## PART 3 — ACCESS YOUR APP

### Step 11 — Get Your App URL

1. Click on your app service in Railway
2. Click the **Settings** tab
3. Under **Domains**, you'll see a URL like:
   `gh-invoice-system-production.up.railway.app`
4. Click **Generate Domain** if no domain is shown
5. Open this URL in your browser

---

### Step 12 — First Login and Setup

1. Open your app URL
2. Log in with:
   - **Username:** `admin`
   - **Password:** `admin123`
3. **IMMEDIATELY** go to → **Change Password** and set a strong password
4. Go to **Companies** and verify GHM, GHT, TRA are listed correctly
5. Go to **Signatories & Stamps** and verify signatures/stamps are shown
6. Go to **Settings** and update bank details if needed
7. Create a test invoice to verify PDF generation works

---

## PART 4 — ONGOING MAINTENANCE

### How to Update the App

When you make changes to the code:

1. Open Command Prompt in your project folder
2. Run:
   ```
   git add .
   git commit -m "Description of what changed"
   git push
   ```
3. Railway automatically detects the push and redeploys

---

### How to View Logs (Troubleshooting)

1. In Railway → your app service → **Deployments** tab
2. Click on the latest deployment
3. Click **View Logs** to see real-time output

Common errors and fixes:

| Error | Fix |
|-------|-----|
| `psycopg2 not found` | Check `requirements.txt` includes `psycopg2-binary` |
| `DATABASE_URL not set` | Add PostgreSQL service to the Railway project |
| `500 Internal Server Error` | Check logs for the exact error message |
| `No such file or directory: uploads/...` | Add a Volume mounted at `/app/static/uploads` |

---

### How to Backup Your Database

1. In Railway → **PostgreSQL** service → **Data** tab
2. Click **Backup** → Railway creates a snapshot
3. You can also use the in-app Backup feature (Admin → Backup Now) to download a zip

---

### Re-uploading Logos and Stamps After First Deploy

Since uploaded images are stored in the Volume (persistent), you only need to do this once:

1. Log in to the app
2. Go to **Companies** → Edit each company → Upload logo and stamp
3. Go to **Signatories & Stamps** → Upload signatures
4. These files are now saved in the Volume and persist across redeploys

---

## QUICK REFERENCE

| What | Where |
|------|-------|
| App URL | Railway → App Service → Settings → Domains |
| Logs | Railway → App Service → Deployments → View Logs |
| DB Backups | Railway → PostgreSQL → Data → Backup |
| Environment Variables | Railway → App Service → Variables |
| Persistent Storage | Railway → App Service → Volumes |
| Redeploy | `git push` from your project folder |

---

## COST ESTIMATE (Railway Pricing as of 2025)

| Plan | Cost | What you get |
|------|------|-------------|
| Hobby | $5/month | 512MB RAM, 1GB disk, PostgreSQL included |
| Pro | $20/month | More resources, team features |

> The Hobby plan is sufficient for normal invoice operations.

---

## SUPPORT

If you encounter issues:
1. Check Railway logs first (Step 12 above)
2. Verify all environment variables are set (Step 9)
3. Confirm the Volume is mounted at `/app/static/uploads` (Step 8)
4. Confirm PostgreSQL service is added to the project (Step 7)

