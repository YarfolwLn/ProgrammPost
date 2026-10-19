import sys
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QComboBox, QTabWidget, QListWidget, QListWidgetItem,
                             QFileDialog, QDateTimeEdit, QCheckBox, QGroupBox,
                             QFormLayout, QLineEdit, QMessageBox, QSplitter,
                             QScrollArea, QDialog)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QPixmap, QImage
from post_manager import PostManager
from database import Database
from config import Config
import asyncio

# Временно закомментируем Instagram для тестирования
try:
    from instagram_poster import InstagramPoster
    INSTAGRAM_AVAILABLE = True
except ImportError:
    INSTAGRAM_AVAILABLE = False
    print("Instagram не доступен (instagrapi не установлен)")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.post_manager = PostManager()
        self.db = Database()
        self.current_quote_data = None
        self.current_image_path = None
        self.current_tiktok_data = None
        
        self.init_ui()
        self.load_quotes()
        self.load_posts()
    
    def init_ui(self):
        self.setWindowTitle("ProgramPost - Автоматизация постинга")
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(800, 500)
        
        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Главный layout
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Создаем вкладки
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Вкладка генерации
        self.create_generation_tab()
        
        # Вкладка цитат
        self.create_quotes_tab()
        
        # Вкладка постов
        self.create_posts_tab()
        
        # Вкладка планировщика
        self.create_scheduler_tab()
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе")
    
    def create_generation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Создаем scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Контейнер для контента
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)
        
        # Группа генерации
        gen_group = QGroupBox("Генерация контента")
        gen_layout = QFormLayout()
        gen_group.setLayout(gen_layout)
        
        # Тема для генерации
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Оставьте пустым для случайной темы")
        gen_layout.addRow("Тема цитаты:", self.topic_input)
        
        # Выбор платформ
        self.platform_checkboxes = {}
        platforms_layout = QHBoxLayout()
        platforms = ['telegram', 'vk', 'instagram', 'tiktok']
        for platform in platforms:
            checkbox = QCheckBox(platform.capitalize())
            if platform in ['telegram', 'vk']:
                checkbox.setChecked(True)
            self.platform_checkboxes[platform] = checkbox
            platforms_layout.addWidget(checkbox)
        gen_layout.addRow("Платформы:", platforms_layout)
        
        # TikTok музыка
        tiktok_music_layout = QHBoxLayout()
        
        self.music_file_input = QLineEdit()
        self.music_file_input.setPlaceholderText("Путь к файлу музыки (необязательно)")
        self.music_file_input.setReadOnly(True)
        tiktok_music_layout.addWidget(self.music_file_input)
        
        select_music_btn = QPushButton("Выбрать файл")
        select_music_btn.clicked.connect(self.select_music_file)
        tiktok_music_layout.addWidget(select_music_btn)
        
        gen_layout.addRow("Музыка для TikTok:", tiktok_music_layout)
        
        self.music_link_input = QLineEdit()
        self.music_link_input.setPlaceholderText("Ссылка на музыку в TikTok (необязательно)")
        gen_layout.addRow("Ссылка на музыку:", self.music_link_input)
        
        # Кнопка генерации
        generate_btn = QPushButton("Сгенерировать цитату")
        generate_btn.clicked.connect(self.generate_quote)
        gen_layout.addRow(generate_btn)
        
        # Кнопка генерации TikTok
        generate_tiktok_btn = QPushButton("Сгенерировать TikTok контент")
        generate_tiktok_btn.clicked.connect(self.generate_tiktok_content)
        gen_layout.addRow(generate_tiktok_btn)
        
        content_layout.addWidget(gen_group)
        
        # Превью сгенерированного
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)
        
        # Изображение с кнопкой
        image_layout = QHBoxLayout()
        
        # Изображение
        self.image_preview = QLabel()
        self.image_preview.setMinimumSize(250, 250)
        self.image_preview.setMaximumSize(250, 250)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("background-color: #333; border: 2px solid #555;")
        self.image_preview.setText("Изображение появится здесь")
        image_layout.addWidget(self.image_preview)
        
        # Кнопка просмотра картинок
        view_images_btn = QPushButton("Посмотреть\nкартинки")
        view_images_btn.setMaximumSize(100, 100)
        view_images_btn.clicked.connect(self.view_generated_images)
        image_layout.addWidget(view_images_btn)
        
        preview_layout.addLayout(image_layout)
        
        # Текст цитаты
        self.quote_text = QTextEdit()
        self.quote_text.setMaximumHeight(50)
        self.quote_text.setReadOnly(True)
        preview_layout.addWidget(QLabel("Цитата:"))
        preview_layout.addWidget(self.quote_text)
        
        # Автор
        self.author_text = QLineEdit()
        self.author_text.setReadOnly(True)
        preview_layout.addWidget(QLabel("Автор:"))
        preview_layout.addWidget(self.author_text)
        
        # Описание
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(60)
        self.description_text.setReadOnly(True)
        preview_layout.addWidget(QLabel("Описание:"))
        preview_layout.addWidget(self.description_text)
        
        content_layout.addWidget(preview_group)
        
        # TikTok превью
        tiktok_group = QGroupBox("TikTok контент")
        tiktok_layout = QVBoxLayout()
        tiktok_group.setLayout(tiktok_layout)
        
        # TikTok заголовок
        self.tiktok_title = QLineEdit()
        self.tiktok_title.setReadOnly(True)
        tiktok_layout.addWidget(QLabel("Заголовок:"))
        tiktok_layout.addWidget(self.tiktok_title)
        
        # TikTok описание
        self.tiktok_description = QTextEdit()
        self.tiktok_description.setMaximumHeight(50)
        self.tiktok_description.setReadOnly(True)
        tiktok_layout.addWidget(QLabel("Описание:"))
        tiktok_layout.addWidget(self.tiktok_description)
        
        # TikTok хэштеги
        self.tiktok_hashtags = QLineEdit()
        self.tiktok_hashtags.setReadOnly(True)
        tiktok_layout.addWidget(QLabel("Хэштеги:"))
        tiktok_layout.addWidget(self.tiktok_hashtags)
        
        # Кнопка открытия папки с TikTok контентом
        open_tiktok_folder_btn = QPushButton("Открыть папку с TikTok контентом")
        open_tiktok_folder_btn.clicked.connect(self.open_tiktok_folder)
        tiktok_layout.addWidget(open_tiktok_folder_btn)
        
        content_layout.addWidget(tiktok_group)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        approve_btn = QPushButton("Одобрить и запланировать")
        approve_btn.clicked.connect(self.approve_and_schedule)
        actions_layout.addWidget(approve_btn)
        
        regenerate_btn = QPushButton("Перегенерировать")
        regenerate_btn.clicked.connect(self.generate_quote)
        actions_layout.addWidget(regenerate_btn)
        
        content_layout.addLayout(actions_layout)
        
        # Добавляем stretch чтобы контент не растягивался
        content_layout.addStretch()
        
        # Устанавливаем контент в scroll area
        scroll.setWidget(content_widget)
        
        # Добавляем scroll в основной layout
        layout.addWidget(scroll)
        
        self.tabs.addTab(tab, "Генерация")
    
    def create_quotes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Создаем scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Контейнер для контента
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)
        
        # Добавление цитаты
        add_group = QGroupBox("Добавить цитату вручную")
        add_layout = QFormLayout()
        add_group.setLayout(add_layout)
        
        self.manual_quote = QTextEdit()
        self.manual_quote.setMaximumHeight(50)
        add_layout.addRow("Цитата:", self.manual_quote)
        
        self.manual_author = QLineEdit()
        add_layout.addRow("Автор:", self.manual_author)
        
        self.manual_description = QTextEdit()
        self.manual_description.setMaximumHeight(50)
        add_layout.addRow("Описание:", self.manual_description)
        
        add_btn = QPushButton("Добавить цитату")
        add_btn.clicked.connect(self.add_manual_quote)
        add_layout.addRow(add_btn)
        
        content_layout.addWidget(add_group)
        
        # Список цитат
        self.quotes_list = QListWidget()
        content_layout.addWidget(QLabel("Список цитат:"))
        content_layout.addWidget(self.quotes_list)
        
        # Кнопки для цитат
        quotes_actions = QHBoxLayout()
        
        reload_quotes_btn = QPushButton("Обновить список")
        reload_quotes_btn.clicked.connect(self.load_quotes)
        quotes_actions.addWidget(reload_quotes_btn)
        
        delete_quote_btn = QPushButton("Удалить цитату")
        delete_quote_btn.clicked.connect(self.delete_quote)
        quotes_actions.addWidget(delete_quote_btn)
        
        update_quote_btn = QPushButton("Обновить цитату")
        update_quote_btn.clicked.connect(self.update_quote)
        quotes_actions.addWidget(update_quote_btn)
        
        post_quote_btn = QPushButton("Опубликовать цитату")
        post_quote_btn.clicked.connect(self.post_selected_quote)
        quotes_actions.addWidget(post_quote_btn)
        
        content_layout.addLayout(quotes_actions)
        
        content_layout.addStretch()
        
        # Устанавливаем контент в scroll area
        scroll.setWidget(content_widget)
        
        # Добавляем scroll в основной layout
        layout.addWidget(scroll)
        
        self.tabs.addTab(tab, "Цитаты")
    
    def create_posts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Создаем scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Контейнер для контента
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)
        
        # Список постов
        self.posts_list = QListWidget()
        content_layout.addWidget(QLabel("Список постов:"))
        content_layout.addWidget(self.posts_list)
        
        # Детали поста
        details_group = QGroupBox("Детали поста")
        details_layout = QFormLayout()
        details_group.setLayout(details_layout)
        
        self.post_status = QLabel()
        details_layout.addRow("Статус:", self.post_status)
        
        self.post_platforms = QLabel()
        details_layout.addRow("Платформы:", self.post_platforms)
        
        self.post_scheduled_time = QLabel()
        details_layout.addRow("Запланировано:", self.post_scheduled_time)
        
        self.post_content = QTextEdit()
        self.post_content.setMaximumHeight(60)
        self.post_content.setReadOnly(True)
        details_layout.addRow("Контент:", self.post_content)
        
        content_layout.addWidget(details_group)
        
        # Кнопки
        actions_layout = QHBoxLayout()
        
        publish_now_btn = QPushButton("Опубликовать сейчас")
        publish_now_btn.clicked.connect(self.publish_now)
        actions_layout.addWidget(publish_now_btn)
        
        delete_post_btn = QPushButton("Удалить пост")
        delete_post_btn.clicked.connect(self.delete_post)
        actions_layout.addWidget(delete_post_btn)
        
        content_layout.addLayout(actions_layout)
        
        content_layout.addStretch()
        
        # Устанавливаем контент в scroll area
        scroll.setWidget(content_widget)
        
        # Добавляем scroll в основной layout
        layout.addWidget(scroll)
        
        self.tabs.addTab(tab, "Посты")
    
    def create_scheduler_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Создаем scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Контейнер для контента
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)
        
        # Управление планировщиком
        scheduler_group = QGroupBox("Планировщик")
        scheduler_layout = QVBoxLayout()
        scheduler_group.setLayout(scheduler_layout)
        
        self.scheduler_status = QLabel("Планировщик остановлен")
        scheduler_layout.addWidget(self.scheduler_status)
        
        scheduler_actions = QHBoxLayout()
        
        start_scheduler_btn = QPushButton("Запустить планировщик")
        start_scheduler_btn.clicked.connect(self.start_scheduler)
        scheduler_actions.addWidget(start_scheduler_btn)
        
        stop_scheduler_btn = QPushButton("Остановить планировщик")
        stop_scheduler_btn.clicked.connect(self.stop_scheduler)
        scheduler_actions.addWidget(stop_scheduler_btn)
        
        scheduler_layout.addLayout(scheduler_actions)
        
        content_layout.addWidget(scheduler_group)
        
        # Генерация постов на день
        generate_day_group = QGroupBox("Генерация постов на день")
        generate_day_layout = QVBoxLayout()
        generate_day_group.setLayout(generate_day_layout)
        
        # Выбор платформ для генерации
        self.scheduler_platform_checkboxes = {}
        scheduler_platforms_layout = QHBoxLayout()
        platforms = ['telegram', 'vk', 'instagram', 'tiktok']
        for platform in platforms:
            checkbox = QCheckBox(platform.capitalize())
            if platform in ['telegram', 'vk']:
                checkbox.setChecked(True)
            self.scheduler_platform_checkboxes[platform] = checkbox
            scheduler_platforms_layout.addWidget(checkbox)
        generate_day_layout.addWidget(QLabel("Платформы:"))
        generate_day_layout.addLayout(scheduler_platforms_layout)
        
        generate_day_btn = QPushButton("Сгенерировать и запланировать посты на сегодня")
        generate_day_btn.clicked.connect(self.generate_day_posts)
        generate_day_layout.addWidget(generate_day_btn)
        
        content_layout.addWidget(generate_day_group)
        
        # Информация
        info_label = QLabel(
            "Планировщик автоматически публикует посты в заданное время.\n"
            f"Настроенное время: {', '.join(Config.POST_TIMES)}\n"
            "Убедитесь, что API ключи настроены в файле .env"
        )
        info_label.setWordWrap(True)
        content_layout.addWidget(info_label)
        
        content_layout.addStretch()
        
        # Устанавливаем контент в scroll area
        scroll.setWidget(content_widget)
        
        # Добавляем scroll в основной layout
        layout.addWidget(scroll)
        
        self.tabs.addTab(tab, "Планировщик")
    
    def generate_quote(self):
        """Генерирует новую цитату"""
        try:
            topic = self.topic_input.text() if self.topic_input.text() else None
            
            self.statusBar().showMessage("Генерация цитаты...")
            
            # Генерируем цитату
            self.current_quote_data = self.post_manager.generate_quote_post(topic)
            
            # Обновляем UI
            self.quote_text.setText(self.current_quote_data['quote_data']['quote'])
            self.author_text.setText(self.current_quote_data['quote_data']['author'])
            self.description_text.setText(self.current_quote_data['quote_data']['description'])
            
            # Показываем изображение
            self.current_image_path = self.current_quote_data['image_path']
            self.show_image(self.current_image_path)
            
            self.statusBar().showMessage("Цитата сгенерирована")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации: {str(e)}")
            self.statusBar().showMessage("Ошибка генерации")
    
    def show_image(self, image_path):
        """Показывает изображение в превью"""
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_preview.setPixmap(scaled_pixmap)
            self.image_preview.setScaledContents(False)
        else:
            self.image_preview.setText("Изображение не найдено")
    
    def approve_and_schedule(self):
        """Одобряет и планирует публикацию"""
        if not self.current_quote_data:
            QMessageBox.warning(self, "Предупреждение", "Сначала сгенерируйте цитату")
            return
        
        try:
            # Получаем выбранные платформы
            platforms = [p for p, cb in self.platform_checkboxes.items() if cb.isChecked()]
            
            if not platforms:
                QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы одну платформу")
                return
            
            # Запрашиваем время публикации
            from PyQt6.QtWidgets import QInputDialog
            time_str, ok = QInputDialog.getText(
                self, "Время публикации",
                "Введите время (HH:MM), 'now' для немедленной публикации или оставьте пустым для следующего слота:"
            )
            
            if not ok:
                return
            
            # Подготавливаем данные поста для немедленной публикации
            post_for_publish = {
                'id': None,  # Пост еще не создан в базе
                'quote_id': self.current_quote_data['quote_id'],
                'platforms': ','.join(platforms),
                'content': self.current_quote_data['main_content'],
                'image_path': self.current_quote_data['image_path']
            }
            
            if time_str:
                # Парсим время
                try:
                    time_str = time_str.strip().lower()
                    
                    # Проверяем на "now" для немедленной публикации
                    if time_str == 'now':
                        # Публикуем сразу
                        print(f"Немедленная публикация поста #{self.current_quote_data['quote_id']} на платформы: {platforms}")
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            success = loop.run_until_complete(self.post_manager.scheduler.publish_post(post_for_publish))
                            
                            if success:
                                # Создаем пост в базе с статусом posted
                                new_post_id = self.db.add_post(
                                    quote_id=self.current_quote_data['quote_id'],
                                    title=self.current_quote_data['quote_data']['quote'][:50],
                                    content=post_for_publish['content'],
                                    image_path=post_for_publish['image_path'],
                                    platforms=platforms,
                                    scheduled_time=datetime.now().isoformat()
                                )
                                self.db.update_post_status(new_post_id, 'posted')
                                QMessageBox.information(self, "Успех", f"Пост опубликован на платформы: {', '.join(platforms)}")
                            else:
                                QMessageBox.warning(self, "Предупреждение", "Не удалось опубликовать на всех платформах. Проверьте консоль для деталей.")
                            
                            self.load_posts()
                        finally:
                            try:
                                loop.run_until_complete(self.post_manager.scheduler.telegram_poster.close())
                            except:
                                pass
                            loop.close()
                        
                        return  # Завершаем функцию, так как уже опубликовали
                    else:
                        parts = time_str.split(':')
                        if len(parts) != 2:
                            raise ValueError("Неверный формат")
                        
                        hour = int(parts[0])
                        minute = int(parts[1])
                        
                        if not (0 <= hour <= 23 and 0 <= minute <= 59):
                            raise ValueError("Неверное время")
                        
                        now = datetime.now()
                        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        if scheduled_time < now:
                            scheduled_time += timedelta(days=1)
                        
                        scheduled_time = scheduled_time.isoformat()
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Неверный формат времени. Используйте HH:MM (например, 14:30) или 'now' для немедленной публикации\nОшибка: {str(e)}")
                    return
            else:
                # Используем следующее доступное время
                now = datetime.now()
                today_posts = now.strftime('%H:%M')
                
                scheduled_time = None
                for post_time in Config.POST_TIMES:
                    if post_time > today_posts:
                        hour, minute = map(int, post_time.split(':'))
                        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
                        break
                
                if not scheduled_time:
                    # На завтра
                    hour, minute = map(int, Config.POST_TIMES[0].split(':'))
                    scheduled_time = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
            
            # Создаем пост с уже сгенерированным контентом и изображением
            post_id = self.post_manager.create_scheduled_post(
                self.current_quote_data['quote_id'],
                platforms,
                scheduled_time,
                content=post_for_publish['content'],
                image_path=post_for_publish['image_path']
            )
            
            QMessageBox.information(self, "Успех", f"Пост запланирован (ID: {post_id})")
            self.load_posts()
            self.statusBar().showMessage("Пост запланирован")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при планировании: {str(e)}")
    
    def add_manual_quote(self):
        """Добавляет цитату вручную"""
        quote = self.manual_quote.toPlainText()
        author = self.manual_author.text()
        description = self.manual_description.toPlainText()
        
        if not quote or not author or not description:
            QMessageBox.warning(self, "Предупреждение", "Заполните все поля")
            return
        
        try:
            self.post_manager.add_manual_quote(quote, author, description)
            self.load_quotes()
            
            # Очищаем поля
            self.manual_quote.clear()
            self.manual_author.clear()
            self.manual_description.clear()
            
            QMessageBox.information(self, "Успех", "Цитата добавлена")
            self.statusBar().showMessage("Цитата добавлена")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
    
    def load_quotes(self):
        """Загружает список цитат"""
        self.quotes_list.clear()
        quotes = self.post_manager.get_all_quotes()
        
        for quote in quotes:
            item = QListWidgetItem(f"{quote['author']}: {quote['quote'][:50]}...")
            item.setData(Qt.ItemDataRole.UserRole, quote['id'])
            self.quotes_list.addItem(item)
    
    def load_posts(self):
        """Загружает список постов"""
        self.posts_list.clear()
        posts = self.post_manager.get_all_posts()
        
        for post in posts:
            status_emoji = {
                'pending': '⏳',
                'posted': '✅',
                'failed': '❌'
            }.get(post['status'], '❓')
            
            item = QListWidgetItem(f"{status_emoji} Пост #{post['id']} - {post['status']} | {post['scheduled_time'] or 'Не запланировано'}")
            item.setData(Qt.ItemDataRole.UserRole, post['id'])
            self.posts_list.addItem(item)
    
    def publish_now(self):
        """Публикует выбранный пост сейчас"""
        current_item = self.posts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите пост")
            return
        
        post_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        try:
            post = self.db.get_post(post_id)
            
            # Создаем диалог выбора платформ
            dialog = QDialog(self)
            dialog.setWindowTitle("Выберите платформы для публикации")
            dialog_layout = QVBoxLayout()
            dialog.setLayout(dialog_layout)
            
            dialog_layout.addWidget(QLabel("Выберите платформы для публикации:"))
            
            # Получаем платформы из поста (уже список)
            post_platforms = post['platforms'] if post['platforms'] else []
            
            platform_checkboxes = {}
            platforms = ['telegram', 'vk', 'instagram', 'tiktok']
            for platform in platforms:
                checkbox = QCheckBox(platform.capitalize())
                # Отмечаем платформы, которые указаны в посте
                if platform in post_platforms:
                    checkbox.setChecked(True)
                platform_checkboxes[platform] = checkbox
                dialog_layout.addWidget(checkbox)
            
            button_layout = QHBoxLayout()
            ok_btn = QPushButton("Опубликовать")
            cancel_btn = QPushButton("Отмена")
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            dialog_layout.addLayout(button_layout)
            
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_platforms = [p for p, cb in platform_checkboxes.items() if cb.isChecked()]
                
                if not selected_platforms:
                    QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы одну платформу")
                    return
                
                # Обновляем пост с выбранными платформами (преобразуем в строку для базы)
                post['platforms'] = ','.join(selected_platforms)
                
                print(f"Начинаем публикацию поста #{post_id} на платформы: {selected_platforms}")
                print(f"Изображение: {post['image_path']}")
                print(f"Контент: {post['content'][:100]}...")
                
                # Запускаем асинхронную публикацию
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    success = loop.run_until_complete(self.post_manager.scheduler.publish_post(post))
                    
                    if success:
                        self.db.update_post_status(post_id, 'posted')
                        QMessageBox.information(self, "Успех", f"Пост опубликован на платформах: {', '.join(selected_platforms)}")
                    else:
                        self.db.update_post_status(post_id, 'failed')
                        QMessageBox.warning(self, "Предупреждение", "Не удалось опубликовать на всех платформах. Проверьте консоль для деталей.")
                    
                    self.load_posts()
                finally:
                    # Закрываем сессию бота
                    try:
                        loop.run_until_complete(self.post_manager.scheduler.telegram_poster.close())
                    except:
                        pass
                    loop.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при публикации: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def delete_post(self):
        """Удаляет выбранный пост"""
        current_item = self.posts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите пост")
            return
        
        post_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить пост?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Удаляем пост из базы (прямым SQL)
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
                    conn.commit()
                
                self.load_posts()
                QMessageBox.information(self, "Успех", "Пост удален")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def start_scheduler(self):
        """Запускает планировщик"""
        try:
            self.post_manager.start_scheduler()
            self.scheduler_status.setText("Планировщик запущен")
            self.scheduler_status.setStyleSheet("color: green;")
            self.statusBar().showMessage("Планировщик запущен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при запуске: {str(e)}")
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        try:
            self.post_manager.stop_scheduler()
            self.scheduler_status.setText("Планировщик остановлен")
            self.scheduler_status.setStyleSheet("color: red;")
            self.statusBar().showMessage("Планировщик остановлен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при остановке: {str(e)}")
    
    def select_music_file(self):
        """Выбирает файл музыки для TikTok"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл музыки", "", 
            "Audio files (*.mp3 *.wav *.ogg *.m4a);;All files (*)"
        )
        if file_path:
            self.music_file_input.setText(file_path)
    
    def generate_tiktok_content(self):
        """Генерирует TikTok контент"""
        if not self.current_quote_data:
            QMessageBox.warning(self, "Предупреждение", "Сначала сгенерируйте цитату")
            return
        
        try:
            self.statusBar().showMessage("Генерация TikTok контента...")
            
            music_path = self.music_file_input.text() if self.music_file_input.text() else None
            music_link = self.music_link_input.text() if self.music_link_input.text() else None
            
            # Генерируем TikTok контент
            tiktok_data = self.post_manager.generate_tiktok_content(
                self.current_quote_data['quote_data'],
                music_path,
                music_link
            )
            
            # Обновляем UI
            self.tiktok_title.setText(tiktok_data['title'])
            self.tiktok_description.setText(tiktok_data['description'])
            self.tiktok_hashtags.setText(tiktok_data['hashtags'])
            
            self.statusBar().showMessage("TikTok контент сгенерирован")
            QMessageBox.information(
                self, "Успех",
                f"TikTok контент сгенерирован!\n\n"
                f"Данные для публикации: {tiktok_data['save_path']}\n\n"
                f"Откройте папку с TikTok контентом для публикации."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации TikTok контента: {str(e)}")
            self.statusBar().showMessage("Ошибка генерации TikTok контента")
    
    def open_tiktok_folder(self):
        """Открывает папку с TikTok контентом"""
        import subprocess
        tiktok_dir = os.path.join(Config.IMAGES_DIR, 'tiktok_content')
        if os.path.exists(tiktok_dir):
            subprocess.run(['open', tiktok_dir])
        else:
            QMessageBox.warning(self, "Предупреждение", "Папка с TikTok контентом не найдена")
    
    def view_generated_images(self):
        """Открывает папку с сгенерированными изображениями"""
        import subprocess
        generated_dir = Config.GENERATED_IMAGES_DIR
        if os.path.exists(generated_dir):
            subprocess.run(['open', generated_dir])
        else:
            QMessageBox.warning(self, "Предупреждение", "Папка с изображениями не найдена")
    
    def delete_quote(self):
        """Удаляет выбранную цитату"""
        current_item = self.quotes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите цитату для удаления")
            return
        
        quote_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить цитату?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_quote(quote_id)
                self.load_quotes()
                QMessageBox.information(self, "Успех", "Цитата удалена")
                self.statusBar().showMessage("Цитата удалена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def create_quote_image_from_dialog(self, quote_edit, author_edit, quote_id=None):
        """Создает картинку из текста в диалоге редактирования"""
        try:
            quote_text = quote_edit.toPlainText()
            author_text = author_edit.text()
            
            if not quote_text or not author_text:
                QMessageBox.warning(self, "Предупреждение", "Заполните цитату и автора")
                return
            
            # Генерируем картинку
            image_path = self.post_manager.image_generator.create_quote_image(quote_text, author_text)
            
            # Если quote_id передан, обновляем путь в базе
            if quote_id:
                self.db.update_quote_image_path(quote_id, image_path)
            
            QMessageBox.information(
                self, "Успех",
                f"Картинка создана!\n\nПуть: {image_path}\n\nВы можете найти её в папке images/generated/"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании картинки: {str(e)}")
    
    def update_quote(self):
        """Обновляет выбранную цитату новым описанием"""
        current_item = self.quotes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите цитату для обновления")
            return
        
        quote_id = current_item.data(Qt.ItemDataRole.UserRole)
        quote_data = self.db.get_quote(quote_id)
        
        # Создаем диалог для редактирования
        dialog = QDialog(self)
        dialog.setWindowTitle("Обновить цитату")
        dialog_layout = QVBoxLayout()
        dialog.setLayout(dialog_layout)
        
        dialog_layout.addWidget(QLabel("Цитата:"))
        quote_edit = QTextEdit()
        quote_edit.setText(quote_data['quote'])
        quote_edit.setMaximumHeight(50)
        dialog_layout.addWidget(quote_edit)
        
        dialog_layout.addWidget(QLabel("Автор:"))
        author_edit = QLineEdit()
        author_edit.setText(quote_data['author'])
        dialog_layout.addWidget(author_edit)
        
        dialog_layout.addWidget(QLabel("Описание:"))
        description_edit = QTextEdit()
        description_edit.setText(quote_data['description'])
        description_edit.setMaximumHeight(80)
        dialog_layout.addWidget(description_edit)
        
        # Кнопка создания картинки
        create_image_btn = QPushButton("Создать картинку")
        create_image_btn.clicked.connect(lambda: self.create_quote_image_from_dialog(quote_edit, author_edit, quote_id))
        dialog_layout.addWidget(create_image_btn)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Обновить")
        cancel_btn = QPushButton("Отмена")
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        dialog_layout.addLayout(button_layout)
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                new_quote = quote_edit.toPlainText()
                new_author = author_edit.text()
                new_description = description_edit.toPlainText()
                
                if not new_quote or not new_author or not new_description:
                    QMessageBox.warning(self, "Предупреждение", "Заполните все поля")
                    return
                
                # Обновляем цитату в базе
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE quotes SET quote = ?, author = ?, description = ?
                        WHERE id = ?
                    ''', (new_quote, new_author, new_description, quote_id))
                    conn.commit()
                
                self.load_quotes()
                QMessageBox.information(self, "Успех", "Цитата обновлена")
                self.statusBar().showMessage("Цитата обновлена")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
    
    def post_selected_quote(self):
        """Публикует выбранную цитату с выбором платформ"""
        current_item = self.quotes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите цитату для публикации")
            return
        
        quote_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        try:
            # Получаем данные цитаты
            quote_data = self.db.get_quote(quote_id)
            
            # Создаем диалог выбора платформ
            dialog = QDialog(self)
            dialog.setWindowTitle("Выберите платформы")
            dialog_layout = QVBoxLayout()
            dialog.setLayout(dialog_layout)
            
            dialog_layout.addWidget(QLabel("Выберите платформы для публикации:"))
            
            platform_checkboxes = {}
            platforms = ['telegram', 'vk', 'instagram', 'tiktok']
            for platform in platforms:
                checkbox = QCheckBox(platform.capitalize())
                if platform in ['telegram', 'vk']:
                    checkbox.setChecked(True)
                platform_checkboxes[platform] = checkbox
                dialog_layout.addWidget(checkbox)
            
            button_layout = QHBoxLayout()
            ok_btn = QPushButton("OK")
            cancel_btn = QPushButton("Отмена")
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            dialog_layout.addLayout(button_layout)
            
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_platforms = [p for p, cb in platform_checkboxes.items() if cb.isChecked()]
                
                if not selected_platforms:
                    QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы одну платформу")
                    return
                
                # Проверяем наличие картинки
                if not quote_data.get('image_path'):
                    QMessageBox.warning(
                        self, "Ошибка",
                        "Для этой цитаты нет изображения. Сначала создайте картинку через кнопку 'Обновить цитату' -> 'Создать картинку'"
                    )
                    return
                
                # Генерируем контент (без создания картинки)
                content = self.post_manager.text_generator.generate_post_content(
                    quote_data['quote'], quote_data['author'], quote_data['description'],
                    selected_platforms[0] if selected_platforms else 'telegram'
                )
                
                image_path = quote_data['image_path']
                
                # Запрашиваем время публикации
                from PyQt6.QtWidgets import QInputDialog
                time_str, ok = QInputDialog.getText(
                    self, "Время публикации",
                    "Введите время (HH:MM), 'now' для немедленной публикации или оставьте пустым для следующего слота:"
                )
                
                if not ok:
                    return
                
                if time_str:
                    # Парсим время
                    try:
                        time_str = time_str.strip().lower()
                        
                        # Проверяем на "now" для немедленной публикации
                        if time_str == 'now':
                            # Публикуем сразу
                            post_data = {
                                'id': None,  # Пост еще не создан в базе
                                'quote_id': quote_id,
                                'platforms': ','.join(selected_platforms),
                                'content': content,
                                'image_path': image_path
                            }
                            
                            print(f"Немедленная публикация цитаты #{quote_id} на платформы: {selected_platforms}")
                            
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            try:
                                success = loop.run_until_complete(self.post_manager.scheduler.publish_post(post_data))
                                
                                if success:
                                    # Создаем пост в базе с статусом posted
                                    post_id = self.db.add_post(
                                        quote_id=quote_id,
                                        title=quote_data['quote'][:50],
                                        content=content,
                                        image_path=image_path,
                                        platforms=selected_platforms,
                                        scheduled_time=datetime.now().isoformat()
                                    )
                                    self.db.update_post_status(post_id, 'posted')
                                    QMessageBox.information(self, "Успех", f"Пост опубликован на платформах: {', '.join(selected_platforms)}")
                                else:
                                    QMessageBox.warning(self, "Предупреждение", "Не удалось опубликовать на всех платформах. Проверьте консоль для деталей.")
                                
                                self.load_posts()
                            finally:
                                try:
                                    loop.run_until_complete(self.post_manager.scheduler.telegram_poster.close())
                                except:
                                    pass
                                loop.close()
                            
                            return  # Завершаем функцию, так как уже опубликовали
                        else:
                            parts = time_str.split(':')
                            if len(parts) != 2:
                                raise ValueError("Неверный формат")
                            
                            hour = int(parts[0])
                            minute = int(parts[1])
                            
                            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                                raise ValueError("Неверное время")
                            
                            now = datetime.now()
                            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            
                            if scheduled_time < now:
                                scheduled_time += timedelta(days=1)
                            
                            scheduled_time = scheduled_time.isoformat()
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка", f"Неверный формат времени. Используйте HH:MM (например, 14:30) или 'now' для немедленной публикации\nОшибка: {str(e)}")
                        return
                else:
                    # Используем следующее доступное время
                    now = datetime.now()
                    today_posts = now.strftime('%H:%M')
                    
                    scheduled_time = None
                    for post_time in Config.POST_TIMES:
                        if post_time > today_posts:
                            hour, minute = map(int, post_time.split(':'))
                            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
                            break
                    
                    if not scheduled_time:
                        # На завтра
                        hour, minute = map(int, Config.POST_TIMES[0].split(':'))
                        scheduled_time = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
                
                # Создаем пост в базе с уже сгенерированным контентом и изображением
                post_id = self.post_manager.create_scheduled_post(
                    quote_id=quote_id,
                    platforms=selected_platforms,
                    scheduled_time=scheduled_time,
                    content=content,
                    image_path=image_path
                )
                
                QMessageBox.information(
                    self, "Успех",
                    f"Пост создан и запланирован на {scheduled_time}\nПлатформы: {', '.join(selected_platforms)}"
                )
                self.load_posts()
                self.statusBar().showMessage("Пост создан")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при публикации: {str(e)}")
    
    def generate_day_posts(self):
        """Генерирует посты на день"""
        try:
            # Получаем выбранные платформы
            platforms = [p for p, cb in self.scheduler_platform_checkboxes.items() if cb.isChecked()]
            
            if not platforms:
                QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы одну платформу")
                return
            
            post_ids = self.post_manager.schedule_posts_for_day(platforms)
            
            QMessageBox.information(
                self, "Успех",
                f"Сгенерировано и запланировано {len(post_ids)} постов для платформ: {', '.join(platforms)}"
            )
            self.load_posts()
            self.statusBar().showMessage("Посты на день сгенерированы")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
