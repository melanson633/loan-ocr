#!/usr/bin/env python3
"""
Simple PDF text extraction utility
Supports multiple PDF libraries for robustness
"""

import logging
from pathlib import Path
from typing import Optional

# Try multiple PDF libraries for robustness
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

logger = logging.getLogger(__name__)

class PDFTextExtractor:
    """Extract text from PDF files using multiple fallback methods"""
    
    def __init__(self):
        """Initialize with available PDF libraries"""
        self.available_methods = []
        
        if HAS_PDFPLUMBER:
            self.available_methods.append("pdfplumber")
        if HAS_PYMUPDF:
            self.available_methods.append("pymupdf")
        if HAS_PYPDF2:
            self.available_methods.append("pypdf2")
        
        if not self.available_methods:
            raise ImportError(
                "No PDF libraries found! Install one of: "
                "pip install pdfplumber PyPDF2 PyMuPDF"
            )
        
        logger.info(f"PDF extraction methods available: {self.available_methods}")
    
    def extract_text(self, pdf_path: Path, method: str = "auto") -> Optional[str]:
        """Extract text from PDF using specified or best available method"""
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        # Auto-select best method
        if method == "auto":
            method = self.available_methods[0]
        
        logger.info(f"Extracting text from {pdf_path.name} using {method}")
        
        try:
            if method == "pdfplumber" and HAS_PDFPLUMBER:
                return self._extract_with_pdfplumber(pdf_path)
            elif method == "pymupdf" and HAS_PYMUPDF:
                return self._extract_with_pymupdf(pdf_path)
            elif method == "pypdf2" and HAS_PYPDF2:
                return self._extract_with_pypdf2(pdf_path)
            else:
                logger.error(f"Method {method} not available")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract text with {method}: {e}")
            
            # Try fallback methods
            for fallback_method in self.available_methods:
                if fallback_method != method:
                    logger.info(f"Trying fallback method: {fallback_method}")
                    try:
                        return self.extract_text(pdf_path, fallback_method)
                    except Exception as e2:
                        logger.warning(f"Fallback {fallback_method} also failed: {e2}")
                        continue
            
            logger.error("All PDF extraction methods failed")
            return None
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber (best for tables/layout)"""
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"\n--- PAGE {page_num} ---\n")
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue
        
        return "\n".join(text_parts)
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF (fast and reliable)"""
        text_parts = []
        
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"\n--- PAGE {page_num + 1} ---\n")
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num + 1}: {e}")
                continue
        
        doc.close()
        return "\n".join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2 (basic but widely compatible)"""
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"\n--- PAGE {page_num} ---\n")
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue
        
        return "\n".join(text_parts)
    
    def get_pdf_info(self, pdf_path: Path) -> dict:
        """Get basic PDF information"""
        if not pdf_path.exists():
            return {"error": "File not found"}
        
        info = {
            "filename": pdf_path.name,
            "size_bytes": pdf_path.stat().st_size,
            "size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2)
        }
        
        # Try to get page count
        try:
            if HAS_PDFPLUMBER:
                with pdfplumber.open(pdf_path) as pdf:
                    info["page_count"] = len(pdf.pages)
            elif HAS_PYMUPDF:
                doc = fitz.open(pdf_path)
                info["page_count"] = doc.page_count
                doc.close()
            elif HAS_PYPDF2:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    info["page_count"] = len(pdf_reader.pages)
        except Exception as e:
            info["page_count"] = "unknown"
            info["error"] = str(e)
        
        return info

def test_pdf_extraction():
    """Test PDF extraction on a sample file"""
    print("\n" + "="*50)
    print("PDF TEXT EXTRACTION TEST")
    print("="*50)
    
    extractor = PDFTextExtractor()
    print(f"Available methods: {extractor.available_methods}")
    
    # Test on a sample file (adjust path as needed)
    test_file = Path("../../data_output/12 Executive Loan Agreement.PDF")
    
    if test_file.exists():
        print(f"\n📄 Testing extraction on: {test_file.name}")
        
        # Get PDF info
        info = extractor.get_pdf_info(test_file)
        print(f"   Size: {info.get('size_mb', 'unknown')} MB")
        print(f"   Pages: {info.get('page_count', 'unknown')}")
        
        # Extract text
        text = extractor.extract_text(test_file)
        if text:
            print(f"   ✅ Extracted {len(text)} characters")
            print(f"   First 200 chars: {text[:200]}...")
        else:
            print("   ❌ Failed to extract text")
    else:
        print(f"\n❌ Test file not found: {test_file}")
        print("   Please adjust the path in test_pdf_extraction()")

if __name__ == "__main__":
    test_pdf_extraction() 