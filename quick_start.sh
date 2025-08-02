#!/bin/bash

echo "🚀 Ferias CLI Toolkit - Quick Start"
echo "=================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
python3 test_installation.py

# Check if test was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "📖 Quick Usage Examples:"
    echo "  # Scrape feria data from a URL"
    echo "  python3 scrape_ferias_json.py -u \"http://example.com/ferias\""
    echo ""
    echo "  # Generate map from JSON data"
    echo "  python3 generate_ferias_map.py -i ferias.json"
    echo ""
    echo "  # Get help"
    echo "  python3 scrape_ferias_json.py --help"
    echo "  python3 generate_ferias_map.py --help"
    echo ""
    echo "📚 For more information, see README.md"
else
    echo ""
    echo "⚠️  Installation completed with warnings. Some features may not work."
    echo "Please check the test output above for details."
fi 