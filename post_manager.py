import asyncio
from datetime import datetime, timedelta
from database import Database
from text_generator import TextGenerator
from image_generator import ImageGenerator
from scheduler import PostScheduler
from tiktok_poster import TikTokPoster
from config import Config

# Временно закомментируем Instagram для тестирования
try:
    from instagram_poster import InstagramPoster
    INSTAGRAM_AVAILABLE = True
except ImportError:
    INSTAGRAM_AVAILABLE = False

class PostManager:
    def __init__(self):
        self.db = Database()
        self.text_generator = TextGenerator()
        self.image_generator = ImageGenerator()
        self.scheduler = PostScheduler()
        self.tiktok_poster = TikTokPoster()
    
    def generate_quote_post(self, topic: str = None, platforms: list = None) -> dict:
        """Генерирует полный пост с цитатой"""
        if platforms is None:
            platforms = ['telegram', 'vk']
        
        # Генерируем цитату с описанием
        quote_data = self.text_generator.generate_quote_with_description(topic)
        
        # Создаем изображение с цитатой
        image_path = self.image_generator.create_quote_image(
            quote_data['quote'],
            quote_data['author']
        )
        
        # Сохраняем цитату в базу с путем к изображению
        quote_id = self.db.add_quote(
            quote_data['quote'],
            quote_data['author'],
            quote_data['description'],
            image_path
        )
        
        # Генерируем контент для каждой платформы
        platform_contents = {}
        for platform in platforms:
            try:
                content = self.text_generator.generate_post_content(
                    quote_data['quote'],
                    quote_data['author'],
                    quote_data['description'],
                    platform
                )
                platform_contents[platform] = content
            except Exception as e:
                print(f"Ошибка при генерации контента для {platform}: {e}")
                platform_contents[platform] = f"{quote_data['quote']}\n\n— {quote_data['author']}\n\n{quote_data['description']}"
        
        # Используем контент для первой платформы как основной
        main_content = platform_contents.get(platforms[0], '')
        
        return {
            'quote_id': quote_id,
            'quote_data': quote_data,
            'image_path': image_path,
            'platform_contents': platform_contents,
            'main_content': main_content
        }
    
    def create_scheduled_post(self, quote_id: int, platforms: list, scheduled_time: str, content: str = None, image_path: str = None) -> int:
        """Создает запланированный пост"""
        quote = self.db.get_quote(quote_id)
        if not quote:
            raise Exception("Цитата не найдена")
        
        # Используем изображение из базы данных цитаты, если есть
        if not image_path:
            image_path = quote.get('image_path')
            if not image_path:
                raise Exception("Для цитаты нет изображения. Сначала создайте картинку через кнопку 'Обновить цитату' -> 'Создать картинку'")
        
        # Генерируем контент только если не передан
        if not content:
            # Генерируем контент для первой платформы как основной
            try:
                content = self.text_generator.generate_post_content(
                    quote['quote'],
                    quote['author'],
                    quote['description'],
                    platforms[0] if platforms else 'telegram'
                )
            except Exception as e:
                print(f"Ошибка при генерации контента: {e}")
                content = f"{quote['quote']}\n\n— {quote['author']}\n\n{quote['description']}"
        
        # Создаем пост в базе
        post_id = self.db.add_post(
            quote_id=quote_id,
            title=f"Цитата от {quote['author']}",
            content=content,
            image_path=image_path,
            platforms=platforms,
            scheduled_time=scheduled_time
        )
        
        # Увеличиваем счетчик использования цитаты
        self.db.increment_quote_usage(quote_id)
        
        return post_id
    
    def schedule_posts_for_day(self, platforms: list = None):
        """Создает посты на день (2 поста)"""
        if platforms is None:
            platforms = ['telegram', 'vk']
        
        scheduled_posts = []
        
        for i, post_time in enumerate(Config.POST_TIMES):
            # Получаем неиспользованную цитату
            quote = self.db.get_random_unused_quote()
            
            if not quote:
                print("Нет неиспользованных цитат")
                break
            
            # Формируем время публикации
            today = datetime.now().date()
            scheduled_datetime = datetime.combine(today, datetime.strptime(post_time, '%H:%M').time())
            
            # Если время уже прошло, планируем на завтра
            if scheduled_datetime < datetime.now():
                scheduled_datetime += timedelta(days=1)
            
            scheduled_time = scheduled_datetime.isoformat()
            
            # Генерируем контент и изображение один раз
            try:
                content = self.text_generator.generate_post_content(
                    quote['quote'],
                    quote['author'],
                    quote['description'],
                    platforms[0] if platforms else 'telegram'
                )
            except Exception as e:
                print(f"Ошибка при генерации контента: {e}")
                content = f"{quote['quote']}\n\n— {quote['author']}\n\n{quote['description']}"
            
            # Используем картинку из базы данных цитаты
            image_path = quote.get('image_path')
            if not image_path:
                print(f"Предупреждение: Для цитаты #{quote['id']} нет изображения, пропускаем")
                continue
            
            # Создаем пост с уже сгенерированным контентом и изображением
            post_id = self.create_scheduled_post(
                quote['id'],
                platforms,
                scheduled_time,
                content=content,
                image_path=image_path
            )
            
            scheduled_posts.append(post_id)
        
        return scheduled_posts
    
    def start_scheduler(self):
        """Запускает планировщик"""
        self.scheduler.start()
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.scheduler.stop()
    
    def get_all_quotes(self):
        """Получает все цитаты"""
        return self.db.get_all_quotes()
    
    def get_all_posts(self):
        """Получает все посты"""
        return self.db.get_all_posts()
    
    def add_manual_quote(self, quote: str, author: str, description: str) -> int:
        """Добавляет цитату вручную"""
        return self.db.add_quote(quote, author, description)
    
    def generate_tiktok_content(self, quote_data: dict, music_path: str = None, music_link: str = None) -> dict:
        """Генерирует контент для TikTok"""
        # Генерируем TikTok специфичный контент
        tiktok_content = self.text_generator.generate_tiktok_content(
            quote_data['quote'],
            quote_data['author'],
            quote_data['description']
        )
        
        # Используем существующую картинку из quote_data, если есть
        image_path = quote_data.get('image_path')
        if not image_path:
            # Если картинки нет, создаем новую
            image_path = self.image_generator.create_quote_image(
                quote_data['quote'],
                quote_data['author']
            )
        
        # Создаем видео с музыкой
        video_path = self.image_generator.create_tiktok_video(
            image_path,
            music_path,
            duration=15
        )
        
        # Сохраняем для ручной публикации
        save_path = self.tiktok_poster.save_for_manual_posting(
            video_path,
            tiktok_content['title'],
            tiktok_content['description'],
            tiktok_content['hashtags'],
            music_link
        )
        
        return {
            'video_path': video_path,
            'title': tiktok_content['title'],
            'description': tiktok_content['description'],
            'hashtags': tiktok_content['hashtags'],
            'music_link': music_link,
            'save_path': save_path,
            'image_path': image_path
        }
