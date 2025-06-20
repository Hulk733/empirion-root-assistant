import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import os
import tempfile
import subprocess
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DigitalAssistantAPI:
    """Digital assistant capabilities for voice interaction and natural language processing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.tts_engine = None
        self.voice_enabled = config.get('voice_enabled', True)
        self.language = config.get('language', 'en-US')
        self.wake_word = config.get('wake_word', 'hey assistant')
        self.command_handlers: Dict[str, Callable] = {}
        self.context_stack: List[Dict[str, Any]] = []
        
        # Initialize TTS engine
        self._initialize_tts()
        
        # Register default commands
        self._register_default_commands()
        
        logger.info(f"DigitalAssistantAPI initialized - Language: {self.language}, Wake word: {self.wake_word}")
    
    def _initialize_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure voice properties
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a voice matching the language
                for voice in voices:
                    if self.language[:2] in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3: {str(e)}. Will use gTTS as fallback.")
            self.tts_engine = None
    
    def _register_default_commands(self):
        """Register default voice commands"""
        default_commands = {
            'time': self._handle_time_command,
            'date': self._handle_date_command,
            'weather': self._handle_weather_command,
            'help': self._handle_help_command,
            'stop': self._handle_stop_command,
            'repeat': self._handle_repeat_command,
            'volume': self._handle_volume_command,
            'brightness': self._handle_brightness_command
        }
        
        for command, handler in default_commands.items():
            self.register_command(command, handler)
    
    def register_command(self, command: str, handler: Callable):
        """Register a voice command handler"""
        self.command_handlers[command.lower()] = handler
        logger.info(f"Registered command: {command}")
    
    async def listen_for_wake_word(self, timeout: Optional[int] = None) -> bool:
        """Listen for the wake word"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening for wake word...")
                
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
                
                try:
                    text = self.recognizer.recognize_google(audio, language=self.language)
                    logger.info(f"Heard: {text}")
                    
                    return self.wake_word.lower() in text.lower()
                    
                except sr.UnknownValueError:
                    return False
                except sr.RequestError as e:
                    logger.error(f"Speech recognition error: {str(e)}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error listening for wake word: {str(e)}")
            return False
    
    async def listen_for_command(self, timeout: int = 5) -> Optional[str]:
        """Listen for a voice command"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Play listening sound
                await self.play_sound('listening')
                
                logger.info("Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
                try:
                    text = self.recognizer.recognize_google(audio, language=self.language)
                    logger.info(f"Recognized: {text}")
                    return text
                    
                except sr.UnknownValueError:
                    await self.speak("Sorry, I didn't catch that.")
                    return None
                except sr.RequestError as e:
                    logger.error(f"Speech recognition error: {str(e)}")
                    await self.speak("Sorry, there was an error with speech recognition.")
                    return None
                    
        except Exception as e:
            logger.error(f"Error listening for command: {str(e)}")
            return None
    
    async def process_voice_command(self, command: str) -> Dict[str, Any]:
        """Process a voice command"""
        try:
            # Add to context
            self.context_stack.append({
                'command': command,
                'timestamp': datetime.now().isoformat()
            })
            
            # Limit context stack size
            if len(self.context_stack) > 10:
                self.context_stack = self.context_stack[-10:]
            
            # Parse command
            parsed = self._parse_command(command)
            
            # Find matching handler
            handler = None
            for key, func in self.command_handlers.items():
                if key in parsed['action'].lower():
                    handler = func
                    break
            
            if handler:
                # Execute handler
                result = await handler(parsed)
                
                # Speak response if available
                if 'response' in result:
                    await self.speak(result['response'])
                
                return {
                    'success': True,
                    'command': command,
                    'parsed': parsed,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # No handler found, return as general query
                response = f"I heard '{command}' but I'm not sure how to handle that."
                await self.speak(response)
                
                return {
                    'success': False,
                    'command': command,
                    'parsed': parsed,
                    'error': 'No handler found',
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _parse_command(self, command: str) -> Dict[str, Any]:
        """Parse a voice command into structured data"""
        command_lower = command.lower()
        
        # Extract action words
        action_words = ['call', 'send', 'open', 'play', 'search', 'set', 'turn', 
                       'show', 'tell', 'what', 'when', 'where', 'how', 'remind']
        
        action = None
        for word in action_words:
            if word in command_lower:
                action = word
                break
        
        if not action:
            action = 'query'
        
        # Extract entities (simple approach)
        entities = {}
        
        # Time patterns
        time_pattern = r'\b(\d{1,2}:\d{2}|\d{1,2}\s*(am|pm))\b'
        time_match = re.search(time_pattern, command_lower)
        if time_match:
            entities['time'] = time_match.group()
        
        # Number patterns
        number_pattern = r'\b\d+\b'
        numbers = re.findall(number_pattern, command)
        if numbers:
            entities['numbers'] = numbers
        
        # Contact patterns (names)
        if action in ['call', 'message', 'text']:
            # Extract everything after the action as potential contact name
            parts = command_lower.split(action)
            if len(parts) > 1:
                potential_name = parts[1].strip()
                # Remove common words
                for word in ['to', 'a', 'the', 'message', 'text']:
                    potential_name = potential_name.replace(word, '').strip()
                if potential_name:
                    entities['contact'] = potential_name
        
        return {
            'action': action,
            'full_text': command,
            'entities': entities,
            'words': command.split()
        }
    
    async def speak(self, text: str, wait: bool = True):
        """Convert text to speech"""
        if not self.voice_enabled:
            logger.info(f"TTS (disabled): {text}")
            return
        
        try:
            if self.tts_engine:
                # Use pyttsx3
                self.tts_engine.say(text)
                if wait:
                    self.tts_engine.runAndWait()
                else:
                    self.tts_engine.startLoop(False)
                    self.tts_engine.iterate()
                    self.tts_engine.endLoop()
            else:
                # Use gTTS as fallback
                await self._speak_with_gtts(text)
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
    
    async def _speak_with_gtts(self, text: str):
        """Use Google TTS as fallback"""
        try:
            tts = gTTS(text=text, lang=self.language[:2])
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tts.save(tmp_file.name)
                tmp_file_path = tmp_file.name
            
            # Play the audio file
            if os.path.exists('/usr/bin/mpg123'):
                subprocess.run(['mpg123', '-q', tmp_file_path])
            elif os.path.exists('/usr/bin/play'):
                subprocess.run(['play', '-q', tmp_file_path])
            else:
                logger.warning("No audio player found for TTS playback")
            
            # Clean up
            os.unlink(tmp_file_path)
            
        except Exception as e:
            logger.error(f"Error with gTTS: {str(e)}")
    
    async def play_sound(self, sound_type: str):
        """Play system sounds"""
        sound_files = {
            'listening': '/system/media/audio/ui/Effect_Tick.ogg',
            'success': '/system/media/audio/ui/Effect_Tick.ogg',
            'error': '/system/media/audio/ui/Effect_Tick.ogg',
            'notification': '/system/media/audio/notifications/Argon.ogg'
        }
        
        sound_file = sound_files.get(sound_type)
        if sound_file and os.path.exists(sound_file):
            try:
                subprocess.run(['play', '-q', sound_file], capture_output=True)
            except:
                pass
    
    # Default command handlers
    async def _handle_time_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle time-related commands"""
        current_time = datetime.now().strftime("%I:%M %p")
        response = f"The current time is {current_time}"
        
        return {
            'action': 'time',
            'response': response,
            'time': current_time
        }
    
    async def _handle_date_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle date-related commands"""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        response = f"Today is {current_date}"
        
        return {
            'action': 'date',
            'response': response,
            'date': current_date
        }
    
    async def _handle_weather_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather-related commands"""
        # This would integrate with a weather API
        response = "Weather information requires location access and API integration."
        
        return {
            'action': 'weather',
            'response': response,
            'requires_integration': True
        }
    
    async def _handle_help_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help commands"""
        available_commands = list(self.command_handlers.keys())
        response = f"I can help you with: {', '.join(available_commands)}"
        
        return {
            'action': 'help',
            'response': response,
            'available_commands': available_commands
        }
    
    async def _handle_stop_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stop/cancel commands"""
        response = "Okay, stopping."
        
        return {
            'action': 'stop',
            'response': response,
            'should_stop': True
        }
    
    async def _handle_repeat_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle repeat last response"""
        if self.context_stack and len(self.context_stack) > 1:
            # Get the second to last item (last is current command)
            previous = self.context_stack[-2]
            response = f"I said: {previous.get('response', 'Nothing to repeat')}"
        else:
            response = "I don't have anything to repeat."
        
        return {
            'action': 'repeat',
            'response': response
        }
    
    async def _handle_volume_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle volume control commands"""
        numbers = parsed['entities'].get('numbers', [])
        
        if numbers:
            level = int(numbers[0])
            response = f"Setting volume to {level} percent"
        else:
            response = "Please specify a volume level"
        
        return {
            'action': 'volume',
            'response': response,
            'level': level if numbers else None
        }
    
    async def _handle_brightness_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle brightness control commands"""
        numbers = parsed['entities'].get('numbers', [])
        
        if numbers:
            level = int(numbers[0])
            response = f"Setting brightness to {level} percent"
        else:
            response = "Please specify a brightness level"
        
        return {
            'action': 'brightness',
            'response': response,
            'level': level if numbers else None
        }
    
    def register_as_default_assistant(self) -> Dict[str, Any]:
        """Register as the default digital assistant"""
        try:
            # This would require system-level permissions
            # For now, return instructions
            
            return {
                'success': False,
                'message': 'To set as default assistant:',
                'instructions': [
                    '1. Go to Settings > Apps > Default apps',
                    '2. Select "Digital assistant app"',
                    '3. Choose "Empirion AI Assistant"',
                    '4. Grant all required permissions'
                ],
                'required_permissions': [
                    'android.permission.RECORD_AUDIO',
                    'android.permission.BIND_VOICE_INTERACTION',
                    'android.permission.ASSIST_STRUCTURE',
                    'android.permission.ASSIST_SCREENSHOT'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error registering as default assistant: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get digital assistant capabilities"""
        return {
            'voice_recognition': True,
            'text_to_speech': self.tts_engine is not None,
            'wake_word_detection': True,
            'multi_language': True,
            'context_awareness': True,
            'command_registration': True,
            'default_assistant': False,  # Requires system integration
            'supported_languages': ['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE'],
            'registered_commands': list(self.command_handlers.keys())
        }
    
    async def start_continuous_listening(self):
        """Start continuous listening mode"""
        logger.info("Starting continuous listening mode...")
        
        while True:
            try:
                # Listen for wake word
                if await self.listen_for_wake_word(timeout=10):
                    # Wake word detected
                    await self.speak("Yes, how can I help?")
                    
                    # Listen for command
                    command = await self.listen_for_command()
                    
                    if command:
                        # Process command
                        result = await self.process_voice_command(command)
                        
                        # Check if should stop
                        if result.get('result', {}).get('should_stop'):
                            break
                
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in continuous listening: {str(e)}")
                await asyncio.sleep(1)
        
        logger.info("Stopped continuous listening mode")
