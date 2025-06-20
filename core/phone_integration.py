import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneIntegration:
    """Handle phone-specific capabilities and integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.termux_api_available = self._check_termux_api()
        self.adb_available = self._check_adb()
        
        logger.info(f"PhoneIntegration initialized - Termux API: {self.termux_api_available}, ADB: {self.adb_available}")
    
    def _check_termux_api(self) -> bool:
        """Check if Termux API is available"""
        try:
            result = subprocess.run(['which', 'termux-telephony-call'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_adb(self) -> bool:
        """Check if ADB is available for advanced operations"""
        try:
            result = subprocess.run(['which', 'adb'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    async def make_phone_call(self, number: str) -> Dict[str, Any]:
        """Make a phone call"""
        try:
            if self.termux_api_available:
                # Use Termux API
                cmd = ['termux-telephony-call', number]
                result = await self._run_command(cmd)
                
                return {
                    'success': True,
                    'action': 'phone_call',
                    'number': number,
                    'method': 'termux_api',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Fallback to intent
                cmd = ['am', 'start', '-a', 'android.intent.action.CALL', 
                       '-d', f'tel:{number}']
                result = await self._run_command(cmd)
                
                return {
                    'success': True,
                    'action': 'phone_call',
                    'number': number,
                    'method': 'intent',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error making phone call: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def send_sms(self, number: str, message: str) -> Dict[str, Any]:
        """Send an SMS message"""
        try:
            if self.termux_api_available:
                # Use Termux API
                cmd = ['termux-sms-send', '-n', number, message]
                result = await self._run_command(cmd)
                
                return {
                    'success': True,
                    'action': 'send_sms',
                    'number': number,
                    'message': message[:50] + '...' if len(message) > 50 else message,
                    'method': 'termux_api',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Fallback to intent
                cmd = ['am', 'start', '-a', 'android.intent.action.SENDTO',
                       '-d', f'sms:{number}', '--es', 'sms_body', message]
                result = await self._run_command(cmd)
                
                return {
                    'success': True,
                    'action': 'send_sms',
                    'number': number,
                    'method': 'intent',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_contacts(self, search_query: Optional[str] = None) -> Dict[str, Any]:
        """Get phone contacts"""
        try:
            if self.termux_api_available:
                cmd = ['termux-contact-list']
                result = await self._run_command(cmd)
                
                contacts = json.loads(result.stdout) if result.stdout else []
                
                # Filter by search query if provided
                if search_query:
                    search_lower = search_query.lower()
                    contacts = [c for c in contacts 
                              if search_lower in c.get('name', '').lower()]
                
                return {
                    'success': True,
                    'contacts': contacts[:20],  # Limit to 20 contacts
                    'total': len(contacts),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Contacts access requires Termux API',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting contacts: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_call_log(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent call log"""
        try:
            if self.termux_api_available:
                cmd = ['termux-call-log', '-l', str(limit)]
                result = await self._run_command(cmd)
                
                call_log = json.loads(result.stdout) if result.stdout else []
                
                return {
                    'success': True,
                    'call_log': call_log,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Call log access requires Termux API',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting call log: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_sms_inbox(self, limit: int = 10) -> Dict[str, Any]:
        """Get SMS inbox messages"""
        try:
            if self.termux_api_available:
                cmd = ['termux-sms-list', '-l', str(limit)]
                result = await self._run_command(cmd)
                
                messages = json.loads(result.stdout) if result.stdout else []
                
                return {
                    'success': True,
                    'messages': messages,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'SMS access requires Termux API',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting SMS inbox: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        try:
            device_info = {}
            
            if self.termux_api_available:
                # Get telephony info
                cmd = ['termux-telephony-deviceinfo']
                result = await self._run_command(cmd)
                if result.stdout:
                    device_info['telephony'] = json.loads(result.stdout)
                
                # Get battery status
                cmd = ['termux-battery-status']
                result = await self._run_command(cmd)
                if result.stdout:
                    device_info['battery'] = json.loads(result.stdout)
            
            # Get system properties using getprop
            properties = ['ro.product.model', 'ro.product.brand', 
                         'ro.build.version.release', 'ro.product.cpu.abi']
            
            for prop in properties:
                cmd = ['getprop', prop]
                result = await self._run_command(cmd)
                if result.stdout:
                    key = prop.split('.')[-1]
                    device_info[key] = result.stdout.strip()
            
            return {
                'success': True,
                'device_info': device_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting device info: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def toggle_airplane_mode(self, enable: bool) -> Dict[str, Any]:
        """Toggle airplane mode"""
        try:
            if self.adb_available:
                # Use ADB for system settings
                value = '1' if enable else '0'
                cmd = ['adb', 'shell', 'settings', 'put', 'global', 
                       'airplane_mode_on', value]
                await self._run_command(cmd)
                
                # Broadcast change
                cmd = ['adb', 'shell', 'am', 'broadcast', '-a', 
                       'android.intent.action.AIRPLANE_MODE']
                await self._run_command(cmd)
                
                return {
                    'success': True,
                    'action': 'airplane_mode',
                    'enabled': enable,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Try using settings command directly
                value = '1' if enable else '0'
                cmd = ['settings', 'put', 'global', 'airplane_mode_on', value]
                await self._run_command(cmd)
                
                return {
                    'success': True,
                    'action': 'airplane_mode',
                    'enabled': enable,
                    'method': 'settings',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error toggling airplane mode: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def set_volume(self, stream: str, level: int) -> Dict[str, Any]:
        """Set volume for different audio streams"""
        try:
            # Map stream names to Android audio stream types
            stream_map = {
                'ring': '2',
                'media': '3',
                'alarm': '4',
                'notification': '5',
                'system': '1',
                'call': '0'
            }
            
            stream_id = stream_map.get(stream, '3')  # Default to media
            
            if self.termux_api_available:
                cmd = ['termux-volume', stream, str(level)]
                await self._run_command(cmd)
            else:
                # Use media command
                cmd = ['media', 'volume', '--stream', stream_id, 
                       '--set', str(level)]
                await self._run_command(cmd)
            
            return {
                'success': True,
                'action': 'set_volume',
                'stream': stream,
                'level': level,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error setting volume: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_notifications(self) -> Dict[str, Any]:
        """Get current notifications"""
        try:
            if self.termux_api_available:
                cmd = ['termux-notification-list']
                result = await self._run_command(cmd)
                
                notifications = json.loads(result.stdout) if result.stdout else []
                
                return {
                    'success': True,
                    'notifications': notifications,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Notification access requires Termux API',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def create_notification(self, title: str, content: str, 
                                priority: str = 'default') -> Dict[str, Any]:
        """Create a notification"""
        try:
            if self.termux_api_available:
                cmd = ['termux-notification', '-t', title, '-c', content,
                       '--priority', priority]
                await self._run_command(cmd)
                
                return {
                    'success': True,
                    'action': 'create_notification',
                    'title': title,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Notification creation requires Termux API',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run a command asynchronously"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout.decode('utf-8') if stdout else '',
            stderr=stderr.decode('utf-8') if stderr else ''
        )
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get available phone capabilities"""
        return {
            'phone_calls': True,
            'sms': True,
            'contacts': self.termux_api_available,
            'call_log': self.termux_api_available,
            'notifications': self.termux_api_available,
            'volume_control': True,
            'airplane_mode': True,
            'device_info': True,
            'advanced_features': self.adb_available
        }
