#!/usr/bin/env python3
"""
Test the Gemini extractor on a single property
Start small before processing all 106 documents!
"""

import os
import json
from pathlib import Path
from gemini_loan_extractor import GeminiLoanExtractor

def load_property_mapping():
    """Load the existing property mapping report"""
    mapping_file = Path("property_mapping_report.json")
    if not mapping_file.exists():
        print("❌ property_mapping_report.json not found!")
        print("   Run the PropertyDocumentMapper first to create it.")
        return None
    
    with open(mapping_file, 'r') as f:
        return json.load(f)

def pick_simple_property(mapping_data):
    """Pick a property with minimal documents for testing"""
    property_bundles = mapping_data['property_bundles']
    
    # Find properties with just 1-2 documents (no amendments)
    simple_properties = []
    for prop_id, bundle in property_bundles.items():
        if (len(bundle['base_documents']) <= 2 and 
            len(bundle['amendments']) == 0):
            simple_properties.append((prop_id, bundle))
    
    if simple_properties:
        # Pick the first simple one
        prop_id, bundle = simple_properties[0]
        print(f"📋 Selected property: {prop_id}")
        print(f"   Documents: {len(bundle['base_documents'])}")
        for doc in bundle['base_documents']:
            print(f"   - {doc['filename']}")
        return prop_id, bundle
    else:
        # Fallback to any property
        prop_id = list(property_bundles.keys())[0]
        bundle = property_bundles[prop_id]
        print(f"📋 Using first property: {prop_id}")
        return prop_id, bundle

def test_single_property():
    """Test extraction on a single property"""
    print("\n" + "="*60)
    print("SINGLE PROPERTY EXTRACTION TEST")
    print("="*60)
    
    # Check for API key
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        print("\n⚠️  Please set your GEMINI_API_KEY environment variable!")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        return
    
    # Load property mapping
    mapping_data = load_property_mapping()
    if not mapping_data:
        return
    
    # Pick a simple property
    prop_id, bundle = pick_simple_property(mapping_data)
    
    # Initialize extractor
    print(f"\n🤖 Initializing Gemini extractor...")
    extractor = GeminiLoanExtractor(API_KEY)
    
    # For now, just show what would be processed
    print(f"\n📄 Would process property bundle:")
    print(f"   Property ID: {prop_id}")
    print(f"   Base documents: {len(bundle['base_documents'])}")
    print(f"   Amendments: {len(bundle['amendments'])}")
    print(f"   Supporting: {len(bundle['supporting_documents'])}")
    
    # TODO: Add actual PDF text extraction and processing
    print(f"\n⚠️  Next steps:")
    print(f"   1. Add PDF text extraction (PyPDF2, pdfplumber, etc.)")
    print(f"   2. Call extractor.extract_from_property_bundle(bundle)")
    print(f"   3. Save results to JSON file")
    
    return bundle

if __name__ == "__main__":
    test_single_property() 