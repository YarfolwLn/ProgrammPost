import os
import re
from PIL import Image, ImageDraw, ImageFont
import random
from config import Config

class ImageGenerator:
    def __init__(self):
        self.width = Config.QUOTE_IMAGE_WIDTH
        self.height = Config.QUOTE_IMAGE_HEIGHT
        self.bg_color = Config.BACKGROUND_COLOR
        self.text_color = Config.TEXT_COLOR
        self.author_color = Config.AUTHOR_COLOR
        
        # Создаем директорию для изображений
        os.makedirs(Config.GENERATED_IMAGES_DIR, exist_ok=True)
    
    def create_textured_background(self):
        """Создает черный текстурированный фон"""
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Добавляем шум и текстуру для эффекта "пошарпанного" фона
        for _ in range(5000):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            # Случайные точки с разной яркостью
            brightness = random.randint(10, 40)
            draw.point((x, y), fill=(brightness, brightness, brightness))
        
        # Добавляем легкие вертикальные линии для текстуры
        for _ in range(50):
            x = random.randint(0, self.width)
            thickness = random.randint(1, 2)
            brightness = random.randint(15, 35)
            draw.line([(x, 0), (x, self.height)], fill=(brightness, brightness, brightness), width=thickness)
        
        # Добавляем легкие горизонтальные линии
        for _ in range(30):
            y = random.randint(0, self.height)
            thickness = random.randint(1, 2)
            brightness = random.randint(15, 35)
            draw.line([(0, y), (self.width, y)], fill=(brightness, brightness, brightness), width=thickness)
        
        return img
    
    def sanitize_filename(self, text: str) -> str:
        """Очищает текст для использования в имени файла"""
        # Заменяем спецсимволы на подчеркивания
        text = re.sub(r'[<>:"/\\|?*]', '_', text)
        # Удаляем лишние пробелы и спецсимволы
        text = re.sub(r'\s+', '_', text.strip())
        # Ограничиваем длину
        text = text[:50]
        return text
    
    def extract_author_name(self, author: str) -> str:
        """Извлекает только фамилию или имя автора"""
        # Разбиваем на слова и берем первое (фамилия или имя)
        words = author.split()
        if words:
            # Берем первое слово и очищаем от запятых и других символов
            name = re.sub(r'[^\wа-яА-ЯёЁ]', '', words[0])
            return name
        return author
    
    def wrap_text(self, text, font, max_width):
        """Разбивает текст на строки для вписывания в заданную ширину"""
        lines = []
        words = text.split()
        current_line = []
        
        for word in words:
            current_line.append(word)
            line_text = ' '.join(current_line)
            bbox = font.getbbox(line_text)
            line_width = bbox[2] - bbox[0]
            
            if line_width > max_width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def create_quote_image(self, quote: str, author: str, output_path: str = None) -> str:
        """Создает изображение с цитатой"""
        # Создаем фон
        img = self.create_textured_background()
        draw = ImageDraw.Draw(img)
        
        # Пытаемся использовать системные шрифты, иначе используем стандартный
        try:
            # Для macOS
            quote_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", Config.QUOTE_FONT_SIZE)
            author_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", Config.AUTHOR_FONT_SIZE)
        except:
            try:
                # Для Linux
                quote_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", Config.QUOTE_FONT_SIZE)
                author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", Config.AUTHOR_FONT_SIZE)
            except:
                # Fallback на стандартный шрифт
                quote_font = ImageFont.load_default()
                author_font = ImageFont.load_default()
        
        # Настройки отступов
        padding = 80
        max_text_width = self.width - (2 * padding)
        
        # Разбиваем цитату на строки
        quote_lines = self.wrap_text(quote, quote_font, max_text_width)
        
        # Вычисляем позицию для цитаты (по центру)
        total_quote_height = len(quote_lines) * (Config.QUOTE_FONT_SIZE + 10)
        quote_start_y = (self.height - total_quote_height) // 2
        
        # Рисуем цитату
        current_y = quote_start_y
        for line in quote_lines:
            bbox = quote_font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, current_y), line, font=quote_font, fill=self.text_color)
            current_y += Config.QUOTE_FONT_SIZE + 10
        
        # Рисуем автора (правее внизу)
        author_text = f"— {author}"
        author_bbox = author_font.getbbox(author_text)
        author_width = author_bbox[2] - author_bbox[0]
        author_x = self.width - padding - author_width
        author_y = self.height - padding - Config.AUTHOR_FONT_SIZE - 20
        draw.text((author_x, author_y), author_text, font=author_font, fill=self.author_color)
        
        # Сохраняем изображение
        if output_path is None:
            # Используем дату и автора для имени файла
            from datetime import datetime
            date_str = datetime.now().strftime('%Y-%m-%d')
            author_name = self.extract_author_name(author)
            # Добавляем timestamp для уникальности, если несколько картинок за день
            timestamp = int(__import__('time').time())
            output_path = os.path.join(Config.GENERATED_IMAGES_DIR, f'{date_str}_{author_name}_{timestamp}.png')
        
        img.save(output_path, 'PNG', quality=95)
        return output_path
    
    def create_video_from_images(self, image_paths: list, output_path: str, duration: int = 5):
        """Создает видео из изображений для TikTok"""
        try:
            from moviepy.editor import ImageSequenceClip
            
            # Создаем клип из изображений
            clip = ImageSequenceClip(image_paths, durations=[duration] * len(image_paths))
            
            # Сохраняем видео
            clip.write_videofile(output_path, fps=24)
            return output_path
        except Exception as e:
            print(f"Ошибка при создании видео: {e}")
            return None
    
    def create_tiktok_video(self, image_path: str, music_path: str = None, duration: int = 15) -> str:
        """Создает видео для TikTok из одного изображения с музыкой"""
        try:
            from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
            
            # Создаем директорию для видео
            videos_dir = os.path.join(Config.IMAGES_DIR, 'videos')
            os.makedirs(videos_dir, exist_ok=True)
            
            # Загружаем изображение
            image_clip = ImageClip(image_path)
            image_clip = image_clip.set_duration(duration)
            
            # Если есть музыка, добавляем её
            if music_path and os.path.exists(music_path):
                audio_clip = AudioFileClip(music_path)
                # Обрезаем или зацикливаем музыку под длительность видео
                if audio_clip.duration < duration:
                    # Зацикливаем музыку
                    audio_clip = audio_clip.loop(duration=duration)
                else:
                    # Обрезаем музыку
                    audio_clip = audio_clip.subclip(0, duration)
                
                final_clip = image_clip.set_audio(audio_clip)
            else:
                final_clip = image_clip
            
            # Устанавливаем размер для TikTok (вертикальное видео)
            # TikTok предпочитает 1080x1920, но мы можем использовать 1080x1080 или 1080x1350
            final_clip = final_clip.resize(height=1920)
            
            # Сохраняем видео
            timestamp = int(__import__('time').time())
            output_path = os.path.join(videos_dir, f'tiktok_{timestamp}.mp4')
            
            final_clip.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                preset='medium'
            )
            
            # Закрываем клипы
            image_clip.close()
            if music_path and os.path.exists(music_path):
                audio_clip.close()
            final_clip.close()
            
            return output_path
            
        except Exception as e:
            print(f"Ошибка при создании TikTok видео: {e}")
            import traceback
            traceback.print_exc()
            return None
