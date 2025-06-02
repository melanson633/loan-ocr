#!/usr/bin/env python3
"""
Simple file checker for the three properties
No API key required - just validates files exist
"""

from pathlib import Path
from manual_test import create_property_bundles, check_file_exists

def main():
    """Check if all files exist for the three properties"""
    print("\n" + "="*60)
    print("FILE VALIDATION CHECK")
    print("Properties: 1020MR, 12 Innovation -, 16 Delta Drive")
    print("="*60)
    
    # Create property bundles
    bundles = create_property_bundles()
    
    total_files = 0
    found_files = 0
    total_size = 0
    
    for bundle in bundles:
        print(f"\n🏢 Property: {bundle['property_id']}")
        print(f"   Expected documents: {len(bundle['base_documents'])}")
        
        property_size = 0
        property_found = 0
        
        for doc in bundle['base_documents']:
            total_files += 1
            exists, size_mb = check_file_exists(doc['filepath'])
            
            if exists:
                print(f"   ✅ {doc['filename']} ({size_mb} MB)")
                found_files += 1
                property_found += 1
                property_size += size_mb
                total_size += size_mb
            else:
                print(f"   ❌ {doc['filename']} - NOT FOUND")
                print(f"      Expected path: {doc['filepath']}")
        
        print(f"   📊 Found: {property_found}/{len(bundle['base_documents'])} files ({property_size:.2f} MB)")
    
    # Summary
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"📄 Total files expected: {total_files}")
    print(f"✅ Files found: {found_files}")
    print(f"❌ Files missing: {total_files - found_files}")
    print(f"📊 Total size: {total_size:.2f} MB")
    
    if found_files == total_files:
        print(f"\n🎉 All files found! Ready for extraction.")
        print(f"   Next step: Set GEMINI_API_KEY and run complete_test.py")
    else:
        print(f"\n⚠️  Missing {total_files - found_files} files.")
        print(f"   Check the file paths in data_output folder.")

if __name__ == "__main__":
    main() 