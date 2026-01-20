# ebay-media-reselling-automation
Automated eBay media reselling tool with AI-powered UPC/EPID research for disc-only items


## Documentation

This project includes comprehensive documentation for development, deployment, and troubleshooting:

- **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API endpoint documentation with examples
  - POST /webhook/airtable - Main webhook for disc image analysis
  - GET /health - Service health check
  - Request/response formats with TypeScript examples
  - Environment variables and deployment info

- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions
  - Make.com integration issues
  - JSON parsing failures
  - Airtable field mapping problems
  - Render free tier behavior
  - Testing procedures and monitoring

- **app.py** - Inline code documentation
  - Service description and dependencies
  - API endpoint documentation
  - Environment variables required
  - Known issues and improvement recommendations

## Quick Start

1. **Deploy to Render:**
   - Connect GitHub repository
   - Set environment variables (PERPLEXITY_API_KEY, AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
   - Service auto-deploys on push to main

2. **Configure Make.com:**
   - Create Airtable Watch Records trigger
   - Add HTTP module pointing to webhook URL
   - Map record data and connect to Airtable Update module

3. **Test the workflow:**
   - Add test record to Airtable with disc image
   - Run Make.com scenario manually
   - Verify Airtable record updates with extracted data

## Architecture

```
Airtable (Data) 
    ↓
Make.com (Orchestration)
    ↓
Render Flask API (Processing)
    ↓
Perplexity AI (Image Analysis)
    ↓
Airtable (Results)
```

**Data Flow:**
1. New/updated record in Airtable triggers Make.com
2. Make.com extracts record ID and attachment URL
3. Flask API receives webhook from Make.com
4. Perplexity AI analyzes disc image
5. Extracted data mapped to Airtable fields
6. Airtable record updated with results

## Project Status

✅ Core functionality implemented  
✅ API deployed and tested  
✅ Make.com integration configured  
⚠️ Scenario currently INACTIVE (needs manual activation)  
📝 Comprehensive documentation added  

## Next Steps

1. Activate Make.com scenario when ready to process items
2. Add test listing to Airtable and verify workflow
3. Monitor initial executions for any issues
4. Refer to TROUBLESHOOTING.md if problems occur
5. Scale up processing as needed
