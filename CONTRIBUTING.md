# Contributing Guide

Thank you for taking the time to contribute to this project!

## Development Setup
1. Install Python 3.8 or newer.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run tests to ensure everything works:
   ```bash
   pytest
   ```

## Style and Linting
We use **flake8** for style checks. Please lint your code before committing:
```bash
flake8
```

Optionally, install the [pre-commit](https://pre-commit.com/) hook to run
checks automatically:
```bash
pip install pre-commit
pre-commit install
```

## Submitting Changes
1. Create a feature branch.
2. Commit your work with clear messages.
3. Ensure `flake8` and `pytest` pass.
4. Open a pull request and describe your changes.

Thank you for improving Loan OCR!
