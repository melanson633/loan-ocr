#!/usr/bin/env python3
"""
Requirements Checker and Installer
Checks for missing dependencies and installs them automatically
"""

import subprocess
import sys
import importlib
from pathlib import Path
import logging

# Handle pkg_resources deprecation in Python 3.12+
try:
    from importlib.metadata import version, PackageNotFoundError
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    MODERN_PACKAGING = True
except ImportError:
    try:
        import pkg_resources
        MODERN_PACKAGING = False
    except ImportError:
        print("Error: Neither importlib.metadata nor pkg_resources is available.")
        print("Please install packaging: pip install packaging")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"Python 3.8+ required. Current version: {version.major}.{version.minor}")
        sys.exit(1)
    logger.info(f"✅ Python version {version.major}.{version.minor} is compatible")


def parse_requirements(requirements_file='requirements.txt'):
    """Parse requirements.txt file"""
    req_path = Path(__file__).parent / requirements_file
    if not req_path.exists():
        logger.error(f"Requirements file not found: {req_path}")
        return []
    
    requirements = []
    with open(req_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                # Handle package names with version specifiers
                if '>=' in line or '==' in line or '<=' in line:
                    pkg_name = line.split('>=')[0].split('==')[0].split('<=')[0].strip()
                else:
                    pkg_name = line.strip()
                requirements.append((pkg_name, line))
    
    return requirements


def is_package_installed(package_spec):
    """Check if a package is installed with the correct version"""
    if MODERN_PACKAGING:
        try:
            # Parse the requirement
            req = Requirement(package_spec)
            
            # Get the installed version
            try:
                installed_version = version(req.name)
            except PackageNotFoundError:
                return False
            
            # Check if the installed version satisfies the requirement
            if req.specifier:
                return req.specifier.contains(installed_version)
            else:
                return True  # No version constraint, just check if installed
                
        except Exception:
            return False
    else:
        # Legacy pkg_resources method
        try:
            pkg_resources.require(package_spec)
            return True
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            return False


def install_package(package_spec):
    """Install a package using pip"""
    try:
        logger.info(f"Installing {package_spec}...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', package_spec
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"✅ Successfully installed {package_spec}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install {package_spec}: {e}")
        return False


def check_and_install_requirements():
    """Main function to check and install requirements"""
    logger.info("="*60)
    logger.info("CHECKING PROJECT REQUIREMENTS")
    logger.info("="*60)
    
    # Check Python version
    check_python_version()
    
    # Parse requirements
    requirements = parse_requirements()
    if not requirements:
        logger.warning("No requirements found")
        return
    
    logger.info(f"\nFound {len(requirements)} packages in requirements.txt")
    
    # Check and install packages
    missing_packages = []
    installed_packages = []
    
    for pkg_name, pkg_spec in requirements:
        if is_package_installed(pkg_spec):
            installed_packages.append(pkg_name)
        else:
            missing_packages.append((pkg_name, pkg_spec))
    
    # Report status
    logger.info(f"\n📦 Already installed: {len(installed_packages)} packages")
    if missing_packages:
        logger.info(f"📦 Missing packages: {len(missing_packages)}")
        
        # Ask for confirmation
        print("\nThe following packages need to be installed:")
        for pkg_name, pkg_spec in missing_packages:
            print(f"  - {pkg_spec}")
        
        response = input("\nDo you want to install these packages? (y/n): ")
        if response.lower() == 'y':
            logger.info("\nInstalling missing packages...")
            failed_installs = []
            
            for pkg_name, pkg_spec in missing_packages:
                if not install_package(pkg_spec):
                    failed_installs.append(pkg_spec)
            
            if failed_installs:
                logger.error(f"\n❌ Failed to install {len(failed_installs)} packages:")
                for pkg in failed_installs:
                    logger.error(f"  - {pkg}")
                logger.info("\nTry installing manually with:")
                logger.info(f"  pip install -r {Path(__file__).parent / 'requirements.txt'}")
            else:
                logger.info("\n✅ All packages installed successfully!")
        else:
            logger.info("Installation cancelled by user")
    else:
        logger.info("✅ All required packages are already installed!")
    
    # Special check for google-genai (new SDK)
    logger.info("\n" + "="*60)
    logger.info("CHECKING GOOGLE GEN AI SDK")
    logger.info("="*60)
    
    try:
        import google.genai
        logger.info("✅ google-genai SDK is installed")
        
        # Check if we can import key modules
        from google import genai
        from google.genai import types
        logger.info("✅ All google-genai modules are accessible")
        
    except ImportError as e:
        logger.warning("⚠️  google-genai SDK not found")
        logger.info("Installing google-genai...")
        if install_package('google-genai'):
            logger.info("✅ google-genai SDK installed successfully")
        else:
            logger.error("❌ Failed to install google-genai SDK")
            logger.info("Try installing manually with: pip install google-genai")
    
    # Check for additional tools that might be needed
    logger.info("\n" + "="*60)
    logger.info("CHECKING ADDITIONAL TOOLS")
    logger.info("="*60)
    
    # Check for Tesseract (for OCR)
    try:
        subprocess.run(['tesseract', '--version'], 
                      capture_output=True, check=True)
        logger.info("✅ Tesseract OCR is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("⚠️  Tesseract OCR not found")
        logger.info("   For OCR functionality, install Tesseract:")
        logger.info("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        logger.info("   - Mac: brew install tesseract")
        logger.info("   - Linux: sudo apt-get install tesseract-ocr")
    
    # Check for Java (for tabula-py)
    try:
        subprocess.run(['java', '-version'], 
                      capture_output=True, check=True)
        logger.info("✅ Java is installed (required for tabula-py)")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("⚠️  Java not found")
        logger.info("   For table extraction with tabula-py, install Java:")
        logger.info("   Download from https://www.java.com/download/")
    
    logger.info("\n" + "="*60)
    logger.info("REQUIREMENTS CHECK COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    check_and_install_requirements() 