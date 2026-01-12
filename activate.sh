#!/bin/bash
# Activation script for Azure OnePager virtual environment
# Usage: source activate.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Activating Azure OnePager virtual environment...${NC}"

# Activate virtual environment
source venv/bin/activate

# Verify activation
if [ "$VIRTUAL_ENV" != "" ]; then
    echo -e "${GREEN}✓ Virtual environment activated!${NC}"
    echo ""
    echo "Python: $(python --version)"
    echo "Location: $VIRTUAL_ENV"
    echo ""
    echo "To run the app:"
    echo "  streamlit run UI/streamlit/main_page.py"
    echo ""
    echo "To deactivate:"
    echo "  deactivate"
else
    echo "Failed to activate virtual environment"
    return 1
fi
