#!/usr/bin/env python3
"""Local test script for end-to-end flow without Telegram.

Usage: python test_flow.py [image_path]
       OR run with no args for stub test
"""
import sys
import json
from pathlib import Path

# Test the complete pipeline
from media_analyzer import analyze_disc_image
from database_lookup import resolve_metadata
from airtable_handler import create_listing
from config import get_config_status
from debug_logging import setup_debug_logger

logger = setup_debug_logger()


def test_with_image(image_path: str):
    """Test pipeline with a real image file."""
    print(f"\n🔍 Testing with image: {image_path}")
    
    # Read image file
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"✓ Loaded image: {len(image_bytes)} bytes")
    except FileNotFoundError:
        print(f"✗ Image file not found: {image_path}")
        return
    
    # Step 1: Analyze
    print("\n1️⃣ Analyzing image...")
    analyzer_result = analyze_disc_image(image_bytes)
    print(f"Result: {json.dumps(analyzer_result, indent=2)}")
    
    if 'error' in analyzer_result:
        print(f"✗ Analysis failed: {analyzer_result['error']}")
        return
    
    # Step 2: Resolve metadata
    print("\n2️⃣ Resolving metadata...")
    media_record = resolve_metadata(analyzer_result)
    print(f"Record: {media_record}")
    print(f"  Title: {media_record.title}")
    print(f"  Type: {media_record.media_type}")
    print(f"  Platform: {media_record.platform}")
    print(f"  Year: {media_record.year}")
    
    # Step 3: Create Airtable listing
    print("\n3️⃣ Creating Airtable listing...")
    airtable_result = create_listing(media_record)
    print(f"Result: {json.dumps(airtable_result, indent=2, default=str)}")
    
    if 'error' in airtable_result:
        print(f"✗ Airtable creation failed: {airtable_result['error']}")
    else:
        print(f"✓ Success! Record ID: {airtable_result.get('record_id')}")


def test_stub_flow():
    """Test pipeline with stub data (no real APIs)."""
    print("\n🤖 Testing with STUB DATA (no API keys needed)")
    
    # Config status
    config = get_config_status()
    print(f"\n🔧 System Status:")
    print(f"  Environment: {config['environment']}")
    print(f"  Using stubs: {config['use_stub_analyzer'] or config['use_stub_lookups']}")
    print(f"  APIs configured:")
    print(f"    - Perplexity: {config['perplexity_ready']}")
    print(f"    - Airtable: {config['airtable_ready']}")
    print(f"    - OMDb: {config['omdb_ready']}")
    print(f"    - IGDB: {config['igdb_ready']}")
    
    # Test with empty bytes (will trigger stub)
    print("\n1️⃣ Analyzing (stub)...")
    analyzer_result = analyze_disc_image(b'')
    print(f"Result: {json.dumps(analyzer_result, indent=2)}")
    
    print("\n2️⃣ Resolving metadata...")
    media_record = resolve_metadata(analyzer_result)
    print(f"  Title: {media_record.title}")
    print(f"  Type: {media_record.media_type.value}")
    print(f"  Platform: {media_record.platform}")
    print(f"  Confidence: {media_record.analyzer_confidence}")
    
    print("\n3️⃣ Creating Airtable listing...")
    airtable_result = create_listing(media_record)
    print(f"Result:")
    print(f"  Success: {airtable_result.get('success')}")
    print(f"  Record ID: {airtable_result.get('record_id')}")
    print(f"  Simulated: {airtable_result.get('simulated')}")
    print(f"  Fields: {len(airtable_result.get('fields', {}))} fields")
    
    print("\n✅ Test complete!")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("eBay Media Reselling Automation - Local Test Flow")
    print("="*60)
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_with_image(image_path)
    else:
        test_stub_flow()
    
    print("\n" + "="*60 + "\n")
