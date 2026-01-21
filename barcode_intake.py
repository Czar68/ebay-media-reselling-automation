#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Barcode Intake Module for eBay Media Reselling

Handles:
- Barcode scanning (UPC/EAN codes)
- Item condition classification
- SKU generation
- Integration with media_analyzer and price_calculator
- Airtable record creation/updates

Condition Classifications:
- UPC (New): Sealed, new condition, original packaging
- UPC-VG (Very Good): Full item with case, disc, cover art, manual
- UPC-A (Acceptable): Disc-only, no case/cover art
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MediaType(Enum):
    """Media type enumeration."""
    VIDEO_GAME = "video_game"
    DVD = "dvd"
    MUSIC_CD = "music_cd"
    UNKNOWN = "unknown"


class ItemCondition(Enum):
    """Item condition enumeration."""
    NEW = "New"
    VERY_GOOD = "Very Good"
    ACCEPTABLE = "Acceptable"


class SKUGenerator:
    """Generate SKU codes based on item characteristics."""
    
    @staticmethod
    def generate(upc: str, condition: ItemCondition, media_type: MediaType) -> str:
        """
        Generate SKU code.
        
        Rules:
        - New items: UPC only
        - Very Good (full): UPC-VG
        - Acceptable (disc-only): UPC-A
        
        Args:
            upc: UPC/EAN barcode
            condition: Item condition
            media_type: Type of media
            
        Returns:
            SKU string
        """
        if condition == ItemCondition.NEW:
            return upc
        elif condition == ItemCondition.VERY_GOOD:
            return f"{upc}-VG"
        elif condition == ItemCondition.ACCEPTABLE:
            return f"{upc}-A"
        else:
            return upc


class BarcodeIntake:
    """Handle barcode scanning and item intake workflow."""
    
    def __init__(self):
        """Initialize barcode intake handler."""
        self.scan_history = []
        self.duplicates_detected = 0
        
    def scan_barcode(self, barcode: str) -> Dict:
        """
        Process barcode scan.
        
        Args:
            barcode: UPC/EAN code (numeric string)
            
        Returns:
            Scan result with validation and duplicate check
        """
        # Validate barcode format
        barcode = barcode.strip()
        
        # UPC-A: 12 digits
        # EAN-13: 13 digits
        # UPC-E: 6 or 8 digits
        if not barcode.isdigit():
            logger.error(f"Invalid barcode format: {barcode}")
            return {
                'valid': False,
                'error': 'Barcode must be numeric',
                'barcode': barcode
            }
            
        if len(barcode) not in [6, 8, 12, 13]:
            logger.warning(f"Unusual barcode length: {len(barcode)} for {barcode}")
        
        # Check for duplicates in current session
        is_duplicate = barcode in [scan['barcode'] for scan in self.scan_history]
        
        if is_duplicate:
            self.duplicates_detected += 1
            logger.warning(f"Duplicate barcode detected: {barcode}")
        
        result = {
            'valid': True,
            'barcode': barcode,
            'timestamp': datetime.now().isoformat(),
            'duplicate': is_duplicate,
            'barcode_type': self._classify_barcode(barcode)
        }
        
        self.scan_history.append(result)
        return result
    
    def _classify_barcode(self, barcode: str) -> str:
        """
        Classify barcode type by length.
        
        Args:
            barcode: Barcode string
            
        Returns:
            Barcode type (UPC-A, EAN-13, UPC-E, etc.)
        """
        length = len(barcode)
        if length == 12:
            return "UPC-A"
        elif length == 13:
            return "EAN-13"
        elif length in [6, 8]:
            return "UPC-E"
        else:
            return f"UNKNOWN_{length}"


class ItemClassifier:
    """Classify items by condition and type."""
    
    def __init__(self):
        """Initialize item classifier."""
        self.media_analyzer = None  # Will be set by external module
        
    def classify_item(self, 
                     barcode: str, 
                     image_url: Optional[str] = None,
                     manual_condition: Optional[str] = None) -> Dict:
        """
        Classify item based on condition and media type.
        
        Classification workflow:
        1. If manual_condition provided → Use that
        2. Else if image available → Analyze with media_analyzer
        3. Else → Default to ACCEPTABLE
        
        Args:
            barcode: UPC/EAN code
            image_url: Optional image URL for Perplexity analysis
            manual_condition: Manual condition override (New/Very Good/Acceptable)
            
        Returns:
            Classification result with condition, media_type, and SKU
        """
        # Step 1: Determine condition
        if manual_condition:
            condition = self._parse_condition(manual_condition)
            source = "manual"
        elif image_url:
            # Would call media_analyzer to determine from image
            # For now: placeholder
            condition = ItemCondition.ACCEPTABLE
            source = "image_analysis"
        else:
            # Default to disc-only (Acceptable)
            condition = ItemCondition.ACCEPTABLE
            source = "default"
        
        # Step 2: Determine media type
        if image_url and self.media_analyzer:
            # Would call media_analyzer.analyze_image(image_url)
            # For now: placeholder
            media_type = MediaType.UNKNOWN
        else:
            media_type = MediaType.UNKNOWN
        
        # Step 3: Generate SKU
        sku = SKUGenerator.generate(barcode, condition, media_type)
        
        return {
            'barcode': barcode,
            'sku': sku,
            'condition': condition.value,
            'media_type': media_type.value,
            'condition_source': source,
            'requires_image_analysis': media_type == MediaType.UNKNOWN,
            'classification_timestamp': datetime.now().isoformat()
        }
    
    def _parse_condition(self, condition_str: str) -> ItemCondition:
        """
        Parse condition string to ItemCondition enum.
        
        Args:
            condition_str: Condition string
            
        Returns:
            ItemCondition enum value
        """
        condition_lower = condition_str.lower().strip()
        
        if condition_lower == "new":
            return ItemCondition.NEW
        elif condition_lower in ["very good", "vg"]:
            return ItemCondition.VERY_GOOD
        elif condition_lower in ["acceptable", "disc-only", "disc only"]:
            return ItemCondition.ACCEPTABLE
        else:
            logger.warning(f"Unknown condition: {condition_str}, defaulting to ACCEPTABLE")
            return ItemCondition.ACCEPTABLE


class IntakeWorkflow:
    """Orchestrate complete barcode intake workflow."""
    
    def __init__(self, airtable_handler=None, media_analyzer=None, price_calculator=None):
        """
        Initialize workflow.
        
        Args:
            airtable_handler: AirtableHandler instance
            media_analyzer: MediaAnalyzer instance
            price_calculator: PriceCalculator instance
        """
        self.barcode_intake = BarcodeIntake()
        self.classifier = ItemClassifier()
        self.classifier.media_analyzer = media_analyzer
        self.airtable_handler = airtable_handler
        self.media_analyzer = media_analyzer
        self.price_calculator = price_calculator
        self.workflow_log = []
        
    def process_item(self,
                    barcode: str,
                    image_url: Optional[str] = None,
                    manual_condition: Optional[str] = None,
                    median_price: Optional[float] = None) -> Dict:
        """
        Complete intake workflow for a single item.
        
        Steps:
        1. Scan and validate barcode
        2. Classify item condition and type
        3. Call media_analyzer if needed
        4. Calculate pricing
        5. Create/update Airtable record
        6. Return result
        
        Args:
            barcode: UPC/EAN code
            image_url: Optional image URL
            manual_condition: Optional manual condition override
            median_price: Optional median price for pricing calculation
            
        Returns:
            Complete workflow result
        """
        workflow_start = datetime.now()
        result = {
            'status': 'pending',
            'barcode': barcode,
            'steps': []
        }
        
        try:
            # Step 1: Scan barcode
            logger.info(f"Step 1: Scanning barcode {barcode}")
            scan_result = self.barcode_intake.scan_barcode(barcode)
            if not scan_result['valid']:
                result['status'] = 'failed'
                result['error'] = scan_result['error']
                return result
            result['steps'].append(('barcode_scan', 'success'))
            
            # Step 2: Classify item
            logger.info(f"Step 2: Classifying item {barcode}")
            classification = self.classifier.classify_item(
                barcode, 
                image_url=image_url,
                manual_condition=manual_condition
            )
            result['steps'].append(('item_classification', 'success'))
            result['classification'] = classification
            
            # Step 3: Analyze image if needed
            if classification['requires_image_analysis'] and image_url and self.media_analyzer:
                logger.info(f"Step 3: Analyzing image for {barcode}")
                # media_analysis = self.media_analyzer.analyze_image(image_url)
                # result['steps'].append(('image_analysis', 'success'))
                # result['media_analysis'] = media_analysis
                pass
            
            # Step 4: Calculate pricing if median price provided
            if median_price and self.price_calculator:
                logger.info(f"Step 4: Calculating pricing for {barcode}")
                pricing = self.price_calculator.calculate_best_offer_prices(
                    self.price_calculator.calculate_list_price(median_price, 0.10)
                )
                result['steps'].append(('pricing_calculation', 'success'))
                result['pricing'] = pricing
            
            # Step 5: Create Airtable record
            if self.airtable_handler:
                logger.info(f"Step 5: Creating Airtable record for {barcode}")
                # record = self.airtable_handler.create_record({
                #     'UPC': barcode,
                #     'SKU': classification['sku'],
                #     'Condition': classification['condition'],
                #     'MediaType': classification['media_type']
                # })
                # result['steps'].append(('airtable_create', 'success'))
                # result['airtable_record_id'] = record['id']
                pass
            
            result['status'] = 'success'
            result['workflow_duration_seconds'] = (datetime.now() - workflow_start).total_seconds()
            
        except Exception as e:
            logger.exception(f"Workflow error for barcode {barcode}")
            result['status'] = 'error'
            result['error'] = str(e)
        
        self.workflow_log.append(result)
        return result


def main():
    """Demonstrate barcode intake workflow."""
    # Example usage
    logger.info("Starting Barcode Intake Demo")
    
    # Initialize workflow
    workflow = IntakeWorkflow()
    
    # Example 1: Valid barcode with condition
    logger.info("\n=== Example 1: Video Game Full Item ===")
    result1 = workflow.process_item(
        barcode="045496508234",
        manual_condition="Very Good"
    )
    print(json.dumps(result1, indent=2))
    
    # Example 2: DVD disc-only
    logger.info("\n=== Example 2: DVD Disc-Only ===")
    result2 = workflow.process_item(
        barcode="012569863147",
        manual_condition="Acceptable"
    )
    print(json.dumps(result2, indent=2))
    
    # Example 3: New item
    logger.info("\n=== Example 3: New CD ===")
    result3 = workflow.process_item(
        barcode="724384960145",
        manual_condition="New"
    )
    print(json.dumps(result3, indent=2))
    
    # Example 4: Duplicate detection
    logger.info("\n=== Example 4: Duplicate Detection ===")
    result4 = workflow.process_item(
        barcode="045496508234",
        manual_condition="Very Good"
    )
    print(json.dumps(result4, indent=2))
    print(f"\nTotal duplicates detected: {workflow.barcode_intake.duplicates_detected}")


if __name__ == '__main__':
    main()
