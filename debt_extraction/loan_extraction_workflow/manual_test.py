#!/usr/bin/env python3
"""
Manually create a property bundle for testing
Perfect for testing without processing all 106 documents
"""

import os
from pathlib import Path
from gemini_loan_extractor import GeminiLoanExtractor

def create_property_bundles():
    """Create property bundles for the three specified properties"""
    
    # Get the script directory and find data_output from there
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # Go up two levels to project root
    data_output = project_root / "data_output"
    
    # Property 1: 1020MR (2 documents)
    property_1020mr = {
        "property_id": "1020MR",
        "property_name": "1020MR", 
        "base_documents": [
            {
                "filename": "1020MR_17. Mortgage Loan Agreement.pdf",
                "filepath": str(data_output / "1020MR_17. Mortgage Loan Agreement.pdf"),
                "doc_type": "loan_agreement",
                "property_identifier": "1020MR",
                "amendment_number": 0,
                "file_size": 0  # Will be calculated
            },
            {
                "filename": "1020MR_18. Promissory Note.pdf",
                "filepath": str(data_output / "1020MR_18. Promissory Note.pdf"),
                "doc_type": "promissory_note",
                "property_identifier": "1020MR",
                "amendment_number": 0,
                "file_size": 0  # Will be calculated
            }
        ],
        "amendments": [],
        "supporting_documents": [],
        "total_documents": 2
    }
    
    # Property 2: 12 Innovation - (3 documents)
    property_12_innovation = {
        "property_id": "12 Innovation -",
        "property_name": "12 Innovation -", 
        "base_documents": [
            {
                "filename": "12 Innovation - Loan Agreement.pdf",
                "filepath": str(data_output / "12 Innovation - Loan Agreement.pdf"),
                "doc_type": "loan_agreement",
                "property_identifier": "12 Innovation -",
                "amendment_number": 0,
                "file_size": 0  # Will be calculated
            },
            {
                "filename": "12 Innovation - Term Note (CSB).pdf",
                "filepath": str(data_output / "12 Innovation - Term Note (CSB).pdf"),
                "doc_type": "promissory_note",
                "property_identifier": "12 Innovation -",
                "amendment_number": 0,
                "file_size": 0  # Will be calculated
            },
            {
                "filename": "12 Innovation - Term Note (SVB).pdf",
                "filepath": str(data_output / "12 Innovation - Term Note (SVB).pdf"),
                "doc_type": "promissory_note",
                "property_identifier": "12 Innovation -",
                "amendment_number": 0,
                "file_size": 0  # Will be calculated
            }
        ],
        "amendments": [],
        "supporting_documents": [],
        "total_documents": 3
    }
    
    # Property 3: 16 Delta Drive (2 documents)
    property_16_delta = {
        "property_id": "16 Delta Drive",
        "property_name": "16 Delta Drive", 
        "base_documents": [
            {
                "filename": "16 Delta Drive - Loan Agreement.pdf",
                "filepath": str(data_output / "16 Delta Drive - Loan Agreement.pdf"),
                "doc_type": "loan_agreement",
                "property_identifier": "16 Delta Drive",
                "amendment_number": 0,
                "file_size": 0  # Will be calculated
            },
            {
                "filename": "16 Delta Drive - Note.pdf",
                "filepath": str(data_output / "16 Delta Drive - Note.pdf"),
                "doc_type": "promissory_note",
                "property_identifier": "16 Delta Drive",
                "amendment_number": 0,
                "file_size": 0  # Will be calculated
            }
        ],
        "amendments": [],
        "supporting_documents": [],
        "total_documents": 2
    }
    
    return [property_1020mr, property_12_innovation, property_16_delta]

def check_file_exists(filepath):
    """Check if a file exists and return file info"""
    path = Path(filepath)
    if path.exists():
        size_mb = round(path.stat().st_size / (1024 * 1024), 2)
        return True, size_mb
    return False, 0

def test_multiple_properties():
    """Test with the three specified properties"""
    print("\n" + "="*70)
    print("MULTI-PROPERTY EXTRACTION TEST")
    print("Testing: 1020MR, 12 Innovation -, 16 Delta Drive")
    print("="*70)
    
    # Check for API key
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        print("\n⚠️  Please set your GEMINI_API_KEY environment variable!")
        print("   For Windows: set GEMINI_API_KEY=your-api-key-here")
        print("   For PowerShell: $env:GEMINI_API_KEY='your-api-key-here'")
        return
    
    # Create property bundles
    bundles = create_property_bundles()
    
    print(f"\n📋 Created {len(bundles)} property bundles:")
    
    # Check file availability for each property
    valid_bundles = []
    for bundle in bundles:
        print(f"\n🏢 Property: {bundle['property_id']}")
        print(f"   Documents: {len(bundle['base_documents'])}")
        
        all_files_exist = True
        total_size = 0
        
        for doc in bundle['base_documents']:
            exists, size_mb = check_file_exists(doc['filepath'])
            if exists:
                print(f"   ✅ {doc['filename']} ({size_mb} MB)")
                doc['file_size'] = size_mb * 1024 * 1024  # Store in bytes
                total_size += size_mb
            else:
                print(f"   ❌ {doc['filename']} - FILE NOT FOUND")
                all_files_exist = False
        
        if all_files_exist:
            print(f"   📊 Total size: {total_size:.2f} MB")
            valid_bundles.append(bundle)
        else:
            print(f"   ⚠️  Skipping property due to missing files")
    
    if not valid_bundles:
        print(f"\n❌ No valid properties found! Check file paths.")
        return
    
    # Initialize extractor
    print(f"\n🤖 Initializing Gemini extractor...")
    try:
        extractor = GeminiLoanExtractor(API_KEY)
        print("   ✅ Extractor initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return
    
    # Show processing summary
    print(f"\n📄 Ready to process {len(valid_bundles)} properties:")
    total_docs = sum(len(bundle['base_documents']) for bundle in valid_bundles)
    print(f"   Total documents: {total_docs}")
    
    for bundle in valid_bundles:
        print(f"   • {bundle['property_id']}: {len(bundle['base_documents'])} docs")
    
    print(f"\n⚠️  Next steps to complete extraction:")
    print(f"   1. Add PDF text extraction (use pdf_reader.py)")
    print(f"   2. Loop through valid_bundles and call:")
    print(f"      result = extractor.extract_from_property_bundle(bundle)")
    print(f"   3. Save results to JSON files")
    print(f"   4. Generate summary report")
    
    return valid_bundles, extractor

# Keep the old function for backward compatibility
def test_manual_bundle():
    """Legacy function - now calls the multi-property test"""
    return test_multiple_properties()

if __name__ == "__main__":
    test_multiple_properties() 