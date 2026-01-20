# Deployment Checklist

Before activating the eBay Media Reselling automation, verify all items in this checklist.

## Pre-Activation Verification

### Infrastructure & Deployment
- [ ] Flask API deployed to Render.com
- [ ] Render health check confirms service is healthy: `GET /health`
- [ ] Environment variables set in Render dashboard:
  - [ ] `PERPLEXITY_API_KEY` - Valid Perplexity AI API key
  - [ ] `AIRTABLE_API_KEY` - Valid Airtable personal access token
  - [ ] `AIRTABLE_BASE_ID` - Correct base ID (appN23V9vthSoYGe6)
  - [ ] `AIRTABLE_TABLE_NAME` - Set to "eBay Listings"
- [ ] Latest code deployed from GitHub (auto-deploy enabled)

### API Verification
- [ ] Test health endpoint manually:
  ```bash
  curl https://ebay-media-reselling-automation.onrender.com/health
  ```
  Expected response: `{"status": "healthy", "service": "ebay-media-reselling-automation"}`

- [ ] Test webhook endpoint with sample data in Make.com HTTP module
  - [ ] HTTP node "Test" button shows successful response
  - [ ] Response includes `extracted_data` object

### Airtable Setup
- [ ] eBay Listings table exists with all required fields:
  - [ ] Title (Single line text)
  - [ ] Notes (Long text)
  - [ ] Status (Single select) - Options include "In progress" and "Analyzed"
  - [ ] Attachments (Attachment field)
  - [ ] UPC/Barcode (Single line text)
  - [ ] UPC (Barcode field)
  - [ ] Media Type (Single select)
  - [ ] Platform (Single select)
  - [ ] Condition (Single select)
  - [ ] Listing Status (Single select)
  - [ ] Cost Basis (Currency)
  - [ ] Sale Price (Currency)
  - [ ] Other fields as needed

- [ ] Airtable API token has proper permissions:
  - [ ] Can read records
  - [ ] Can write/update records
  - [ ] Has access to eBay Media Reselling base

### Make.com Configuration
- [ ] Airtable Watch Records trigger configured:
  - [ ] Base: "eBay Media Reselling"
  - [ ] Table: "eBay Listings"
  - [ ] Trigger field: "Last Modified Time"
  - [ ] Correctly detects new/modified records

- [ ] HTTP module configured correctly:
  - [ ] URL: `https://ebay-media-reselling-automation.onrender.com/webhook/airtable`
  - [ ] Method: POST
  - [ ] Content-Type: application/json
  - [ ] Request body maps correctly:
    ```
    {"record_id": "{{1.ID}}", "image_url": "{{1.Attachments[1].URL}}"}
    ```

- [ ] Airtable Update Record module configured:
  - [ ] Correct Base selected: "eBay Media Reselling"
  - [ ] Correct Table selected: "eBay Listings"
  - [ ] Record ID mapped to: `{{1.ID}}`
  - [ ] Field mappings correct:
    - [ ] Title ← `{{2.extracted_data.ebay_title}}`
    - [ ] Status ← "Analyzed"
    - [ ] UPC/Barcode ← `{{2.extracted_data.upc}}`
    - [ ] Platform ← `{{2.extracted_data.platform}}`
    - [ ] Notes ← `{{2.extracted_data}}`  (if using concatenation)

### Integration Testing
- [ ] Create test record in Airtable:
  - [ ] Add new row to eBay Listings table
  - [ ] Upload test disc image (clear, well-lit photo)
  - [ ] Note the Record ID for reference

- [ ] Test webhook manually:
  - [ ] Go to Make.com scenario
  - [ ] Click HTTP module "Test" button
  - [ ] Verify no errors in execution log
  - [ ] Response shows extracted data from image

- [ ] Test full workflow:
  - [ ] Go to Make.com scenario
  - [ ] Click "Run" to manually trigger scenario
  - [ ] Check Airtable record - verify fields updated:
    - [ ] Title populated with eBay title
    - [ ] Status changed to "Analyzed"
    - [ ] UPC field filled (if barcode visible)
    - [ ] Platform detected correctly
  - [ ] If any field is empty, check:
    - [ ] Image quality sufficient for AI analysis
    - [ ] Field mapping in Make.com module
    - [ ] Render logs for errors

## Pre-Activation Configuration

### Make.com Scenario Schedule
- [ ] Scenario schedule configured:
  - [ ] Trigger type: "Every 15 minutes"
  - [ ] OR: Use "Last Modified Time" trigger for immediate processing
  - [ ] Verify no conflicting schedules

- [ ] Error handling configured:
  - [ ] "Return error if HTTP request fails" is enabled
  - [ ] Timeout set appropriately (30+ seconds)
  - [ ] Retry logic configured (recommended: 1-2 retries)

### Monitoring Setup (Optional but Recommended)
- [ ] Set up alerts for:
  - [ ] Make.com execution failures
  - [ ] Render service downtime
  - [ ] API quota warnings

- [ ] Create monitoring dashboard:
  - [ ] Make.com scenario execution history
  - [ ] Airtable record update frequency
  - [ ] Render logs and error tracking

## Activation Steps

1. **Final Verification**
   - [ ] All checklist items above completed
   - [ ] Test record processed successfully
   - [ ] No errors in any system logs

2. **Activate Scenario**
   - [ ] Open Make.com scenario
   - [ ] Toggle scenario from "Inactive" to "Active"
   - [ ] Verify status shows "Active"
   - [ ] Check execution history begins updating

3. **Monitor Initial Executions**
   - [ ] Watch first 3-5 executions in Make.com history
   - [ ] Check Airtable for successful updates
   - [ ] Review Render logs for any errors
   - [ ] Monitor Make.com credit usage

4. **Document Issues**
   - [ ] If errors occur, note:
     - [ ] Error message
     - [ ] Timestamp
     - [ ] Record/image that failed
     - [ ] Steps to reproduce
   - [ ] Refer to TROUBLESHOOTING.md for solutions

## Post-Activation

### First 24 Hours
- [ ] Monitor execution success rate (target: 95%+)
- [ ] Verify field updates are accurate
- [ ] Check for data quality issues
- [ ] Monitor Make.com credit usage
- [ ] Review Render logs daily

### Ongoing Maintenance
- [ ] Weekly: Review Make.com execution history
- [ ] Weekly: Check Render logs for warnings
- [ ] Monthly: Monitor API usage and costs
- [ ] Monthly: Review extracted data quality
- [ ] As needed: Update field mappings or prompts

## Rollback Plan

If critical issues arise, quickly:

1. **Pause Processing:**
   - Go to Make.com scenario
   - Click toggle to turn off
   - Verify status shows "Inactive"

2. **Assess Issue:**
   - Check Render logs for errors
   - Review Make.com execution history
   - Check Airtable for partial updates

3. **Identify Root Cause:**
   - Is it Perplexity API error?
   - Is it Airtable connectivity?
   - Is it Make.com configuration?
   - Refer to TROUBLESHOOTING.md

4. **Fix Issue:**
   - Update environment variables if needed
   - Fix Make.com module configuration
   - Test webhook again before reactivating
   - Commit code changes to GitHub

5. **Resume Processing:**
   - Test with one record manually
   - Once confirmed working, reactivate scenario

## Success Criteria

Workflow is considered **successfully deployed** when:

✅ Scenario runs without errors for 24+ hours  
✅ 90%+ of records update successfully  
✅ Extracted data is accurate and complete  
✅ No manual intervention required  
✅ Processing time < 30 seconds per record  
✅ Airtable fields populate consistently  
✅ Make.com credits used as expected  

## Support Resources

- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API documentation
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions
- [app.py](./app.py) - Inline code documentation
- Make.com Docs: https://www.make.com/en/help
- Airtable Docs: https://support.airtable.com/
- Perplexity Docs: https://www.perplexity.ai/

---

**Last Updated:** January 20, 2026  
**Status:** Ready for Activation  
**Next Action:** Complete checklist and activate scenario
