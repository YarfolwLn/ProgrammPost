import os
import json
from datetime import datetime
from config import Config

class TikTokPoster:
    def __init__(self):
        self.api_key = None
        # Создаем директорию для TikTok контента
        self.tiktok_dir = os.path.join(Config.IMAGES_DIR, 'tiktok_content')
        os.makedirs(self.tiktok_dir, exist_ok=True)
    
    def save_for_manual_posting(self, video_path: str, title: str, description: str, hashtags: str, music_link: str = None) -> str:
        """Сохраняет данные для ручной публикации в TikTok"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Создаем структуру данных
            post_data = {
                'title': title,
                'description': description,
                'hashtags': hashtags,
                'music_link': music_link,
                'video_path': video_path,
                'created_at': datetime.now().isoformat(),
                'full_caption': f"{description}\n\n{hashtags}",
                'instructions': [
                    "1. Откройте TikTok приложение",
                    "2. Нажмите + для создания нового видео",
                    "3. Загрузите видео из папки",
                    f"4. Добавьте музыку: {music_link if music_link else 'выберите в TikTok'}",
                    "5. Добавьте описание из файла caption.txt",
                    "6. Опубликуйте"
                ]
            }
            
            # Сохраняем JSON с данными
            json_path = os.path.join(self.tiktok_dir, f'post_data_{timestamp}.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(post_data, f, ensure_ascii=False, indent=2)
            
            # Сохраняем описание в отдельный текстовый файл
            caption_path = os.path.join(self.tiktok_dir, f'caption_{timestamp}.txt')
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(f"ЗАГОЛОВОК: {title}\n\n")
                f.write(f"ОПИСАНИЕ:\n{description}\n\n")
                f.write(f"ХЭШТЕГИ:\n{hashtags}\n\n")
                if music_link:
                    f.write(f"МУЗЫКА: {music_link}\n\n")
                f.write("-" * 50 + "\n")
                f.write("ПОЛНЫЙ ТЕКСТ ДЛЯ КОПИРОВАНИЯ:\n")
                f.write("-" * 50 + "\n\n")
                f.write(f"{description}\n\n{hashtags}")
            
            print(f"TikTok контент сохранен для ручной публикации:")
            print(f"- Видео: {video_path}")
            print(f"- Данные: {json_path}")
            print(f"- Описание: {caption_path}")
            
            return json_path
            
        except Exception as e:
            print(f"Ошибка при сохранении TikTok контента: {e}")
            return None
    
    def post_video(self, video_path: str, caption: str) -> bool:
        """Публикует видео с описанием (заглушка для будущей автоматизации)"""
        print("Автоматическая публикация в TikTok пока не реализована.")
        print("Используйте save_for_manual_posting() для сохранения контента.")
        return False
    
    def get_upload_url(self) -> str:
        """Получает URL для загрузки видео (заглушка)"""
        return None
