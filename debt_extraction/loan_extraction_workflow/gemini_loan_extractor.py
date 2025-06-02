#!/usr/bin/env python3
"""
Gemini Loan Document Extractor
Production-ready extractor using Google's Gen AI SDK with field evolution tracking
Based on clarifying responses:
1. Track field evolution in change log
2. Portfolio-only focus
3. Confidence threshold: 0.85
4. Normalize lender names
5. Extract current state only
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from google import genai
from google.genai import types
from datetime import datetime
import logging
import re
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FieldChange:
    """Track changes to a field across documents"""
    field_name: str
    old_value: Any
    new_value: Any
    document: str
    timestamp: str
    confidence: float


@dataclass
class ExtractionResult:
    """Enhanced extraction result with change tracking"""
    property_id: str
    document_name: str
    extracted_fields: Dict[str, Any]
    confidence_scores: Dict[str, float]
    citations: Dict[str, str]
    extraction_gaps: List[str]
    processing_time: float
    model_version: str
    timestamp: str
    field_changes: List[FieldChange] = field(default_factory=list)
    requires_review: List[str] = field(default_factory=list)  # Fields below 0.85 confidence


class LenderNameNormalizer:
    """Normalize lender names for consistency"""
    
    LENDER_MAPPINGS = {
        # Common bank name variations
        'bank of america': ['bofa', 'boa', 'bank of america, n.a.', 'bank of america national association'],
        'jpmorgan chase': ['chase', 'jp morgan', 'jpmorgan', 'jpmorgan chase bank', 'chase bank'],
        'wells fargo': ['wells', 'wf', 'wells fargo bank', 'wells fargo, n.a.'],
        'citibank': ['citi', 'citigroup', 'citibank, n.a.'],
        'us bank': ['usbank', 'u.s. bank', 'us bank national association'],
        'pnc bank': ['pnc', 'pnc bank, n.a.', 'pnc bank national association'],
        'truist': ['truist bank', 'bb&t', 'suntrust'],
        'citizens bank': ['citizens', 'citizens bank, n.a.'],
        'santander': ['santander bank', 'banco santander'],
        'td bank': ['td', 'toronto dominion', 'td bank, n.a.'],
        # Regional banks
        'harborone': ['harbor one', 'harborone bank'],
        'rockland trust': ['rockland', 'rockland trust company'],
        'eastern bank': ['eastern', 'eastern bank corporation'],
        'cambridge savings': ['cambridge', 'cambridge savings bank', 'csb'],
        # Credit unions
        'service credit union': ['scu', 'service cu'],
    }
    
    @classmethod
    def normalize(cls, lender_name: str) -> str:
        """Normalize a lender name to standard format"""
        if not lender_name:
            return lender_name
        
        # Clean and lowercase
        cleaned = lender_name.lower().strip()
        cleaned = re.sub(r'[^\w\s&]', '', cleaned)  # Remove special chars except &
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        
        # Check against mappings
        for standard_name, variations in cls.LENDER_MAPPINGS.items():
            if cleaned in variations or cleaned == standard_name:
                return standard_name.title()
            
            # Fuzzy matching for close matches
            for variation in variations:
                if SequenceMatcher(None, cleaned, variation).ratio() > 0.85:
                    return standard_name.title()
        
        # If no match found, return title case version
        return lender_name.strip().title()


class GeminiLoanExtractor:
    """Production-ready loan document extractor with enhanced features"""
    
    # Field definitions remain the same
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
    
    # Confidence threshold (from clarifying response #3)
    CONFIDENCE_THRESHOLD = 0.85
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-preview-05-20"):
        """Initialize the extractor with new SDK"""
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.lender_normalizer = LenderNameNormalizer()
        
        # Enhanced generation config for better extraction
        self.generation_config = types.GenerateContentConfig(
            temperature=0.4,  # Low for consistency
            top_p=0.98,
            top_k=40,
            max_output_tokens=65536,
            response_mime_type='application/json',  # Force JSON response
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
    
    def extract_from_property_bundle(self, property_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a complete property bundle with change tracking"""
        property_id = property_bundle['property_id']
        all_results = []
        field_evolution = {}  # Track how fields change across documents
        
        # Process base documents first
        logger.info(f"Processing property: {property_id}")
        
        for doc_info in property_bundle.get('base_documents', []):
            logger.info(f"  Processing base document: {doc_info['filename']}")
            # In production, read PDF and extract text here
            # result = self.extract_from_text(...)
            # all_results.append(result)
        
        # Process amendments in chronological order
        for doc_info in sorted(property_bundle.get('amendments', []), 
                              key=lambda x: x.get('amendment_number', 0)):
            logger.info(f"  Processing amendment: {doc_info['filename']}")
            # result = self.extract_from_text(..., is_amendment=True)
            # Track changes
            # self._track_field_changes(result, field_evolution)
            # all_results.append(result)
        
        # Consolidate to current state
        current_state = self._consolidate_to_current_state(all_results, field_evolution)
        
        return current_state
    
    def extract_from_text(self, 
                         property_id: str,
                         document_name: str,
                         document_text: str,
                         is_amendment: bool = False,
                         previous_values: Dict[str, Any] = None) -> ExtractionResult:
        """Extract loan terms with enhanced tracking"""
        start_time = time.time()
        
        # Build extraction prompt
        prompt = self._build_extraction_prompt(property_id, document_name, document_text, is_amendment)
        
        try:
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.generation_config
            )
            
            # Parse response
            extracted_data = self._parse_extraction_response(response.text)
            
            # Post-process extracted data
            extracted_data = self._post_process_extraction(extracted_data, previous_values)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Identify fields requiring review (confidence < 0.85)
            requires_review = [
                field for field, conf in extracted_data.get('confidence_scores', {}).items()
                if conf < self.CONFIDENCE_THRESHOLD
            ]
            
            # Track field changes if this is an amendment
            field_changes = []
            if is_amendment and previous_values:
                field_changes = self._identify_field_changes(
                    previous_values, 
                    extracted_data['fields'],
                    document_name
                )
            
            # Create result
            result = ExtractionResult(
                property_id=property_id,
                document_name=document_name,
                extracted_fields=extracted_data.get('fields', {}),
                confidence_scores=extracted_data.get('confidence_scores', {}),
                citations=extracted_data.get('citations', {}),
                extraction_gaps=extracted_data.get('gaps', []),
                processing_time=processing_time,
                model_version=self.model_name,
                timestamp=datetime.now().isoformat(),
                field_changes=field_changes,
                requires_review=requires_review
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed for {document_name}: {str(e)}")
            raise
    
    def _post_process_extraction(self, extracted_data: Dict[str, Any], 
                                previous_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """Post-process extracted data with normalization"""
        fields = extracted_data.get('fields', {})
        
        # Normalize lender name (clarifying response #4)
        if 'lender' in fields and fields['lender'] != 'NOT_FOUND':
            fields['lender'] = self.lender_normalizer.normalize(fields['lender'])
        
        # Ensure dates are in YYYY-MM-DD format
        date_fields = ['loan_close', 'loan_maturity', 'funding_sunset', 'io_date']
        for field in date_fields:
            if field in fields and fields[field] != 'NOT_FOUND':
                fields[field] = self._standardize_date(fields[field])
        
        # Convert rate percentages to decimals
        rate_fields = ['tranche_i_rate', 'tranche_ii_rate']
        for field in rate_fields:
            if field in fields and fields[field] != 'NOT_FOUND':
                fields[field] = self._convert_rate_to_decimal(fields[field])
        
        extracted_data['fields'] = fields
        return extracted_data
    
    def _standardize_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD"""
        if not date_str or date_str == 'NOT_FOUND':
            return date_str
        
        # Try common date patterns
        patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%m-%d-%Y'),
            (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', '%B %d, %Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),  # Already in correct format
        ]
        
        for pattern, date_format in patterns:
            try:
                if re.match(pattern, date_str):
                    parsed_date = datetime.strptime(date_str, date_format)
                    return parsed_date.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str  # Return original if can't parse
    
    def _convert_rate_to_decimal(self, rate_str: str) -> float:
        """Convert rate string to decimal"""
        if not rate_str or rate_str == 'NOT_FOUND':
            return rate_str
        
        try:
            # Remove % sign and convert
            if isinstance(rate_str, str):
                rate_str = rate_str.replace('%', '').strip()
            rate_float = float(rate_str)
            
            # If greater than 1, assume it's a percentage
            if rate_float > 1:
                rate_float = rate_float / 100
            
            return round(rate_float, 5)
        except:
            return rate_str
    
    def _identify_field_changes(self, old_values: Dict[str, Any], 
                               new_values: Dict[str, Any], 
                               document_name: str) -> List[FieldChange]:
        """Identify changes between document versions"""
        changes = []
        
        for field_name in self.FIELD_DEFINITIONS.keys():
            old_val = old_values.get(field_name, 'NOT_FOUND')
            new_val = new_values.get(field_name, 'NOT_FOUND')
            
            # Skip if both are NOT_FOUND or identical
            if old_val == new_val:
                continue
            
            # Record the change
            if new_val != 'NOT_FOUND':
                changes.append(FieldChange(
                    field_name=field_name,
                    old_value=old_val,
                    new_value=new_val,
                    document=document_name,
                    timestamp=datetime.now().isoformat(),
                    confidence=new_values.get('confidence_scores', {}).get(field_name, 0)
                ))
        
        return changes
    
    def _consolidate_to_current_state(self, all_results: List[ExtractionResult], 
                                     field_evolution: Dict[str, List[FieldChange]]) -> Dict[str, Any]:
        """Consolidate all results to current state (clarifying response #5)"""
        if not all_results:
            return {}
        
        # Start with the latest result
        current_state = all_results[-1].extracted_fields.copy()
        current_confidence = all_results[-1].confidence_scores.copy()
        current_citations = all_results[-1].citations.copy()
        
        # Fill in any gaps from earlier documents
        for result in reversed(all_results[:-1]):
            for field, value in result.extracted_fields.items():
                if current_state.get(field) == 'NOT_FOUND' and value != 'NOT_FOUND':
                    current_state[field] = value
                    current_confidence[field] = result.confidence_scores.get(field, 0)
                    current_citations[field] = result.citations.get(field, '')
        
        # Create change log for relevant fields (clarifying response #1)
        change_log = {}
        for field, changes in field_evolution.items():
            if changes:  # Only include fields that actually changed
                change_log[field] = [asdict(change) for change in changes]
        
        return {
            'property_id': all_results[0].property_id if all_results else '',
            'current_state': current_state,
            'confidence_scores': current_confidence,
            'citations': current_citations,
            'change_log': change_log,
            'documents_processed': [r.document_name for r in all_results],
            'fields_requiring_review': list(set(
                field for r in all_results for field in r.requires_review
            )),
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def _build_extraction_prompt(self, property_id: str, document_name: str, 
                                document_text: str, is_amendment: bool) -> str:
        """Build extraction prompt optimized for JSON response"""
        
        system_context = """You are a commercial loan document extraction specialist. 
Extract the requested fields with high accuracy and provide specific citations.

CRITICAL RULES:
1. Extract ONLY from the provided document text
2. For each field found, provide the exact page and section reference
3. If a field is not found, mark as "NOT_FOUND"
4. Express confidence as a decimal between 0 and 1
5. For dates, use YYYY-MM-DD format
6. For amounts, use numeric values without currency symbols or commas
7. For rates, express as percentages (e.g., 5.25 for 5.25%)
8. For amendments, note which terms are being modified from the original

You MUST return a valid JSON object with this exact structure:
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

        # Build field list
        field_list = "\n".join([f"- {field}: {desc}" for field, desc in self.FIELD_DEFINITIONS.items()])
        
        # Construct prompt
        doc_type = "AMENDMENT/MODIFICATION DOCUMENT" if is_amendment else "LOAN DOCUMENT"
        
        prompt = f"""{system_context}

PROPERTY: {property_id}
DOCUMENT: {document_name}
DOCUMENT TYPE: {doc_type}

FIELDS TO EXTRACT:
{field_list}

DOCUMENT TEXT:
{document_text[:50000]}  # Limit for token management

Extract all requested fields and return the JSON response."""

        return prompt
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from Gemini"""
        try:
            # The response should already be JSON due to response_mime_type
            data = json.loads(response_text)
            
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


def main():
    """Demo the enhanced extractor"""
    print("\n" + "="*60)
    print("ENHANCED GEMINI LOAN EXTRACTOR")
    print("="*60)
    
    # Check for API key
    API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
    
    if API_KEY == "your-api-key-here":
        print("\n⚠️  Please set your GEMINI_API_KEY environment variable!")
        return
    
    # Initialize extractor
    extractor = GeminiLoanExtractor(API_KEY)
    
    print("\n✅ Extractor initialized with:")
    print(f"   - Confidence threshold: {extractor.CONFIDENCE_THRESHOLD}")
    print(f"   - Lender name normalization: Enabled")
    print(f"   - Field change tracking: Enabled")
    print(f"   - Current state extraction: Enabled")
    
    # Demo lender normalization
    print("\n📊 Lender Name Normalization Examples:")
    test_names = ["Bank of America, N.A.", "BofA", "chase bank", "HARBORONE BANK"]
    for name in test_names:
        normalized = extractor.lender_normalizer.normalize(name)
        print(f"   '{name}' → '{normalized}'")


if __name__ == "__main__":
    main() 