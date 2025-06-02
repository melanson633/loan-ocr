# Commercial Loan Document Extraction Workflow Plan
## Using Gemini 2.5 Pro via Google Gen AI SDK

---

## 🎯 Executive Summary

This plan outlines a robust workflow for extracting structured data from commercial loan documents using Gemini 2.5 Pro. The system will map properties from the reference file "_042025 Debt Terms.pdf" to their corresponding loan documents, bundle related agreements with amendments, and extract 25+ key fields per property.

---

## 📋 Project Overview

### Objectives:
1. Map each property in the reference PDF to its loan documents
2. Bundle original agreements with amendments/modifications
3. Extract 25 key fields using Gemini 2.5 Pro
4. Maintain field-level provenance and confidence scores
5. Implement reconciliation and validation checks

### Key Components:
- **Input**: Reference PDF with property list + 106 loan documents
- **Processing**: Gemini 2.5 Pro for extraction
- **Output**: Structured JSON with extracted fields per property

---

## 🗂️ Phase 1: Document Mapping & Bundling

### 1.1 Property-to-Document Mapping Strategy

```python
# Mapping Algorithm
1. Extract property list from reference PDF
2. For each property:
   a. Search for matching filenames in data_output/
   b. Use fuzzy matching for property addresses
   c. Group by property identifier patterns:
      - Address-based: "121 Technology Drive", "15 Guest Street"
      - Portfolio-based: "Cherry Hill Portfolio", "HarborOne"
      - Code-based: "100q", "326bal", "8TECH"
```

### 1.2 Document Bundling Rules

```yaml
Bundle Structure:
  Property_ID:
    base_documents:
      - Original Loan Agreement
      - Original Promissory Note
      - Original Term Note (if exists)
    amendments:
      - 1st Amendment/Modification
      - 2nd Amendment/Modification
      - Amended and Restated versions
    supporting:
      - Allonges
      - Security Instruments
      - Line of Credit Notes
```

### 1.3 Bundling Logic

```python
# Document Classification Patterns
DOCUMENT_TYPES = {
    'base_loan': ['Loan Agreement', 'Mortgage Loan Agreement'],
    'base_note': ['Promissory Note', 'Term Note', 'Note'],
    'amendment': ['Amendment', 'Modification', 'Amended and Restated'],
    'supporting': ['Allonge', 'Security', 'Line of Credit']
}

# Chronological Ordering
- Parse dates from filenames/content
- Order amendments: Original → 1st → 2nd → 3rd → Amended & Restated
- Latest amendment supersedes specific fields
```

---

## 🤖 Phase 2: Gemini 2.5 Pro Integration

### 2.1 Model Configuration

```python
import google.generativeai as genai

# Configuration
genai.configure(api_key=GEMINI_API_KEY)

model_config = {
    'model_name': 'gemini-2.0-flash-exp',  # Latest available
    'generation_config': {
        'temperature': 0.1,  # Low for consistency
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 8192,
    },
    'safety_settings': [
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
    ]
}
```

### 2.2 Extraction Schema

```json
{
  "property_id": "string",
  "extraction_metadata": {
    "timestamp": "ISO 8601",
    "model_version": "string",
    "confidence_score": "float"
  },
  "loan_terms": {
    "lender": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    },
    "loan_close": {
      "value": "YYYY-MM-DD",
      "citation": "page:line",
      "confidence": 0.95
    },
    "loan_maturity": {
      "value": "YYYY-MM-DD",
      "citation": "page:line",
      "confidence": 0.95
    },
    "max_loan_balance": {
      "total": {
        "value": "number",
        "citation": "page:line",
        "confidence": 0.95
      },
      "tranche_i": {
        "value": "number",
        "citation": "page:line",
        "confidence": 0.95
      },
      "tranche_ii": {
        "value": "number",
        "citation": "page:line",
        "confidence": 0.95
      }
    },
    "funding_sunset": {
      "value": "YYYY-MM-DD",
      "citation": "page:line",
      "confidence": 0.95
    },
    "io_date": {
      "value": "YYYY-MM-DD",
      "citation": "page:line",
      "confidence": 0.95
    },
    "extensions_available": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    },
    "amortization_period": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    },
    "interest_rates": {
      "tranche_i_rate": {
        "value": "number",
        "citation": "page:line",
        "confidence": 0.95
      },
      "tranche_i_type": {
        "value": "Fixed/Float",
        "citation": "page:line",
        "confidence": 0.95
      },
      "tranche_ii_rate": {
        "value": "number",
        "citation": "page:line",
        "confidence": 0.95
      },
      "tranche_ii_type": {
        "value": "Fixed/Float",
        "citation": "page:line",
        "confidence": 0.95
      },
      "index": {
        "value": "string",
        "citation": "page:line",
        "confidence": 0.95
      },
      "spread_bps": {
        "value": "number",
        "citation": "page:line",
        "confidence": 0.95
      }
    },
    "covenants": {
      "dscr_test": {
        "value": "string",
        "citation": "page:line",
        "confidence": 0.95
      },
      "dscr_definition_notes": {
        "value": "string",
        "citation": "page:line",
        "confidence": 0.95
      }
    },
    "prepayment_penalty": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    },
    "guaranty_notes": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    },
    "reserves": {
      "funds_in_escrow": {
        "value": "string",
        "citation": "page:line",
        "confidence": 0.95
      },
      "other_reserves": {
        "value": "string",
        "citation": "page:line",
        "confidence": 0.95
      }
    },
    "reporting_requirements": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    },
    "special_notes": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    },
    "lender_lease_approval_requirements": {
      "value": "string",
      "citation": "page:line",
      "confidence": 0.95
    }
  },
  "amendments_applied": ["list of amendment files processed"],
  "extraction_gaps": ["list of fields not found"],
  "validation_flags": ["any discrepancies or warnings"]
}
```

### 2.3 Prompt Engineering Strategy

```python
SYSTEM_PROMPT = """
You are a commercial loan document extraction specialist. Your task is to extract specific fields from loan documents with high accuracy and provide citations.

Rules:
1. Extract ONLY the requested fields
2. Provide page:line citations for each value
3. If a field is not found, mark as "NOT_FOUND"
4. For amendments, note which document supersedes the original
5. Maintain confidence scores: High (>0.9), Medium (0.7-0.9), Low (<0.7)
6. Flag any ambiguities or conflicting information
"""

EXTRACTION_PROMPT_TEMPLATE = """
Property: {property_name}
Documents: {document_list}

Extract the following fields:
{field_list}

For each field, provide:
- Value (exact text or parsed format)
- Citation (document name, page, line/paragraph)
- Confidence score
- Notes if ambiguous

Special Instructions:
- For dates, use YYYY-MM-DD format
- For amounts, use numeric values without currency symbols
- For rates, express as decimals (e.g., 5.25% = 0.0525)
- Check amendments for updates to original terms
"""
```

---

## 🔄 Phase 3: Processing Pipeline

### 3.1 Pipeline Architecture

```python
class LoanExtractionPipeline:
    def __init__(self, gemini_model, reference_pdf, documents_dir):
        self.model = gemini_model
        self.reference_pdf = reference_pdf
        self.documents_dir = documents_dir
        
    def process(self):
        # Step 1: Extract property list
        properties = self.extract_properties_from_reference()
        
        # Step 2: Map documents to properties
        property_bundles = self.map_documents_to_properties(properties)
        
        # Step 3: Extract fields for each property
        results = []
        for property_id, bundle in property_bundles.items():
            extracted_data = self.extract_loan_terms(property_id, bundle)
            validated_data = self.validate_extraction(extracted_data)
            results.append(validated_data)
            
        # Step 4: Generate output
        self.generate_output(results)
```

### 3.2 Error Handling & Retry Logic

```python
RETRY_CONFIG = {
    'max_retries': 3,
    'backoff_factor': 2,
    'retry_on': [
        'RATE_LIMIT_ERROR',
        'TIMEOUT_ERROR',
        'PARSING_ERROR'
    ]
}

def robust_extraction(document, fields, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = gemini_extract(document, fields)
            if validate_extraction(result):
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                return fallback_extraction(document, fields)
            time.sleep(2 ** attempt)
```

---

## 📊 Phase 4: Output & Validation

### 4.1 Output Formats

```python
# 1. Structured JSON (Primary)
output/
  ├── extracted_data/
  │   ├── {property_id}_extracted.json
  │   └── consolidated_results.json
  ├── validation_reports/
  │   ├── extraction_confidence_report.csv
  │   └── missing_fields_report.csv
  └── logs/
      └── extraction_log_{timestamp}.log

# 2. Excel Summary (Secondary)
- Property-by-property comparison sheet
- Field completion matrix
- Amendment tracking sheet
```

### 4.2 Validation Checks

```python
VALIDATION_RULES = {
    'date_consistency': 'loan_close < loan_maturity',
    'amount_reconciliation': 'tranche_i + tranche_ii = total',
    'rate_bounds': '0 < interest_rate < 0.20',
    'required_fields': ['lender', 'loan_close', 'loan_maturity', 'max_loan_balance']
}
```

---

## ❓ Clarifying Questions for Design Improvement

### 1. **Amendment Hierarchy & Field Precedence**
   - When multiple amendments exist, should we track the evolution of each field across amendments, or only extract the "final" value?
   - Are there specific fields that should ALWAYS come from the original agreement vs. latest amendment?

### 2. **Multi-Property Loan Handling**
   - How should we handle loan agreements that cover multiple properties (e.g., portfolio loans)?
   - Should these be split into individual property records or maintained as a single bundle?

### 3. **Confidence Thresholds & Manual Review**
   - What confidence threshold should trigger manual review? (e.g., <0.8?)
   - Should we implement a two-pass extraction with different prompts for low-confidence fields?

### 4. **Data Normalization Requirements**
   - Should lender names be normalized? (e.g., "Bank of America, N.A." vs "BofA" vs "Bank of America")
   - How should we handle rate structures that change over time (e.g., fixed-to-float conversions)?

### 5. **Historical vs. Current State**
   - Do you need point-in-time snapshots of loan terms, or only the current/final state?
   - Should superseded terms be preserved in a separate "history" section?

---

## 🏗️ Suggested File Structure

```
debt_extraction/
├── loan_extraction_workflow/
│   ├── config/
│   │   ├── extraction_schema.json
│   │   ├── field_mappings.yaml
│   │   └── gemini_config.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── document_mapper.py
│   │   ├── gemini_extractor.py
│   │   ├── validation_engine.py
│   │   └── output_generator.py
│   ├── prompts/
│   │   ├── system_prompts.py
│   │   ├── extraction_templates.py
│   │   └── validation_prompts.py
│   ├── output/
│   │   ├── extracted_data/
│   │   ├── validation_reports/
│   │   └── logs/
│   └── tests/
│       ├── test_extraction.py
│       └── sample_outputs/
```

---

## ⚠️ Gemini 2.5 Pro Limitations & Mitigation Strategies

### 1. **PDF Parsing Limitations**
   - **Issue**: Gemini works with text, not native PDF parsing
   - **Mitigation**: 
     - Use PyPDF2 or pdfplumber for text extraction first
     - Maintain page/line mapping for citations
     - Consider OCR quality checks before processing

### 2. **Context Window Constraints**
   - **Issue**: Large loan agreements may exceed token limits
   - **Mitigation**:
     - Implement document chunking with overlap
     - Use targeted extraction (search for specific sections)
     - Prioritize key pages (signature pages, schedules, exhibits)

### 3. **Structured Data Extraction**
   - **Issue**: Tables and complex layouts may not extract cleanly
   - **Mitigation**:
     - Pre-process tables with tabula-py
     - Use specific prompts for table extraction
     - Implement fallback regex patterns for common formats

### 4. **Rate Limiting**
   - **Issue**: API rate limits for large document sets
   - **Mitigation**:
     - Implement batching and queuing
     - Use exponential backoff
     - Consider parallel processing with rate limit awareness

### 5. **Consistency Across Documents**
   - **Issue**: Varying document formats and terminology
   - **Mitigation**:
     - Build a terminology dictionary
     - Use few-shot examples in prompts
     - Implement post-processing normalization

---

## 🚀 Alternative Approaches & Fallbacks

### 1. **Hybrid Extraction Pipeline**
```python
# Primary: Gemini 2.5 Pro
# Fallback 1: Claude 3 Opus (via Anthropic API)
# Fallback 2: GPT-4 Vision (for complex PDFs)
# Fallback 3: Rule-based extraction with spaCy/regex
```

### 2. **Specialized Tools Integration**
- **DocAI**: For complex table extraction
- **Amazon Textract**: For form-based documents
- **Custom NER models**: For entity extraction

### 3. **Human-in-the-Loop**
- Low confidence → Manual review queue
- Ambiguous terms → Expert clarification
- Missing documents → Flag for acquisition

---

## 📈 Success Metrics

1. **Extraction Completeness**: % of fields successfully extracted
2. **Accuracy Score**: Validation against manual samples
3. **Processing Time**: Documents per hour
4. **Confidence Distribution**: % high/medium/low confidence
5. **Amendment Coverage**: % of amendments properly linked

---

## 🎯 Next Steps

1. **Validate** this plan against your requirements
2. **Prioritize** the clarifying questions
3. **Select** primary vs. nice-to-have features
4. **Define** success criteria and acceptance thresholds
5. **Begin** with a pilot subset of 5-10 properties

This plan provides a robust foundation for your loan document extraction workflow. Please review and provide feedback on the clarifying questions to refine the implementation approach. 