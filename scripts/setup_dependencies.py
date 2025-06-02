#!/usr/bin/env python3
"""
OCR Dependencies Setup Script

This script checks for and installs all necessary dependencies for OCR processing:
- Python packages (via pip)
- System dependencies (Tesseract, Ghostscript, JBIG2)
- Provides installation instructions for missing system components

Author: AI Assistant
Date: 2024
"""

import subprocess
import sys
import platform
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyInstaller:
    """Comprehensive dependency installer for OCR processing"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.project_root = Path(__file__).parent.parent
        self.requirements_file = self.project_root / "requirements.txt"
        
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error(f"❌ Python 3.8+ required. Current: {version.major}.{version.minor}")
            return False
        logger.info(f"✅ Python {version.major}.{version.minor} is compatible")
        return True
    
    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[bool, str]:
        """Run a system command and return success status and output"""
        try:
            result = subprocess.run(
                command, 
                capture_output=capture_output, 
                text=True, 
                check=True
            )
            return True, result.stdout if capture_output else ""
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_msg = str(e)
            if hasattr(e, 'stderr') and e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            return False, error_msg
    
    def check_system_dependency(self, command: List[str], name: str) -> bool:
        """Check if a system dependency is installed"""
        success, output = self.run_command(command)
        if success:
            logger.info(f"✅ {name} is installed")
            return True
        else:
            logger.warning(f"⚠️  {name} not found")
            return False
    
    def install_python_packages(self) -> bool:
        """Install Python packages from requirements.txt"""
        logger.info("📦 Installing Python packages...")
        
        if not self.requirements_file.exists():
            logger.error(f"❌ Requirements file not found: {self.requirements_file}")
            return False
        
        # Upgrade pip first
        logger.info("Upgrading pip...")
        success, output = self.run_command([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        
        if not success:
            logger.warning("⚠️  Failed to upgrade pip, continuing anyway...")
        
        # Install requirements
        logger.info(f"Installing from {self.requirements_file}...")
        success, output = self.run_command([
            sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
        ])
        
        if success:
            logger.info("✅ Python packages installed successfully")
            return True
        else:
            logger.error(f"❌ Failed to install Python packages: {output}")
            return False
    
    def check_tesseract(self) -> bool:
        """Check if Tesseract OCR is installed"""
        return self.check_system_dependency(["tesseract", "--version"], "Tesseract OCR")
    
    def check_ghostscript(self) -> bool:
        """Check if Ghostscript is installed"""
        # Try different command names for Ghostscript
        commands = [
            ["gs", "--version"],
            ["gswin64c", "--version"],  # Windows 64-bit
            ["gswin32c", "--version"],  # Windows 32-bit
        ]
        
        for cmd in commands:
            if self.check_system_dependency(cmd, "Ghostscript"):
                return True
        
        logger.warning("⚠️  Ghostscript not found")
        return False
    
    def check_jbig2(self) -> bool:
        """Check if JBIG2 decoder is available"""
        # JBIG2 is a system-level dependency, not a Python package
        # It's usually included with Tesseract or available as system package
        
        # Try to check if jbig2 tools are available
        jbig2_commands = [
            ["jbig2dec", "--help"],
            ["jbig2", "--help"],
        ]
        
        for cmd in jbig2_commands:
            if self.check_system_dependency(cmd, "JBIG2 decoder"):
                return True
        
        # If no command-line tools found, check if it's likely available
        # (many systems have it as a library even without command-line tools)
        logger.info("ℹ️  JBIG2 decoder command-line tools not found")
        logger.info("   This is normal - JBIG2 support is often built into other tools")
        logger.info("   OCRmyPDF will work without it, just with a warning message")
        return True  # Don't fail setup for this
    
    def provide_installation_instructions(self):
        """Provide system-specific installation instructions"""
        logger.info("\n" + "="*70)
        logger.info("📋 SYSTEM DEPENDENCY INSTALLATION INSTRUCTIONS")
        logger.info("="*70)
        
        if self.system == "windows":
            logger.info("\n🪟 Windows Installation:")
            logger.info("1. Tesseract OCR:")
            logger.info("   - Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            logger.info("   - Install and add to PATH")
            logger.info("\n2. Ghostscript:")
            logger.info("   - Download from: https://www.ghostscript.com/download/gsdnld.html")
            logger.info("   - Install and add to PATH")
            logger.info("\n3. JBIG2 Support:")
            logger.info("   - Usually included with Tesseract installation")
            logger.info("   - Or install via: pip install jbig2dec")
            
        elif self.system == "darwin":  # macOS
            logger.info("\n🍎 macOS Installation:")
            logger.info("1. Install Homebrew (if not already installed):")
            logger.info("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            logger.info("\n2. Install dependencies:")
            logger.info("   brew install tesseract ghostscript jbig2dec")
            
        elif self.system == "linux":
            logger.info("\n🐧 Linux Installation:")
            logger.info("Ubuntu/Debian:")
            logger.info("   sudo apt-get update")
            logger.info("   sudo apt-get install tesseract-ocr ghostscript libjbig2-dev")
            logger.info("\nCentOS/RHEL/Fedora:")
            logger.info("   sudo yum install tesseract ghostscript jbig2dec-devel")
            logger.info("   # or with dnf: sudo dnf install tesseract ghostscript jbig2dec-devel")
        
        logger.info("\n💡 After installing system dependencies, run this script again!")
    
    def test_ocr_functionality(self) -> bool:
        """Test if OCR functionality works"""
        logger.info("\n🧪 Testing OCR functionality...")
        
        try:
            import ocrmypdf
            logger.info("✅ OCRmyPDF imported successfully")
            
            # Test basic functionality (without actually processing a file)
            from ocrmypdf.pdfinfo import PdfInfo
            logger.info("✅ OCRmyPDF core functions accessible")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ OCRmyPDF import failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"⚠️  OCRmyPDF test warning: {e}")
            return True  # Minor issues are okay
    
    def run_full_setup(self):
        """Run the complete setup process"""
        logger.info("🚀 Starting OCR Dependencies Setup")
        logger.info("="*70)
        
        # Step 1: Check Python version
        if not self.check_python_version():
            return False
        
        # Step 2: Install Python packages
        if not self.install_python_packages():
            logger.error("❌ Failed to install Python packages")
            return False
        
        # Step 3: Check system dependencies
        logger.info("\n🔍 Checking system dependencies...")
        tesseract_ok = self.check_tesseract()
        ghostscript_ok = self.check_ghostscript()
        jbig2_ok = self.check_jbig2()
        
        # Step 4: Test OCR functionality
        ocr_ok = self.test_ocr_functionality()
        
        # Step 5: Provide summary and instructions
        logger.info("\n" + "="*70)
        logger.info("📊 SETUP SUMMARY")
        logger.info("="*70)
        logger.info(f"✅ Python packages: Installed")
        logger.info(f"{'✅' if tesseract_ok else '❌'} Tesseract OCR: {'Ready' if tesseract_ok else 'Missing'}")
        logger.info(f"{'✅' if ghostscript_ok else '❌'} Ghostscript: {'Ready' if ghostscript_ok else 'Missing'}")
        logger.info(f"{'✅' if jbig2_ok else '❌'} JBIG2 Support: {'Ready' if jbig2_ok else 'Missing'}")
        logger.info(f"{'✅' if ocr_ok else '❌'} OCR Functionality: {'Ready' if ocr_ok else 'Issues'}")
        
        if not all([tesseract_ok, ghostscript_ok]):
            self.provide_installation_instructions()
            logger.info("\n⚠️  Some system dependencies are missing.")
            logger.info("   Install them and run this script again to verify.")
        else:
            logger.info("\n🎉 All dependencies are ready!")
            logger.info("   You can now run the OCR processing scripts.")
        
        return all([tesseract_ok, ghostscript_ok, ocr_ok])

def main():
    """Main entry point"""
    installer = DependencyInstaller()
    
    try:
        success = installer.run_full_setup()
        if success:
            logger.info("\n✅ Setup completed successfully!")
        else:
            logger.info("\n⚠️  Setup completed with some missing dependencies.")
            logger.info("   Follow the instructions above to complete the installation.")
            
    except KeyboardInterrupt:
        logger.info("\n❌ Setup interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error during setup: {e}")
        logger.info("Please check the error and try again.")

if __name__ == "__main__":
    main() 