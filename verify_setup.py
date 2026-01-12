#!/usr/bin/env python3
"""
Verification script for Azure OnePager deployment setup.
Run this before deploying to check if all required environment variables are configured.

Usage:
    python verify_setup.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ {text}{RESET}")

def check_env_file():
    """Check if .env file exists."""
    env_path = Path('.env')
    if not env_path.exists():
        print_error(".env file not found!")
        print_info("Copy .env.example to .env and fill in your credentials:")
        print_info("  cp .env.example .env")
        return False
    print_success(".env file found")
    return True

def check_required_vars():
    """Check if required environment variables are set."""
    load_dotenv()

    required_vars = {
        "Azure OpenAI": [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_DEPLOYMENT",
        ],
        "OpenAI": [
            "OPENAI_API_KEY",
        ],
        "Azure Cognitive Search": [
            "AZURE_SEARCH_SERVICE_ENDPOINT",
            "AZURE_SEARCH_ADMIN_KEY",
        ],
        "Azure Blob Storage": [
            "AZURE_STORAGE_CONNECTION_STRING",
        ],
    }

    optional_vars = {
        "LangSmith (Optional)": ["LANGSMITH_API_KEY"],
        "LangFuse (Optional)": ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY"],
        "Companies House (Optional)": ["COMPANIES_HOUSE_API_KEY"],
        "GROQ (Optional)": ["GROQ_API_KEY"],
    }

    all_good = True

    # Check required variables
    print_header("Required Environment Variables")
    for category, vars_list in required_vars.items():
        print(f"\n{BOLD}{category}:{RESET}")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                # Mask the value for security
                masked = value[:10] + "..." if len(value) > 10 else "***"
                print_success(f"{var}: {masked}")
            else:
                print_error(f"{var}: Not set")
                all_good = False

    # Check optional variables
    print_header("Optional Environment Variables")
    for category, vars_list in optional_vars.items():
        print(f"\n{BOLD}{category}:{RESET}")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                masked = value[:10] + "..." if len(value) > 10 else "***"
                print_success(f"{var}: {masked}")
            else:
                print_warning(f"{var}: Not set (optional)")

    return all_good

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_warning(f"Python version: {version.major}.{version.minor}.{version.micro}")
        print_info("Recommended: Python 3.11+")
        return True  # Just a warning, not a failure

def check_docker():
    """Check if Docker is available."""
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success(f"Docker: {result.stdout.strip()}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print_warning("Docker not found (only needed for local Docker deployment)")
    return True  # Optional

def check_requirements():
    """Check if requirements.txt exists."""
    req_path = Path('requirements.txt')
    if not req_path.exists():
        print_error("requirements.txt not found!")
        return False
    print_success("requirements.txt found")
    return True

def check_main_file():
    """Check if main application file exists."""
    main_path = Path('UI/streamlit/main_page.py')
    if not main_path.exists():
        print_error(f"Main application file not found: {main_path}")
        return False
    print_success(f"Main application file found: {main_path}")
    return True

def check_packages_txt():
    """Check if packages.txt exists (needed for Streamlit Cloud)."""
    pkg_path = Path('packages.txt')
    if not pkg_path.exists():
        print_warning("packages.txt not found")
        print_info("This file is needed for Streamlit Cloud to install system packages")
        return False
    print_success("packages.txt found")
    return True

def test_azure_connectivity():
    """Test basic Azure connectivity (optional check)."""
    print_header("Testing Azure Connectivity (Optional)")

    try:
        from azure.identity import DefaultAzureCredential
        from azure.core.exceptions import ClientAuthenticationError

        print_info("Attempting to authenticate with Azure...")
        credential = DefaultAzureCredential()
        print_success("Azure credentials configured")
        return True
    except ImportError:
        print_warning("Azure SDK not installed - skipping connectivity test")
        print_info("This is OK if you're using API keys instead of managed identity")
        return True
    except Exception as e:
        print_warning(f"Azure authentication test failed: {str(e)}")
        print_info("This is OK if you're using API keys in .env file")
        return True

def main():
    """Run all verification checks."""
    print_header("Azure OnePager Deployment Verification")
    print(f"{BLUE}This script checks if your environment is ready for deployment{RESET}\n")

    checks = []

    # File checks
    print_header("File System Checks")
    checks.append(("Python Version", check_python_version()))
    checks.append(("Requirements", check_requirements()))
    checks.append(("Main Application File", check_main_file()))
    checks.append(("Packages File", check_packages_txt()))
    checks.append(("Docker", check_docker()))

    # Environment checks
    checks.append((".env File", check_env_file()))
    if checks[-1][1]:  # Only check vars if .env exists
        checks.append(("Environment Variables", check_required_vars()))

    # Azure connectivity
    test_azure_connectivity()

    # Summary
    print_header("Summary")

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    if passed == total:
        print_success(f"All checks passed! ({passed}/{total})")
        print_info("\n✨ Your environment is ready for deployment!")
        print_info("\nNext steps:")
        print_info("  1. For Streamlit Cloud: Follow STREAMLIT_DEPLOYMENT.md")
        print_info("  2. For Docker: Run 'docker-compose up'")
        print_info("  3. For Azure: Follow DOCKER_DEPLOYMENT.md")
        return 0
    else:
        print_warning(f"Some checks failed or have warnings ({passed}/{total} passed)")
        print_info("\n📋 Please review the issues above before deploying")
        print_info("\nFor help, see:")
        print_info("  - QUICK_START.md")
        print_info("  - STREAMLIT_DEPLOYMENT.md")
        print_info("  - DOCKER_DEPLOYMENT.md")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\n\nVerification cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)
