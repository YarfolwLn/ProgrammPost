import asyncio
from aiogram import Bot
from aiogram.types import FSInputFile
from config import Config

class TelegramPoster:
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN) if Config.TELEGRAM_BOT_TOKEN else None
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
    
    async def post_text(self, text: str) -> bool:
        """Публикует текстовый пост"""
        if not self.bot or not self.channel_id:
            print("Telegram не настроен")
            return False
        
        try:
            print(f"Публикация текста в Telegram (channel_id: {self.channel_id})")
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=text,
                parse_mode='HTML'
            )
            print("Успешно опубликовано в Telegram")
            return True
        except Exception as e:
            print(f"Ошибка при публикации в Telegram: {e}")
            return False
    
    async def post_photo(self, photo_path: str, caption: str = None) -> bool:
        """Публикует пост с фото"""
        if not self.bot or not self.channel_id:
            print("Telegram не настроен")
            return False
        
        try:
            print(f"Публикация фото в Telegram (channel_id: {self.channel_id}, photo: {photo_path})")
            photo = FSInputFile(photo_path)
            await self.bot.send_photo(
                chat_id=self.channel_id,
                photo=photo,
                caption=caption,
                parse_mode='HTML'
            )
            print("Успешно опубликовано фото в Telegram")
            return True
        except Exception as e:
            print(f"Ошибка при публикации фото в Telegram: {e}")
            return False
    
    async def close(self):
        """Закрывает соединение с ботом"""
        if self.bot:
            await self.bot.session.close()
