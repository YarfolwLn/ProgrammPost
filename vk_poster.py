import vk_api
from config import Config

class VKPoster:
    def __init__(self):
        self.vk = None
        self.group_id = Config.VK_GROUP_ID
        
        if Config.VK_ACCESS_TOKEN:
            try:
                self.vk = vk_api.VkApi(token=Config.VK_ACCESS_TOKEN)
                self.vk_api = self.vk.get_api()
            except Exception as e:
                print(f"Ошибка при инициализации VK API: {e}")
    
    def post_text(self, text: str) -> bool:
        """Публикует текстовый пост"""
        if not self.vk or not self.group_id:
            print("VK не настроен")
            return False
        
        try:
            self.vk_api.wall.post(
                owner_id=f"-{self.group_id}",
                from_group=1,
                message=text
            )
            return True
        except Exception as e:
            print(f"Ошибка при публикации в VK: {e}")
            return False
    
    def post_photo(self, photo_path: str, message: str = None) -> bool:
        """Публикует пост с фото"""
        if not self.vk or not self.group_id:
            print("VK не настроен")
            return False
        
        try:
            # Загружаем фото на сервер VK
            upload_url = self.vk_api.photos.getWallUploadServer(
                group_id=self.group_id
            )['upload_url']
            
            import requests
            with open(photo_path, 'rb') as photo:
                response = requests.post(upload_url, files={'photo': photo})
            
            photo_data = response.json()
            
            # Сохраняем фото
            saved_photo = self.vk_api.photos.saveWallPhoto(
                group_id=self.group_id,
                photo=photo_data['photo'],
                server=photo_data['server'],
                hash=photo_data['hash']
            )
            
            photo_id = f"photo{saved_photo[0]['owner_id']}_{saved_photo[0]['id']}"
            
            # Публикуем пост с фото
            self.vk_api.wall.post(
                owner_id=f"-{self.group_id}",
                from_group=1,
                attachments=photo_id,
                message=message
            )
            return True
        except Exception as e:
            print(f"Ошибка при публикации фото в VK: {e}")
            return False
