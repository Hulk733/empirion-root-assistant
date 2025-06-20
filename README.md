# Empirion AI Assistant

A comprehensive mobile AI assistant designed specifically for Samsung devices, featuring advanced voice interaction, phone integration, Samsung Store API access, and a modern web interface.

## Features

### 🎯 Core Capabilities
- **AI-Powered Conversations**: Natural language processing using OpenAI's GPT models
- **Voice Interaction**: Wake word detection, speech recognition, and text-to-speech
- **Phone Integration**: Make calls, send SMS, manage contacts, and control device settings
- **Samsung Store Integration**: Search, install, update, and manage apps
- **Web Interface**: Modern, responsive dashboard for remote control
- **Real-time Communication**: WebSocket-based architecture for instant updates

### 📱 Phone Features
- Make phone calls
- Send SMS messages
- Access and manage contacts
- View call logs
- Control volume and brightness
- Toggle airplane mode
- Manage notifications

### 🏪 Samsung Store Features
- Search for apps
- Get app details and reviews
- Install and uninstall apps
- Check for updates
- Get personalized recommendations
- Browse by categories

### 🎤 Voice Assistant Features
- Wake word activation ("Hey Empirion")
- Natural voice commands
- Multi-language support
- Context-aware responses
- Custom command registration
- Continuous listening mode

## Installation

### Prerequisites
- Python 3.8 or higher
- Samsung Android device (for full functionality)
- Termux (for running on Android)
- Node.js (optional, for web interface development)

### Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/empirion-assistant.git
cd empirion-assistant
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. **For Android/Termux setup**
```bash
# Install required packages
pkg install python nodejs git
pkg install portaudio # For audio support

# Install Termux API
pkg install termux-api

# Grant necessary permissions
termux-setup-storage
```

## Usage

### Starting the Assistant

**Basic usage:**
```bash
python main.py
```

**With custom options:**
```bash
# Specify custom port
python main.py --port 8080

# Disable voice features
python main.py --no-voice

# Enable debug mode
python main.py --debug

# Use custom config file
python main.py --config my_config.json
```

### Web Interface

1. Start the assistant server
2. Open `web/index.html` in your browser
3. Configure the WebSocket URL in settings
4. Start interacting with the assistant

### Voice Commands

Default wake word: "Hey Empirion"

Example commands:
- "Hey Empirion, call John"
- "Hey Empirion, send a message to Mom"
- "Hey Empirion, install WhatsApp"
- "Hey Empirion, what's the weather?"
- "Hey Empirion, set volume to 50"

## Configuration

Create a `config.json` file to customize settings:

```json
{
    "openai_api_key": "your-api-key",
    "websocket": {
        "host": "0.0.0.0",
        "port": 8765
    },
    "voice": {
        "enabled": true,
        "language": "en-US",
        "wake_word": "hey empirion"
    },
    "phone": {
        "enabled": true
    },
    "samsung_store": {
        "enabled": true
    }
}
```

## API Documentation

### WebSocket API

Connect to `ws://localhost:8765`

**Authentication:**
```json
{
    "type": "auth",
    "data": {
        "user_id": "user123",
        "token": "your-token"
    }
}
```

**Send a request:**
```json
{
    "type": "request",
    "request_id": "unique-id",
    "data": {
        "type": "text",
        "content": "Hello, assistant!",
        "metadata": {}
    }
}
```

**Subscribe to events:**
```json
{
    "type": "subscribe",
    "events": ["notification", "call", "message", "system"]
}
```

### REST API Endpoints

The assistant also exposes REST endpoints (when enabled):

- `GET /api/status` - Get assistant status
- `POST /api/message` - Send a message
- `GET /api/capabilities` - Get available features
- `POST /api/phone/call` - Make a phone call
- `GET /api/store/search` - Search apps

## Development

### Project Structure
```
empirion-assistant/
├── core/
│   ├── assistant_core.py      # Main assistant logic
│   ├── websocket_server.py    # WebSocket server
│   ├── phone_integration.py   # Phone features
│   ├── samsung_store_api.py   # Store integration
│   └── digital_assistant_api.py # Voice features
├── web/
│   ├── index.html             # Web interface
│   ├── app.js                 # JavaScript client
│   └── styles.css             # Custom styles
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
└── README.md                  # Documentation
```

### Adding Custom Commands

```python
from core.digital_assistant_api import DigitalAssistantAPI

# Create custom handler
async def handle_custom_command(parsed):
    return {
        'action': 'custom',
        'response': 'Custom command executed!'
    }

# Register the command
assistant.register_command('custom', handle_custom_command)
```

### Extending Phone Integration

```python
from core.phone_integration import PhoneIntegration

class ExtendedPhoneIntegration(PhoneIntegration):
    async def custom_phone_action(self):
        # Your custom implementation
        pass
```

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Check firewall settings
   - Ensure port is not in use
   - Verify network connectivity

2. **Voice recognition not working**
   - Check microphone permissions
   - Install required audio libraries
   - Verify language settings

3. **Phone features not available**
   - Install Termux API
   - Grant necessary Android permissions
   - Run as root (for some features)

### Debug Mode

Enable debug logging:
```bash
python main.py --debug
```

Check logs in:
- Console output
- `logs/assistant.log` (if configured)

## Security Considerations

- Store API keys securely (use environment variables)
- Implement proper authentication for WebSocket connections
- Use HTTPS for web interface in production
- Regularly update dependencies
- Review permissions requested by the app

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- Samsung for device APIs
- The open-source community for various libraries used

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: support@empirion-assistant.com
- Documentation: https://docs.empirion-assistant.com

---

**Note**: This assistant requires appropriate permissions and may not work with all features on non-rooted devices. Some features are specific to Samsung devices and Termux environment.
