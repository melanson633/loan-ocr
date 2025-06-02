# 🚀 Quick Start Guide - Loan Document Extraction Workflow

## Overview
This workflow extracts structured data from commercial loan documents using Google's Gemini 2.5 Pro AI model with the new unified Google Gen AI SDK.

---

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Google Gemini API Key** (get one at https://makersuite.google.com/app/apikey)
3. **PDF loan documents** in the `data_output/` directory

---

## 🛠️ Setup Instructions

### 1. Check and Install Dependencies

```bash
cd debt_extraction/loan_extraction_workflow

# Check requirements and install missing packages
python check_and_install_requirements.py

# Or install manually
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file:
```bash
GEMINI_API_KEY=your-actual-api-key-here
```

Or export directly:
```bash
export GEMINI_API_KEY='your-actual-api-key-here'
```

### 3. List Available Gemini Models

Check which models are available with your API key:
```bash
python list_gemini_models.py

# Or with verbose output
python list_gemini_models.py -v

# Export to JSON
python list_gemini_models.py -e
```

### 4. Test Document Mapping

Run the property mapper to see how documents are grouped:
```bash
python property_document_mapper.py
```

This will:
- Scan all PDFs in `data_output/`
- Group them by property
- Generate `property_mapping_report.json`

### 5. Test Gemini Extraction (Demo)

```bash
python gemini_extractor_demo.py

# Or use the enhanced extractor with your clarifying responses
python gemini_loan_extractor.py
```

---

## 📊 Full Pipeline Execution

### Step 1: Map Properties to Documents
```python
from property_document_mapper import PropertyDocumentMapper

mapper = PropertyDocumentMapper("../../data_output")
mapper.scan_documents()
bundles = mapper.create_property_bundles()
mapper.generate_mapping_report()
```

### Step 2: Extract Data with Gemini
```python
from gemini_extractor_demo import GeminiLoanExtractor
import os

# Initialize extractor
api_key = os.getenv("GEMINI_API_KEY")
extractor = GeminiLoanExtractor(api_key)

# Extract from a property bundle
for property_id, bundle in bundles.items():
    results = extractor.extract_from_bundle(bundle)
    # Process results...
```

---

## 📁 Output Structure

```
loan_extraction_workflow/
├── output/
│   ├── extracted_data/
│   │   ├── {property_id}_extracted.json    # Per-property results
│   │   └── consolidated_results.json       # All properties
│   ├── validation_reports/
│   │   ├── extraction_confidence_report.csv
│   │   └── missing_fields_report.csv
│   └── logs/
│       └── extraction_log_{timestamp}.log
```

---

## 🔍 Key Fields Extracted

The system extracts 25 fields per property:
- **Basic Info**: Lender, Loan Close Date, Maturity Date
- **Amounts**: Total Balance, Tranche I/II amounts
- **Rates**: Interest rates, Fixed/Float, Index, Spread
- **Terms**: Extensions, Amortization, Prepayment
- **Covenants**: DSCR requirements and definitions
- **Other**: Guarantees, Reserves, Reporting requirements

---

## ⚡ Quick Tips

1. **Large PDFs**: The system chunks documents >50k characters automatically
2. **Amendments**: Processed in chronological order, latest values win
3. **Confidence Scores**: Fields with <0.8 confidence are flagged for review
4. **Rate Limits**: Built-in retry logic handles API limits

---

## 🐛 Troubleshooting

### Common Issues:

1. **"API Key not found"**
   - Ensure GEMINI_API_KEY is set in environment
   - Check `.env` file is in the correct directory

2. **"PDF parsing error"**
   - Some PDFs may need OCR preprocessing
   - Check if PDF is corrupted or password-protected

3. **"Token limit exceeded"**
   - Document is too large for single extraction
   - System should auto-chunk, but check logs

4. **"Low confidence scores"**
   - Document format may be non-standard
   - Consider adding document-specific prompts

---

## 📈 Next Steps

1. **Run on Full Dataset**: Process all 106 documents
2. **Review Extraction Quality**: Check confidence scores and gaps
3. **Implement Validation**: Add business logic checks
4. **Export to Excel**: Generate summary reports
5. **Set up Monitoring**: Track extraction performance

---

## 📞 Support

For issues or questions:
1. Check the logs in `output/logs/`
2. Review the extraction confidence report
3. Refer to the main plan document: `LOAN_EXTRACTION_PLAN.md`

---

**Happy Extracting! 🎉** 