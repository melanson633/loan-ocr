# Data Structure Documentation

## Overview
This document describes the expected data structure and file formats for the Loan Agreement OCR Processing System.

## Input Data Structure

### PDF Document Types
The system processes the following types of loan documents:

1. **Primary Loan Agreements**
   - Format: PDF
   - Typical size: 2-30MB
   - Content: Main loan terms, conditions, and legal clauses

2. **Promissory Notes**
   - Format: PDF
   - Typical size: 0.5-5MB
   - Content: Payment terms, interest rates, maturity dates

3. **Modification Agreements**
   - Format: PDF
   - Typical size: 1-10MB
   - Content: Changes to original loan terms

4. **Amendment Documents**
   - Format: PDF
   - Typical size: 0.5-5MB
   - Content: Legal amendments and updates

### Expected File Naming Conventions
```
Examples (anonymized):
- Property_Address_Loan_Agreement.pdf
- Property_Address_Promissory_Note.pdf
- Property_Address_1st_Modification_Agreement.pdf
- Property_Address_Amendment.pdf
```

## Output Data Structure

### Extracted Data Fields
The system extracts the following key information:

#### Financial Terms
- Principal amount
- Interest rate
- Payment schedule
- Maturity date
- Late fees and penalties

#### Property Information
- Property address
- Property type
- Collateral details

#### Parties Involved
- Borrower information
- Lender information
- Guarantor details (if applicable)

#### Legal Terms
- Default conditions
- Acceleration clauses
- Prepayment terms

### Output File Formats

#### CSV Export
```csv
Document_Name,Principal_Amount,Interest_Rate,Maturity_Date,Property_Address,Borrower_Name
```

#### JSON Export
```json
{
  "document_info": {
    "filename": "document.pdf",
    "processed_date": "2024-01-01",
    "confidence_score": 0.95
  },
  "financial_terms": {
    "principal": 1000000,
    "interest_rate": 5.5,
    "term_months": 60
  },
  "property_info": {
    "address": "123 Main St",
    "type": "Commercial"
  }
}
```

## Directory Structure

```
data_input/
├── loan_agreements/
│   ├── primary_loans/
│   ├── modifications/
│   └── amendments/
└── promissory_notes/

data_output/
├── extracted_data/
│   ├── csv_exports/
│   ├── json_exports/
│   └── summary_reports/
└── processed_documents/
    ├── text_extractions/
    └── confidence_scores/

extraction_results/
├── batch_summaries/
├── error_reports/
└── validation_results/
```

## Data Quality Metrics

### Confidence Scoring
- **High Confidence**: 0.9-1.0 (Clean OCR, clear text)
- **Medium Confidence**: 0.7-0.89 (Some OCR issues, mostly readable)
- **Low Confidence**: 0.5-0.69 (Significant OCR challenges)
- **Review Required**: <0.5 (Manual review needed)

### Validation Checks
- Date format validation
- Currency amount validation
- Address format validation
- Legal entity name validation

## Sample Data for Testing

For development and testing purposes, use synthetic data that mimics the structure but contains no real financial information:

```
Sample files (not included in repo):
- Sample_Commercial_Loan_Agreement.pdf
- Sample_Promissory_Note.pdf
- Sample_Modification_Agreement.pdf
```

## Security Considerations

### Data Classification
- **Highly Sensitive**: Actual loan documents with real financial data
- **Sensitive**: Processed extractions with anonymized data
- **Internal**: System logs and processing metadata
- **Public**: Code, documentation, and synthetic examples

### Handling Guidelines
1. Never commit actual loan documents to version control
2. Use environment variables for sensitive configuration
3. Implement proper access controls for production data
4. Regular security audits of data handling processes
5. Compliance with financial data protection regulations

## Performance Considerations

### File Size Optimization
- Large PDFs (>10MB) may require special handling
- Batch processing recommended for multiple documents
- Memory management important for large document sets

### Processing Time Estimates
- Small documents (<2MB): 30-60 seconds
- Medium documents (2-10MB): 1-3 minutes
- Large documents (>10MB): 3-10 minutes

## Error Handling

### Common Issues
- Scanned documents with poor image quality
- Handwritten annotations
- Complex table structures
- Multi-column layouts
- Watermarks and background images

### Recovery Strategies
- Image preprocessing and enhancement
- Multiple OCR engine fallbacks
- Manual review workflows
- Confidence-based validation

---

**Note**: This documentation describes the data structure without including any actual sensitive financial information. All examples are synthetic and for illustration purposes only. 