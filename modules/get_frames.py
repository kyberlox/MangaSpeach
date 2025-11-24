import os
import cv2
import numpy as np
from pathlib import Path
import time
from datetime import datetime

class FrameExtractor:
    def __init__(self):
        self.stats = {
            'total_chapters': 0,
            'processed_chapters': 0,
            'total_images': 0,
            'processed_images': 0,
            'failed_images': 0,
            'total_objects': 0,
            'small_objects_skipped': 0,
            'start_time': None,
            'end_time': None
        }
        
    def debug_print(self, message):
        """Простой вывод для отладки"""
        print(f"[DEBUG] {datetime.now().strftime('%H:%M:%S')} - {message}")
        
    def check_directory_structure(self):
        """Проверка структуры директорий"""
        self.debug_print("Проверка структуры директорий...")
        
        current_dir = Path(".").absolute()
        self.debug_print(f"Текущая директория: {current_dir}")
        
        # ПРОВЕРЯЕМ ПРАВИЛЬНЫЙ ПУТЬ - ./static/ а не ./static/frames/
        static_path = Path("./static/")
        self.debug_print(f"Путь к static: {static_path.absolute()}")
        self.debug_print(f"Static существует: {static_path.exists()}")
        
        if static_path.exists():
            items = list(static_path.iterdir())
            self.debug_print(f"Содержимое static: {[item.name for item in items]}")
            
            chapters = [item for item in items if item.is_dir() and item.name.startswith('chapter_')]
            self.debug_print(f"Найдено папок глав: {len(chapters)}")
            
            for chapter in sorted(chapters):
                images = list(chapter.glob("*.png")) + list(chapter.glob("*.jpg")) + list(chapter.glob("*.jpeg"))
                self.debug_print(f"  {chapter.name}: {len(images)} изображений")
                
        return static_path.exists()
    
    def process_images(self):
        """Основной процесс обработки"""
        self.debug_print("Запуск process_images")
        
        # Проверяем структуру директорий
        if not self.check_directory_structure():
            self.debug_print("❌ ОШИБКА: Неправильная структура директорий!")
            return
        
        self.stats['start_time'] = datetime.now()
        
        print("🚀 ЗАПУСК ПРОГРАММЫ ИЗВЛЕЧЕНИЯ КАДРОВ")
        print(f"⏰ Время начала: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Создаем папку для фреймов (это куда сохраняем результат)
        frames_dir = Path('./static/frames')
        frames_dir.mkdir(parents=True, exist_ok=True)
        self.debug_print(f"Создана папка для фреймов: {frames_dir.absolute()}")
        
        # Ищем все папки глав в ПРАВИЛЬНОМ МЕСТЕ - ./static/
        chapters = sorted([p for p in Path('./static/').iterdir() 
                          if p.is_dir() and p.name.startswith('chapter_')])
        
        self.stats['total_chapters'] = len(chapters)
        self.debug_print(f"Найдено глав для обработки: {self.stats['total_chapters']}")
        
        if self.stats['total_chapters'] == 0:
            print("❌ ОШИБКА: Папки глав не найдены!")
            print("Убедитесь, что:")
            print("  - Папки называются chapter_001, chapter_002, ...")
            print("  - Папки расположены в ./static/")  # ИСПРАВЛЕНО
            print("  - Программа запущена из правильной директории")
            return
        
        # Подсчет общего количества изображений
        total_images = 0
        for chapter_path in chapters:
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(chapter_path.glob(ext))
            total_images += len(images)
        
        self.stats['total_images'] = total_images
        print(f"📁 Обнаружено глав: {self.stats['total_chapters']}")
        print(f"🖼️  Всего изображений для обработки: {total_images}")
        print()
        
        if total_images == 0:
            print("❌ ОШИБКА: Изображения не найдены!")
            print("Убедитесь, что в папках глав есть файлы .png, .jpg или .jpeg")
            return
        
        # Обработка глав
        for chapter_idx, chapter_path in enumerate(chapters, 1):
            print(f"📖 Обрабатывается глава {chapter_path.name} ({chapter_idx}/{self.stats['total_chapters']})")
            
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(sorted(chapter_path.glob(ext)))
            
            chapter_objects = 0
            
            for image_idx, image_path in enumerate(images, 1):
                print(f"  🖼️  Обработка {image_idx}/{len(images)}: {image_path.name}")
                
                try:
                    # Загружаем изображение
                    img = cv2.imread(str(image_path))
                    if img is None:
                        print(f"    ❌ Не удалось загрузить изображение")
                        self.stats['failed_images'] += 1
                        continue
                    
                    self.debug_print(f"Изображение загружено: {img.shape}")
                    
                    # Создаем копию и преобразуем в grayscale
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Определяем тип фона по среднему значению яркости
                    mean_val = np.mean(gray)
                    is_light_bg = mean_val > 127
                    
                    print(f"    📊 Размер: {img.shape[1]}x{img.shape[0]}px, фон: {'светлый' if is_light_bg else 'темный'} (яркость: {mean_val:.1f})")
                    
                    # Бинаризация в зависимости от типа фона
                    if is_light_bg:
                        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
                    else:
                        _, thresh = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
                    
                    # Морфологические операции для улучшения маски
                    kernel = np.ones((3,3), np.uint8)
                    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
                    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                    
                    # Поиск контуров
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    self.debug_print(f"Найдено контуров: {len(contours)}")
                    
                    objects_found = 0
                    small_objects = 0
                    
                    for i, contour in enumerate(contours):
                        area = cv2.contourArea(contour)
                        
                        if area < 500:  # Фильтр маленьких областей
                            small_objects += 1
                            continue
                        
                        # Получаем ограничивающую рамку
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Добавляем отступы
                        padding = 5
                        x = max(0, x - padding)
                        y = max(0, y - padding)
                        w = min(img.shape[1] - x, w + 2 * padding)
                        h = min(img.shape[0] - y, h + 2 * padding)
                        
                        # Вырезаем объект
                        object_img = img[y:y+h, x:x+w]
                        
                        # Сохраняем кадр в frames_dir
                        frame_filename = frames_dir / f"frame_{self.stats['total_objects']:06d}.png"
                        success = cv2.imwrite(str(frame_filename), object_img)
                        
                        if success:
                            self.stats['total_objects'] += 1
                            objects_found += 1
                        else:
                            print(f"    ❌ Ошибка сохранения кадра {frame_filename}")
                    
                    self.stats['small_objects_skipped'] += small_objects
                    self.stats['processed_images'] += 1
                    
                    if objects_found > 0:
                        print(f"    ✅ Найдено объектов: {objects_found} (пропущено мелких: {small_objects})")
                    else:
                        print(f"    ⚠️  Объекты не обнаружены (пропущено мелких: {small_objects})")
                    
                    chapter_objects += objects_found
                    
                    # Прогресс в реальном времени
                    progress = (self.stats['processed_images'] / total_images) * 100
                    print(f"    📊 Общий прогресс: {progress:.1f}% ({self.stats['processed_images']}/{total_images})")
                    
                except Exception as e:
                    print(f"    ❌ Ошибка при обработке {image_path}: {str(e)}")
                    self.stats['failed_images'] += 1
                    continue
                
                print()  # Пустая строка между изображениями
            
            print(f"✅ Глава {chapter_path.name} завершена: {chapter_objects} объектов")
            self.stats['processed_chapters'] += 1
            print("-" * 50)
        
        self.stats['end_time'] = datetime.now()
        
        # Финальная статистика
        self.print_stats()
    
    def print_stats(self):
        """Вывод подробной статистики"""
        print("\n" + "="*60)
        print("ФИНАЛЬНАЯ СТАТИСТИКА")
        print("="*60)
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"Общее время обработки: {duration}")
        
        print(f"Всего глав обнаружено: {self.stats['total_chapters']}")
        print(f"Обработано глав: {self.stats['processed_chapters']}")
        print(f"Всего изображений: {self.stats['total_images']}")
        print(f"Успешно обработано: {self.stats['processed_images']}")
        print(f"Не удалось обработать: {self.stats['failed_images']}")
        print(f"Обнаружено объектов: {self.stats['total_objects']}")
        print(f"Пропущено мелких объектов: {self.stats['small_objects_skipped']}")
        
        if self.stats['processed_images'] > 0:
            success_rate = (self.stats['processed_images'] / self.stats['total_images']) * 100
            objects_per_image = self.stats['total_objects'] / self.stats['processed_images'] if self.stats['processed_images'] > 0 else 0
            print(f"Процент успешной обработки: {success_rate:.1f}%")
            print(f"Среднее объектов на изображение: {objects_per_image:.1f}")
        
        print("="*60)

def main():
    print("🎬 ИНИЦИАЛИЗАЦИЯ ПРОГРАММЫ")
    extractor = FrameExtractor()
    
    try:
        extractor.process_images()
    except KeyboardInterrupt:
        print("\n\n⚠️  Обработка прервана пользователем")
        if extractor.stats['start_time'] and not extractor.stats['end_time']:
            extractor.stats['end_time'] = datetime.now()
        extractor.print_stats()
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        if extractor.stats['start_time'] and not extractor.stats['end_time']:
            extractor.stats['end_time'] = datetime.now()
        extractor.print_stats()

if __name__ == "__main__":
    main()