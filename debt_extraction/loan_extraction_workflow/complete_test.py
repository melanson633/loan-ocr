#!/usr/bin/env python3
"""
Complete end-to-end test for the three specified properties:
1020MR, 12 Innovation -, 16 Delta Drive

This script actually extracts PDF text and processes with Gemini!
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import our modules
from manual_test import create_property_bundles, check_file_exists
from pdf_reader import PDFTextExtractor
from gemini_loan_extractor import GeminiLoanExtractor

def process_property_with_extraction(bundle: Dict[str, Any], 
                                   extractor: GeminiLoanExtractor,
                                   pdf_extractor: PDFTextExtractor) -> Dict[str, Any]:
    """Process a single property bundle with actual PDF extraction and AI processing"""
    
    property_id = bundle['property_id']
    print(f"\n🔄 Processing property: {property_id}")
    
    results = []
    
    # Process each document in the bundle
    for i, doc_info in enumerate(bundle['base_documents'], 1):
        filename = doc_info['filename']
        filepath = Path(doc_info['filepath'])
        
        print(f"   📄 Document {i}/{len(bundle['base_documents'])}: {filename}")
        
        # Extract PDF text
        print(f"      🔍 Extracting text...")
        document_text = pdf_extractor.extract_text(filepath)
        
        if not document_text:
            print(f"      ❌ Failed to extract text from {filename}")
            continue
        
        print(f"      ✅ Extracted {len(document_text):,} characters")
        
        # Process with Gemini
        print(f"      🤖 Processing with Gemini AI...")
        try:
            result = extractor.extract_from_text(
                property_id=property_id,
                document_name=filename,
                document_text=document_text,
                is_amendment=False,
                previous_values=None
            )
            
            print(f"      ✅ Extraction completed in {result.processing_time:.2f}s")
            print(f"      📊 Found {len([f for f, v in result.extracted_fields.items() if v != 'NOT_FOUND'])} fields")
            
            # Show confidence summary
            low_confidence = [f for f in result.requires_review]
            if low_confidence:
                print(f"      ⚠️  {len(low_confidence)} fields need review (confidence < 85%)")
            
            results.append(result)
            
        except Exception as e:
            print(f"      ❌ Gemini processing failed: {e}")
            continue
    
    # Consolidate results if multiple documents
    if len(results) > 1:
        print(f"   🔄 Consolidating {len(results)} document results...")
        # For now, just use the last result as the "current state"
        # In production, you'd implement proper consolidation logic
        final_result = results[-1]
    elif len(results) == 1:
        final_result = results[0]
    else:
        print(f"   ❌ No successful extractions for {property_id}")
        return None
    
    # Create summary
    summary = {
        'property_id': property_id,
        'processing_timestamp': datetime.now().isoformat(),
        'documents_processed': len(results),
        'total_fields_extracted': len([f for f, v in final_result.extracted_fields.items() if v != 'NOT_FOUND']),
        'fields_requiring_review': final_result.requires_review,
        'average_confidence': sum(final_result.confidence_scores.values()) / len(final_result.confidence_scores) if final_result.confidence_scores else 0,
        'extracted_fields': final_result.extracted_fields,
        'confidence_scores': final_result.confidence_scores,
        'citations': final_result.citations
    }
    
    print(f"   ✅ Property {property_id} completed!")
    print(f"      📊 {summary['total_fields_extracted']} fields extracted")
    print(f"      🎯 {summary['average_confidence']:.1%} average confidence")
    
    return summary

def save_results(results: List[Dict[str, Any]], output_dir: Path):
    """Save extraction results to JSON files"""
    
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save individual property results
    for result in results:
        if result:
            property_id = result['property_id'].replace(' ', '_').replace('-', '_')
            filename = f"{property_id}_extraction_{timestamp}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"💾 Saved: {filepath}")
    
    # Save summary report
    summary_report = {
        'extraction_summary': {
            'timestamp': datetime.now().isoformat(),
            'properties_processed': len([r for r in results if r]),
            'total_documents': sum(r['documents_processed'] for r in results if r),
            'properties': [r['property_id'] for r in results if r]
        },
        'detailed_results': [r for r in results if r]
    }
    
    summary_file = output_dir / f"extraction_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary_report, f, indent=2)
    
    print(f"📋 Summary saved: {summary_file}")
    return summary_file

def main():
    """Run the complete extraction test"""
    print("\n" + "="*80)
    print("COMPLETE LOAN EXTRACTION TEST")
    print("Properties: 1020MR, 12 Innovation -, 16 Delta Drive")
    print("="*80)
    
    # Check for API key
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        print("\n❌ GEMINI_API_KEY environment variable not set!")
        print("   For PowerShell: $env:GEMINI_API_KEY='your-api-key-here'")
        print("   For Windows CMD: set GEMINI_API_KEY=your-api-key-here")
        return
    
    # Create property bundles
    print("\n📋 Creating property bundles...")
    bundles = create_property_bundles()
    
    # Validate files exist
    print("\n🔍 Validating files...")
    valid_bundles = []
    for bundle in bundles:
        print(f"   🏢 {bundle['property_id']}")
        all_exist = True
        for doc in bundle['base_documents']:
            exists, size_mb = check_file_exists(doc['filepath'])
            if exists:
                print(f"      ✅ {doc['filename']} ({size_mb} MB)")
            else:
                print(f"      ❌ {doc['filename']} - NOT FOUND")
                all_exist = False
        
        if all_exist:
            valid_bundles.append(bundle)
    
    if not valid_bundles:
        print("\n❌ No valid properties found! Check file paths.")
        return
    
    print(f"\n✅ {len(valid_bundles)} properties ready for processing")
    
    # Initialize extractors
    print("\n🔧 Initializing extractors...")
    try:
        pdf_extractor = PDFTextExtractor()
        print(f"   ✅ PDF extractor ready (methods: {pdf_extractor.available_methods})")
        
        gemini_extractor = GeminiLoanExtractor(API_KEY)
        print(f"   ✅ Gemini extractor ready (model: {gemini_extractor.model_name})")
        
    except Exception as e:
        print(f"   ❌ Failed to initialize extractors: {e}")
        return
    
    # Process each property
    print(f"\n🚀 Starting extraction process...")
    start_time = time.time()
    
    results = []
    for i, bundle in enumerate(valid_bundles, 1):
        print(f"\n{'='*50}")
        print(f"PROPERTY {i}/{len(valid_bundles)}")
        print(f"{'='*50}")
        
        try:
            result = process_property_with_extraction(
                bundle, gemini_extractor, pdf_extractor
            )
            results.append(result)
            
        except Exception as e:
            print(f"❌ Failed to process {bundle['property_id']}: {e}")
            results.append(None)
    
    # Calculate total time
    total_time = time.time() - start_time
    
    # Save results
    print(f"\n💾 Saving results...")
    output_dir = Path("extraction_results")
    summary_file = save_results(results, output_dir)
    
    # Final summary
    successful_results = [r for r in results if r]
    print(f"\n" + "="*80)
    print("EXTRACTION COMPLETE!")
    print("="*80)
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(f"✅ Successful extractions: {len(successful_results)}/{len(valid_bundles)}")
    print(f"📄 Total documents processed: {sum(r['documents_processed'] for r in successful_results)}")
    print(f"📊 Average fields per property: {sum(r['total_fields_extracted'] for r in successful_results) / len(successful_results):.1f}")
    print(f"🎯 Average confidence: {sum(r['average_confidence'] for r in successful_results) / len(successful_results):.1%}")
    print(f"📋 Results saved to: {summary_file}")
    
    # Show field extraction summary
    if successful_results:
        print(f"\n📈 Field Extraction Summary:")
        all_fields = set()
        for result in successful_results:
            all_fields.update(result['extracted_fields'].keys())
        
        for field in sorted(all_fields):
            found_count = sum(1 for r in successful_results 
                            if r['extracted_fields'].get(field, 'NOT_FOUND') != 'NOT_FOUND')
            print(f"   {field}: {found_count}/{len(successful_results)} properties")

if __name__ == "__main__":
    main() 