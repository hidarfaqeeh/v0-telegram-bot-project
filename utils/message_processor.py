import re
import asyncio
from typing import Dict, Any, Optional, List
from telegram import Message
from telegram.constants import MessageType
import validators

class MessageProcessor:
    def __init__(self, task_settings: Dict[str, Any]):
        self.settings = task_settings
    
    async def should_forward_message(self, message: Message) -> bool:
        """Check if message should be forwarded based on filters"""
        
        # Check media filters
        if not self._check_media_filter(message):
            return False
        
        # Check text filters
        if not self._check_text_filters(message):
            return False
        
        # Check advanced filters
        if not self._check_advanced_filters(message):
            return False
        
        # Check whitelist/blacklist
        if not self._check_user_lists(message):
            return False
        
        return True
    
    def _check_media_filter(self, message: Message) -> bool:
        """Check media type filters"""
        media_filters = self.settings.get('media_filters', {})
        if not media_filters.get('enabled', True):
            return True
        
        allowed_types = media_filters.get('allowed_types', [])
        if not allowed_types:
            return True
        
        message_type = self._get_message_type(message)
        return message_type in allowed_types
    
    def _get_message_type(self, message: Message) -> str:
        """Get message type"""
        if message.photo:
            return 'photo'
        elif message.video:
            return 'video'
        elif message.audio:
            return 'audio'
        elif message.document:
            return 'document'
        elif message.voice:
            return 'voice'
        elif message.video_note:
            return 'video_note'
        elif message.sticker:
            return 'sticker'
        elif message.animation:
            return 'animation'
        else:
            return 'text'
    
    def _check_text_filters(self, message: Message) -> bool:
        """Check text-based filters"""
        if not message.text and not message.caption:
            return True
        
        text = message.text or message.caption or ""
        
        # Check blocked words
        blocked_words = self.settings.get('blocked_words', [])
        for word in blocked_words:
            if word.lower() in text.lower():
                return False
        
        # Check required words
        required_words = self.settings.get('required_words', [])
        if required_words:
            for word in required_words:
                if word.lower() in text.lower():
                    break
            else:
                return False
        
        return True
    
    def _check_advanced_filters(self, message: Message) -> bool:
        """Check advanced filters"""
        advanced_filters = self.settings.get('advanced_filters', {})
        
        # Block links
        if advanced_filters.get('block_links', False):
            text = message.text or message.caption or ""
            if self._contains_links(text):
                return False
        
        # Block usernames/mentions
        if advanced_filters.get('block_mentions', False):
            if message.entities:
                for entity in message.entities:
                    if entity.type in ['mention', 'text_mention']:
                        return False
        
        # Block forwarded messages
        if advanced_filters.get('block_forwarded', False):
            if message.forward_date:
                return False
        
        # Block messages with inline keyboards
        if advanced_filters.get('block_inline_keyboards', False):
            if message.reply_markup and message.reply_markup.inline_keyboard:
                return False
        
        return True
    
    def _check_user_lists(self, message: Message) -> bool:
        """Check whitelist and blacklist"""
        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            return True
        
        # Check blacklist
        blacklist = self.settings.get('blacklist', [])
        if user_id in blacklist:
            return False
        
        # Check whitelist
        whitelist = self.settings.get('whitelist', [])
        if whitelist and user_id not in whitelist:
            return False
        
        return True
    
    def _contains_links(self, text: str) -> bool:
        """Check if text contains links"""
        # URL pattern
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        if re.search(url_pattern, text):
            return True
        
        # Telegram links
        telegram_pattern = r'(?:@[a-zA-Z0-9_]+|t\.me/[a-zA-Z0-9_]+)'
        if re.search(telegram_pattern, text):
            return True
        
        return False
    
    async def process_message_text(self, text: str) -> str:
        """Process message text with replacements, header, footer"""
        if not text:
            return text
        
        processed_text = text
        
        # Apply replacements
        replacements = self.settings.get('replacements', {})
        for old_text, new_text in replacements.items():
            processed_text = processed_text.replace(old_text, new_text)
        
        # Remove links if enabled
        if self.settings.get('remove_links', False):
            processed_text = self._remove_links(processed_text)
        
        # Remove lines containing specific words
        remove_lines_with = self.settings.get('remove_lines_with', [])
        if remove_lines_with:
            lines = processed_text.split('\n')
            filtered_lines = []
            for line in lines:
                should_remove = False
                for word in remove_lines_with:
                    if word.lower() in line.lower():
                        should_remove = True
                        break
                if not should_remove:
                    filtered_lines.append(line)
            processed_text = '\n'.join(filtered_lines)
        
        # Remove empty lines
        if self.settings.get('remove_empty_lines', False):
            lines = processed_text.split('\n')
            processed_text = '\n'.join(line for line in lines if line.strip())
        
        # Add header
        header = self.settings.get('header', '')
        if header:
            processed_text = f"{header}\n\n{processed_text}"
        
        # Add footer
        footer = self.settings.get('footer', '')
        if footer:
            processed_text = f"{processed_text}\n\n{footer}"
        
        return processed_text
    
    def _remove_links(self, text: str) -> str:
        """Remove links from text"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove Telegram links
        text = re.sub(r'(?:@[a-zA-Z0-9_]+|t\.me/[a-zA-Z0-9_]+)', '', text)
        
        return text
    
    async def get_delay(self) -> int:
        """Get delay for message forwarding"""
        delay_settings = self.settings.get('delay', {})
        if not delay_settings.get('enabled', False):
            return 0
        
        return delay_settings.get('seconds', 0)
