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
            'text_objects_found': 0,
            'image_objects_found': 0,
            'start_time': None,
            'end_time': None
        }
    
    def detect_text_regions(self, img):
        """Обнаружение текстовых регионов"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            denoised = cv2.medianBlur(gray, 3)
            
            _, text_mask1 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            _, text_mask2 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            text_mask = cv2.bitwise_or(text_mask1, text_mask2)
            
            kernel_horizontal = np.ones((1, 15), np.uint8)
            kernel_vertical = np.ones((5, 1), np.uint8)
            
            text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel_horizontal)
            text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel_vertical)
            
            return text_mask
        except Exception:
            return None
    
    def detect_image_objects(self, img):
        """Обнаружение графических объектов"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            binary_adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            
            _, binary_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            combined_binary = cv2.bitwise_or(binary_adaptive, binary_otsu)
            
            kernel = np.ones((3, 3), np.uint8)
            combined_binary = cv2.morphologyEx(combined_binary, cv2.MORPH_OPEN, kernel)
            combined_binary = cv2.morphologyEx(combined_binary, cv2.MORPH_CLOSE, kernel)
            
            return combined_binary
        except Exception:
            return None
    
    def process_contours(self, contours, img, frames_dir, object_type="image"):
        """Обработка контуров и сохранение объектов"""
        objects_found = 0
        small_objects = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            min_area = 50 if object_type == "text" else 100
            
            if area < min_area:
                small_objects += 1
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            padding = 10 if object_type == "text" else 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.shape[1] - x, w + 2 * padding)
            h = min(img.shape[0] - y, h + 2 * padding)
            
            aspect_ratio = w / h
            if aspect_ratio > 10 or aspect_ratio < 0.1:
                continue
            
            object_img = img[y:y+h, x:x+w]
            
            frame_filename = frames_dir / f"frame_{self.stats['total_objects']:06d}.png"
            success = cv2.imwrite(str(frame_filename), object_img)
            
            if success:
                self.stats['total_objects'] += 1
                objects_found += 1
                
                if object_type == "text":
                    self.stats['text_objects_found'] += 1
                else:
                    self.stats['image_objects_found'] += 1
        
        return objects_found, small_objects
    
    def process_images(self):
        """Основной процесс обработки"""
        self.stats['start_time'] = datetime.now()
        
        print("🚀 Запуск программы")
        print(f"⏰ Время начала: {self.stats['start_time'].strftime('%H:%M:%S')}")
        
        # Создаем папку для фреймов
        frames_dir = Path('./static/frames')
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Ищем все папки глав
        chapters = sorted([p for p in Path('./static/').iterdir() 
                          if p.is_dir() and p.name.startswith('chapter_')])
        
        self.stats['total_chapters'] = len(chapters)
        
        if self.stats['total_chapters'] == 0:
            print("❌ Ошибка: Папки глав не найдены")
            return
        
        # Подсчет общего количества изображений
        total_images = 0
        for chapter_path in chapters:
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(chapter_path.glob(ext))
            total_images += len(images)
        
        self.stats['total_images'] = total_images
        
        print(f"📁 Глав: {self.stats['total_chapters']}")
        print(f"🖼️ Изображений: {total_images}")
        print()
        
        if total_images == 0:
            print("❌ Ошибка: Изображения не найдены")
            return
        
        # Обработка глав
        for chapter_idx, chapter_path in enumerate(chapters, 1):
            print(f"📖 {chapter_path.name} ({chapter_idx}/{self.stats['total_chapters']})")
            
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(sorted(chapter_path.glob(ext)))
            
            chapter_objects = 0
            chapter_text_objects = 0
            chapter_image_objects = 0
            chapter_small_objects = 0
            
            for image_idx, image_path in enumerate(images, 1):
                try:
                    img = cv2.imread(str(image_path))
                    if img is None:
                        self.stats['failed_images'] += 1
                        continue
                    
                    # Обнаружение текста
                    text_mask = self.detect_text_regions(img)
                    text_objects_found = 0
                    text_small_objects = 0
                    
                    if text_mask is not None:
                        text_contours, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        text_objects, text_small = self.process_contours(text_contours, img, frames_dir, "text")
                        text_objects_found = text_objects
                        text_small_objects = text_small
                    
                    # Обнаружение изображений
                    image_mask = self.detect_image_objects(img)
                    image_objects_found = 0
                    image_small_objects = 0
                    
                    if image_mask is not None:
                        image_contours, _ = cv2.findContours(image_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        image_objects, image_small = self.process_contours(image_contours, img, frames_dir, "image")
                        image_objects_found = image_objects
                        image_small_objects = image_small
                    
                    # Обновляем статистику
                    self.stats['small_objects_skipped'] += text_small_objects + image_small_objects
                    self.stats['processed_images'] += 1
                    
                    total_objects_found = text_objects_found + image_objects_found
                    chapter_objects += total_objects_found
                    chapter_text_objects += text_objects_found
                    chapter_image_objects += image_objects_found
                    chapter_small_objects += text_small_objects + image_small_objects
                    
                except Exception:
                    self.stats['failed_images'] += 1
                    continue
            
            print(f"   📝 Текст: {chapter_text_objects}")
            print(f"   🖼️  Изобр: {chapter_image_objects}")
            print(f"   📊 Всего: {chapter_objects}")
            self.stats['processed_chapters'] += 1
        
        self.stats['end_time'] = datetime.now()
        
        # Финальная статистика
        self.print_stats()
    
    def print_stats(self):
        """Вывод статистики"""
        print("\n" + "="*40)
        print("РЕЗУЛЬТАТЫ")
        print("="*40)
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"Время: {duration}")
        
        print(f"Глав: {self.stats['processed_chapters']}/{self.stats['total_chapters']}")
        print(f"Изображений: {self.stats['processed_images']}/{self.stats['total_images']}")
        print(f"Ошибок: {self.stats['failed_images']}")
        print(f"Текст: {self.stats['text_objects_found']}")
        print(f"Изобр: {self.stats['image_objects_found']}")
        print(f"Всего: {self.stats['total_objects']}")
        
        if self.stats['processed_images'] > 0:
            success_rate = (self.stats['processed_images'] / self.stats['total_images']) * 100
            objects_per_image = self.stats['total_objects'] / self.stats['processed_images'] if self.stats['processed_images'] > 0 else 0
            print(f"Успешно: {success_rate:.1f}%")
            print(f"На изображение: {objects_per_image:.1f}")
        
        print("="*40)

def main():
    extractor = FrameExtractor()
    
    try:
        extractor.process_images()
    except KeyboardInterrupt:
        print("\nПрервано пользователем")
        if extractor.stats['start_time'] and not extractor.stats['end_time']:
            extractor.stats['end_time'] = datetime.now()
        extractor.print_stats()
    except Exception as e:
        print(f"\nОшибка: {str(e)}")
        if extractor.stats['start_time'] and not extractor.stats['end_time']:
            extractor.stats['end_time'] = datetime.now()
        extractor.print_stats()

if __name__ == "__main__":
    main()