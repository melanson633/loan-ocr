#!/usr/bin/env python3
"""
Gemini 2.5 Pro Loan Document Extractor Demo
Demonstrates how to extract structured data from loan documents using Google's Gemini API
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from google import genai
from google.genai import types
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of extracting data from a document"""
    property_id: str
    document_name: str
    extracted_fields: Dict[str, Any]
    confidence_scores: Dict[str, float]
    citations: Dict[str, str]
    extraction_gaps: List[str]
    processing_time: float
    model_version: str
    timestamp: str


class GeminiLoanExtractor:
    """Extract loan terms using Gemini 2.5 Pro"""
    
    # Field definitions with extraction hints
    FIELD_DEFINITIONS = {
        'lender': 'Name of the lending institution or bank',
        'loan_close': 'Loan closing or origination date',
        'loan_maturity': 'Loan maturity or termination date',
        'max_loan_balance_total': 'Maximum total loan amount or commitment',
        'max_loan_balance_tranche_i': 'Maximum amount for Tranche I or Term Loan A',
        'max_loan_balance_tranche_ii': 'Maximum amount for Tranche II or Term Loan B',
        'funding_sunset': 'Last date to draw funds or funding expiration',
        'io_date': 'Interest-only period end date',
        'extensions_available': 'Number and terms of available extension options',
        'amortization_period': 'Amortization schedule or period in months/years',
        'tranche_i_rate': 'Interest rate for Tranche I',
        'tranche_i_type': 'Fixed or Floating rate for Tranche I',
        'tranche_ii_rate': 'Interest rate for Tranche II',
        'tranche_ii_type': 'Fixed or Floating rate for Tranche II',
        'index': 'Reference rate index (e.g., SOFR, Prime, LIBOR)',
        'spread_bps': 'Spread over index in basis points',
        'dscr_test': 'Debt Service Coverage Ratio requirement',
        'dscr_definition_notes': 'How DSCR is calculated or defined',
        'prepayment_penalty': 'Prepayment penalty terms or schedule',
        'guaranty_notes': 'Guarantor requirements and terms',
        'funds_in_escrow': 'Escrow requirements and amounts',
        'other_reserves': 'Other reserve requirements',
        'reporting_requirements': 'Financial reporting obligations',
        'special_notes': 'Other important terms or conditions',
        'lender_lease_approval_requirements': 'Lender consent requirements for leases'
    }
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-preview-05-20"):
        """Initialize the Gemini extractor"""
        # Initialize client with the new SDK
        self.client = genai.Client(api_key=api_key)
        
        self.model_name = model_name
        
        # Generation configuration
        self.generation_config = types.GenerateContentConfig(
            temperature=0.1,  # Low for consistency
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            safety_settings=[
                types.SafetySetting(
                    category='HARM_CATEGORY_DANGEROUS_CONTENT',
                    threshold='BLOCK_NONE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_HATE_SPEECH',
                    threshold='BLOCK_NONE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_HARASSMENT',
                    threshold='BLOCK_NONE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                    threshold='BLOCK_NONE'
                )
            ]
        )
        
    def extract_from_text(self, 
                         property_id: str,
                         document_name: str,
                         document_text: str,
                         is_amendment: bool = False) -> ExtractionResult:
        """Extract loan terms from document text"""
        start_time = time.time()
        
        # Build the extraction prompt
        prompt = self._build_extraction_prompt(property_id, document_name, document_text, is_amendment)
        
        try:
            # Call Gemini API with the new SDK
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.generation_config
            )
            
            # Parse the response
            extracted_data = self._parse_extraction_response(response.text)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create result object
            result = ExtractionResult(
                property_id=property_id,
                document_name=document_name,
                extracted_fields=extracted_data.get('fields', {}),
                confidence_scores=extracted_data.get('confidence_scores', {}),
                citations=extracted_data.get('citations', {}),
                extraction_gaps=extracted_data.get('gaps', []),
                processing_time=processing_time,
                model_version=self.model_name,
                timestamp=datetime.now().isoformat()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed for {document_name}: {str(e)}")
            raise
    
    def _build_extraction_prompt(self, property_id: str, document_name: str, 
                                document_text: str, is_amendment: bool) -> str:
        """Build the extraction prompt for Gemini"""
        
        system_context = """You are a commercial loan document extraction specialist. 
Extract the requested fields with high accuracy and provide specific citations.

CRITICAL RULES:
1. Extract ONLY from the provided document text
2. For each field found, provide the exact page and section reference
3. If a field is not found, mark as "NOT_FOUND"
4. Express confidence as High (>0.9), Medium (0.7-0.9), or Low (<0.7)
5. For dates, use YYYY-MM-DD format
6. For amounts, use numeric values without currency symbols
7. For rates, express as decimals (e.g., 5.25% = 0.0525)
8. For amendments, note which terms are being modified from the original

OUTPUT FORMAT:
Return a valid JSON object with this structure:
{
    "fields": {
        "field_name": "extracted_value"
    },
    "confidence_scores": {
        "field_name": 0.95
    },
    "citations": {
        "field_name": "Section X.Y, Page Z"
    },
    "gaps": ["list of fields not found"],
    "amendment_notes": "summary of what this amendment changes" (only if amendment)
}"""

        # Build field list with definitions
        field_list = "\n".join([f"- {field}: {desc}" for field, desc in self.FIELD_DEFINITIONS.items()])
        
        # Construct the full prompt
        if is_amendment:
            doc_type = "AMENDMENT/MODIFICATION DOCUMENT"
            extra_instruction = "\nPay special attention to what terms are being modified from the original agreement."
        else:
            doc_type = "LOAN DOCUMENT"
            extra_instruction = ""
        
        prompt = f"""{system_context}

PROPERTY: {property_id}
DOCUMENT: {document_name}
DOCUMENT TYPE: {doc_type}

FIELDS TO EXTRACT:
{field_list}
{extra_instruction}

DOCUMENT TEXT:
{document_text[:50000]}  # Limit to first 50k chars for token management

Please extract all requested fields and return the JSON response."""

        return prompt
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the JSON response from Gemini"""
        try:
            # Clean the response text (remove markdown code blocks if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            # Parse JSON
            data = json.loads(cleaned_text.strip())
            
            # Validate structure
            required_keys = ['fields', 'confidence_scores', 'citations', 'gaps']
            for key in required_keys:
                if key not in data:
                    data[key] = {} if key != 'gaps' else []
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            
            # Return empty structure
            return {
                'fields': {},
                'confidence_scores': {},
                'citations': {},
                'gaps': list(self.FIELD_DEFINITIONS.keys())
            }
    
    def extract_from_bundle(self, property_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a complete property bundle (base docs + amendments)"""
        results = []
        
        # Process base documents first
        for doc_info in property_bundle.get('base_documents', []):
            # In real implementation, you would read the PDF and extract text
            # For demo, we'll simulate
            logger.info(f"Processing base document: {doc_info['filename']}")
            # result = self.extract_from_text(...)
            # results.append(result)
        
        # Process amendments in order
        for doc_info in sorted(property_bundle.get('amendments', []), 
                              key=lambda x: x.get('amendment_number', 0)):
            logger.info(f"Processing amendment: {doc_info['filename']}")
            # result = self.extract_from_text(..., is_amendment=True)
            # results.append(result)
        
        # Consolidate results (latest values win)
        consolidated = self._consolidate_results(results)
        
        return consolidated
    
    def _consolidate_results(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """Consolidate multiple extraction results into final values"""
        # Implementation would merge results, with amendments overriding base values
        # For demo, returning empty dict
        return {}


def demo_extraction():
    """Demonstrate the extraction process"""
    print("\n" + "="*60)
    print("GEMINI 2.5 PRO LOAN EXTRACTION DEMO")
    print("="*60)
    
    # Note: You need to set your actual API key
    API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
    
    if API_KEY == "your-api-key-here":
        print("\n⚠️  Please set your GEMINI_API_KEY environment variable!")
        print("   export GEMINI_API_KEY='your-actual-key'")
        return
    
    # Initialize extractor
    extractor = GeminiLoanExtractor(API_KEY)
    
    # Sample document text (in real use, this would come from PDF extraction)
    sample_text = """
    LOAN AGREEMENT
    
    This Loan Agreement dated as of January 15, 2024 between 
    FIRST NATIONAL BANK ("Lender") and 123 MAIN STREET LLC ("Borrower").
    
    LOAN TERMS:
    - Maximum Loan Amount: $5,000,000
    - Tranche I: $3,500,000
    - Tranche II: $1,500,000
    - Closing Date: January 15, 2024
    - Maturity Date: January 15, 2029
    - Interest Rate: SOFR + 325 basis points
    - Prepayment: 3-2-1 prepayment penalty
    
    FINANCIAL COVENANTS:
    - Minimum DSCR: 1.25x calculated quarterly
    - DSCR Definition: Net Operating Income divided by Debt Service
    """
    
    # Simulate extraction
    print("\n📄 Extracting from sample document...")
    print(f"   Property: 123 Main Street")
    print(f"   Document: Loan Agreement")
    
    try:
        result = extractor.extract_from_text(
            property_id="123_main_street",
            document_name="123_Main_Street_Loan_Agreement.pdf",
            document_text=sample_text
        )
        
        print("\n✅ Extraction Complete!")
        print(f"   Processing Time: {result.processing_time:.2f} seconds")
        print(f"   Fields Extracted: {len(result.extracted_fields)}")
        print(f"   Gaps Identified: {len(result.extraction_gaps)}")
        
        print("\n📊 Sample Extracted Fields:")
        for field, value in list(result.extracted_fields.items())[:5]:
            confidence = result.confidence_scores.get(field, 0)
            print(f"   - {field}: {value} (confidence: {confidence:.2f})")
            
    except Exception as e:
        print(f"\n❌ Extraction failed: {str(e)}")


if __name__ == "__main__":
    demo_extraction() 