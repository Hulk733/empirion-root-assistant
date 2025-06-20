#!/usr/bin/env python3
"""
Minimal test server for Empirion AI Assistant
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any

# Import only essential components
from core.assistant_core import AssistantCore
from core.websocket_server import WebSocketServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinimalEmpirionAssistant:
    """Minimal version for testing"""
    
    def __init__(self):
        self.config = {
            'openai_api_key': os.getenv('OPENAI_API_KEY', 'demo-key'),
            'websocket': {
                'host': '0.0.0.0',
                'port': 8765
            }
        }
        self.components = {}
        
    async def start(self):
        """Start the minimal assistant"""
        logger.info("Starting Minimal Empirion AI Assistant...")
        
        # Initialize core assistant
        self.components['core'] = AssistantCore(self.config)
        self.components['core'].start()
        
        # Initialize WebSocket server
        self.components['websocket'] = WebSocketServer(
            self.components['core'],
            host=self.config['websocket']['host'],
            port=self.config['websocket']['port']
        )
        
        logger.info(f"Starting WebSocket server on {self.config['websocket']['host']}:{self.config['websocket']['port']}")
        
        # Start WebSocket server
        await self.components['websocket'].start_server()

def main():
    """Main entry point"""
    assistant = MinimalEmpirionAssistant()
    
    try:
        asyncio.run(assistant.start())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == '__main__':
    main()
