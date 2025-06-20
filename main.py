#!/usr/bin/env python3
"""
Empirion AI Assistant - Main Application
A comprehensive mobile AI assistant for Samsung devices
"""

import asyncio
import logging
import argparse
import json
import os
from typing import Dict, Any

# Import core components
from core.assistant_core import AssistantCore
from core.websocket_server import WebSocketServer
from core.phone_integration import PhoneIntegration
from core.samsung_store_api import SamsungStoreAPI
from core.digital_assistant_api import DigitalAssistantAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmpirionAssistant:
    """Main application class for Empirion AI Assistant"""
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.components = {}
        self.running = False
        
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'websocket': {
                'host': '0.0.0.0',
                'port': 8765
            },
            'voice': {
                'enabled': True,
                'language': 'en-US',
                'wake_word': 'hey empirion'
            },
            'phone': {
                'enabled': True
            },
            'samsung_store': {
                'enabled': True
            },
            'debug': False
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **user_config}
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {str(e)}")
        
        return default_config
    
    async def initialize_components(self):
        """Initialize all assistant components"""
        logger.info("Initializing Empirion AI Assistant components...")
        
        # Initialize core assistant
        self.components['core'] = AssistantCore(self.config)
        self.components['core'].start()
        
        # Initialize phone integration
        if self.config['phone']['enabled']:
            self.components['phone'] = PhoneIntegration(self.config)
            self.components['core'].phone_integration = self.components['phone']
        
        # Initialize Samsung Store API
        if self.config['samsung_store']['enabled']:
            self.components['samsung_store'] = SamsungStoreAPI(self.config)
            self.components['core'].samsung_store = self.components['samsung_store']
        
        # Initialize digital assistant
        if self.config['voice']['enabled']:
            self.components['digital_assistant'] = DigitalAssistantAPI(self.config['voice'])
            self.components['core'].digital_assistant = self.components['digital_assistant']
        
        # Initialize WebSocket server
        self.components['websocket'] = WebSocketServer(
            self.components['core'],
            host=self.config['websocket']['host'],
            port=self.config['websocket']['port']
        )
        
        logger.info("All components initialized successfully")
    
    async def start(self):
        """Start the assistant"""
        self.running = True
        logger.info("Starting Empirion AI Assistant...")
        
        # Initialize components
        await self.initialize_components()
        
        # Create tasks for different components
        tasks = []
        
        # WebSocket server task
        websocket_task = asyncio.create_task(
            self.components['websocket'].start_server()
        )
        tasks.append(websocket_task)
        
        # Voice assistant task (if enabled)
        if self.config['voice']['enabled'] and 'digital_assistant' in self.components:
            voice_task = asyncio.create_task(
                self.run_voice_assistant()
            )
            tasks.append(voice_task)
        
        # Status monitoring task
        monitor_task = asyncio.create_task(self.monitor_status())
        tasks.append(monitor_task)
        
        logger.info(f"Empirion AI Assistant is running!")
        logger.info(f"WebSocket server: ws://{self.config['websocket']['host']}:{self.config['websocket']['port']}")
        logger.info(f"Web interface: Open web/index.html in your browser")
        
        try:
            # Wait for all tasks
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        finally:
            await self.shutdown()
    
    async def run_voice_assistant(self):
        """Run the voice assistant in continuous listening mode"""
        logger.info("Starting voice assistant...")
        
        # Register custom commands
        assistant = self.components['digital_assistant']
        
        # Register phone commands
        if 'phone' in self.components:
            assistant.register_command('call', self.handle_call_command)
            assistant.register_command('message', self.handle_message_command)
            assistant.register_command('text', self.handle_message_command)
        
        # Register app commands
        if 'samsung_store' in self.components:
            assistant.register_command('install', self.handle_install_command)
            assistant.register_command('search', self.handle_search_command)
        
        # Start continuous listening
        try:
            await assistant.start_continuous_listening()
        except Exception as e:
            logger.error(f"Voice assistant error: {str(e)}")
    
    async def handle_call_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice call commands"""
        contact = parsed['entities'].get('contact')
        
        if contact:
            # In a real implementation, would look up contact number
            response = f"I'll call {contact} for you"
            # Simulate making a call
            result = await self.components['phone'].make_phone_call(contact)
        else:
            response = "Who would you like to call?"
            result = {'success': False}
        
        return {
            'action': 'call',
            'response': response,
            'result': result
        }
    
    async def handle_message_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SMS/message commands"""
        contact = parsed['entities'].get('contact')
        
        if contact:
            response = f"What message would you like to send to {contact}?"
        else:
            response = "Who would you like to message?"
        
        return {
            'action': 'message',
            'response': response,
            'needs_followup': True
        }
    
    async def handle_install_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle app installation commands"""
        # Extract app name from command
        words = parsed['words']
        if 'install' in words:
            idx = words.index('install')
            if idx < len(words) - 1:
                app_name = ' '.join(words[idx+1:])
                
                # Search for app
                search_result = await self.components['samsung_store'].search_apps(app_name, limit=1)
                
                if search_result['success'] and search_result['results']:
                    app = search_result['results'][0]
                    response = f"I found {app['name']}. Installing it now..."
                    
                    # Initiate installation
                    install_result = await self.components['samsung_store'].install_app(app['package_name'])
                else:
                    response = f"I couldn't find an app called {app_name}"
            else:
                response = "What app would you like to install?"
        else:
            response = "Please specify which app to install"
        
        return {
            'action': 'install',
            'response': response
        }
    
    async def handle_search_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search commands"""
        words = parsed['words']
        if 'search' in words or 'find' in words:
            # Extract search query
            search_words = ['search', 'find', 'for']
            query_words = [w for w in words if w not in search_words]
            query = ' '.join(query_words)
            
            if query:
                response = f"Searching for {query}..."
                # Could search apps, contacts, etc.
            else:
                response = "What would you like to search for?"
        else:
            response = "Please specify what to search"
        
        return {
            'action': 'search',
            'response': response,
            'query': query if 'query' in locals() else None
        }
    
    async def monitor_status(self):
        """Monitor system status periodically"""
        while self.running:
            try:
                # Get status from all components
                status = {
                    'core': self.components['core'].get_status(),
                    'websocket': self.components['websocket'].get_server_stats(),
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                # Log active connections
                if status['websocket']['total_connections'] > 0:
                    logger.debug(f"Active connections: {status['websocket']['total_connections']}")
                
                # Check for any issues
                if not status['core']['is_running']:
                    logger.warning("Core assistant is not running!")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in status monitor: {str(e)}")
                await asyncio.sleep(30)
    
    async def shutdown(self):
        """Shutdown the assistant gracefully"""
        logger.info("Shutting down Empirion AI Assistant...")
        self.running = False
        
        # Stop core assistant
        if 'core' in self.components:
            self.components['core'].stop()
        
        # Close WebSocket connections
        if 'websocket' in self.components:
            # Send shutdown event to all clients
            await self.components['websocket'].send_event('system', {
                'message': 'Server is shutting down',
                'action': 'shutdown'
            })
        
        logger.info("Empirion AI Assistant shutdown complete")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Empirion AI Assistant')
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file',
        default='config.json'
    )
    parser.add_argument(
        '--host',
        type=str,
        help='WebSocket server host',
        default='0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='WebSocket server port',
        default=8765
    )
    parser.add_argument(
        '--no-voice',
        action='store_true',
        help='Disable voice assistant'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create assistant instance
    assistant = EmpirionAssistant(args.config)
    
    # Override config with command line arguments
    if args.host:
        assistant.config['websocket']['host'] = args.host
    if args.port:
        assistant.config['websocket']['port'] = args.port
    if args.no_voice:
        assistant.config['voice']['enabled'] = False
    
    # Run the assistant
    try:
        asyncio.run(assistant.start())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == '__main__':
    main()
