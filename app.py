"""
eBay Media Reselling Automation - Flask API
Automated disc image analysis with Perplexity AI integration
Integrates with Airtable for inventory management and Telegram bot for disc scanning
"""
from flask import Flask, request, jsonify
import os
import requests
import json
import base64
from dotenv import load_dotenv
from json_utils import extract_json_safe, extract_json_from_response
from debug_logging import setup_debug_logger, log_api_response, log_json_extraction, log_error_context
from bot import handle_update
from config import get_config_status

load_dotenv()
app = Flask(__name__)

# Initialize debug logger
debug_logger = setup_debug_logger()

# Environment variables
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'appN23V9vthSoYGe6')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'eBay Listings')


def analyze_disc_image(image_url):
    """Use Perplexity API to extract structured data from disc image"""
    
    prompt = """Analyze this video game disc image and extract the following information in JSON format:
{
 "game_title": "The exact game title from the disc",
 "platform": "Gaming platform (Xbox One, PS4, PS5, Xbox 360, PS3, Nintendo Switch, Wii, Wii U, etc.)",
 "upc": "UPC/Barcode number if visible on disc or case (numbers only, no spaces)",
 "publisher": "Game publisher name",
 "esrb_rating": "ESRB rating (E, E10+, T, M, AO, RP)",
 "year": "Copyright or release year if visible",
 "condition_notes": "Note if disc appears scratched, pristine, or has visible damage",
 "disc_art_description": "Brief description of the artwork on the disc",
 "ebay_title": "Create an optimized eBay title under 80 characters with format: [Game Title] - [Platform] - [Key Feature/Edition] - Disc Only",
 "website_title": "Create a descriptive title for a website: [Game Title] for [Platform] - [Publisher] ([Year])",
 "keywords": ["list", "of", "relevant", "eBay", "search", "keywords"]
}
If any field is not visible or determinable, use null for that field. Be precise and extract exact text from the disc."""
    try:
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'sonar-pro',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {'type': 'image_url', 'image_url': {'url': image_url}}
                        ]
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 1000
            },
            timeout=30
        )
        log_api_response(response.status_code, response.json(), '/chat/completions')
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Log extraction attempt
            log_json_extraction(content, "Perplexity API response")
            
            # Use the robust JSON extraction utility
            data = extract_json_safe(content, {})
            
            if data:
                log_json_extraction(data, "extract_json_safe", success=True)
                return data
            else:
                log_json_extraction(content, "extract_json_safe", error="Could not parse JSON")
                return {'error': 'Could not extract JSON from API response'}
        else:
            log_error_context('APIError', f'Perplexity API returned {response.status_code}', 
                {'status_code': response.status_code, 'response': response.text})
            return {'error': f'Perplexity API error: {response.status_code}', 'details': response.text}
    except Exception as e:
        log_error_context('AnalysisException', str(e), {'image_url': image_url})
        return {'error': str(e)}


def update_airtable_record(record_id, fields_data):
    """Update Airtable record with extracted data"""
    
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}'
    
    # Map extracted data to Airtable fields
    airtable_fields = {}
    
    if fields_data.get('ebay_title'):
        airtable_fields['Title'] = fields_data['ebay_title']
    
    if fields_data.get('upc'):
        airtable_fields['UPC/Barcode'] = fields_data['upc']
        airtable_fields['UPC'] = fields_data['upc'] # Update both UPC fields
    
    if fields_data.get('platform'):
        airtable_fields['Platform'] = fields_data['platform']
    
    if fields_data.get('game_title') or fields_data.get('website_title'):
        # Store full game info in Notes field for reference
        notes = []
        if fields_data.get('game_title'):
            notes.append(f"Game: {fields_data['game_title']}")
        if fields_data.get('website_title'):
            notes.append(f"Website Title: {fields_data['website_title']}")
        if fields_data.get('publisher'):
            notes.append(f"Publisher: {fields_data['publisher']}")
        if fields_data.get('year'):
            notes.append(f"Year: {fields_data['year']}")
        if fields_data.get('esrb_rating'):
            notes.append(f"Rating: {fields_data['esrb_rating']}")
        if fields_data.get('keywords'):
            notes.append(f"Keywords: {', '.join(fields_data['keywords'])}")
        
        airtable_fields['Notes'] = '\n'.join(notes)
    
    # Set Media Type to Video Game
    airtable_fields['Media Type'] = 'Video Game'
    
    # Set Condition to Disc Only (assuming from the images)
    airtable_fields['Condition'] = 'Disc Only'
    
    try:
        response = requests.patch(
            url,
            headers={
                'Authorization': f'Bearer {AIRTABLE_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={'fields': airtable_fields},
            timeout=10
        )
        
        log_airtable_update(AIRTABLE_TABLE_NAME, record_id, airtable_fields, 
            success=(response.status_code == 200))
        
        if response.status_code == 200:
            return {'success': True, 'updated_fields': airtable_fields}
        else:
            log_error_context('AirtableError', f'Airtable returned {response.status_code}',
                {'record_id': record_id, 'response': response.text})
            return {'error': f'Airtable update failed: {response.status_code}', 'details': response.text}
        
    except Exception as e:
        log_error_context('AirtableException', str(e), {'record_id': record_id})
        return {'error': str(e)}


def log_airtable_update(table_name, record_id, fields, success=False):
    """Log Airtable update (wrapper for consistency)"""
    debug_logger.debug(f"Airtable Update: {table_name} - Record {record_id}")
    debug_logger.debug(f"Fields being updated: {list(fields.keys())}")
    if success:
        debug_logger.debug(f"✓ Successfully updated {record_id}")
    else:
        debug_logger.debug(f"✗ Failed to update {record_id}")


# =============================================================================
# Legacy Airtable Webhook (Phase 1 compatibility) - IMPROVED ROBUSTNESS
# =============================================================================
@app.route('/webhook/airtable', methods=['POST'])
def airtable_webhook():
    """Handle webhook from Airtable automation - supports both JSON and form-encoded"""
    
    try:
        # Log the incoming request for debugging
        debug_logger.info(f"Webhook received - Content-Type: {request.content_type}")
        debug_logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Handle both JSON and form-encoded payloads
        if request.is_json:
            data = request.json
            debug_logger.debug(f"Parsed JSON payload: {data}")
        elif request.form:
            data = request.form.to_dict()
            debug_logger.debug(f"Parsed form payload: {data}")
        else:
            # Try to parse raw data as JSON
            try:
                data = json.loads(request.data.decode('utf-8'))
                debug_logger.debug(f"Parsed raw JSON payload: {data}")
            except:
                log_error_context('WebhookException', 'Could not parse request body', 
                    {'content_type': request.content_type, 'data': request.data.decode('utf-8', errors='ignore')})
                return jsonify({'error': 'Invalid request format. Expected JSON or form data.'}), 400
        
        # Extract required fields
        record_id = data.get('record_id')
        image_url = data.get('image_url')
        
        debug_logger.info(f"Webhook processing - Record: {record_id}, Image URL: {image_url}")
        
        if not record_id or not image_url:
            log_error_context('WebhookException', 'Missing required fields',
                {'record_id': record_id, 'image_url': image_url})
            return jsonify({'error': 'Missing required fields: record_id and image_url'}), 400
        
        # Step 1: Analyze the disc image
        debug_logger.info(f"Starting image analysis for record {record_id}")
        analysis_result = analyze_disc_image(image_url)
        
        if 'error' in analysis_result:
            log_error_context('AnalysisError', 'Image analysis failed',
                {'record_id': record_id, 'error': analysis_result.get('error')})
            return jsonify({'error': 'Image analysis failed', 'details': analysis_result}), 500
        
        debug_logger.debug(f"Analysis successful: {list(analysis_result.keys())}")
        
        # Step 2: Update Airtable with extracted data
        debug_logger.info(f"Updating Airtable record {record_id}")
        update_result = update_airtable_record(record_id, analysis_result)
        
        if 'error' in update_result:
            log_error_context('UpdateError', 'Airtable update failed',
                {'record_id': record_id, 'error': update_result.get('error')})
            return jsonify({'error': 'Airtable update failed', 'details': update_result}), 500
        
        debug_logger.info(f"✓ Successfully processed webhook for record {record_id}")
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'extracted_data': analysis_result,
            'updated_fields': update_result.get('updated_fields', {})
        }), 200
        
    except Exception as e:
        log_error_context('WebhookException', str(e), {'request_data': request.data.decode('utf-8', errors='ignore')})
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Telegram Bot Webhook (Phase 1 MVP)
# =============================================================================
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Handle incoming Telegram bot updates via webhook"""
    try:
        update_data = request.json
        debug_logger.info(f"Received Telegram update: {update_data.get('update_id')}")
        
        # Process the update (delegate to bot module)
        result = handle_update(update_data)
        
        # Always return 200 to Telegram to acknowledge receipt
        return jsonify({'success': True}), 200
    except Exception as e:
        debug_logger.error(f"Error processing Telegram update: {str(e)}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Health Check and Status Endpoints
# =============================================================================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'ebay-media-reselling-automation'}), 200


@app.route('/status', methods=['GET'])
def status_endpoint():
    """Check configuration and API readiness status"""
    config = get_config_status()
    return jsonify(config), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
