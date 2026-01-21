#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for barcode_intake.py

Tests barcode scanning, condition classification, and intake workflow.
"""

import pytest
from barcode_intake import (
    BarcodeIntake,
    ItemClassifier,
    SKUGenerator,
    IntakeWorkflow,
    ItemCondition,
    MediaType
)


class TestBarcodeIntake:
    """Test suite for BarcodeIntake class."""
    
    def test_scan_valid_upc_a(self):
        """Test scanning valid UPC-A (12 digits)."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('045496508234')
        
        assert result['valid'] is True
        assert result['barcode'] == '045496508234'
        assert result['barcode_type'] == 'UPC-A'
        assert result['duplicate'] is False
        
    def test_scan_valid_ean_13(self):
        """Test scanning valid EAN-13 (13 digits)."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('5901234123457')
        
        assert result['valid'] is True
        assert result['barcode_type'] == 'EAN-13'
        
    def test_scan_valid_upc_e(self):
        """Test scanning valid UPC-E (6 digits)."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('123456')
        
        assert result['valid'] is True
        assert result['barcode_type'] == 'UPC-E'
        
    def test_scan_invalid_non_numeric(self):
        """Test that non-numeric barcodes are rejected."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('ABC123XYZ')
        
        assert result['valid'] is False
        assert 'error' in result
        
    def test_scan_with_whitespace(self):
        """Test that whitespace is trimmed."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('  045496508234  ')
        
        assert result['valid'] is True
        assert result['barcode'] == '045496508234'
        
    def test_duplicate_detection(self):
        """Test duplicate barcode detection."""
        intake = BarcodeIntake()
        
        # First scan
        result1 = intake.scan_barcode('045496508234')
        assert result1['duplicate'] is False
        assert intake.duplicates_detected == 0
        
        # Second scan (duplicate)
        result2 = intake.scan_barcode('045496508234')
        assert result2['duplicate'] is True
        assert intake.duplicates_detected == 1
        
    def test_barcode_history(self):
        """Test that scan history is maintained."""
        intake = BarcodeIntake()
        
        intake.scan_barcode('012569863147')
        intake.scan_barcode('724384960145')
        intake.scan_barcode('045496508234')
        
        assert len(intake.scan_history) == 3
        assert intake.scan_history[0]['barcode'] == '012569863147'
        assert intake.scan_history[2]['barcode'] == '045496508234'


class TestItemClassifier:
    """Test suite for ItemClassifier class."""
    
    def test_classify_with_manual_condition_new(self):
        """Test classification with manual New condition."""
        classifier = ItemClassifier()
        result = classifier.classify_item('045496508234', manual_condition='New')
        
        assert result['condition'] == 'New'
        assert result['condition_source'] == 'manual'
        assert result['sku'] == '045496508234'
        
    def test_classify_with_manual_condition_very_good(self):
        """Test classification with manual Very Good condition."""
        classifier = ItemClassifier()
        result = classifier.classify_item('012569863147', manual_condition='Very Good')
        
        assert result['condition'] == 'Very Good'
        assert result['sku'] == '012569863147-VG'
        
    def test_classify_with_manual_condition_acceptable(self):
        """Test classification with manual Acceptable condition."""
        classifier = ItemClassifier()
        result = classifier.classify_item('724384960145', manual_condition='Acceptable')
        
        assert result['condition'] == 'Acceptable'
        assert result['sku'] == '724384960145-A'
        
    def test_classify_without_condition_defaults_acceptable(self):
        """Test that missing condition defaults to Acceptable."""
        classifier = ItemClassifier()
        result = classifier.classify_item('045496508234')
        
        assert result['condition'] == 'Acceptable'
        assert result['condition_source'] == 'default'
        
    def test_classify_condition_case_insensitive(self):
        """Test that condition parsing is case-insensitive."""
        classifier = ItemClassifier()
        
        result1 = classifier.classify_item('045496508234', manual_condition='vg')
        result2 = classifier.classify_item('012569863147', manual_condition='VERY GOOD')
        result3 = classifier.classify_item('724384960145', manual_condition='disc-only')
        
        assert result1['condition'] == 'Very Good'
        assert result2['condition'] == 'Very Good'
        assert result3['condition'] == 'Acceptable'
        
    def test_classify_unknown_condition_defaults(self):
        """Test that unknown conditions default to Acceptable."""
        classifier = ItemClassifier()
        result = classifier.classify_item('045496508234', manual_condition='Unknown')
        
        assert result['condition'] == 'Acceptable'
        
    def test_classify_unknown_media_type(self):
        """Test that media type is unknown when not provided."""
        classifier = ItemClassifier()
        result = classifier.classify_item('045496508234')
        
        assert result['media_type'] == 'unknown'
        assert result['requires_image_analysis'] is True


class TestSKUGenerator:
    """Test suite for SKU generation."""
    
    def test_generate_sku_new(self):
        """Test SKU generation for New condition."""
        sku = SKUGenerator.generate('045496508234', ItemCondition.NEW, MediaType.VIDEO_GAME)
        assert sku == '045496508234'
        
    def test_generate_sku_very_good(self):
        """Test SKU generation for Very Good condition."""
        sku = SKUGenerator.generate('012569863147', ItemCondition.VERY_GOOD, MediaType.DVD)
        assert sku == '012569863147-VG'
        
    def test_generate_sku_acceptable(self):
        """Test SKU generation for Acceptable condition."""
        sku = SKUGenerator.generate('724384960145', ItemCondition.ACCEPTABLE, MediaType.MUSIC_CD)
        assert sku == '724384960145-A'
        
    def test_generate_sku_different_upcs(self):
        """Test SKU generation with various UPC codes."""
        skus = [
            SKUGenerator.generate('012345678901', ItemCondition.NEW, MediaType.VIDEO_GAME),
            SKUGenerator.generate('112345678902', ItemCondition.VERY_GOOD, MediaType.DVD),
            SKUGenerator.generate('212345678903', ItemCondition.ACCEPTABLE, MediaType.MUSIC_CD),
        ]
        
        assert skus[0] == '012345678901'
        assert skus[1] == '112345678902-VG'
        assert skus[2] == '212345678903-A'


class TestIntakeWorkflow:
    """Test suite for IntakeWorkflow orchestration."""
    
    def test_process_item_valid_flow(self):
        """Test complete valid item intake."""
        workflow = IntakeWorkflow()
        result = workflow.process_item(
            barcode='045496508234',
            manual_condition='Very Good'
        )
        
        assert result['status'] == 'success'
        assert result['barcode'] == '045496508234'
        assert len(result['steps']) > 0
        assert ('barcode_scan', 'success') in result['steps']
        assert ('item_classification', 'success') in result['steps']
        
    def test_process_item_invalid_barcode(self):
        """Test workflow with invalid barcode."""
        workflow = IntakeWorkflow()
        result = workflow.process_item(
            barcode='INVALID',
            manual_condition='Very Good'
        )
        
        assert result['status'] == 'failed'
        assert 'error' in result
        
    def test_process_item_duplicate_detection(self):
        """Test duplicate detection in workflow."""
        workflow = IntakeWorkflow()
        
        # Process same barcode twice
        result1 = workflow.process_item(
            barcode='045496508234',
            manual_condition='Very Good'
        )
        
        result2 = workflow.process_item(
            barcode='045496508234',
            manual_condition='Acceptable'
        )
        
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'
        # Duplicate detected in second call
        assert workflow.barcode_intake.duplicates_detected == 1
        
    def test_process_item_workflow_log(self):
        """Test that workflow maintains processing log."""
        workflow = IntakeWorkflow()
        
        workflow.process_item('045496508234', manual_condition='New')
        workflow.process_item('012569863147', manual_condition='Very Good')
        workflow.process_item('724384960145', manual_condition='Acceptable')
        
        assert len(workflow.workflow_log) == 3
        assert all(log['status'] == 'success' for log in workflow.workflow_log)
        
    def test_process_item_sku_generation(self):
        """Test SKU generation in workflow."""
        workflow = IntakeWorkflow()
        
        result = workflow.process_item(
            barcode='045496508234',
            manual_condition='Very Good'
        )
        
        assert result['classification']['sku'] == '045496508234-VG'
        
    def test_process_item_with_pricing(self):
        """Test workflow with pricing integration."""
        workflow = IntakeWorkflow()
        result = workflow.process_item(
            barcode='045496508234',
            manual_condition='Very Good',
            median_price=20.00
        )
        
        # Note: Pricing integration is mocked in workflow
        assert result['status'] == 'success'


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_very_long_barcode(self):
        """Test handling of unusually long barcode."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('12345678901234567890')
        
        assert result['valid'] is True  # Still valid (numeric)
        assert 'warning' not in result or result['valid']
        
    def test_empty_barcode(self):
        """Test handling of empty barcode."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('')
        
        assert result['valid'] is False
        
    def test_barcode_with_leading_zeros(self):
        """Test that leading zeros are preserved."""
        intake = BarcodeIntake()
        result = intake.scan_barcode('001234567890')
        
        assert result['valid'] is True
        assert result['barcode'] == '001234567890'
        
    def test_multiple_duplicates(self):
        """Test handling of multiple duplicate scans."""
        intake = BarcodeIntake()
        barcode = '045496508234'
        
        # Scan same barcode 5 times
        for _ in range(5):
            intake.scan_barcode(barcode)
        
        # First scan is not a duplicate, next 4 are
        assert intake.duplicates_detected == 4


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_end_to_end_new_item(self):
        """Test complete end-to-end workflow for new item."""
        workflow = IntakeWorkflow()
        result = workflow.process_item(
            barcode='045496508234',
            manual_condition='New'
        )
        
        assert result['status'] == 'success'
        assert result['classification']['sku'] == '045496508234'
        assert result['classification']['condition'] == 'New'
        
    def test_end_to_end_disc_only(self):
        """Test complete end-to-end workflow for disc-only item."""
        workflow = IntakeWorkflow()
        result = workflow.process_item(
            barcode='012569863147',
            manual_condition='Acceptable'
        )
        
        assert result['status'] == 'success'
        assert result['classification']['sku'] == '012569863147-A'
        assert result['classification']['condition'] == 'Acceptable'
        
    def test_mixed_batch_processing(self):
        """Test processing multiple items with different conditions."""
        workflow = IntakeWorkflow()
        
        barcodes_and_conditions = [
            ('045496508234', 'New'),
            ('012569863147', 'Very Good'),
            ('724384960145', 'Acceptable'),
        ]
        
        results = []
        for barcode, condition in barcodes_and_conditions:
            result = workflow.process_item(barcode, manual_condition=condition)
            results.append(result)
        
        assert all(r['status'] == 'success' for r in results)
        assert len(workflow.workflow_log) == 3
        
        # Verify SKUs are correct
        assert results[0]['classification']['sku'] == '045496508234'
        assert results[1]['classification']['sku'] == '012569863147-VG'
        assert results[2]['classification']['sku'] == '724384960145-A'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
