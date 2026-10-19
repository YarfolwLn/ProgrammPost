from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import asyncio
from database import Database
from telegram_poster import TelegramPoster
from vk_poster import VKPoster
from tiktok_poster import TikTokPoster
from config import Config

# Временно закомментируем Instagram для тестирования
try:
    from instagram_poster import InstagramPoster
    INSTAGRAM_AVAILABLE = True
except ImportError:
    INSTAGRAM_AVAILABLE = False

class PostScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db = Database()
        self.telegram_poster = TelegramPoster()
        self.vk_poster = VKPoster()
        self.instagram_poster = InstagramPoster() if INSTAGRAM_AVAILABLE else None
        self.tiktok_poster = TikTokPoster()
    
    def start(self):
        """Запускает планировщик"""
        # Добавляем задачи для каждого времени публикации
        for post_time in Config.POST_TIMES:
            hour, minute = map(int, post_time.split(':'))
            self.scheduler.add_job(
                self.process_scheduled_posts,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=f'post_{post_time}',
                name=f'Публикация постов в {post_time}'
            )
        
        self.scheduler.start()
        print(f"Планировщик запущен. Время публикации: {', '.join(Config.POST_TIMES)}")
    
    def stop(self):
        """Останавливает планировщик"""
        self.scheduler.shutdown()
        print("Планировщик остановлен")
    
    async def process_scheduled_posts(self):
        """Обрабатывает запланированные посты"""
        print(f"Обработка запланированных постов в {datetime.now().strftime('%H:%M')}")
        
        pending_posts = self.db.get_pending_posts()
        
        for post in pending_posts:
            print(f"Публикация поста #{post['id']}")
            success = await self.publish_post(post)
            
            if success:
                self.db.update_post_status(post['id'], 'posted')
                print(f"Пост #{post['id']} успешно опубликован")
            else:
                self.db.update_post_status(post['id'], 'failed')
                print(f"Пост #{post['id']} не удалось опубликовать")
    
    async def publish_post(self, post: dict) -> bool:
        """Публикует пост на все указанные платформы"""
        # Убедимся, что platforms - это список
        platforms = post['platforms']
        if isinstance(platforms, str):
            platforms = platforms.split(',')
        
        content = post['content']
        image_path = post['image_path']
        
        print(f"Публикация поста #{post['id']} на платформы: {platforms}")
        
        all_success = True
        
        for platform in platforms:
            try:
                if platform == 'telegram':
                    if image_path:
                        success = await self.telegram_poster.post_photo(image_path, content)
                    else:
                        success = await self.telegram_poster.post_text(content)
                    
                    # Добавляем лог только если post_id существует
                    if post['id']:
                        self.db.add_post_log(post['id'], 'telegram', 'success' if success else 'failed')
                    
                elif platform == 'vk':
                    if image_path:
                        success = self.vk_poster.post_photo(image_path, content)
                    else:
                        success = self.vk_poster.post_text(content)
                    
                    # Добавляем лог только если post_id существует
                    if post['id']:
                        self.db.add_post_log(post['id'], 'vk', 'success' if success else 'failed')
                    
                elif platform == 'instagram':
                    if self.instagram_poster and image_path:
                        success = self.instagram_poster.post_photo(image_path, content)
                    else:
                        success = False
                        if not self.instagram_poster:
                            print("Instagram не доступен")
                        else:
                            print("Instagram требует изображение")
                    
                    # Добавляем лог только если post_id существует
                    if post['id']:
                        self.db.add_post_log(post['id'], 'instagram', 'success' if success else 'failed')
                    
                elif platform == 'tiktok':
                    # TikTok требует видео
                    success = False
                    # Добавляем лог только если post_id существует
                    if post['id']:
                        self.db.add_post_log(post['id'], 'tiktok', 'failed', 'Требуется видео, не фото')
                
                if not success:
                    all_success = False
                    
            except Exception as e:
                print(f"Ошибка при публикации на {platform}: {e}")
                # Добавляем лог только если post_id существует
                if post['id']:
                    self.db.add_post_log(post['id'], platform, 'failed', str(e))
                all_success = False
        
        return all_success
    
    def schedule_post(self, post_id: int, scheduled_time: str):
        """Добавляет пост в расписание"""
        # Пост добавляется в базу с указанным временем
        # Планировщик проверяет базу в заданное время
        print(f"Пост #{post_id} запланирован на {scheduled_time}")
