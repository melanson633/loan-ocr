"""
Unrelated OCR Processor

This script processes all PDF files in the unrelated_ocr subfolder:
- Processes all PDF files in the directory automatically
- Saves OCR'd results back to the same folder
- Maintains original filename with "_OCR" suffix
- Never overwrites original files
- Provides detailed logging and validation
- Shows progress for batch processing

Author: AI Assistant
Date: 2024
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import ocrmypdf
    from ocrmypdf.exceptions import PriorOcrFoundError, UnsupportedImageFormatError
    from tqdm import tqdm
except ImportError as exc:
    missing = []
    if "ocrmypdf" in str(exc):
        missing.append("ocrmypdf")
    if "tqdm" in str(exc):
        missing.append("tqdm")
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print(f"📦 Install with: pip install {' '.join(missing)}")
        sys.exit(1)

# Configuration
class Config:
    """Configuration for the unrelated OCR processor"""
    
    # Directories
    PROJECT_ROOT = Path(__file__).parent.parent
    UNRELATED_OCR_DIR = PROJECT_ROOT / "data_input" / "unrelated_ocr"
    LOGS_DIR = PROJECT_ROOT / "logs"
    TEMP_DIR = PROJECT_ROOT / "temp"
    
    # OCR settings optimized for quality and safety
    OCR_OPTIONS = {
        "force_ocr": False,          # Only OCR if no text detected
        "skip_text": False,          # Process all pages
        "deskew": True,             # Fix rotation
        "rotate_pages": True,        # Auto-rotate if needed
        "optimize": 2,              # Balanced optimization
        "jpeg_quality": 90,         # High quality
        "png_quality": 90,          # High quality
        "pdfa_image_compression": "jpeg",
        "remove_background": False,  # Preserve original appearance
        "progress_bar": False,      # Disable for batch processing
        "output_type": "pdf",
    }
    
    # Validation thresholds
    MIN_FILE_SIZE = 1024  # 1KB minimum
    MAX_SIZE_RATIO = 10   # Output shouldn't be 10x larger than input

def setup_logging() -> logging.Logger:
    """Configure comprehensive logging"""
    Config.LOGS_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Config.LOGS_DIR / f"unrelated_ocr_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger("UnrelatedOCR")
    logger.setLevel(logging.INFO)
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - summary logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_pdf(file_path: Path) -> Tuple[bool, str]:
    """Validate that a PDF file is not corrupted"""
    try:
        # Check file exists and has size
        if not file_path.exists():
            return False, "File does not exist"
        
        size = file_path.stat().st_size
        if size < Config.MIN_FILE_SIZE:
            return False, f"File too small ({size} bytes)"
        
        # Try to open with ocrmypdf to validate structure
        from ocrmypdf.pdfinfo import PdfInfo
        info = PdfInfo(file_path)
        
        # Basic validation
        if not hasattr(info, 'pages') or len(info.pages) == 0:
            return False, "No pages found in PDF"
        
        return True, "Valid PDF"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def generate_output_filename(input_path: Path) -> Path:
    """Generate output filename with _OCR suffix"""
    stem = input_path.stem
    suffix = input_path.suffix
    parent = input_path.parent
    
    # Add _OCR suffix if not already present
    if not stem.endswith("_OCR"):
        new_name = f"{stem}_OCR{suffix}"
    else:
        new_name = input_path.name
    
    return parent / new_name

def process_pdf_file(
    input_path: Path,
    logger: logging.Logger
) -> Dict[str, any]:
    """Process a single PDF with comprehensive safety checks"""
    
    result = {
        "input_file": str(input_path),
        "status": "pending",
        "output_file": None,
        "error": None,
        "processing_time": 0,
        "input_size": 0,
        "output_size": 0,
        "hash_before": None,
        "hash_after": None,
    }
    
    start_time = time.time()
    temp_output = None
    
    try:
        # Step 1: Validate input
        logger.info(f"🔍 Validating: {input_path.name}")
        valid, msg = validate_pdf(input_path)
        if not valid:
            raise ValueError(f"Invalid input PDF: {msg}")
        
        result["input_size"] = input_path.stat().st_size
        result["hash_before"] = calculate_file_hash(input_path)
        
        # Step 2: Generate output filename
        output_path = generate_output_filename(input_path)
        
        # Check if output already exists
        if output_path.exists():
            logger.warning(f"⚠️ Output file already exists: {output_path.name}")
            response = input("Do you want to overwrite it? (y/N): ").strip().lower()
            if response != 'y':
                result["status"] = "skipped"
                result["error"] = "User chose not to overwrite existing file"
                return result
        
        # Step 3: Create temp output file
        Config.TEMP_DIR.mkdir(exist_ok=True)
        temp_output = Config.TEMP_DIR / f"temp_ocr_{input_path.name}"
        
        # Step 4: Perform OCR
        logger.info(f"🔄 Processing: {input_path.name}")
        logger.info(f"📄 Output will be: {output_path.name}")
        
        ocrmypdf.ocr(
            input_file=str(input_path),
            output_file=str(temp_output),
            **Config.OCR_OPTIONS
        )
        
        # Step 5: Validate output
        valid, msg = validate_pdf(temp_output)
        if not valid:
            raise ValueError(f"Invalid output PDF: {msg}")
        
        output_size = temp_output.stat().st_size
        result["output_size"] = output_size
        
        # Check size ratio
        size_ratio = output_size / result["input_size"]
        if size_ratio > Config.MAX_SIZE_RATIO:
            raise ValueError(
                f"Output file suspiciously large "
                f"({size_ratio:.1f}x input size)"
            )
        
        # Step 6: Move to final output location
        shutil.move(str(temp_output), str(output_path))
        
        result["output_file"] = str(output_path)
        result["hash_after"] = calculate_file_hash(output_path)
        result["status"] = "success"
        logger.info(f"✅ Success: {output_path.name}")
        
    except PriorOcrFoundError:
        # File already has OCR, copy with new name
        logger.info(f"ℹ️ Already has OCR: {input_path.name}")
        output_path = generate_output_filename(input_path)
        shutil.copy2(input_path, output_path)
        result["output_file"] = str(output_path)
        result["status"] = "skipped"
        result["error"] = "Already has OCR text - copied as-is"
        
    except Exception as e:
        logger.error(f"❌ Failed: {input_path.name} - {str(e)}")
        result["status"] = "failed"
        result["error"] = str(e)
        
    finally:
        # Cleanup temp files
        if temp_output and temp_output.exists():
            temp_output.unlink()
        
        result["processing_time"] = time.time() - start_time
    
    return result

def find_pdf_files(directory: Path, logger: logging.Logger) -> List[Path]:
    """Find all PDF files in the directory that need processing"""
    
    if not directory.exists():
        logger.error(f"❌ Directory not found: {directory}")
        return []
    
    # Find all PDF files
    pdf_files = list(directory.glob("*.pdf"))
    
    # Filter out files that already have _OCR suffix
    files_to_process = []
    for pdf_file in pdf_files:
        if not pdf_file.stem.endswith("_OCR"):
            files_to_process.append(pdf_file)
        else:
            logger.info(f"⏭️ Skipping already processed file: {pdf_file.name}")
    
    logger.info(f"📁 Found {len(pdf_files)} PDF files, {len(files_to_process)} need processing")
    return files_to_process

def generate_batch_report(results: List[Dict], output_dir: Path, logger: logging.Logger):
    """Generate a comprehensive batch processing report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"unrelated_ocr_batch_report_{timestamp}.json"
    
    # Calculate summary statistics
    total_files = len(results)
    successful = len([r for r in results if r['status'] == 'success'])
    skipped = len([r for r in results if r['status'] == 'skipped'])
    failed = len([r for r in results if r['status'] == 'failed'])
    
    total_time = sum(r['processing_time'] for r in results)
    total_input_size = sum(r['input_size'] for r in results)
    total_output_size = sum(r['output_size'] for r in results if r['output_size'] > 0)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "directory_processed": str(output_dir),
        "summary": {
            "total_files": total_files,
            "successful": successful,
            "skipped": skipped,
            "failed": failed,
            "total_processing_time": round(total_time, 2),
            "total_input_size": total_input_size,
            "total_output_size": total_output_size
        },
        "results": results
    }
    
    # Save detailed report
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print summary to console
    logger.info("\n" + "="*80)
    logger.info("📊 BATCH PROCESSING COMPLETE")
    logger.info(f"   📁 Directory: {output_dir}")
    logger.info(f"   📄 Total files: {total_files}")
    logger.info(f"   ✅ Successful: {successful}")
    logger.info(f"   ⏭️ Skipped: {skipped}")
    logger.info(f"   ❌ Failed: {failed}")
    logger.info(f"   📏 Total size: {total_input_size:,} → {total_output_size:,} bytes")
    logger.info(f"   ⏱️  Total time: {total_time:.1f}s")
    logger.info(f"   📄 Report: {report_path}")
    
    # Show failed files if any
    if failed > 0:
        logger.info("\n❌ Failed files:")
        for result in results:
            if result['status'] == 'failed':
                logger.info(f"   • {Path(result['input_file']).name}: {result['error']}")
    
    logger.info("="*80)

def main(directory_path: str = None):
    """Main entry point for batch processing"""
    
    # Setup
    logger = setup_logging()
    logger.info("🚀 Unrelated OCR Batch Processor Starting")
    
    # Create directories
    Config.TEMP_DIR.mkdir(exist_ok=True, parents=True)
    
    # Determine target directory
    if directory_path is None:
        if len(sys.argv) > 1:
            target_dir = Path(sys.argv[1])
        else:
            # Use default unrelated_ocr directory
            target_dir = Config.UNRELATED_OCR_DIR
    else:
        target_dir = Path(directory_path)
    
    # Validate directory
    if not target_dir.exists():
        logger.error(f"❌ Directory not found: {target_dir}")
        logger.info("Usage: python unrelated_ocr_processor.py [directory_path]")
        logger.info(f"Default directory: {Config.UNRELATED_OCR_DIR}")
        return
    
    logger.info(f"📁 Processing directory: {target_dir}")
    
    # Find PDF files to process
    pdf_files = find_pdf_files(target_dir, logger)
    
    if not pdf_files:
        logger.info("✨ No PDF files found that need processing")
        return
    
    # Ask for confirmation
    logger.info(f"\n🔍 Found {len(pdf_files)} files to process:")
    for pdf_file in pdf_files:
        logger.info(f"   • {pdf_file.name}")
    
    response = input(f"\nProceed with processing {len(pdf_files)} files? (Y/n): ").strip().lower()
    if response == 'n':
        logger.info("❌ Processing cancelled by user")
        return
    
    # Process all files
    results = []
    logger.info(f"\n🔄 Starting batch processing...")
    
    try:
        # Use tqdm for progress bar
        with tqdm(pdf_files, desc="Processing PDFs", unit="file") as pbar:
            for pdf_file in pbar:
                pbar.set_description(f"Processing {pdf_file.name}")
                
                result = process_pdf_file(pdf_file, logger)
                results.append(result)
                
                # Update progress bar with status
                if result['status'] == 'success':
                    pbar.set_postfix(status="✅", refresh=True)
                elif result['status'] == 'skipped':
                    pbar.set_postfix(status="⏭️", refresh=True)
                else:
                    pbar.set_postfix(status="❌", refresh=True)
        
        # Generate comprehensive report
        generate_batch_report(results, target_dir, logger)
        
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        if results:
            generate_batch_report(results, target_dir, logger)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        # Cleanup temp directory
        if Config.TEMP_DIR.exists():
            for temp_file in Config.TEMP_DIR.glob("temp_ocr_*"):
                try:
                    temp_file.unlink()
                except:
                    pass

if __name__ == "__main__":
    main() 