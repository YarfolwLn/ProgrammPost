from instagrapi import Client
from config import Config

class InstagramPoster:
    def __init__(self):
        self.client = None
        
        if Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
            try:
                self.client = Client()
                self.client.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
            except Exception as e:
                print(f"Ошибка при входе в Instagram: {e}")
    
    def post_photo(self, photo_path: str, caption: str) -> bool:
        """Публикует фото с описанием"""
        if not self.client:
            print("Instagram не настроен")
            return False
        
        try:
            self.client.photo_upload(photo_path, caption)
            return True
        except Exception as e:
            print(f"Ошибка при публикации в Instagram: {e}")
            # Пробуем перелогиниться
            try:
                self.client.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
                self.client.photo_upload(photo_path, caption)
                return True
            except Exception as e2:
                print(f"Ошибка при повторной публикации в Instagram: {e2}")
                return False
    
    def logout(self):
        """Выходит из аккаунта"""
        if self.client:
            try:
                self.client.logout()
            except:
                pass
