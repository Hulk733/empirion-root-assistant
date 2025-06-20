#!/bin/bash
# Empirion AI Assistant - Setup Script

echo "======================================"
echo "Empirion AI Assistant Setup"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s
' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p cache
echo "✓ Directories created"

# Copy configuration files
echo ""
echo "Setting up configuration files..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo "  Please edit .env and add your API keys"
else
    echo "✓ .env file already exists"
fi

if [ ! -f "config.json" ]; then
    cp config.example.json config.json
    echo "✓ Created config.json from template"
    echo "  Please review and update config.json as needed"
else
    echo "✓ config.json already exists"
fi

# Check for Termux environment
if [ -n "$TERMUX_VERSION" ]; then
    echo ""
    echo "Detected Termux environment..."
    echo "Installing Termux-specific packages..."
    
    # Install Termux API
    pkg install termux-api -y
    
    # Install audio support
    pkg install portaudio -y
    
    # Request permissions
    echo "Requesting necessary permissions..."
    termux-setup-storage
    
    echo "✓ Termux setup completed"
fi

# Test imports
echo ""
echo "Testing Python imports..."
python3 -c "
try:
    import openai
    print('✓ OpenAI module imported')
except:
    print('✗ OpenAI module not found')
    
try:
    import websockets
    print('✓ WebSockets module imported')
except:
    print('✗ WebSockets module not found')
    
try:
    import speech_recognition
    print('✓ Speech Recognition module imported')
except:
    print('✗ Speech Recognition module not found')
"

echo ""
echo "======================================"
echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Review config.json for any customizations"
echo "3. Run the assistant with: python main.py"
echo "4. Open web/index.html in your browser"
echo ""
echo "For testing: python test_assistant.py"
echo "======================================"
