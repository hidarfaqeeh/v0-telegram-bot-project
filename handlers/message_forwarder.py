import asyncio
from typing import Dict, Any, List
from telegram import Bot, Message
from telegram.error import TelegramError
from database.task_manager import TaskManager
from database.statistics_manager import StatisticsManager
from utils.message_processor import MessageProcessor
from config import Config

class MessageForwarder:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.active_tasks: Dict[int, Dict[str, Any]] = {}
        self.running = False
    
    async def start_monitoring(self):
        """Start monitoring active tasks"""
        self.running = True
        await self.load_active_tasks()
        
        # Start monitoring loop
        asyncio.create_task(self.monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
    
    async def load_active_tasks(self):
        """Load active tasks from database"""
        tasks = await TaskManager.get_active_tasks()
        self.active_tasks = {task['id']: task for task in tasks}
        print(f"Loaded {len(self.active_tasks)} active tasks")
    
    async def monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Reload tasks every 5 minutes
                await self.load_active_tasks()
                await asyncio.sleep(300)  # 5 minutes
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def process_message(self, message: Message) -> bool:
        """Process incoming message for forwarding"""
        try:
            chat_id = message.chat.id
            
            # Find tasks that monitor this chat
            relevant_tasks = [
                task for task in self.active_tasks.values()
                if task['source_chat_id'] == chat_id
            ]
            
            if not relevant_tasks:
                return False
            
            # Process each relevant task
            for task in relevant_tasks:
                await self.process_task_message(task, message)
            
            return True
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return False
    
    async def process_task_message(self, task: Dict[str, Any], message: Message):
        """Process message for specific task"""
        try:
            task_id = task['id']
            processor = MessageProcessor(task['settings'])
            
            # Check if message should be forwarded
            if not await processor.should_forward_message(message):
                await StatisticsManager.increment_filtered(task_id)
                return
            
            # Apply delay if configured
            delay = await processor.get_delay()
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Forward or copy message
            if task['task_type'] == 'forward':
                await self.forward_message(task, message, processor)
            else:
                await self.copy_message(task, message, processor)
            
            # Update statistics
            await StatisticsManager.increment_forwarded(task_id)
            
        except Exception as e:
            print(f"Error processing task message: {e}")
    
    async def forward_message(self, task: Dict[str, Any], message: Message, 
                            processor: MessageProcessor):
        """Forward message to target chat"""
        try:
            target_chat_id = task['target_chat_id']
            
            # Forward the message
            forwarded = await self.bot.forward_message(
                chat_id=target_chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            
            # Add inline buttons if configured
            await self.add_inline_buttons(task, forwarded)
            
        except TelegramError as e:
            print(f"Error forwarding message: {e}")
    
    async def copy_message(self, task: Dict[str, Any], message: Message, 
                          processor: MessageProcessor):
        """Copy message to target chat"""
        try:
            target_chat_id = task['target_chat_id']
            
            # Process text
            text = message.text or message.caption or ""
            processed_text = await processor.process_message_text(text)
            
            # Copy based on message type
            if message.photo:
                await self.bot.send_photo(
                    chat_id=target_chat_id,
                    photo=message.photo[-1].file_id,
                    caption=processed_text
                )
            elif message.video:
                await self.bot.send_video(
                    chat_id=target_chat_id,
                    video=message.video.file_id,
                    caption=processed_text
                )
            elif message.audio:
                await self.bot.send_audio(
                    chat_id=target_chat_id,
                    audio=message.audio.file_id,
                    caption=processed_text
                )
            elif message.document:
                await self.bot.send_document(
                    chat_id=target_chat_id,
                    document=message.document.file_id,
                    caption=processed_text
                )
            elif message.voice:
                await self.bot.send_voice(
                    chat_id=target_chat_id,
                    voice=message.voice.file_id,
                    caption=processed_text
                )
            elif message.video_note:
                await self.bot.send_video_note(
                    chat_id=target_chat_id,
                    video_note=message.video_note.file_id
                )
            elif message.sticker:
                await self.bot.send_sticker(
                    chat_id=target_chat_id,
                    sticker=message.sticker.file_id
                )
            elif message.animation:
                await self.bot.send_animation(
                    chat_id=target_chat_id,
                    animation=message.animation.file_id,
                    caption=processed_text
                )
            else:
                # Text message
                if processed_text:
                    sent_message = await self.bot.send_message(
                        chat_id=target_chat_id,
                        text=processed_text
                    )
                    
                    # Add inline buttons if configured
                    await self.add_inline_buttons(task, sent_message)
            
        except TelegramError as e:
            print(f"Error copying message: {e}")
    
    async def add_inline_buttons(self, task: Dict[str, Any], message: Message):
        """Add inline buttons to message if configured"""
        try:
            buttons_config = task['settings'].get('inline_buttons', {})
            if not buttons_config.get('enabled', False):
                return
            
            buttons = buttons_config.get('buttons', [])
            if not buttons:
                return
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = []
            for button in buttons:
                keyboard.append([
                    InlineKeyboardButton(
                        text=button.get('text', ''),
                        url=button.get('url', ''),
                        callback_data=button.get('callback_data', '')
                    )
                ])
            
            await self.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"Error adding inline buttons: {e}")
