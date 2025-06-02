"""
Directory Comparison Script
Compare OCR input folder with backup docs folder to identify missing files
"""

import os
import shutil
from pathlib import Path

def compare_directories():
    """Compare the two directories and identify files that need to be restored."""
    
    # Define the directories
    ocr_input = Path(r'\\rjk-dc01-2017\Users\mmelanson\Desktop\OCR_output\_input')
    backup_docs = Path(r'P:\Accounting\MM Projects\_LOAN AGREEMENTS\DOCS')

    print('=== DIRECTORY COMPARISON ANALYSIS ===')
    print(f'OCR Input Directory: {ocr_input}')
    print(f'Backup Docs Directory: {backup_docs}')
    print()

    # Check if directories exist
    if not ocr_input.exists():
        print(f'❌ OCR input directory not accessible: {ocr_input}')
        return False
        
    if not backup_docs.exists():
        print(f'❌ Backup docs directory not accessible: {backup_docs}')
        return False

    print('✅ Both directories are accessible')
    print()

    # Get file lists
    try:
        ocr_files = {f.name.lower(): f for f in ocr_input.iterdir() if f.is_file() and f.suffix.lower() == '.pdf'}
        backup_files = {f.name.lower(): f for f in backup_docs.iterdir() if f.is_file() and f.suffix.lower() == '.pdf'}
        
        print(f'📁 OCR Input folder contains: {len(ocr_files)} PDF files')
        print(f'📁 Backup Docs folder contains: {len(backup_files)} PDF files')
        print()
        
        # Find files that exist in backup but missing from OCR input
        missing_in_ocr = set(backup_files.keys()) - set(ocr_files.keys())
        
        # Find files that exist in OCR input but not in backup
        missing_in_backup = set(ocr_files.keys()) - set(backup_files.keys())
        
        # Find common files (for verification)
        common_files = set(ocr_files.keys()) & set(backup_files.keys())
        
        print(f'🔍 ANALYSIS RESULTS:')
        print(f'   Files missing from OCR input (need to copy): {len(missing_in_ocr)}')
        print(f'   Files missing from backup (OCR-only): {len(missing_in_backup)}')
        print(f'   Common files (already present): {len(common_files)}')
        print()
        
        if missing_in_ocr:
            print('📋 FILES TO COPY FROM BACKUP TO OCR INPUT:')
            for i, filename in enumerate(sorted(missing_in_ocr), 1):
                backup_path = backup_files[filename]
                print(f'   {i:2d}. {filename}')
                print(f'       Source: {backup_path}')
            print()
        
        if missing_in_backup:
            print('⚠️  FILES ONLY IN OCR INPUT (no backup available):')
            for i, filename in enumerate(sorted(missing_in_backup), 1):
                print(f'   {i:2d}. {filename}')
            print()
        
        if common_files:
            print(f'✅ COMMON FILES ({len(common_files)} files already present in both locations)')
            print()
            
        return {
            'missing_in_ocr': missing_in_ocr,
            'missing_in_backup': missing_in_backup,
            'common_files': common_files,
            'ocr_files': ocr_files,
            'backup_files': backup_files,
            'ocr_input': ocr_input,
            'backup_docs': backup_docs
        }
        
    except Exception as e:
        print(f'❌ Error accessing directories: {e}')
        return False

def copy_missing_files(comparison_result):
    """Copy missing files from backup to OCR input directory."""
    
    if not comparison_result:
        print("❌ No comparison data available")
        return False
        
    missing_files = comparison_result['missing_in_ocr']
    backup_files = comparison_result['backup_files']
    ocr_input = comparison_result['ocr_input']
    
    if not missing_files:
        print("✅ No files need to be copied - all files are present!")
        return True
        
    print(f"🚀 COPYING {len(missing_files)} FILES...")
    print()
    
    copied_count = 0
    failed_count = 0
    
    for filename in sorted(missing_files):
        source_file = backup_files[filename]
        dest_file = ocr_input / source_file.name  # Use original case from source
        
        try:
            print(f"📄 Copying: {source_file.name}")
            shutil.copy2(source_file, dest_file)
            print(f"   ✅ Success: {dest_file}")
            copied_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed_count += 1
        
        print()
    
    print(f"📊 COPY SUMMARY:")
    print(f"   ✅ Successfully copied: {copied_count} files")
    print(f"   ❌ Failed to copy: {failed_count} files")
    print(f"   📁 Destination: {ocr_input}")
    
    return failed_count == 0

if __name__ == "__main__":
    # First, compare directories
    result = compare_directories()
    
    if result:
        print("\n" + "="*60)
        response = input("Do you want to copy the missing files? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            copy_missing_files(result)
        else:
            print("Copy operation cancelled.")
    else:
        print("❌ Directory comparison failed.") 