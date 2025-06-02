#!/usr/bin/env python3
"""
Property Document Mapper
Maps properties from reference PDF to their associated loan documents
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """Information about a loan document"""
    filename: str
    filepath: str
    doc_type: str  # 'loan_agreement', 'promissory_note', 'amendment', etc.
    property_identifier: str
    amendment_number: int = 0  # 0 for original, 1+ for amendments
    file_size: int = 0


@dataclass
class PropertyBundle:
    """Bundle of documents for a single property"""
    property_id: str
    property_name: str
    base_documents: List[DocumentInfo]
    amendments: List[DocumentInfo]
    supporting_documents: List[DocumentInfo]
    
    def to_dict(self):
        return {
            'property_id': self.property_id,
            'property_name': self.property_name,
            'base_documents': [asdict(d) for d in self.base_documents],
            'amendments': [asdict(d) for d in self.amendments],
            'supporting_documents': [asdict(d) for d in self.supporting_documents],
            'total_documents': len(self.base_documents) + len(self.amendments) + len(self.supporting_documents)
        }


class PropertyDocumentMapper:
    """Maps properties to their associated loan documents"""
    
    # Document type patterns
    DOC_TYPE_PATTERNS = {
        'loan_agreement': [
            r'loan\s*agreement',
            r'mortgage\s*loan\s*agreement',
            r'commercial\s*loan\s*agreement',
            r'term\s*loan\s*agreement'
        ],
        'promissory_note': [
            r'promissory\s*note',
            r'term\s*note',
            r'note(?!\s*purchase)',  # Exclude "note purchase"
            r'line\s*of\s*credit\s*note'
        ],
        'amendment': [
            r'(?:1st|2nd|3rd|4th|first|second|third|fourth)\s*(?:amendment|modification)',
            r'amended\s*and\s*restated',
            r'modification\s*agreement',
            r'amendment\s*to\s*loan'
        ],
        'supporting': [
            r'allonge',
            r'security\s*instrument',
            r'ratification',
            r'tab\s*\d+'  # Tab documents
        ]
    }
    
    # Property identifier patterns
    PROPERTY_PATTERNS = {
        'address_based': [
            r'(\d+)\s+([A-Za-z\s]+(?:Street|St|Drive|Dr|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Way|Place|Pl|Court|Ct))',
            r'(\d+)\s+([A-Za-z\s]+)\s*-\s*',  # e.g., "121 Technology Drive -"
        ],
        'portfolio_based': [
            r'(Cherry\s*Hill\s*Portfolio)',
            r'(HarborOne)',
            r'(Harbor\s*One)',
            r'(RJ\s*Kelly)',
            r'(Plymouth)'
        ],
        'code_based': [
            r'(100q)',
            r'(326bal)',
            r'(8TECH)',
            r'(1020MR)',
            r'(6Post)',
            r'(_77sbed)'
        ]
    }
    
    def __init__(self, documents_dir: str):
        self.documents_dir = Path(documents_dir)
        self.document_index = []
        self.property_bundles = {}
        
    def scan_documents(self) -> List[DocumentInfo]:
        """Scan directory and classify all documents"""
        logger.info(f"Scanning documents in {self.documents_dir}")
        
        for filepath in self.documents_dir.glob("*.pdf"):
            filename = filepath.name
            doc_info = self._classify_document(filename, str(filepath))
            if doc_info:
                self.document_index.append(doc_info)
                
        logger.info(f"Found {len(self.document_index)} PDF documents")
        return self.document_index
    
    def _classify_document(self, filename: str, filepath: str) -> DocumentInfo:
        """Classify a single document"""
        filename_lower = filename.lower()
        
        # Determine document type
        doc_type = 'unknown'
        for dtype, patterns in self.DOC_TYPE_PATTERNS.items():
            if any(re.search(pattern, filename_lower) for pattern in patterns):
                doc_type = dtype
                break
        
        # Extract property identifier
        property_id = self._extract_property_identifier(filename)
        
        # Extract amendment number
        amendment_number = self._extract_amendment_number(filename_lower)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        return DocumentInfo(
            filename=filename,
            filepath=filepath,
            doc_type=doc_type,
            property_identifier=property_id,
            amendment_number=amendment_number,
            file_size=file_size
        )
    
    def _extract_property_identifier(self, filename: str) -> str:
        """Extract property identifier from filename"""
        # Try address-based patterns first
        for pattern in self.PROPERTY_PATTERNS['address_based']:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        # Try portfolio-based patterns
        for pattern in self.PROPERTY_PATTERNS['portfolio_based']:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Try code-based patterns
        for pattern in self.PROPERTY_PATTERNS['code_based']:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: use first part of filename
        return filename.split('-')[0].split('.')[0].strip()
    
    def _extract_amendment_number(self, filename_lower: str) -> int:
        """Extract amendment number from filename"""
        # Check for numbered amendments
        patterns = [
            (r'1st|first', 1),
            (r'2nd|second', 2),
            (r'3rd|third', 3),
            (r'4th|fourth', 4)
        ]
        
        for pattern, number in patterns:
            if re.search(pattern, filename_lower):
                return number
        
        # Check if it's an amended and restated (typically latest)
        if 'amended and restated' in filename_lower:
            return 99  # High number to sort last
        
        return 0  # Original document
    
    def create_property_bundles(self) -> Dict[str, PropertyBundle]:
        """Group documents by property"""
        logger.info("Creating property bundles...")
        
        # Group documents by property identifier
        property_groups = defaultdict(list)
        for doc in self.document_index:
            property_groups[doc.property_identifier].append(doc)
        
        # Create bundles
        for property_id, documents in property_groups.items():
            # Sort documents by type and amendment number
            base_docs = []
            amendments = []
            supporting = []
            
            for doc in documents:
                if doc.doc_type in ['loan_agreement', 'promissory_note'] and doc.amendment_number == 0:
                    base_docs.append(doc)
                elif doc.doc_type == 'amendment' or doc.amendment_number > 0:
                    amendments.append(doc)
                else:
                    supporting.append(doc)
            
            # Sort amendments by number
            amendments.sort(key=lambda x: x.amendment_number)
            
            bundle = PropertyBundle(
                property_id=property_id,
                property_name=property_id,  # Can be enhanced with better naming
                base_documents=base_docs,
                amendments=amendments,
                supporting_documents=supporting
            )
            
            self.property_bundles[property_id] = bundle
        
        logger.info(f"Created {len(self.property_bundles)} property bundles")
        return self.property_bundles
    
    def generate_mapping_report(self, output_file: str = "property_mapping_report.json"):
        """Generate a comprehensive mapping report"""
        report = {
            'summary': {
                'total_documents': len(self.document_index),
                'total_properties': len(self.property_bundles),
                'documents_by_type': self._count_by_type(),
                'properties_with_amendments': self._count_properties_with_amendments()
            },
            'property_bundles': {
                prop_id: bundle.to_dict() 
                for prop_id, bundle in self.property_bundles.items()
            },
            'unmapped_documents': self._find_unmapped_documents()
        }
        
        # Create output directory if it doesn't exist
        output_dir = self.documents_dir.parent / 'debt_extraction' / 'loan_extraction_workflow'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Mapping report saved to {output_path}")
        return report
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count documents by type"""
        counts = defaultdict(int)
        for doc in self.document_index:
            counts[doc.doc_type] += 1
        return dict(counts)
    
    def _count_properties_with_amendments(self) -> int:
        """Count properties that have amendments"""
        return sum(1 for bundle in self.property_bundles.values() if bundle.amendments)
    
    def _find_unmapped_documents(self) -> List[str]:
        """Find documents that couldn't be properly mapped"""
        return [doc.filename for doc in self.document_index if doc.doc_type == 'unknown']
    
    def print_summary(self):
        """Print a summary of the mapping"""
        print("\n" + "="*60)
        print("PROPERTY DOCUMENT MAPPING SUMMARY")
        print("="*60)
        print(f"Total Documents Scanned: {len(self.document_index)}")
        print(f"Total Properties Identified: {len(self.property_bundles)}")
        print("\nDocument Types:")
        for doc_type, count in self._count_by_type().items():
            print(f"  - {doc_type}: {count}")
        print(f"\nProperties with Amendments: {self._count_properties_with_amendments()}")
        print("\nSample Property Bundles:")
        
        # Show first 5 properties
        for i, (prop_id, bundle) in enumerate(list(self.property_bundles.items())[:5]):
            print(f"\n{i+1}. {prop_id}")
            print(f"   Base Documents: {len(bundle.base_documents)}")
            print(f"   Amendments: {len(bundle.amendments)}")
            print(f"   Supporting: {len(bundle.supporting_documents)}")


def main():
    """Main execution function"""
    # Use the data_output directory
    documents_dir = Path("C:/Users/mmelanson/.cursor-tutor/projects/loan-agreement-ocr/data_output")
    
    # Create mapper instance
    mapper = PropertyDocumentMapper(documents_dir)
    
    # Scan and classify documents
    mapper.scan_documents()
    
    # Create property bundles
    mapper.create_property_bundles()
    
    # Generate report
    mapper.generate_mapping_report()
    
    # Print summary
    mapper.print_summary()


if __name__ == "__main__":
    main() 