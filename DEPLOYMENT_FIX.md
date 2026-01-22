# Render Deployment Troubleshooting Guide

## 7-Step Deployment Fix Procedure

### Step 1: Check Render Logs for Build/Runtime Failures

**Location:** Render Dashboard → Your Service → "Logs" tab

**What to look for:**

```
✗ Build Failed: "ModuleNotFoundError: No module named 'xyz'"
✗ Runtime Error: "SyntaxError in app.py line 42"
✗ Port binding error: "Address already in use"
```

**Action:**
- Scroll through build and runtime logs
- Identify the FIRST error (failures often cascade)
- Note the exact error message and line number
- Screenshot or copy the full error

**Common Build Errors:**

```
ERROR: Could not find a version that satisfies the requirement
→ Fix: Check requirements.txt syntax and version constraints

ImportError: cannot import name 'X' from 'module_y'
→ Fix: Verify import paths match your file structure

No module named 'requests'
→ Fix: Add package to requirements.txt
```

---

### Step 2: Verify requirements.txt Installation

**Action Items:**

1. **Check syntax:**
   - Each line should be one package: `package==version` or `package>=version`
   - No blank lines between entries (optional comments with `#` are OK)
   - Example valid format:
     ```
     flask==3.0.0
     requests==2.31.0
     # Database
     airtable-python-wrapper==0.15.3
     ```

2. **Verify in Render Dashboard:**
   - Go to "Settings" → "Build Command"
   - Should include: `pip install -r requirements.txt`
   - Confirm this line is present

3. **Test locally:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
   - If this fails locally, it will fail on Render

**Common issues:**
- Typo in package name (e.g., `guicorn` instead of `gunicorn`)
- Version conflict (e.g., two packages requiring incompatible versions of a dependency)
- Private packages that require authentication

---

### Step 3: Verify Python Version, PORT Binding, and Start Command

**Action Items:**

1. **Set Python version:**
   - Render Dashboard → Settings → "Environment"
   - Add: `PYTHON_VERSION=3.11` (or 3.10, 3.12 as needed)
   - Recommended: 3.11 for best compatibility

2. **Verify PORT binding:**
   - Your `app.py` should include:
     ```python
     port = int(os.environ.get('PORT', 5000))
     app.run(host='0.0.0.0', port=port)
     ```
   - This allows Render to inject `PORT=10000` (or whatever it assigns)

3. **Check start command:**
   - Render Dashboard → Settings → "Start Command"
   - Should be ONE of:
     ```
     python app.py                          # Simple Flask (dev mode)
     gunicorn app:app                       # Production (recommended for MVP)
     gunicorn --bind 0.0.0.0:$PORT app:app # Explicit bind
     ```
   - **Recommendation:** Use `gunicorn app:app` for MVP

**Apply changes:**
- Make changes in Render Dashboard
- Trigger manual deploy: "Settings" → "Deploy" button
- OR push new code to GitHub (if auto-deploy enabled)

---

### Step 4: Verify `/health` and `/status` Endpoints Respond

**What these do:**
- `/health`: Simple "I'm alive" check (used by Render's health probes)
- `/status`: Detailed config/API readiness check

**From your app.py:**
```python
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'ebay-media-reselling-automation'}), 200

@app.route('/status', methods=['GET'])
def status_endpoint():
    config = get_config_status()
    return jsonify(config), 200
```

**Test endpoints:**

1. **Get your Render URL:**
   - Render Dashboard → "Logs" or "Overview"
   - Look for: `<your-service>.onrender.com`

2. **Test health check:**
   ```bash
   curl https://<your-service>.onrender.com/health
   ```
   - Expected response: `{"status": "healthy", ...}`
   - Status code: `200`

3. **Test status endpoint:**
   ```bash
   curl https://<your-service>.onrender.com/status
   ```
   - Should show which environment variables are loaded
   - Should indicate if eBay/Airtable/Telegram keys are present

**If endpoints fail:**
- Check Render logs for error at `/health` call
- Verify Flask app is actually running (check "Processes" in Render dashboard)
- Manually trigger a redeploy

---

### Step 5: Verify Environment Variables

**Critical vars for MVP:**

```
EBAY_APP_ID=<your_app_id>
EBAY_CERT_ID=<your_client_secret>
EBAY_DEV_ID=<your_user_id>
AIRTABLE_API_KEY=<your_airtable_token>
AIRTABLE_BASE_ID=appN23V9vthSoYGe6  (or your base ID)
PERPLEXITY_API_KEY=<your_perplexity_key>
TELEGRAM_BOT_TOKEN=<your_telegram_token>
```

**Action Items:**

1. **In Render Dashboard:**
   - Go to your service → "Environment"
   - Add each env var as a key-value pair
   - Do NOT use quotes around values

2. **Verify vars are loaded:**
   - Test `/status` endpoint
   - Should show which keys are present/missing
   - Example output:
     ```json
     {
       "ebay_configured": true,
       "airtable_configured": true,
       "perplexity_configured": true,
       "telegram_configured": false,
       "errors": ["TELEGRAM_BOT_TOKEN missing"]
     }
     ```

3. **Check for typos:**
   - Env var names are case-sensitive
   - In Render: `EBAY_APP_ID` (all caps)
   - In Python code: `os.getenv('EBAY_APP_ID')`

**Secret Management:**
- Never commit `.env` files to GitHub
- Always use Render's "Environment" section for secrets
- For local testing: create `.env` file (add to `.gitignore`)

---

### Step 6: Check Flask/Gunicorn Configuration

**Common Flask Misconfigs:**

1. **Missing imports:**
   ```python
   from flask import Flask, request, jsonify  # These must be present
   app = Flask(__name__)  # Initialize Flask app
   ```

2. **Blueprint registration (if using blueprints):**
   ```python
   from my_module import my_blueprint
   app.register_blueprint(my_blueprint)  # Must register before running
   ```

3. **Incorrect app export for Gunicorn:**
   - Gunicorn expects: `gunicorn app:app`
   - This means: import `app` from `app.py`, use the `app` object
   - Your app.py MUST have: `app = Flask(__name__)`

**Test Gunicorn locally:**
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
# Should print: "Listening on 0.0.0.0:5000"
```

**If Gunicorn fails:**
- Check app.py for syntax errors (run `python app.py` first)
- Verify all imports work (`python -c "from app import app"`)
- Check for circular imports

---

### Step 7: Post-Fix Verification Checklist

After making changes, verify each of these:

- [ ] **Build succeeds:** Render Dashboard → "Logs" shows no build errors
- [ ] **App starts:** Logs show "Listening on 0.0.0.0:PORT" or similar
- [ ] **Health endpoint responds:** `curl .../health` returns 200
- [ ] **Status endpoint shows config:** `/status` lists loaded env vars
- [ ] **No lingering errors in logs:** Scan logs for last 5 minutes, confirm no ERROR messages
- [ ] **Webhook is reachable:** Test with `/telegram-webhook` or `/webhook/airtable` (use POST)
- [ ] **Airtable writes work:** Trigger a test record update, check Airtable base
- [ ] **Telegram webhook receives updates:** Send test message to bot, check Render logs for webhook call

---

## Deployment Prevention Best Practices

**To avoid future deployment issues:**

1. **Test locally first:**
   ```bash
   pip install -r requirements.txt
   python app.py  # or gunicorn app:app
   curl http://localhost:5000/health
   ```

2. **Use a staging environment on Render:**
   - Create a second service for staging
   - Test code changes there before merging to main

3. **Set up auto-deploy cautiously:**
   - GitHub → Settings → Deployments
   - Only auto-deploy from `main` branch after testing
   - Keep a manual approval step for critical changes

4. **Version pinning:**
   - Always pin exact versions in requirements.txt: `package==X.Y.Z`
   - Avoid `package>=X.Y` (can introduce breaking changes)
   - Test version upgrades in staging before deploying to production

5. **Keep logs available:**
   - Export Render logs weekly for reference
   - Use `curl https://<url>/status` as a heartbeat check (cron job)
   - Set up alerts if health checks start failing

---

## Quick Reference: Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'X'` | Package not in requirements.txt | Add to requirements.txt, redeploy |
| `SyntaxError in app.py` | Typo or misformatted Python | Fix code, test locally, push |
| `Address already in use` | Port binding conflict | Ensure PORT env var is used |
| `ImportError: cannot import name 'Y'` | Wrong import path or module not installed | Check import statement, add to requirements.txt |
| `gunicorn: command not found` | Gunicorn not installed | Add `gunicorn==21.2.0` to requirements.txt |
| Webhook never called | URL incorrect or not reachable | Verify URL in bot/Airtable config, test with curl |
| 502 Bad Gateway | App crashed after startup | Check recent logs, look for errors after "Listening" |

---

## Next Steps

1. Run through all 7 steps above
2. Collect specific error messages/logs
3. Share logs in our next session for detailed diagnosis
4. Once deployment is stable, proceed to eBay API integration
