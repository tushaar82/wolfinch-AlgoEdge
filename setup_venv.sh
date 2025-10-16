#!/bin/bash
# Setup script for Wolfinch with virtual environment

echo "=========================================="
echo "Wolfinch Setup Script"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created"
    else
        echo "❌ Failed to create virtual environment"
        echo "Try: sudo apt install python3-venv python3-full"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo ""
echo "Installing Wolfinch dependencies..."
pip install -r requirement.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "To use Wolfinch:"
    echo "  1. Activate virtual environment:"
    echo "     source venv/bin/activate"
    echo ""
    echo "  2. Run Wolfinch:"
    echo "     ./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml"
    echo ""
    echo "  3. Deactivate when done:"
    echo "     deactivate"
    echo ""
else
    echo ""
    echo "❌ Installation failed. Check errors above."
    exit 1
fi
