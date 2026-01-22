# Dependency Audit & Optimization

## Current requirements.txt Analysis

### Status of Each Dependency

| Package | Version | Used? | Status | Note |
|---------|---------|-------|--------|------|
| flask | 3.0.0 | ✅ YES | Current | Core web framework; fine to keep |
| python-dotenv | 1.0.0 | ✅ YES | Current | Loads .env files; essential |
| requests | 2.31.0 | ✅ YES | Current | HTTP client for Perplexity, eBay, Airtable APIs |
| gunicorn | 21.2.0 | ✅ YES | Current | Production WSGI server; use on Render |
| Pillow | 11.0.0 | ⚠️ MAYBE | Current | Image processing; used if OCR added later |
| airtable-python-wrapper | 0.15.3 | ✅ YES | ⚠️ DEPRECATED | Wrapper is unmaintained; consider switch to raw requests |
| python-telegram-bot | 20.7 | ✅ YES | Current | Telegram bot integration; well-maintained |
| selenium | 4.15.2 | ✅ YES | Transition | Browser automation; replacing with eBay API in Phase 2 |
| beautifulsoup4 | 4.12.2 | ✅ YES | Transition | HTML parsing for Selenium; can remove in Phase 2 |
| click | 8.1.7 | ⚠️ MAYBE | Current | CLI tool framework; used if you add CLI commands |
| colorama | 0.4.6 | ⚠️ MAYBE | Current | Terminal colors; cosmetic only |

---

## Recommended Optimizations

### Priority 1: Keep (Essential)

✅ **Keep these packages:**
- flask==3.0.0
- requests==2.31.0
- python-dotenv==1.0.0
- gunicorn==21.2.0
- python-telegram-bot==20.7

**Reason:** Core MVP functionality

### Priority 2: Monitor (Deprecation Risk)

⚠️ **airtable-python-wrapper==0.15.3**
- **Status:** Unmaintained (last update 2 years ago)
- **Options:**
  - Option A: Switch to raw `requests` calls (simplest)
  - Option B: Use `pyairtable` (newer maintained fork)

**Recommendation:** Stick with current for MVP; switch in Phase 2 if issues arise.

**If switching now:**
```python
# Current (wrapper)
from airtable import Airtable
ai = Airtable(base_id, table_name, api_key)
record = ai.update(record_id, {'field': 'value'})

# Replacement (raw requests)
import requests
response = requests.patch(
    f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"fields": {"field": "value"}}
)
```

### Priority 3: Transition (Replacing)

🔄 **Selenium + BeautifulSoup (Phase 2 removal)**
- selenium==4.15.2: Replace with eBay API
- beautifulsoup4==4.12.2: Remove when Selenium goes

**Timeline:** Keep through MVP, remove in Phase 2

### Priority 4: Optional (Nice-to-Have)

❓ **click==8.1.7**
- Used if you create CLI commands (e.g., `python cli.py scan-upc`)
- Currently NOT used
- **Action:** Remove if no CLI planned

❓ **colorama==0.4.6**
- Terminal colors for logging
- Cosmetic only
- **Action:** Remove to reduce bloat

❓ **Pillow==11.0.0**
- Image processing library
- Currently NOT used (you use Perplexity API for image analysis)
- **Action:** Remove for MVP; add back if you implement local OCR

---

## Optimized requirements.txt (MVP)

### Minimal (Phase 1)

```
# Core Framework
flask==3.0.0
gunicorn==21.2.0

# Configuration
python-dotenv==1.0.0

# HTTP Client
requests==2.31.0

# Integrations
python-telegram-bot==20.7
airtable-python-wrapper==0.15.3

# Scraping (Phase 2 removal)
selenium==4.15.2
beautifulsoup4==4.12.2
```

**Total packages:** 8  
**Total size:** ~50MB (with dependencies)

### Lean (Aggressive)

If you want to minimize immediately:

```
flask==3.0.0
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
python-telegram-bot==20.7
airtable-python-wrapper==0.15.3
```

**Remove:** selenium, beautifulsoup4  
**Tradeoff:** Breaks current Selenium scraping until eBay API is integrated

---

## Version Compatibility Checks

**Run locally to verify:**

```bash
# Create fresh venv
python -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Test imports
python -c "from flask import Flask; from selenium import webdriver; from airtable import Airtable; print('All OK')"

# Check for conflicts
pip check  # Warns if version conflicts
```

### Known Version Issues

**None identified** for your current requirements.txt.

All versions are compatible with Python 3.11+.

---

## Installation Size Analysis

```
Package                  | Size | Purpose
------------------------+------+----------
selenium                 | 18MB | Web driver (remove in Phase 2)
beautifulsoup4           | 3MB  | HTML parsing (remove in Phase 2)
requests                 | 2MB  | HTTP client
python-telegram-bot      | 1.5MB | Telegram
pillow                   | 6MB  | Image processing (not used yet)
gunicorn                 | 0.5MB | WSGI server
flask                    | 1MB  | Web framework
airtable-python-wrapper | 0.1MB | Airtable wrapper
python-dotenv           | 0.1MB | ENV loader
click                    | 0.2MB | CLI (not used)
colorama                 | 0.1MB | Colors (not used)
```

**Current total:** ~32MB (with all deps)  
**After Selenium removal:** ~14MB  
**Lean version:** ~10MB

---

## Deployment Recommendations

### For Render

1. **Keep current requirements.txt as-is for MVP**
   - Render builds fast enough
   - Selenium is needed until eBay API ready
   - No need to optimize size yet

2. **When Phase 2 arrives:**
   - Replace selenium + beautifulsoup4 with ebay_api_wrapper
   - Drop unused packages (click, colorama)
   - New requirements.txt will be ~10MB

3. **Build command stays:**
   ```
   pip install -r requirements.txt
   ```

### Version Pinning Strategy

**Current approach (recommended):** Exact pinning (`package==X.Y.Z`)
- Ensures reproducible builds
- Avoids breaking changes

**Do NOT use:** Loose ranges (`package>=X.Y`)
- Will cause non-reproducible builds
- Can break deployment unexpectedly

---

## Future: Automated Dependency Updates

### Option 1: Dependabot (GitHub)

1. Enable in GitHub repo
2. Automatic PRs for updates
3. Review and merge manually

### Option 2: pip-audit

```bash
pip install pip-audit
pip-audit  # Check for vulnerabilities
```

### Option 3: Manual quarterly review

Simplest for MVP:
- Every 3 months, check: `pip list --outdated`
- Review changelogs
- Test in staging
- Commit updates

---

## Checklist

- [ ] Run `pip install -r requirements.txt` locally
- [ ] Run `pip check` to verify no conflicts
- [ ] Run `python app.py` to verify all imports work
- [ ] Test `/health` endpoint (curl)
- [ ] Verify `selenium` works with current version
- [ ] Approve current requirements.txt for MVP
- [ ] Plan Selenium removal for Phase 2
- [ ] Document optional packages to remove: click, colorama, Pillow

---

## Recommended Action

**For MVP: No changes needed.**

Current requirements.txt is solid. Optimizations can happen in Phase 2 when you:
1. Replace Selenium with eBay API
2. Remove BeautifulSoup4
3. Drop unused packages (click, colorama)
