# Monitoring & Observability Setup Guide

## Overview

Production monitoring for MVP: Render logs + application-level structured logging. No external SaaS required initially.

---

## Tier 1: Built-In Render Monitoring

### 1. Render Logs Dashboard

**Access:** Render Service Dashboard → "Logs" tab

**What it captures:**
- Build output (deployment)
- Runtime output (stdout/stderr)
- Crash messages
- Environment variable loading

**Best for:** Immediate troubleshooting, deployment issues

### 2. Render Health Checks

**Built-in:**
- Render automatically pings `/health` endpoint every 30 seconds
- If 3 consecutive checks fail, service is marked "unhealthy"
- Trigger: service restart or alert (if configured)

**Your endpoint (from app.py):**
```python
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200
```

### 3. Metrics Render Collects

- **CPU Usage:** % of allocated CPU
- **Memory Usage:** MB used
- **Requests:** Total count
- **Response Time:** Median latency
- **Errors (5xx):** Count

**View in:** Render Dashboard → "Metrics" tab

---

## Tier 2: Application-Level Structured Logging

### Implement Logging in app.py

```python
import logging
import json
from datetime import datetime

# Structured logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StructuredLogger:
    @staticmethod
    def log_request(endpoint: str, method: str, params: dict):
        """Log incoming request"""
        logger.info(json.dumps({
            "event": "request",
            "endpoint": endpoint,
            "method": method,
            "params": str(params)[:200],  # Truncate for privacy
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    @staticmethod
    def log_api_call(service: str, endpoint: str, status: int, latency_ms: float):
        """Log external API call"""
        logger.info(json.dumps({
            "event": "api_call",
            "service": service,
            "endpoint": endpoint,
            "status": status,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    @staticmethod
    def log_error(error_type: str, message: str, context: dict):
        """Log error with context"""
        logger.error(json.dumps({
            "event": "error",
            "error_type": error_type,
            "message": message,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }))
```

### Usage in Routes

```python
from time import time

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        start = time()
        update_data = request.json
        
        StructuredLogger.log_request("/telegram-webhook", "POST", {"update_id": update_data.get('update_id')})
        
        result = handle_update(update_data)
        latency = (time() - start) * 1000
        
        StructuredLogger.log_api_call("telegram", "/webhook", 200, latency)
        return jsonify({'success': True}), 200
    
    except Exception as e:
        StructuredLogger.log_error("TelegramWebhookException", str(e), {"update": str(update_data)[:200]})
        return jsonify({'error': str(e)}), 500
```

---

## Tier 3: Key Metrics to Track

### Request Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate (5xx) | > 5% in 5 min | Alert: check logs |
| p95 Latency | > 2000ms | Check eBay/Airtable API |
| Request Count | < 1/min (sustained) | Service might be crashed |
| 429 Rate Limits | > 2/hour | API quota issue |

### Application Metrics

```python
# Track at startup
logger.info(json.dumps({
    "event": "startup",
    "config_loaded": {
        "ebay_configured": bool(os.getenv('EBAY_APP_ID')),
        "airtable_configured": bool(os.getenv('AIRTABLE_API_KEY')),
        "perplexity_configured": bool(os.getenv('PERPLEXITY_API_KEY')),
        "telegram_configured": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
    },
    "timestamp": datetime.utcnow().isoformat()
}))

# Track API usage
api_calls_count = 0
api_errors_count = 0

def track_api_call(success: bool):
    global api_calls_count, api_errors_count
    api_calls_count += 1
    if not success:
        api_errors_count += 1
    
    # Log every 100 calls
    if api_calls_count % 100 == 0:
        logger.info(json.dumps({
            "event": "api_stats",
            "total_calls": api_calls_count,
            "errors": api_errors_count,
            "error_rate": f"{(api_errors_count/api_calls_count)*100:.1f}%"
        }))
```

---

## Tier 4: Simple Health Check Script

**File:** `health_check.py` (run via cron job)

```python
#!/usr/bin/env python3
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

SERVICE_URL = "https://your-service.onrender.com"
CHECK_INTERVAL = 300  # 5 minutes

def check_health():
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            print(f"✓ Service healthy at {datetime.now()}")
            return True
        else:
            print(f"✗ Service returned {response.status_code}")
            send_alert(f"Health check failed: {response.status_code}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"✗ Service timeout at {datetime.now()}")
        send_alert("Service timeout")
        return False
    
    except Exception as e:
        print(f"✗ Check failed: {e}")
        send_alert(f"Check failed: {e}")
        return False

def send_alert(message: str):
    """Send email alert (requires config)"""
    # Placeholder: implement with your email provider
    # or Telegram bot
    pass

if __name__ == "__main__":
    check_health()
```

**Setup cron job (runs every 5 minutes):**
```bash
*/5 * * * * /usr/bin/python3 /path/to/health_check.py >> /var/log/health_check.log 2>&1
```

---

## Tier 5: Log Export & Analysis

### Export Logs Weekly

**Manual (via Render Dashboard):**
1. Go to Logs tab
2. Set date range (last 7 days)
3. Click "Download" button (if available)
4. Save to local archive

**Automated (via Render API):**
```bash
# Get your API token from Render
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-xxxxx/logs?limit=10000 \
  > logs-2026-01-22.json
```

### Analyze Logs

```bash
# Count errors
grep '"event": "error"' logs-*.json | wc -l

# Find slowest requests
grep '"event": "request"' logs-*.json | jq '.latency_ms' | sort -rn | head -10

# API failures by service
grep '"event": "api_call"' logs-*.json | jq '.service, .status' | sort | uniq -c
```

---

## Alert Strategy (MVP)

### Option A: Telegram Bot Alerts

**Pro:** Instant notification to your phone  
**Con:** Requires Telegram bot setup

```python
import requests

def send_telegram_alert(message: str):
    """Send alert via Telegram"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('ALERT_CHAT_ID')  # Your personal chat ID
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": f"🚨 Alert: {message}"
    })
```

### Option B: Email Alerts

**Pro:** No additional setup  
**Con:** Slower response

```python
import smtplib

def send_email_alert(message: str):
    """Send alert via email"""
    # Requires SMTP credentials in env
    pass
```

### Option C: Render Native Alerts

**Pro:** Built-in integration  
**Con:** Limited customization

1. Render Dashboard → Notifications
2. Add email for alerts
3. Render sends notification on service crash

---

## Monitoring Checklist

**Week 1 (Deployment):**
- [ ] Verify `/health` endpoint responds
- [ ] Check Render Logs tab works
- [ ] Enable structured logging in app.py
- [ ] Deploy health_check.py locally

**Week 2 (Validation):**
- [ ] Review last 7 days of logs
- [ ] Identify any errors or timeouts
- [ ] Measure average latency
- [ ] Set up cron job for health checks

**Week 3 (Optimization):**
- [ ] Analyze error patterns
- [ ] Optimize slowest endpoints
- [ ] Add alerts to Telegram or email
- [ ] Export and archive logs

---

## Future: Advanced Monitoring (Phase 2)

When scaling beyond MVP:

- **Better Stack** (free tier): Log aggregation + parsing
- **Sentry** (free tier): Error tracking + source maps
- **DataDog** or **New Relic**: Full observability ($ but comprehensive)
- **Prometheus + Grafana:** Self-hosted metrics + dashboards

**For now:** Render logs + structured logging is sufficient.
