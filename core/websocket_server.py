import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Set
from datetime import datetime
import uuid
from core.assistant_core import AssistantCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket server for real-time communication with mobile clients"""
    
    def __init__(self, assistant_core: AssistantCore, host: str = '0.0.0.0', port: int = 8765):
        self.assistant_core = assistant_core
        self.host = host
        self.port = port
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.active_connections: Set[websockets.WebSocketServerProtocol] = set()
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Register a new client connection"""
        client_id = str(uuid.uuid4())
        client_info = {
            'id': client_id,
            'websocket': websocket,
            'connected_at': datetime.now().isoformat(),
            'path': path,
            'authenticated': False,
            'user_id': None
        }
        
        self.clients[client_id] = client_info
        self.active_connections.add(websocket)
        
        # Send welcome message
        await self.send_message(websocket, {
            'type': 'connection',
            'status': 'connected',
            'client_id': client_id,
            'message': 'Welcome to Empirion AI Assistant',
            'capabilities': self.assistant_core.get_status()['capabilities']
        })
        
        logger.info(f"Client {client_id} connected from {websocket.remote_address}")
        return client_id
    
    async def unregister_client(self, client_id: str):
        """Unregister a client connection"""
        if client_id in self.clients:
            websocket = self.clients[client_id]['websocket']
            self.active_connections.discard(websocket)
            del self.clients[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def authenticate_client(self, client_id: str, auth_data: Dict[str, Any]) -> bool:
        """Authenticate a client"""
        # TODO: Implement actual authentication
        # For now, accept any auth attempt
        if client_id in self.clients:
            self.clients[client_id]['authenticated'] = True
            self.clients[client_id]['user_id'] = auth_data.get('user_id', client_id)
            return True
        return False
    
    async def send_message(self, websocket: websockets.WebSocketServerProtocol, message: Dict[str, Any]):
        """Send a message to a specific client"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Attempted to send message to closed connection")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    async def broadcast_message(self, message: Dict[str, Any], exclude_client: str = None):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        
        for client_id, client_info in self.clients.items():
            if exclude_client and client_id == exclude_client:
                continue
                
            try:
                await self.send_message(client_info['websocket'], message)
            except:
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.unregister_client(client_id)
    
    async def handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """Handle incoming message from client"""
        try:
            message_type = message.get('type', 'unknown')
            
            if message_type == 'auth':
                # Handle authentication
                auth_success = await self.authenticate_client(client_id, message.get('data', {}))
                await self.send_message(self.clients[client_id]['websocket'], {
                    'type': 'auth_response',
                    'success': auth_success,
                    'timestamp': datetime.now().isoformat()
                })
                
            elif message_type == 'request':
                # Handle assistant request
                if not self.clients[client_id]['authenticated']:
                    await self.send_message(self.clients[client_id]['websocket'], {
                        'type': 'error',
                        'message': 'Authentication required',
                        'timestamp': datetime.now().isoformat()
                    })
                    return
                
                user_id = self.clients[client_id]['user_id']
                request_data = message.get('data', {})
                
                # Process request through assistant core
                response = await self.assistant_core.process_request(user_id, request_data)
                
                # Send response back to client
                await self.send_message(self.clients[client_id]['websocket'], {
                    'type': 'response',
                    'request_id': message.get('request_id'),
                    'data': response,
                    'timestamp': datetime.now().isoformat()
                })
                
            elif message_type == 'ping':
                # Handle ping/pong for connection keep-alive
                await self.send_message(self.clients[client_id]['websocket'], {
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })
                
            elif message_type == 'status':
                # Send assistant status
                status = self.assistant_core.get_status()
                await self.send_message(self.clients[client_id]['websocket'], {
                    'type': 'status_response',
                    'data': status,
                    'timestamp': datetime.now().isoformat()
                })
                
            elif message_type == 'subscribe':
                # Handle event subscriptions
                events = message.get('events', [])
                if 'events' not in self.clients[client_id]:
                    self.clients[client_id]['events'] = set()
                self.clients[client_id]['events'].update(events)
                
                await self.send_message(self.clients[client_id]['websocket'], {
                    'type': 'subscription_confirmed',
                    'events': list(self.clients[client_id]['events']),
                    'timestamp': datetime.now().isoformat()
                })
                
            else:
                # Unknown message type
                await self.send_message(self.clients[client_id]['websocket'], {
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error handling client message: {str(e)}")
            await self.send_message(self.clients[client_id]['websocket'], {
                'type': 'error',
                'message': 'Internal server error',
                'timestamp': datetime.now().isoformat()
            })
    
    async def client_handler(self, websocket: websockets.WebSocketServerProtocol):
        """Handle a client connection"""
        path = "/"  # Default path since newer websockets doesn't pass it
        client_id = await self.register_client(websocket, path)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(client_id, data)
                except json.JSONDecodeError:
                    await self.send_message(websocket, {
                        'type': 'error',
                        'message': 'Invalid JSON format',
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} connection closed")
        except Exception as e:
            logger.error(f"Unexpected error with client {client_id}: {str(e)}")
        finally:
            await self.unregister_client(client_id)
    
    async def send_event(self, event_type: str, event_data: Dict[str, Any]):
        """Send an event to all subscribed clients"""
        message = {
            'type': 'event',
            'event_type': event_type,
            'data': event_data,
            'timestamp': datetime.now().isoformat()
        }
        
        for client_id, client_info in self.clients.items():
            if 'events' in client_info and event_type in client_info['events']:
                try:
                    await self.send_message(client_info['websocket'], message)
                except:
                    logger.warning(f"Failed to send event to client {client_id}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(self.client_handler, self.host, self.port):
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        authenticated_clients = sum(1 for c in self.clients.values() if c['authenticated'])
        
        return {
            'total_connections': len(self.active_connections),
            'authenticated_clients': authenticated_clients,
            'clients': [
                {
                    'id': client_id,
                    'authenticated': info['authenticated'],
                    'connected_at': info['connected_at'],
                    'subscribed_events': list(info.get('events', []))
                }
                for client_id, info in self.clients.items()
            ]
        }

# Example usage and protocol documentation
WEBSOCKET_PROTOCOL = """
WebSocket Protocol Documentation:

1. Connection:
   - Connect to ws://host:port
   - Receive welcome message with capabilities

2. Authentication:
   {
       "type": "auth",
       "data": {
           "user_id": "user123",
           "token": "auth_token"
       }
   }

3. Making Requests:
   {
       "type": "request",
       "request_id": "unique_id",
       "data": {
           "type": "text|voice|action|system",
           "content": "request content",
           "metadata": {}
       }
   }

4. Subscribing to Events:
   {
       "type": "subscribe",
       "events": ["notification", "call", "message", "system"]
   }

5. Keep-Alive:
   {
       "type": "ping"
   }

6. Response Format:
   {
       "type": "response|event|error",
       "request_id": "matching_request_id",
       "data": {},
       "timestamp": "ISO 8601 timestamp"
   }
"""

if __name__ == "__main__":
    # Example standalone server
    config = {
        'openai_api_key': None,  # Add your API key
        'debug': True
    }
    
    assistant = AssistantCore(config)
    assistant.start()
    
    server = WebSocketServer(assistant)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        assistant.stop()
