from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Environment variables from .env
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'appN23V9vthSoYGe6')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'eBay Listings')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
EBAY_APP_ID = os.getenv('EBAY_APP_ID')

@app.route('/webhook/airtable', methods=['POST'])
def airtable_webhook():
    """Handle new record from Airtable automation"""
    try:
        data = request.json
        record_id = data.get('record_id')
        title = data.get('title', '')
        media_type = data.get('media_type', '')
        
        if not record_id or not title:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Step 1: Research UPC
        upc = research_upc(title, media_type)
        
        # Step 2: Find eBay EPID
        epid = find_ebay_epid(title, upc) if upc else None
        
        # Step 3: Get market value
        market_value = get_market_value(title) if epid else 0
        
        # Step 4: Update Airtable record
        update_data = {
            'Status': 'UPC Found' if upc else 'UPC Research Needed'
        }
        if upc:
            update_data['UPC/Barcode'] = upc
        if epid:
            update_data['eBay EPID'] = epid
            update_data['Status'] = 'Ready to List'
        if market_value:
            update_data['Market Value'] = market_value
            
        update_airtable_record(record_id, update_data)
        
        return jsonify({
            'success': True,
            'upc': upc,
            'epid': epid,
            'market_value': market_value
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def research_upc(title, media_type):
    """Use Perplexity AI to find UPC"""
    try:
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [{
                "role": "user",
                "content": f"Find the UPC barcode number for this {media_type}: {title}. Return ONLY the UPC number with no additional text."
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            # Extract just the UPC number
            upc = ''.join(filter(str.isdigit, content))
            return upc if len(upc) in [12, 13] else None
    except:
        pass
    return None

def find_ebay_epid(title, upc):
    """Use Perplexity AI to find eBay EPID"""
    try:
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        search_query = f"{title} UPC {upc}" if upc else title
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [{
                "role": "user",
                "content": f"Find the eBay EPID (eBay Product ID / catalog ID) for: {search_query}. Return ONLY the numeric EPID."
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            epid = ''.join(filter(str.isdigit, content))
            return epid if epid else None
    except:
        pass
    return None

def get_market_value(title):
    """Get average market value from eBay completed listings"""
    try:
        url = "https://svcs.ebay.com/services/search/FindingService/v1"
        params = {
            'OPERATION-NAME': 'findCompletedItems',
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': EBAY_APP_ID,
            'RESPONSE-DATA-FORMAT': 'JSON',
            'keywords': title,
            'itemFilter(0).name': 'SoldItemsOnly',
            'itemFilter(0).value': 'true',
            'sortOrder': 'EndTimeSoonest'
        }
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            search_result = data.get('findCompletedItemsResponse', [{}])[0]
            items = search_result.get('searchResult', [{}])[0].get('item', [])
            
            if items:
                prices = [
                    float(item['sellingStatus'][0]['currentPrice'][0]['__value__'])
                    for item in items[:10]
                    if 'sellingStatus' in item
                ]
                return round(sum(prices) / len(prices), 2) if prices else 0
    except:
        pass
    return 0

def update_airtable_record(record_id, fields):
    """Update Airtable record with research results"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {"fields": fields}
    response = requests.patch(url, json=payload, headers=headers, timeout=30)
    return response.status_code == 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
