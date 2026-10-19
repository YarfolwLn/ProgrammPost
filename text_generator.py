import os
import time
from groq import Groq
from config import Config

class TextGenerator:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None
        self.max_retries = 3
        self.retry_delay = 2  # секунды
    
    def _call_api_with_retry(self, messages, model, temperature, max_tokens):
        """Вызывает API с повторными попытками при ошибках"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response
            except Exception as e:
                error_msg = str(e)
                if attempt < self.max_retries - 1:
                    print(f"Ошибка API (попытка {attempt + 1}/{self.max_retries}): {error_msg}")
                    print(f"Повторная попытка через {self.retry_delay} секунд...")
                    time.sleep(self.retry_delay)
                else:
                    raise
    
    def generate_quote_with_description(self, topic: str = None) -> dict:
        """Генерирует цитату с автором и описанием"""
        if not self.client:
            raise Exception("Groq API key не установлен")
        
        try:
            topics_list = [
                "бизнес и предпринимательство",
                "наука и открытия",
                "искусство и творчество",
                "психология и самопознание",
                "технологии и будущее",
                "политика и общество",
                "история и цивилизация",
                "отношения и общение",
                "образование и обучение",
                "здоровье и медицина",
                "философия и этика",
                "экономика и финансы"
            ]
            
            import random
            selected_topic = topic if topic else random.choice(topics_list)
            
            prompt = f"""Найди И ПОЛНОСТЬЮ ПРИВЕДИ РЕАЛЬНУЮ цитату известного человека на тему: {selected_topic}.
            
Формат ответа (строго по структуре):
Цитата: [точный текст реальной цитаты известного человека]
Автор: [полное имя реального автора с указанием его профессии/статуса]
Описание: [глубокий анализ этой цитаты, её контекст и значение, 200-300 слов]

КРИТИЧЕСКИ ВАЖНО:
- Цитата ДОЛЖНА БЫТЬ РЕАЛЬНОЙ от известного человека (ученого, философа, писателя, предпринимателя, политика, художника и т.д.)
- НЕ генерируй выдуманные цитаты
- Цитата должна быть точной, а не перефразированной
- Автор должен быть реально существовавшим или существующим человеком
- Темы должны быть разнообразными: бизнес, наука, искусство, психология, технологии, политика, история, отношения, образование
- Цитата должна заставлять задуматься и вникнуть в суть
- Описание должно содержать контекст, когда и почему была сказана эта цитата
- Пиши на русском языке"""
            
            response = self._call_api_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - эксперт по цитатам и биографиям известных людей. Ты находишь реальные цитаты от ученых, философов, писателей, предпринимателей, политиков, художников и других выдающихся личностей. Ты точно приводишь цитаты и даешь контекст их происхождения."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=1024,
            )
            
            content = response.choices[0].message.content
            
            # Парсим ответ
            quote = ""
            author = ""
            description = ""
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Цитата:'):
                    current_section = 'quote'
                    quote = line.replace('Цитата:', '').strip()
                elif line.startswith('Автор:'):
                    current_section = 'author'
                    author = line.replace('Автор:', '').strip()
                elif line.startswith('Описание:'):
                    current_section = 'description'
                    description = line.replace('Описание:', '').strip()
                elif current_section == 'quote':
                    quote += ' ' + line
                elif current_section == 'description':
                    description += ' ' + line
            
            return {
                'quote': quote.strip(),
                'author': author.strip(),
                'description': description.strip()
            }
            
        except Exception as e:
            print(f"Ошибка при генерации цитаты: {e}")
            raise
    
    def truncate_text(self, text: str, max_length: int) -> str:
        """Обрезает текст до указанной длины, сохраняя целостность предложений"""
        if len(text) <= max_length:
            return text
        
        # Обрезаем до максимальной длины
        truncated = text[:max_length]
        
        # Ищем последнее полное предложение
        last_sentence_end = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_sentence_end > max_length * 0.7:  # Если предложение заканчивается после 70% длины
            return truncated[:last_sentence_end + 1]
        else:
            # Иначе обрезаем на пробеле
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:
                return truncated[:last_space] + '...'
            else:
                return truncated[:max_length] + '...'
    
    def generate_post_content(self, quote: str, author: str, description: str, platform: str) -> str:
        """Генерирует контент для поста под конкретную платформу"""
        if not self.client:
            raise Exception("Groq API key не установлен")
        
        try:
            platform_instructions = {
                'telegram': 'Длина: СТРОГО до 1024 символов. БЕЗ ЭМОДЗИ. Используй повествовательный стиль, который удерживает внимание и заставляет дочитать до конца. Структура: интригующее начало, цитата, глубокое описание, хештеги. ВАЖНО: НЕ превышай 1024 символа!',
                'vk': 'Длина: до 2000 символов. БЕЗ ЭМОДЗИ. Более формальный стиль, но вовлекающий. Структура: интригующее начало, цитата, глубокое описание, хештеги.',
                'instagram': 'Длина: до 2200 символов. БЕЗ ЭМОДЗИ. Визуальный стиль через слова, а не эмодзи. Структура: интригующий крючок, цитата, глубокое описание, призыв к действию, хештеги.',
                'tiktok': 'Длина: до 150 символов для описания видео. БЕЗ ЭМОДЗИ. Кратко и емко. Фокус на визуальной составляющей.'
            }
            
            # Ограничения по длине для каждой платформы
            platform_limits = {
                'telegram': 1024,
                'vk': 2000,
                'instagram': 2200,
                'tiktok': 2200
            }
            
            instruction = platform_instructions.get(platform, platform_instructions['telegram'])
            max_length = platform_limits.get(platform, 1024)
            
            prompt = f"""Создай пост для {platform} на основе следующей цитаты:

Цитата: {quote}
Автор: {author}
Описание: {description}

Инструкции: {instruction}

Дополнительные требования:
- НЕ ИСПОЛЬЗУЙ ЭМОДЗИ вообще
- Создавай контент, который заставляет читателя дочитать до конца
- Начинай с интригующей мысли, вопроса или утверждения
- Используй мощные слова и фразы для эмоционального воздействия
- Создавай повествование, которое удерживает внимание
- Делай текст максимально интересным и вовлекающим

Сгенерируй готовый текст для публикации."""
            
            response = self._call_api_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": f"Ты - опытный SMM специалист для {platform}. Ты создаешь вовлекающие посты."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1024,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Обрезаем контент до максимальной длины для платформы
            content = self.truncate_text(content, max_length)
            
            return content
            
        except Exception as e:
            print(f"Ошибка при генерации контента для {platform}: {e}")
            raise
    
    def generate_tiktok_content(self, quote: str, author: str, description: str) -> dict:
        """Генерирует контент для TikTok: заголовок, описание, хэштеги"""
        if not self.client:
            raise Exception("Groq API key не установлен")
        
        try:
            prompt = f"""Создай контент для TikTok на основе следующей цитаты:

Цитата: {quote}
Автор: {author}
Описание: {description}

Формат ответа (строго по структуре):
Заголовок: [краткий говорящий заголовок, 3-5 слов, цепляющий внимание]
Описание: [глубокое описание без эмодзи, СТРОГО до 2200 символов для описания видео, которое заставляет читателя дочитать до конца]
Хэштеги: [5-10 релевантных хэштегов с символом #, через пробел, например: #мотивация #успех #жизнь]

Важно:
- Заголовок должен быть коротким и цепляющим
- Описание должно быть глубоким, вдохновляющим и БЕЗ ЭМОДЗИ
- Используй повествовательный стиль, который удерживает внимание и заставляет дочитать до конца
- Начинай с интригующей мысли или вопроса
- Создавай эмоциональную связь с читателем через слова, а не эмодзи
- Хэштеги должны начинаться с символа # и быть популярными и релевантными теме
- Пиши на русском языке"""
            
            response = self._call_api_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - опытный TikTok контент-креатор. Ты создаешь вирусный контент с короткими заголовками и глубокими описаниями."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=1024,
            )
            
            content = response.choices[0].message.content
            
            # Парсим ответ
            title = ""
            description = ""
            hashtags = ""
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Заголовок:'):
                    current_section = 'title'
                    title = line.replace('Заголовок:', '').strip()
                elif line.startswith('Описание:'):
                    current_section = 'description'
                    description = line.replace('Описание:', '').strip()
                elif line.startswith('Хэштеги:'):
                    current_section = 'hashtags'
                    hashtags = line.replace('Хэштеги:', '').strip()
                elif current_section == 'title':
                    title += ' ' + line
                elif current_section == 'description':
                    description += ' ' + line
                elif current_section == 'hashtags':
                    hashtags += ' ' + line
            
            return {
                'title': title.strip(),
                'description': description.strip(),
                'hashtags': hashtags.strip()
            }
            
        except Exception as e:
            print(f"Ошибка при генерации контента для TikTok: {e}")
            raise
    
    def generate_post_ideas(self, count: int = 5) -> list:
        """Генерирует идеи для постов"""
        if not self.client:
            raise Exception("Groq API key не установлен")
        
        try:
            prompt = f"""Сгенерируй {count} идей для постов с РЕАЛЬНЫМИ цитатами известных людей на РАЗНЫЕ темы.

Темы должны быть разнообразными: бизнес, наука, искусство, психология, технологии, политика, история, отношения, образование, здоровье, философия, экономика.

Каждая идея должна включать:
- Тему для цитаты (конкретная область)
- Краткое описание направления
- Предлагаемую аудиторию
- Пример известного человека, чьи цитаты подходят

Формат: каждая идея на новой строке в формате: Тема | Описание | Аудитория | Пример автора"""
            
            response = self._call_api_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - креативный контент-менеджер. Ты генерируешь идеи для вовлекающего контента."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=1024,
            )
            
            ideas = []
            lines = response.choices[0].message.content.strip().split('\n')
            for line in lines:
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        ideas.append({
                            'topic': parts[0].strip(),
                            'description': parts[1].strip(),
                            'audience': parts[2].strip()
                        })
            
            return ideas
            
        except Exception as e:
            print(f"Ошибка при генерации идей: {e}")
            raise
