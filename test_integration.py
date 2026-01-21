#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for complete workflow

Tests end-to-end flows combining barcode intake, pricing, and eBay listing.
"""

import pytest
import json
from price_calculator import PriceCalculator, MIN_PROFIT_MARGIN
from barcode_intake import IntakeWorkflow, ItemCondition
from datetime import datetime


class TestPricingWorkflowIntegration:
    """Integration tests for pricing with item intake."""
    
    def test_video_game_full_complete_workflow(self):
        """Test complete workflow: intake → pricing → margin check."""
        # Phase 1: Intake
        workflow = IntakeWorkflow()
        intake_result = workflow.process_item(
            barcode='045496508234',
            manual_condition='Very Good'
        )
        
        assert intake_result['status'] == 'success'
        sku = intake_result['classification']['sku']
        assert sku == '045496508234-VG'
        
        # Phase 2: Pricing
        calc = PriceCalculator('video_game', 'Very Good', cog=1.00)
        median_price = 35.00
        list_price = calc.calculate_list_price(median_price, 0.10)
        offers = calc.calculate_best_offer_prices(list_price)
        
        # Phase 3: Validation
        assert offers['profit_auto_accept'] >= MIN_PROFIT_MARGIN
        assert offers['profit_minimum'] >= MIN_PROFIT_MARGIN
        
    def test_dvd_disc_only_complete_workflow(self):
        """Test disc-only DVD workflow with pricing."""
        # Intake
        workflow = IntakeWorkflow()
        intake_result = workflow.process_item(
            barcode='012569863147',
            manual_condition='Acceptable'
        )
        
        assert intake_result['classification']['sku'] == '012569863147-A'
        
        # Pricing
        calc = PriceCalculator('dvd', 'Acceptable', cog=1.00)
        median = 12.50
        list_price = calc.calculate_list_price(median, 0.10)
        offers = calc.calculate_best_offer_prices(list_price)
        
        # Verify viability
        assert offers['profit_auto_accept'] >= MIN_PROFIT_MARGIN
        
    def test_music_cd_new_complete_workflow(self):
        """Test new music CD workflow."""
        # Intake
        workflow = IntakeWorkflow()
        intake_result = workflow.process_item(
            barcode='724384960145',
            manual_condition='New'
        )
        
        assert intake_result['classification']['sku'] == '724384960145'
        
        # Pricing
        calc = PriceCalculator('music_cd', 'New', cog=1.00)
        median = 18.00
        list_price = calc.calculate_list_price(median, 0.10)
        offers = calc.calculate_best_offer_prices(list_price)
        
        assert offers['profit_auto_accept'] >= MIN_PROFIT_MARGIN


class TestBatchProcessingWorkflow:
    """Integration tests for batch processing scenarios."""
    
    def test_process_mixed_batch(self):
        """Test processing mixed inventory batch."""
        inventory_batch = [
            {'barcode': '045496508234', 'condition': 'Very Good', 'median': 35.00, 'media_type': 'video_game'},
            {'barcode': '012569863147', 'condition': 'Acceptable', 'median': 12.50, 'media_type': 'dvd'},
            {'barcode': '724384960145', 'condition': 'New', 'median': 18.00, 'media_type': 'music_cd'},
        ]
        
        workflow = IntakeWorkflow()
        results = []
        
        for item in inventory_batch:
            intake = workflow.process_item(
                barcode=item['barcode'],
                manual_condition=item['condition']
            )
            
            calc = PriceCalculator(item['media_type'], item['condition'])
            pricing = calc.calculate_best_offer_prices(
                calc.calculate_list_price(item['median'], 0.10)
            )
            
            results.append({
                'sku': intake['classification']['sku'],
                'pricing': pricing,
                'viable': pricing['profit_auto_accept'] >= MIN_PROFIT_MARGIN
            })
        
        # All items should be viable
        assert len(results) == 3
        assert all(r['viable'] for r in results)
        assert results[0]['sku'] == '045496508234-VG'
        assert results[1]['sku'] == '012569863147-A'
        assert results[2]['sku'] == '724384960145'
        
    def test_batch_with_duplicates(self):
        """Test batch processing with duplicate detection."""
        workflow = IntakeWorkflow()
        
        batch = [
            '045496508234',
            '012569863147',
            '045496508234',  # Duplicate
            '724384960145',
        ]
        
        for barcode in batch:
            workflow.process_item(barcode, manual_condition='Very Good')
        
        assert workflow.barcode_intake.duplicates_detected == 1
        assert len(workflow.workflow_log) == 4
        
    def test_large_batch_processing_100_items(self):
        """Test processing large batch (100 items)."""
        workflow = IntakeWorkflow()
        
        # Generate 100 unique barcodes
        barcodes = [str(i).zfill(12) for i in range(1000, 1100)]
        
        results = []
        for barcode in barcodes:
            result = workflow.process_item(barcode, manual_condition='Very Good')
            results.append(result)
        
        assert len(results) == 100
        assert all(r['status'] == 'success' for r in results)
        assert len(workflow.workflow_log) == 100


class TestPricingMarginValidation:
    """Integration tests for margin validation across inventory."""
    
    def test_identify_unprofitable_items(self):
        """Test workflow identifies items below margin threshold."""
        workflow = IntakeWorkflow()
        calc = PriceCalculator('dvd', cog=1.00)
        
        # Test very low median (likely unprofitable)
        low_median = 2.00
        list_price = calc.calculate_list_price(low_median, 0.10)
        offers = calc.calculate_best_offer_prices(list_price)
        
        is_viable = offers['profit_auto_accept'] >= MIN_PROFIT_MARGIN
        assert not is_viable  # Should be unprofitable
        
    def test_identify_profitable_items(self):
        """Test workflow identifies profitable items."""
        workflow = IntakeWorkflow()
        calc = PriceCalculator('video_game', cog=1.00)
        
        # Healthy median
        median = 30.00
        list_price = calc.calculate_list_price(median, 0.10)
        offers = calc.calculate_best_offer_prices(list_price)
        
        is_viable = offers['profit_auto_accept'] >= MIN_PROFIT_MARGIN
        assert is_viable
        
    def test_margin_validation_report(self):
        """Test generating margin report for batch."""
        items = [
            {'media_type': 'video_game', 'median': 40.00},
            {'media_type': 'dvd', 'median': 15.00},
            {'media_type': 'music_cd', 'median': 8.00},
            {'media_type': 'video_game', 'median': 25.00},
        ]
        
        report = {
            'total_items': len(items),
            'profitable': 0,
            'unprofitable': 0,
            'items': []
        }
        
        for item in items:
            calc = PriceCalculator(item['media_type'], cog=1.00)
            list_price = calc.calculate_list_price(item['median'], 0.10)
            offers = calc.calculate_best_offer_prices(list_price)
            
            is_profitable = offers['profit_auto_accept'] >= MIN_PROFIT_MARGIN
            if is_profitable:
                report['profitable'] += 1
            else:
                report['unprofitable'] += 1
            
            report['items'].append({
                'media_type': item['media_type'],
                'median': item['median'],
                'list_price': list_price,
                'profit': offers['profit_auto_accept'],
                'profitable': is_profitable
            })
        
        assert report['total_items'] == 4
        assert report['profitable'] > 0


class TestSkuGenerationWorkflow:
    """Integration tests for SKU generation across conditions."""
    
    def test_sku_assignment_workflow(self):
        """Test complete SKU assignment for different conditions."""
        workflow = IntakeWorkflow()
        
        test_cases = [
            ('045496508234', 'New', '045496508234'),
            ('012569863147', 'Very Good', '012569863147-VG'),
            ('724384960145', 'Acceptable', '724384960145-A'),
        ]
        
        for barcode, condition, expected_sku in test_cases:
            result = workflow.process_item(barcode, manual_condition=condition)
            assert result['classification']['sku'] == expected_sku
            
    def test_sku_consistency_across_reprocessing(self):
        """Test SKU generation is consistent across multiple processes."""
        workflow1 = IntakeWorkflow()
        workflow2 = IntakeWorkflow()
        
        barcode = '045496508234'
        condition = 'Very Good'
        
        result1 = workflow1.process_item(barcode, manual_condition=condition)
        result2 = workflow2.process_item(barcode, manual_condition=condition)
        
        assert result1['classification']['sku'] == result2['classification']['sku']
        assert result1['classification']['sku'] == '045496508234-VG'


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""
    
    def test_invalid_barcode_workflow(self):
        """Test workflow handles invalid barcodes gracefully."""
        workflow = IntakeWorkflow()
        result = workflow.process_item('INVALID_CODE', manual_condition='New')
        
        assert result['status'] == 'failed'
        assert 'error' in result
        
    def test_missing_condition_defaults_gracefully(self):
        """Test workflow handles missing condition."""
        workflow = IntakeWorkflow()
        result = workflow.process_item('045496508234')
        
        assert result['status'] == 'success'
        assert result['classification']['condition'] == 'Acceptable'
        
    def test_pricing_with_zero_median(self):
        """Test pricing calculation with edge case zero median."""
        calc = PriceCalculator('dvd', cog=1.00)
        list_price = calc.calculate_list_price(0.00, 0.10)
        
        # Should enforce minimum
        assert list_price >= 5.00


class TestDataConsistency:
    """Integration tests for data consistency."""
    
    def test_workflow_log_consistency(self):
        """Test workflow maintains consistent logging."""
        workflow = IntakeWorkflow()
        
        barcodes = ['045496508234', '012569863147', '724384960145']
        
        for barcode in barcodes:
            workflow.process_item(barcode, manual_condition='Very Good')
        
        # Check log integrity
        assert len(workflow.workflow_log) == 3
        for i, log_entry in enumerate(workflow.workflow_log):
            assert 'status' in log_entry
            assert 'barcode' in log_entry
            assert 'steps' in log_entry
            
    def test_duplicate_detection_consistency(self):
        """Test duplicate detection is consistent."""
        workflow = IntakeWorkflow()
        
        # Process same barcode twice, then different one
        workflow.process_item('045496508234', manual_condition='New')
        workflow.process_item('045496508234', manual_condition='Very Good')
        workflow.process_item('012569863147', manual_condition='Acceptable')
        
        assert workflow.barcode_intake.duplicates_detected == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
