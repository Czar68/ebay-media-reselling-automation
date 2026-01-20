# Troubleshooting Guide

## Overview
This guide helps diagnose and resolve common issues with the eBay Media Reselling Automation system.

## Common Issues & Solutions

### 1. Make.com Scenario Shows "Error" Status

**Symptoms:**
- Make.com execution history shows red "Error" badges
- Airtable records are not being updated
- Make.com dashboard shows high error rate

**Possible Causes:**
- Render service is down or unreachable
- Webhook URL is incorrect or has changed
- Missing or invalid API keys (PERPLEXITY_API_KEY, AIRTABLE_API_KEY)
- Airtable attachment URLs are broken or expired

**Solutions:**
1. **Check Render health:**
   ```bash
   curl https://ebay-media-reselling-automation.onrender.com/health
   ```
   Expected response: `{"status": "healthy", "service": "ebay-media-reselling-automation"}`

2. **Verify webhook URL in Make.com:**
   - Go to Make.com scenario > HTTP node > URL field
   - Should be: `https://ebay-media-reselling-automation.onrender.com/webhook/airtable`
   - If you changed domains, update the URL

3. **Check environment variables in Render:**
   - Dashboard > Web Service > Environment
   - Verify PERPLEXITY_API_KEY is set
   - Verify AIRTABLE_API_KEY is set
   - Verify AIRTABLE_BASE_ID matches your base

4. **Test webhook manually in Make.com:**
   - Click "Test" on HTTP node with sample data
   - Watch the execution logs for detailed error messages

---

### 2. "Could not extract JSON from API response"

**Symptoms:**
- Error message in Make.com execution logs
- Perplexity API appears to respond but JSON parsing fails

**Possible Causes:**
- Perplexity returned unexpected response format
- Image quality too poor for model to analyze
- Timeout occurred during processing

**Solutions:**
1. **Check image quality:**
   - Ensure disc image is clear and well-lit
   - Try with different image formats (JPEG, PNG)
   - Verify image URL is still accessible

2. **Increase timeout in Flask:**
   - In app.py, find the Perplexity API call (line ~50)
   - Increase `timeout=30` to `timeout=60` seconds
   - Commit and redeploy to Render

3. **Check Perplexity API status:**
   - Visit https://status.perplexity.ai/ to check for outages
   - Verify API key has not been revoked

---

### 3. Airtable Fields Not Updating

**Symptoms:**
- Record in Airtable remains unchanged after webhook execution
- Make.com shows success but Airtable is empty

**Possible Causes:**
- Record ID is incorrect or malformed
- Airtable API key lacks update permissions
- Field names in Make.com don't match Airtable schema

**Solutions:**
1. **Verify record ID format:**
   - In Airtable, right-click record and copy record ID
   - Should look like: `rec123ABC456def`
   - Make sure it's being passed correctly from Make.com

2. **Check Airtable permissions:**
   - Verify token has `data.records:write` scope
   - Token should have access to the specific base
   - Generate new token if unsure

3. **Validate field mappings in Make.com:**
   - Go to Airtable Update node in Make.com
   - Verify field names match exactly (case-sensitive):
     - Title (not title)
     - Notes (not notes)
     - Status (not status)
     - UPC/Barcode (exact special characters)

---

### 4. Render Free Tier Spinning Down

**Symptoms:**
- First request after inactivity is very slow
- Service takes 30-50 seconds to respond
- Services on free tier occasionally unavailable

**Why it happens:**
- Render free tier services spin down after 15 minutes of inactivity
- First request wakes the service (called "cold start")
- Subsequent requests are fast

**Solutions:**
1. **Accept the behavior:**
   - This is normal for free tier
   - Make.com runs every 15 minutes, so should keep service warm

2. **Upgrade to paid tier:**
   - Upgrade your Render service to avoid spin-down
   - Cost: ~$7/month for basic instance

3. **Use external monitoring:**
   - Set up a cron job to ping `/health` every 10 minutes
   - Keeps service warm and logs to Render

---

### 5. Make.com Scenario is Inactive

**Symptoms:**
- Make.com scenario shows toggle as "OFF"
- No executions appear in history

**Solutions:**
1. **Activate the scenario:**
   - Go to Make.com scenario dashboard
   - Click the toggle to turn it ON
   - Should show "Active" status

2. **Check schedule:**
   - Should be set to "Every 15 minutes"
   - Verify trigger is set to "Last Modified Time" in Airtable

---

### 6. JSON Parsing Fails with Regex Pattern

**Symptoms:**
- Error: "Could not extract JSON from API response"
- Regex pattern doesn't match Perplexity output

**Why it happens:**
- Perplexity sometimes wraps JSON in markdown code blocks
- Sometimes returns raw JSON
- Formatting varies based on model and prompt

**Solution:**
- The app.py handles multiple formats (see lines 70-85)
- If still failing, check Make.com execution logs for exact response
- May need to add additional regex pattern

---

## Testing Your Setup

### Step 1: Health Check
```bash
curl https://ebay-media-reselling-automation.onrender.com/health
# Expected: {"status": "healthy", "service": "ebay-media-reselling-automation"}
```

### Step 2: Test Webhook in Make.com
1. Open Make.com scenario
2. Click HTTP node
3. Click "Test" button
4. Should show success response with extracted_data

### Step 3: Full Integration Test
1. Add a test record to Airtable with disc image
2. Note the record ID
3. Manually trigger Make.com scenario
4. Check if Airtable record updates within 30 seconds

---

## Log Files & Monitoring

### Render Logs
- Dashboard > Web Service > Logs
- Shows Flask app output and errors
- Useful for debugging API issues

### Make.com Execution History
- Make.com > Scenario > History tab
- Shows each execution with input/output
- Click execution to see detailed request/response

### Airtable Activity
- Base > Tools > Activity
- Shows all changes to records
- Can trace when/if updates occur

---

## Performance Tips

1. **Optimize image sizes:**
   - Compress images before uploading
   - Large images increase processing time

2. **Monitor Make.com credits:**
   - Each execution costs ~2 credits
   - Check usage dashboard periodically
   - Current usage: ~4-5 executions per hour

3. **Handle failures gracefully:**
   - Make.com should retry on error
   - Check "Return error if HTTP request fails" is enabled
   - Set reasonable timeout values

---

## Getting Help

1. **Check GitHub Issues** (if any)
   - Common problems may be documented

2. **Review app.py documentation:**
   - Comments at end of file explain architecture
   - Error handling logic documented

3. **Test components in isolation:**
   - Test Perplexity API directly
   - Test Airtable API directly
   - Test Make.com webhook with dummy data
