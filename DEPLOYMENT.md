# Aureta Digital deployment guide (macOS)

This project is an **independent financial software demonstration platform**. Every displayed balance and transaction is simulated sample data. It is not a bank, it does not move real money, and it must never be used as proof of funds.

This guide is written for a first deployment from macOS using:

- GitHub for source control
- Neon for PostgreSQL
- Render for the public Django web service

**Status of this repository:** the application is prepared for deployment. A public URL, Neon database, Render service, custom domain, and production email provider exist only after *you* create them and verify they work. This file does not claim those accounts are already configured.

Prices below were checked against official documentation on 24 October 2026. Providers change plans. Confirm on the linked pages before you rely on a free tier.

## 0. What this stack is, and what free tiers are not

| Service | Official docs | Typical starter cost | Important limits |
|---|---|---|---|
| Render web service | [render.com/docs/free](https://render.com/docs/free), [render.com/pricing](https://render.com/pricing) | **$0** on the Free compute plan (Hobby workspace is $0/month + compute) | Free web services **spin down after 15 minutes without inbound traffic**. Wake-up can take about **one minute**. Each workspace gets **750 Free instance hours / month**. Storage is **ephemeral** (never store the database on the web service). Paid web compute currently starts around **$7/month**. |
| Neon PostgreSQL | [neon.com/pricing](https://neon.com/pricing), [Free plan limits](https://neon.com/faqs/free-plan-limits-and-quotas) | **$0** on the Free plan | **100 CU-hours / project / month**, **1 GB storage / project** (20 GB account-wide), **5 GB** public network transfer / project / month. Compute **scales to zero after 5 minutes of inactivity** on the Free plan and that cannot be disabled. Hitting compute or transfer limits **suspends compute until the next month or an upgrade**. Storage limits reject writes; they do not promise that data stays available forever. Instant restore history on Free is short (currently **6 hours**, capped). |
| GitHub | [github.com/pricing](https://github.com/pricing) | **$0** for public or private repos on Free | Fine for this project. GitHub does not host the Django process. |
| Optional custom domain | Your registrar | Often **$10–$20 / year** | You buy this separately. Render can issue HTTPS after DNS is correct. Do not assume a domain is connected until you have tested it. |
| Future paid hosting | Render / Neon paid plans | Render from ~**$7/month** compute; Neon Launch is usage-based (compute + about **$0.35/GB-month** storage per current docs) | Paid plans reduce sleep, raise limits, and add backup/restore options. They are still not an SLA unless the provider states one. |

**Do not assume free services stay free, stay awake, or keep data indefinitely.** Use Neon exports if you care about the demonstration records.

Migrations must run as a **controlled release step**, not as part of the process that starts Gunicorn, and not twice.

Suggested split:

- **Build:** install dependencies and collect static files
- **Pre-deploy / release:** `migrate` once, then `createcachetable`
- **Start:** Gunicorn only

## 1. Inspect and prepare the project on your Mac

```bash
cd /Users/kavanalabsuser/Developments/aureta_digital
python3.13 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Generate a local secret and put it in `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Keep local `.env` values similar to:

```
SECRET_KEY=the-key-you-just-generated
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
DATABASE_URL=
```

Leave `DATABASE_URL` empty locally to use SQLite. Production on Render must use Neon PostgreSQL.

```bash
python manage.py migrate
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/ and confirm registration, dashboard, and the simulated-funds disclosure. Local email uses the **console backend** (`DEBUG=True`): password-reset messages print in the terminal.

## 2. GitHub repository

This folder already has a Git working tree. Create a GitHub repository (private is fine), then:

```bash
cd /Users/kavanalabsuser/Developments/aureta_digital
git add .
git status   # confirm .env is not listed
git commit -m "Prepare Aureta Digital for Render and Neon."
git branch -M main
git remote add origin https://github.com/YOUR_USER/aureta_digital.git
git push -u origin main
```

Never commit `.env`, Neon credentials, or Render API keys. `.gitignore` excludes virtualenvs, `.env`, SQLite files, and `staticfiles/`.

Later changes deploy when you `git push` if Render is connected to this GitHub repo (usually the `main` branch).

## 3. Create a Neon PostgreSQL database

1. Sign in at [https://neon.tech/](https://neon.tech/).
2. Create a project (one project is enough).
3. Create a database if the default `neondb` is not the name you want.
4. Open **Dashboard → Connection details**.
5. Copy the connection string for an application role. Prefer the pooled connection if Neon shows one for serverless/web apps.
6. Confirm the URI includes SSL, for example `sslmode=require`.

Store that string in a password manager. Do not paste it into Git, screenshots, issue trackers, or frontend JavaScript.

### Backups and restore (Neon)

On the Free plan, restore options are limited (short instant restore window and a small number of manual snapshots). Before a risky change:

1. In the Neon console, create a **branch** or a **manual snapshot** if your plan allows it.
2. Or export from your laptop:

```bash
brew install libpq
# pg_dump is in libpq; PATH may need /opt/homebrew/opt/libpq/bin
pg_dump "$DATABASE_URL" --no-owner --format=custom --file aureta.dump
```

Restore into a new database only when you intend to replace data:

```bash
pg_restore --clean --no-owner --dbname="$DATABASE_URL" aureta.dump
```

`--clean` drops objects in the target. Never run destructive restore commands against production unless you mean to replace it.

## 4. Create the Render web service

1. Sign in at [https://render.com/](https://render.com/).
2. **New → Web Service**.
3. Connect the GitHub repository and the `main` branch.
4. Runtime: **Python**.
5. Instance type: **Free** if you are staying on the $0 budget.
6. Commands:

   - **Build command:**  
     `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Pre-deploy command** (Render’s release step; run migrations here only):  
     `bash scripts/release.sh`  
     which runs `python manage.py migrate --noinput` and `python manage.py createcachetable`
   - **Start command:**  
     `gunicorn config.wsgi:application`

   Do **not** put `migrate` in the start command. That can run migrations twice or start the app before a migration has been reviewed.

7. Health check path: `/health/`
8. Create the service, then add environment variables before the first successful boot if the first deploy failed on missing config.

Render assigns a URL such as `https://aureta-digital.onrender.com`. HTTPS is provided by Render for that subdomain.

### Render free-tier behaviour you will notice

- First request after idle time can hang on Render’s loading page while the service wakes.
- Files written on the instance disappear after restart or sleep. That is why SQLite is not used in production.
- If the workspace exhausts free instance hours or bandwidth without a payment method, Free services can be suspended until the next month.

## 5. Production environment variables

Set these in **Render → your service → Environment**. Values are examples; replace them.

| Variable | Production value |
|---|---|
| `SECRET_KEY` | Unique Django secret. Generate with `get_random_secret_key()`. Never reuse the local key if it was committed or shared. |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `aureta-digital.onrender.com` (add your custom domain later, comma-separated, no `https://`) |
| `CSRF_TRUSTED_ORIGINS` | `https://aureta-digital.onrender.com` (full origins, including `https://`) |
| `DATABASE_URL` | Neon URI with `sslmode=require` |
| `EMAIL_HOST` | Your SMTP host, or leave empty to keep the console backend (password reset will not reach users) |
| `EMAIL_PORT` | `587` unless your provider says otherwise |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password / app password |
| `EMAIL_USE_TLS` | `True` |
| `DEFAULT_FROM_EMAIL` | `Aureta Digital <noreply@yourdomain>` |

The application **refuses to start** in production if `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, or `DATABASE_URL` is missing, or if `SECRET_KEY` is a known insecure placeholder.

After variables are saved, trigger a **manual deploy**.

## 6. Initialize the production database

The pre-deploy command creates tables. It does **not** delete data (`migrate` is forward-only here; there is no `flush` or `reset`).

If you need a Django admin user, use Render **Shell** after the service is live:

```bash
python manage.py createsuperuser
```

That user is for administration of the demonstration app only.

## 7. Open the public URL and test

Wait for the deploy to show **Live**, then:

1. Open `https://YOUR-SERVICE.onrender.com/health/` — JSON `{"status":"ok",...}`.
2. Open the homepage. Confirm the simulated-funds disclosure.
3. Register with your name, email, and a password of at least 10 characters.
4. On the dashboard, confirm **Available balance — simulated funds** shows `$56,075,294.00 USD`.
5. Sign out, sign in again, refresh, and confirm the **same stored balance** (it must not reset).
6. Open **Activity**, search a sample description such as `Payroll`, and confirm only your rows appear.
7. Request a password reset. If SMTP is not configured, this still shows a generic “check your email” page and does not reveal whether the address is registered.

If the first request is slow, wait for Render and Neon to wake. That is expected on free tiers.

## 8. Custom domain later

Do not purchase or point a domain until you choose one.

1. In Render: **Settings → Custom Domains → Add**.
2. At your registrar, create the records Render shows. Common patterns:
   - Apex (`example.com`): `A` or `ALIAS`/`ANAME` as Render instructs
   - `www`: `CNAME` to the Render hostname
3. Wait for DNS. Render then provisions a certificate.
4. Update environment variables (do not hardcode the domain in Python):

```
ALLOWED_HOSTS=aureta-digital.onrender.com,example.com,www.example.com
CSRF_TRUSTED_ORIGINS=https://aureta-digital.onrender.com,https://example.com,https://www.example.com
```

5. Redeploy or restart so Django reloads settings.
6. Visit `https://example.com` and confirm the certificate is valid.

You can keep the Render subdomain working at the same time. To switch away from it later, remove it from `ALLOWED_HOSTS` only after the custom domain is verified.

## 9. Logs, troubleshooting, and operations

- **Render logs:** service → Logs. Look for Gunicorn boot, missing env vars, or migration errors.
- **Health check failing:** `/health/` does not query the database, so a 502 is usually a crash on startup (bad `SECRET_KEY`, missing `DATABASE_URL`, collectstatic/migrate failure).
- **CSRF failures:** `CSRF_TRUSTED_ORIGINS` must be HTTPS origins that match the browser URL.
- **Disappearing balances:** you are on SQLite or another ephemeral disk. Production must use `DATABASE_URL` on Neon.
- **Sleep / cold start:** Render idle spin-down and Neon scale-to-zero. First request after a pause can be slow.
- **Duplicate migrate:** remove `migrate` from the start command if it is also in pre-deploy.

Local production-style check (does not deploy anything):

```bash
DEBUG=False SECRET_KEY='your-production-like-key' \
ALLOWED_HOSTS=example.onrender.com \
CSRF_TRUSTED_ORIGINS=https://example.onrender.com \
DATABASE_URL='postgres://user:pass@localhost:5432/db' \
python manage.py check --deploy
```

## 10. Verification checklist

- [ ] `python manage.py test` passes locally
- [ ] `.env` is not in Git
- [ ] GitHub `main` contains this source
- [ ] Neon project exists and the URI uses SSL
- [ ] Render build, pre-deploy, and start commands match section 4
- [ ] `DEBUG=False` on Render
- [ ] `/health/` returns 200
- [ ] Registration creates one demo account
- [ ] Dashboard label reads **Available balance — simulated funds**
- [ ] Initial simulated figure is `$56,075,294.00 USD`
- [ ] Balance is unchanged after logout/login
- [ ] Users cannot see another user’s account number or sample transactions
- [ ] Persistent disclosure states that funds are fictional
- [ ] Password reset does not disclose whether an email is registered
- [ ] Custom domain left unset until you add DNS and update hosts/origins
- [ ] You have not treated this UI as a real bank statement

## Development email vs production email

- **Local / `DEBUG=True`:** Django console backend. Reset links appear in the `runserver` terminal.
- **Production:** set `EMAIL_HOST` and related variables to a real SMTP provider (for example a transactional email service). Until those are set, the app keeps the console backend so it still boots; users will not receive mail.

## Application server

Production WSGI path:

```text
gunicorn config.wsgi:application
```

The Django project package is `config`.
