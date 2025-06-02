#!/usr/bin/env python3
"""
List Available Gemini Models
Shows all available models accessible with the provided API key
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
except ImportError:
    logger.error("❌ google-genai SDK not installed!")
    logger.info("Please run: pip install google-genai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed. Using environment variables only.")


class GeminiModelLister:
    """List and display information about available Gemini models"""
    
    def __init__(self, api_key: str = None):
        """Initialize with API key"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "No API key found! Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable, "
                "or pass api_key parameter."
            )
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        logger.info("✅ Initialized Gemini client")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        models = []
        try:
            logger.info("Fetching available models...")
            for model in self.client.models.list():
                models.append(model)
            logger.info(f"✅ Found {len(models)} models")
            return models
        except Exception as e:
            logger.error(f"❌ Error listing models: {e}")
            return []
    
    def categorize_models(self, models: List[Any]) -> Dict[str, List[Any]]:
        """Categorize models by their capabilities"""
        categories = {
            'text_generation': [],
            'multimodal': [],
            'embedding': [],
            'code': [],
            'vision': [],
            'other': []
        }
        
        for model in models:
            model_name = model.name.lower()
            
            # Categorize based on model name patterns
            if 'embed' in model_name:
                categories['embedding'].append(model)
            elif 'gemini' in model_name:
                if 'vision' in model_name:
                    categories['vision'].append(model)
                elif 'code' in model_name:
                    categories['code'].append(model)
                else:
                    # Most Gemini models are multimodal
                    categories['multimodal'].append(model)
            elif 'text' in model_name:
                categories['text_generation'].append(model)
            else:
                categories['other'].append(model)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def print_model_details(self, model: Any, verbose: bool = False):
        """Print details about a model"""
        print(f"\n  📌 {model.name}")
        print(f"     Display Name: {getattr(model, 'display_name', 'N/A')}")
        
        if hasattr(model, 'description') and model.description:
            print(f"     Description: {model.description[:100]}...")
        
        if hasattr(model, 'supported_generation_methods'):
            methods = model.supported_generation_methods
            if methods:
                print(f"     Capabilities: {', '.join(methods)}")
        
        if verbose:
            # Print additional details if available
            if hasattr(model, 'input_token_limit'):
                print(f"     Input Token Limit: {model.input_token_limit:,}")
            if hasattr(model, 'output_token_limit'):
                print(f"     Output Token Limit: {model.output_token_limit:,}")
            if hasattr(model, 'temperature'):
                print(f"     Default Temperature: {model.temperature}")
    
    def print_models_summary(self, models: List[Any], verbose: bool = False):
        """Print a formatted summary of all models"""
        print("\n" + "="*70)
        print("🤖 AVAILABLE GEMINI MODELS")
        print("="*70)
        print(f"\nAPI Key: {self.api_key[:10]}...{self.api_key[-4:]}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Models: {len(models)}")
        
        # Categorize and display models
        categories = self.categorize_models(models)
        
        for category, category_models in categories.items():
            if category_models:
                print(f"\n{'─'*50}")
                category_title = category.replace('_', ' ').title()
                print(f"📂 {category_title} Models ({len(category_models)})")
                print('─'*50)
                
                for model in category_models:
                    self.print_model_details(model, verbose)
        
        # Print recommended models for loan extraction
        print("\n" + "="*70)
        print("💡 RECOMMENDED MODELS FOR LOAN EXTRACTION")
        print("="*70)
        
        recommendations = [
            ("gemini-2.0-flash-exp", "Latest, fastest model with excellent performance"),
            ("gemini-1.5-pro", "High capability model for complex documents"),
            ("gemini-1.5-flash", "Good balance of speed and capability"),
        ]
        
        available_recommendations = []
        model_names = [m.name for m in models]
        
        for model_id, description in recommendations:
            # Check if model or variant is available
            matching_models = [m for m in model_names if model_id in m]
            if matching_models:
                available_recommendations.append((matching_models[0], description))
        
        if available_recommendations:
            for model_name, description in available_recommendations:
                print(f"\n  ✅ {model_name}")
                print(f"     {description}")
        else:
            print("\n  ⚠️  No recommended models found in available list")
    
    def export_models_list(self, models: List[Any], output_file: str = "available_models.json"):
        """Export models list to JSON file"""
        import json
        
        models_data = []
        for model in models:
            model_dict = {
                'name': model.name,
                'display_name': getattr(model, 'display_name', None),
                'description': getattr(model, 'description', None),
                'supported_generation_methods': getattr(model, 'supported_generation_methods', []),
                'input_token_limit': getattr(model, 'input_token_limit', None),
                'output_token_limit': getattr(model, 'output_token_limit', None),
            }
            models_data.append(model_dict)
        
        output_path = Path(__file__).parent / output_file
        with open(output_path, 'w') as f:
            json.dump(models_data, f, indent=2)
        
        logger.info(f"✅ Exported models list to {output_path}")


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='List available Gemini models')
    parser.add_argument('--api-key', help='Gemini API key (optional if set in environment)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed model information')
    parser.add_argument('--export', '-e', action='store_true', help='Export models list to JSON')
    args = parser.parse_args()
    
    try:
        # Initialize lister
        lister = GeminiModelLister(api_key=args.api_key)
        
        # List models
        models = lister.list_models()
        
        if models:
            # Print summary
            lister.print_models_summary(models, verbose=args.verbose)
            
            # Export if requested
            if args.export:
                lister.export_models_list(models)
        else:
            logger.error("No models found or error occurred")
            
    except ValueError as e:
        logger.error(f"❌ {e}")
        print("\nTo use this script, you need to:")
        print("1. Set GEMINI_API_KEY environment variable:")
        print("   export GEMINI_API_KEY='your-api-key'")
        print("2. Or pass it as argument:")
        print("   python list_gemini_models.py --api-key 'your-api-key'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 