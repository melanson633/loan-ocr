"""
Safe OCR Processor for Loan Agreement Documents

This script safely processes PDF documents with OCR:
- Never overwrites original files
- Validates output before considering complete
- Handles network storage properly
- Provides detailed logging and progress tracking
- Supports parallel processing for efficiency

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
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    """Central configuration for the OCR processor"""
    
    # Directories
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_INPUT = PROJECT_ROOT / "data_input"
    DATA_OUTPUT = PROJECT_ROOT / "data_output"
    LOGS_DIR = PROJECT_ROOT / "logs"
    TEMP_DIR = PROJECT_ROOT / "temp"
    
    # Processing settings
    MAX_WORKERS = min(3, os.cpu_count() or 1)  # Conservative for network storage
    BATCH_SIZE = 10  # Process in batches to avoid overwhelming network
    
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
        "progress_bar": False,      # We'll use our own
        "output_type": "pdf",
    }
    
    # Validation thresholds
    MIN_FILE_SIZE = 1024  # 1KB minimum
    MAX_SIZE_RATIO = 10   # Output shouldn't be 10x larger than input
    MIN_TEXT_LENGTH = 50  # Minimum characters to consider OCR successful

# Setup logging
def setup_logging() -> logging.Logger:
    """Configure comprehensive logging"""
    Config.LOGS_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Config.LOGS_DIR / f"ocr_processing_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger("SafeOCR")
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

# File operations
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

def copy_to_local_temp(source: Path) -> Optional[Path]:
    """Copy network file to local temp for processing"""
    try:
        temp_file = Config.TEMP_DIR / f"temp_{source.name}"
        shutil.copy2(source, temp_file)
        return temp_file
    except Exception as e:
        logging.error(f"Failed to copy {source} to temp: {e}")
        return None

# OCR Processing
def process_single_pdf(
    input_path: Path,
    output_dir: Path,
    logger: logging.Logger
) -> Dict[str, any]:
    """Process a single PDF with comprehensive safety checks"""
    
    result = {
        "input_file": input_path.name,
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
    temp_input = None
    temp_output = None
    
    try:
        # Step 1: Validate input
        logger.info(f"🔍 Validating: {input_path.name}")
        valid, msg = validate_pdf(input_path)
        if not valid:
            raise ValueError(f"Invalid input PDF: {msg}")
        
        result["input_size"] = input_path.stat().st_size
        result["hash_before"] = calculate_file_hash(input_path)
        
        # Step 2: Copy to local temp (for network files)
        if str(input_path).startswith("\\\\"):
            logger.debug("Network file detected, copying to local temp")
            temp_input = copy_to_local_temp(input_path)
            if not temp_input:
                raise IOError("Failed to copy network file to temp")
            processing_input = temp_input
        else:
            processing_input = input_path
        
        # Step 3: Create temp output file
        temp_output = Config.TEMP_DIR / f"ocr_{input_path.name}"
        
        # Step 4: Perform OCR
        logger.info(f"🔄 Processing: {input_path.name}")
        ocrmypdf.ocr(
            input_file=str(processing_input),
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
        final_output = output_dir / input_path.name
        shutil.move(str(temp_output), str(final_output))
        
        result["output_file"] = str(final_output)
        result["hash_after"] = calculate_file_hash(final_output)
        result["status"] = "success"
        logger.info(f"✅ Success: {input_path.name}")
        
    except PriorOcrFoundError:
        # File already has OCR, copy as-is
        logger.info(f"ℹ️ Already has OCR: {input_path.name}")
        final_output = output_dir / input_path.name
        shutil.copy2(input_path, final_output)
        result["output_file"] = str(final_output)
        result["status"] = "skipped"
        result["error"] = "Already has OCR text"
        
    except Exception as e:
        logger.error(f"❌ Failed: {input_path.name} - {str(e)}")
        result["status"] = "failed"
        result["error"] = str(e)
        
    finally:
        # Cleanup temp files
        if temp_input and temp_input.exists():
            temp_input.unlink()
        if temp_output and temp_output.exists():
            temp_output.unlink()
        
        result["processing_time"] = time.time() - start_time
    
    return result

def process_batch_parallel(
    pdf_files: List[Path],
    output_dir: Path,
    logger: logging.Logger
) -> List[Dict]:
    """Process multiple PDFs in parallel with progress tracking"""
    
    results = []
    
    with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_pdf = {
            executor.submit(
                process_single_pdf, pdf, output_dir, logger
            ): pdf for pdf in pdf_files
        }
        
        # Process with progress bar
        with tqdm(total=len(pdf_files), desc="Processing PDFs") as pbar:
            for future in as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update progress bar with status
                    status_icon = {
                        "success": "✅",
                        "skipped": "⏭️",
                        "failed": "❌"
                    }.get(result["status"], "❓")
                    
                    pbar.set_postfix_str(f"{status_icon} {pdf.name}")
                    
                except Exception as e:
                    logger.error(f"Unexpected error processing {pdf}: {e}")
                    results.append({
                        "input_file": pdf.name,
                        "status": "failed",
                        "error": f"Unexpected error: {str(e)}"
                    })
                
                pbar.update(1)
    
    return results

def generate_report(results: List[Dict], output_dir: Path, logger: logging.Logger):
    """Generate a comprehensive processing report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"ocr_report_{timestamp}.json"
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] == "failed")
    
    total_time = sum(r.get("processing_time", 0) for r in results)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_files": total,
            "successful": successful,
            "skipped": skipped,
            "failed": failed,
            "total_processing_time": f"{total_time:.2f} seconds",
            "average_time_per_file": f"{total_time/total:.2f} seconds" if total > 0 else "0"
        },
        "details": results
    }
    
    # Save report
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("📊 PROCESSING COMPLETE")
    logger.info(f"   Total files: {total}")
    logger.info(f"   ✅ Successful: {successful}")
    logger.info(f"   ⏭️  Skipped: {skipped}")
    logger.info(f"   ❌ Failed: {failed}")
    logger.info(f"   ⏱️  Total time: {total_time:.1f}s")
    logger.info(f"   📄 Report saved: {report_path}")
    logger.info("="*60)

def main():
    """Main entry point"""
    
    # Setup
    logger = setup_logging()
    logger.info("🚀 Safe OCR Processor Starting")
    
    # Create directories
    for dir_path in [Config.DATA_INPUT, Config.DATA_OUTPUT, Config.TEMP_DIR]:
        dir_path.mkdir(exist_ok=True, parents=True)
    
    # Check for input files
    pdf_files = list(Config.DATA_INPUT.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {Config.DATA_INPUT}")
        logger.info("Please copy your PDF files to the data_input directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process files
    try:
        results = process_batch_parallel(pdf_files, Config.DATA_OUTPUT, logger)
        generate_report(results, Config.DATA_OUTPUT, logger)
        
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        # Cleanup temp directory
        if Config.TEMP_DIR.exists():
            for temp_file in Config.TEMP_DIR.glob("*"):
                try:
                    temp_file.unlink()
                except:
                    pass

if __name__ == "__main__":
    main() 