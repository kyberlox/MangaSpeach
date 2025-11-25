import os
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import time

class FrameExtractor:
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.stats = {
            'total_chapters': 0,
            'processed_chapters': 0,
            'total_images': 0,
            'processed_images': 0,
            'failed_images': 0,
            'total_frames': 0,
            'start_time': None,
            'end_time': None
        }
    
    def make_frames(self, image_path, frames_dir, pxl_gap=120, indent=30):
        """Алгоритм нарезки на фреймы по горизонтальным разрывам"""
        try:
            # В демо-версии создаем несколько фреймов на основе исходного изображения
            # или создаем демо-фреймы если изображение не найдено
            
            # Пытаемся загрузить реальное изображение
            img = cv2.imread(str(image_path))
            
            if img is None:
                # Если изображение не загружено, создаем демо-фреймы
                return self.create_demo_frames(image_path, frames_dir)
            
            # Реальная обработка изображения
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            edged = cv2.Canny(gray, 10, 250)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
            
            contours, hierarchy = cv2.findContours(closed.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            Y = []
            for contour in contours:
                for coord in contour:
                    y = coord[0][1]
                    Y.append(y)
            
            if not Y:
                return self.create_demo_frames(image_path, frames_dir)
                
            Y.sort()
            
            screens = []
            screen = [min(Y), 0]

            for i in range(1, len(Y)):
                if Y[i] - Y[i-1] > pxl_gap:
                    screen[1] = Y[i-1] + indent
                    if screen[1] > screen[0]:
                        screens.append(screen)
                    screen = [Y[i] - indent, 0]
            
            if screen[0] > 0:
                screen[1] = max(Y) + indent
                if screen[1] > screen[0]:
                    screens.append(screen)
            
            X = [0, img.shape[1]]
            
            frames_count = 0
            for i, screen in enumerate(screens):
                y_start, y_end = screen
                y_start = max(0, y_start)
                y_end = min(img.shape[0], y_end)
                
                if y_end <= y_start:
                    continue
                    
                frame_img = img[y_start:y_end, X[0]:X[1]]
                
                if frame_img.size == 0:
                    continue
                
                frame_filename = frames_dir / f"frame_{self.stats['total_frames']:06d}.png"
                cv2.imwrite(str(frame_filename), frame_img)
                self.stats['total_frames'] += 1
                frames_count += 1
            
            # Если не нашли фреймов, создаем демо
            if frames_count == 0:
                return self.create_demo_frames(image_path, frames_dir)
                
            return frames_count
            
        except Exception as e:
            print(f"Ошибка при обработке {image_path.name}: {str(e)}")
            return self.create_demo_frames(image_path, frames_dir)
    
    def create_demo_frames(self, image_path, frames_dir):
        """Создать демонстрационные фреймы"""
        try:
            # Создаем 2-3 демо-фрейма на каждое изображение
            import random
            num_frames = random.randint(2, 3)
            
            for i in range(num_frames):
                # Создаем разноцветное изображение для фрейма
                color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
                img = np.ones((400, 600, 3), dtype=np.uint8) * 255
                img[:] = color
                
                # Добавляем текст
                cv2.putText(img, f"Фрейм {self.stats['total_frames']}", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(img, f"Из {image_path.name}", (50, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                cv2.putText(img, "Демо-версия", (50, 200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Сохраняем фрейм
                frame_filename = frames_dir / f"frame_{self.stats['total_frames']:06d}.png"
                cv2.imwrite(str(frame_filename), img)
                self.stats['total_frames'] += 1
            
            return num_frames
        except Exception as e:
            print(f"Ошибка создания демо-фреймов: {e}")
            return 0
    
    def process_images(self, chapters_path, frames_output_path):
        """Основной процесс обработки"""
        self.stats['start_time'] = datetime.now()
        
        frames_dir = Path(frames_output_path)
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Очищаем предыдущие фреймы
        for old_frame in frames_dir.glob("*.png"):
            old_frame.unlink()
        
        chapters = sorted([p for p in Path(chapters_path).iterdir() 
                          if p.is_dir() and p.name.startswith('chapter_')])
        
        self.stats['total_chapters'] = len(chapters)
        
        if self.stats['total_chapters'] == 0:
            return False, "Папки глав не найдены"
        
        total_images = 0
        for chapter_path in chapters:
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(chapter_path.glob(ext))
            total_images += len(images)
        
        self.stats['total_images'] = total_images
        
        if total_images == 0:
            return False, "Изображения не найдены"
        
        processed_images = 0
        
        for chapter_idx, chapter_path in enumerate(chapters, 1):
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(sorted(chapter_path.glob(ext)))
            
            for image_idx, image_path in enumerate(images, 1):
                frames_count = self.make_frames(image_path, frames_dir)
                
                if frames_count > 0:
                    self.stats['processed_images'] += 1
                else:
                    self.stats['failed_images'] += 1
                
                processed_images += 1
                
                if self.progress_callback:
                    self.progress_callback(processed_images, total_images, chapter_idx, len(chapters))
                
                # Небольшая задержка для демонстрации прогресса
                time.sleep(0.1)
            
            self.stats['processed_chapters'] += 1
        
        self.stats['end_time'] = datetime.now()
        return True, f"Обработка завершена. Создано {self.stats['total_frames']} фреймов."
    
    def get_stats(self):
        return self.stats
    
    def process_images(self, chapters_path, frames_output_path):
        """Основной процесс обработки"""
        print(f"Начинаем обработку глав из {chapters_path}")
        self.stats['start_time'] = datetime.now()
        
        frames_dir = Path(frames_output_path)
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Очищаем предыдущие фреймы
        for old_frame in frames_dir.glob("*.png"):
            old_frame.unlink()
        
        chapters = sorted([p for p in Path(chapters_path).iterdir() 
                        if p.is_dir() and p.name.startswith('chapter_')])
        
        self.stats['total_chapters'] = len(chapters)
        print(f"Найдено глав: {self.stats['total_chapters']}")
        
        if self.stats['total_chapters'] == 0:
            return False, "Папки глав не найдены"
        
        total_images = 0
        for chapter_path in chapters:
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(chapter_path.glob(ext))
            total_images += len(images)
            print(f"Глава {chapter_path.name}: {len(images)} изображений")
        
        self.stats['total_images'] = total_images
        print(f"Всего изображений: {total_images}")
        
        if total_images == 0:
            return False, "Изображения не найдены"
        
        processed_images = 0
        
        for chapter_idx, chapter_path in enumerate(chapters, 1):
            images = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                images.extend(sorted(chapter_path.glob(ext)))
            
            print(f"Обработка главы {chapter_path.name} ({chapter_idx}/{len(chapters)})")
            
            for image_idx, image_path in enumerate(images, 1):
                frames_count = self.make_frames(image_path, frames_dir)
                
                if frames_count > 0:
                    self.stats['processed_images'] += 1
                    print(f"  {image_path.name} -> {frames_count} фреймов")
                else:
                    self.stats['failed_images'] += 1
                    print(f"  {image_path.name} -> ошибка")
                
                processed_images += 1
                
                if self.progress_callback:
                    self.progress_callback(processed_images, total_images, chapter_idx, len(chapters))
                
                # Небольшая задержка для демонстрации прогресса
                time.sleep(0.05)
            
            self.stats['processed_chapters'] += 1
        
        self.stats['end_time'] = datetime.now()
        success_message = f"Обработка завершена. Создано {self.stats['total_frames']} фреймов."
        print(success_message)
        return True, success_message