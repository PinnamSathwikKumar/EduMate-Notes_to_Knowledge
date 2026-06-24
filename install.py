#!/usr/bin/env python3
"""
Edumate - Installation Script
Automatically installs dependencies and sets up the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"Command: {command}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported.")
        print("Please install Python 3.8 or higher.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r {requirements_file}", "Installing dependencies"):
        return False
    
    return True

def download_models():
    """Download AI models"""
    download_script = Path(__file__).parent / "download_models.py"
    if not download_script.exists():
        print("❌ download_models.py not found!")
        return False
    
    if not run_command(f"{sys.executable} {download_script}", "Downloading AI models"):
        print("⚠️ Model download failed, but you can try running it manually later")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    base_path = Path(__file__).parent
    
    directories = [
        base_path / "uploads",
        base_path / "models",
        base_path / "models" / "summarizer",
        base_path / "models" / "qa_model",
        base_path / "models" / "sentence_embedder"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    return True

def main():
    """Main installation process"""
    print("🚀 Edumate - Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)
    
    # Download models
    print("\n📥 Downloading AI models...")
    print("This may take several minutes depending on your internet connection...")
    download_models()
    
    print("\n" + "=" * 50)
    print("🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the application: python app.py")
    print("2. Open your browser: http://localhost:5000")
    print("3. Start analyzing your documents!")
    
    print("\n💡 Tips:")
    print("- If model download failed, run: python download_models.py")
    print("- For help, check the README.md file")
    print("- Make sure you have at least 4GB RAM for optimal performance")

if __name__ == "__main__":
    main()

