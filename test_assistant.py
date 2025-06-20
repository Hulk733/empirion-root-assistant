#!/usr/bin/env python3
"""
Test script for Empirion AI Assistant
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test WebSocket connection and basic messaging"""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to {uri}")
            
            # Wait for connection message
            response = await websocket.recv()
            logger.info(f"Connection response: {response}")
            
            # Send authentication
            auth_message = {
                "type": "auth",
                "data": {
                    "user_id": "test_user",
                    "token": "test_token"
                }
            }
            await websocket.send(json.dumps(auth_message))
            logger.info("Sent authentication")
            
            # Wait for auth response
            auth_response = await websocket.recv()
            logger.info(f"Auth response: {auth_response}")
            
            # Send a test message
            test_message = {
                "type": "request",
                "request_id": "test_001",
                "data": {
                    "type": "text",
                    "content": "Hello, Empirion! What can you do?",
                    "metadata": {
                        "language": "en-US"
                    }
                }
            }
            await websocket.send(json.dumps(test_message))
            logger.info("Sent test message")
            
            # Wait for response
            message_response = await websocket.recv()
            logger.info(f"Message response: {message_response}")
            
            # Test quick action
            action_message = {
                "type": "request",
                "request_id": "test_002",
                "data": {
                    "type": "action",
                    "content": "get_capabilities",
                    "metadata": {}
                }
            }
            await websocket.send(json.dumps(action_message))
            logger.info("Sent capabilities request")
            
            # Wait for response
            capabilities_response = await websocket.recv()
            logger.info(f"Capabilities: {capabilities_response}")
            
            logger.info("WebSocket test completed successfully!")
            
    except Exception as e:
        logger.error(f"WebSocket test failed: {str(e)}")
        return False
    
    return True

def test_imports():
    """Test that all modules can be imported"""
    try:
        from core.assistant_core import AssistantCore
        logger.info("✓ assistant_core imported successfully")
        
        from core.websocket_server import WebSocketServer
        logger.info("✓ websocket_server imported successfully")
        
        from core.phone_integration import PhoneIntegration
        logger.info("✓ phone_integration imported successfully")
        
        from core.samsung_store_api import SamsungStoreAPI
        logger.info("✓ samsung_store_api imported successfully")
        
        from core.digital_assistant_api import DigitalAssistantAPI
        logger.info("✓ digital_assistant_api imported successfully")
        
        return True
    except ImportError as e:
        logger.error(f"Import test failed: {str(e)}")
        return False

async def test_phone_integration():
    """Test phone integration capabilities"""
    from core.phone_integration import PhoneIntegration
    
    config = {"phone": {"enabled": True}}
    phone = PhoneIntegration(config)
    
    # Test capabilities
    capabilities = phone.get_capabilities()
    logger.info(f"Phone capabilities: {json.dumps(capabilities, indent=2)}")
    
    # Test getting contacts (simulated)
    contacts = await phone.get_contacts(limit=5)
    logger.info(f"Contacts test: {contacts['success']}")
    
    return True

async def test_samsung_store():
    """Test Samsung Store API"""
    from core.samsung_store_api import SamsungStoreAPI
    
    config = {"samsung_store": {"enabled": True}}
    
    async with SamsungStoreAPI(config) as store:
        # Test search
        search_result = await store.search_apps("notes", limit=3)
        logger.info(f"Search test: {search_result['success']}")
        
        # Test recommendations
        recommendations = await store.get_app_recommendations()
        logger.info(f"Recommendations test: {recommendations['success']}")
        
        # Test capabilities
        capabilities = store.get_capabilities()
        logger.info(f"Store capabilities: {json.dumps(capabilities, indent=2)}")
    
    return True

async def test_digital_assistant():
    """Test digital assistant API"""
    from core.digital_assistant_api import DigitalAssistantAPI
    
    config = {
        "enabled": True,
        "language": "en-US",
        "wake_word": "hey empirion"
    }
    
    assistant = DigitalAssistantAPI(config)
    
    # Test capabilities
    capabilities = assistant.get_capabilities()
    logger.info(f"Assistant capabilities: {json.dumps(capabilities, indent=2)}")
    
    # Test command parsing
    parsed = assistant._parse_command("Call John at 3 PM")
    logger.info(f"Parsed command: {json.dumps(parsed, indent=2)}")
    
    # Test TTS (without actually speaking)
    assistant.voice_enabled = False
    await assistant.speak("This is a test")
    logger.info("TTS test completed")
    
    return True

async def run_all_tests():
    """Run all tests"""
    logger.info("Starting Empirion AI Assistant tests...")
    logger.info("=" * 50)
    
    # Test imports
    logger.info("\n1. Testing imports...")
    if not test_imports():
        logger.error("Import tests failed. Please check dependencies.")
        return
    
    # Test individual components
    logger.info("\n2. Testing Phone Integration...")
    await test_phone_integration()
    
    logger.info("\n3. Testing Samsung Store API...")
    await test_samsung_store()
    
    logger.info("\n4. Testing Digital Assistant...")
    await test_digital_assistant()
    
    # Test WebSocket (requires server to be running)
    logger.info("\n5. Testing WebSocket connection...")
    logger.info("Note: This requires the server to be running (python main.py)")
    # Uncomment to test when server is running
    # await test_websocket_connection()
    
    logger.info("\n" + "=" * 50)
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
