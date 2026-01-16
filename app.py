from flask import Flask, request, jsonify
import os
import requests
import json
import base64
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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
                'model': 'llama-3.1-sonar-large-128k-online',
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
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Extract JSON from response (Perplexity might return JSON in code blocks)
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0].strip()
            else:
                json_str = content.strip()
            
            data = json.loads(json_str)
            return data
        else:
            return {'error': f'Perplexity API error: {response.status_code}', 'details': response.text}
            
    except Exception as e:
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
        airtable_fields['UPC'] = fields_data['upc']  # Update both UPC fields
    
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
        
        if response.status_code == 200:
            return {'success': True, 'updated_fields': airtable_fields}
        else:
            return {'error': f'Airtable update failed: {response.status_code}', 'details': response.text}
            
    except Exception as e:
        return {'error': str(e)}

@app.route('/webhook/airtable', methods=['POST'])
def airtable_webhook():
    """Handle webhook from Airtable automation"""
    try:
        data = request.json
        record_id = data.get('record_id')
        image_url = data.get('image_url')
        
        if not record_id or not image_url:
            return jsonify({'error': 'Missing required fields: record_id and image_url'}), 400
        
        # Step 1: Analyze the disc image
        analysis_result = analyze_disc_image(image_url)
        
        if 'error' in analysis_result:
            return jsonify({'error': 'Image analysis failed', 'details': analysis_result}), 500
        
        # Step 2: Update Airtable with extracted data
        update_result = update_airtable_record(record_id, analysis_result)
        
        if 'error' in update_result:
            return jsonify({'error': 'Airtable update failed', 'details': update_result}), 500
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'extracted_data': analysis_result,
            'updated_fields': update_result.get('updated_fields', {})
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'ebay-media-reselling-automation'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
