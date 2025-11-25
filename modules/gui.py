import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from PIL import Image, ImageTk
import os
import shutil

from .download_manga_chapter import MangaDownloader
from .frame_extractor import FrameExtractor

class MainWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Manga Speech App - Главное меню")
        self.window.geometry("500x400")
        
        self.setup_ui()
        
    def setup_ui(self):
        tk.Label(self.window, text="Manga Speech App", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Разделительная линия
        ttk.Separator(self.window, orient='horizontal').pack(fill='x', padx=50, pady=10)
        
        # Вариант 1: Скачать новые главы
        tk.Label(self.window, text="Вариант 1: Скачать новые главы", font=("Arial", 12, "bold")).pack(pady=10)
        
        download_frame = tk.Frame(self.window)
        download_frame.pack(pady=10, padx=50, fill='x')
        
        tk.Button(download_frame, text="Скачать мангу", command=self.open_download_window, 
                 width=20, height=2, bg="#4CAF50", fg="white").pack(pady=5)
        
        # Разделительная линия
        ttk.Separator(self.window, orient='horizontal').pack(fill='x', padx=50, pady=10)
        
        # Вариант 2: Работа с готовыми главами
        tk.Label(self.window, text="Вариант 2: Работа с готовыми главами", font=("Arial", 12, "bold")).pack(pady=10)
        
        existing_frame = tk.Frame(self.window)
        existing_frame.pack(pady=10, padx=50, fill='x')
        
        tk.Button(existing_frame, text="Выбрать папку с главами", command=self.open_existing_chapters, 
                 width=20, height=2, bg="#2196F3", fg="white").pack(pady=5)
        
        # Разделительная линия
        ttk.Separator(self.window, orient='horizontal').pack(fill='x', padx=50, pady=10)
        
        # Прямой переход к фреймам (если они уже есть)
        tk.Label(self.window, text="Просмотр готовых фреймов", font=("Arial", 12, "bold")).pack(pady=10)
        
        frames_frame = tk.Frame(self.window)
        frames_frame.pack(pady=10, padx=50, fill='x')
        
        tk.Button(frames_frame, text="Просмотреть фреймы", command=self.open_view_frames, 
                 width=20, height=2, bg="#FF9800", fg="white").pack(pady=5)
    
    def open_download_window(self):
        self.window.destroy()
        DownloadWindow(self.parent)
    
    def open_existing_chapters(self):
        chapters_path = filedialog.askdirectory(title="Выберите папку с главами")
        if chapters_path:
            self.window.destroy()
            ExtractWindow(self.parent, chapters_path)
    
    def open_view_frames(self):
        frames_path = "./static/frames/"
        if Path(frames_path).exists() and any(Path(frames_path).glob("*.png")):
            self.window.destroy()
            ViewFramesWindow(self.parent, frames_path)
        else:
            messagebox.showwarning("Предупреждение", "Фреймы не найдены. Сначала создайте фреймы через обработку глав.")

class DownloadWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Скачивание манги")
        self.window.geometry("500x350")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.download_complete = False
        self.downloader = None
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        tk.Label(self.window, text="Скачивание манги", font=("Arial", 14, "bold")).pack(pady=10)
        
        # URL
        tk.Label(self.window, text="URL первой главы:").pack(pady=5)
        self.url_entry = tk.Entry(self.window, width=60)
        self.url_entry.pack(pady=5)
        
        # Количество глав
        tk.Label(self.window, text="Количество глав:").pack(pady=5)
        self.chapters_entry = tk.Entry(self.window, width=10)
        self.chapters_entry.insert(0, "1")
        self.chapters_entry.pack(pady=5)
        
        # Папка для сохранения
        tk.Label(self.window, text="Папка для сохранения глав:").pack(pady=5)
        self.folder_frame = tk.Frame(self.window)
        self.folder_frame.pack(pady=5)
        
        self.folder_var = tk.StringVar(value="./static/chapters/")
        self.folder_entry = tk.Entry(self.folder_frame, textvariable=self.folder_var, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        
        self.browse_btn = tk.Button(self.folder_frame, text="Обзор", command=self.browse_folder)
        self.browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Прогресс
        self.progress_frame = tk.Frame(self.window)
        self.progress_frame.pack(pady=20, fill='x', padx=50)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(fill='x')
        
        self.progress_label = tk.Label(self.progress_frame, text="Готов к скачиванию")
        self.progress_label.pack(pady=5)
        
        # Кнопки
        self.btn_frame = tk.Frame(self.window)
        self.btn_frame.pack(pady=20)
        
        self.download_btn = tk.Button(self.btn_frame, text="Начать скачивание", 
                                    command=self.start_download, width=15, height=1)
        self.download_btn.pack(side=tk.LEFT, padx=10)
        
        self.cancel_btn = tk.Button(self.btn_frame, text="Отмена", 
                                  command=self.cancel_download, width=10, height=1, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = tk.Button(self.btn_frame, text="Далее →", 
                                command=self.next_window, state=tk.DISABLED, width=10, height=1)
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        self.back_btn = tk.Button(self.btn_frame, text="← Назад", 
                                command=self.go_back, width=10, height=1)
        self.back_btn.pack(side=tk.LEFT, padx=10)
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
    
    def start_download(self):
        url = self.url_entry.get()
        chapters_text = self.chapters_entry.get()
        
        if not url or not chapters_text:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        try:
            num_chapters = int(chapters_text)
        except ValueError:
            messagebox.showerror("Ошибка", "Количество глав должно быть числом")
            return
        
        self.download_btn.config(state=tk.DISABLED)
        self.back_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.download_thread, args=(url, num_chapters))
        thread.daemon = True
        thread.start()
    
    def download_thread(self, url, num_chapters):  # Исправлено: используем num_chapters вместо chapters
        def update_progress(current_page, total_pages, current_chapter):
            # Вычисляем общий прогресс
            chapters_done = current_chapter - 1
            progress_from_previous = chapters_done / num_chapters * 100
            progress_current = (current_page / total_pages) * (1 / num_chapters) * 100
            total_progress = progress_from_previous + progress_current
            
            self.progress['value'] = total_progress
            self.progress_label.config(text=f"Глава {current_chapter}: {current_page}/{total_pages} страниц")
            self.window.update_idletasks()
        
        try:
            self.downloader = MangaDownloader(progress_callback=update_progress)
            success = self.downloader.download_multiple_chapters(url, num_chapters, self.folder_var.get())
            
            if success:
                self.download_complete = True
                self.progress['value'] = 100
                self.progress_label.config(text="Скачивание завершено!")
                self.next_btn.config(state=tk.NORMAL)
                messagebox.showinfo("Успех", f"Успешно скачано глав!")
            else:
                self.progress_label.config(text="Скачивание завершено с ошибками")
                messagebox.showwarning("Предупреждение", "Некоторые главы не были скачаны")
            
            # Всегда разблокируем кнопки после завершения
            self.download_btn.config(state=tk.NORMAL)
            self.back_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Ошибка в потоке скачивания: {e}")
            import traceback
            traceback.print_exc()
            self.progress_label.config(text="Ошибка при скачивании")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
            self.download_btn.config(state=tk.NORMAL)
            self.back_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            
    def cancel_download(self):
        if self.downloader:
            self.downloader.cancel_download()
        self.progress_label.config(text="Скачивание отменено")
        self.download_btn.config(state=tk.NORMAL)
        self.back_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def next_window(self):
        if self.download_complete:
            self.window.destroy()
            ExtractWindow(self.parent, self.folder_var.get())
    
    def go_back(self):
        self.window.destroy()
        MainWindow(self.parent)
    
    def on_close(self):
        self.window.destroy()
        MainWindow(self.parent)

class ExtractWindow:
    def __init__(self, parent, chapters_path):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Генерация фреймов")
        self.window.geometry("500x350")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.chapters_path = chapters_path
        self.extraction_complete = False
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        tk.Label(self.window, text="Генерация фреймов", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Информация о папке с главами
        tk.Label(self.window, text="Папка с главами:").pack(pady=5)
        tk.Label(self.window, text=self.chapters_path, wraplength=400, justify="left").pack(pady=5)
        
        # Папка для фреймов
        tk.Label(self.window, text="Папка для сохранения фреймов:").pack(pady=5)
        self.frames_frame = tk.Frame(self.window)
        self.frames_frame.pack(pady=5)
        
        self.frames_var = tk.StringVar(value="./static/frames/")
        self.frames_entry = tk.Entry(self.frames_frame, textvariable=self.frames_var, width=50)
        self.frames_entry.pack(side=tk.LEFT, padx=5)
        
        self.browse_frames_btn = tk.Button(self.frames_frame, text="Обзор", command=self.browse_frames)
        self.browse_frames_btn.pack(side=tk.LEFT, padx=5)
        
        # Прогресс
        self.progress_frame = tk.Frame(self.window)
        self.progress_frame.pack(pady=20, fill='x', padx=50)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(fill='x')
        
        self.progress_label = tk.Label(self.progress_frame, text="Готов к обработке")
        self.progress_label.pack(pady=5)
        
        # Кнопки
        self.btn_frame = tk.Frame(self.window)
        self.btn_frame.pack(pady=20)
        
        self.extract_btn = tk.Button(self.btn_frame, text="Начать генерацию", 
                                   command=self.start_extraction, width=15, height=1)
        self.extract_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = tk.Button(self.btn_frame, text="Далее →", 
                                command=self.next_window, state=tk.DISABLED, width=10, height=1)
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        self.back_btn = tk.Button(self.btn_frame, text="← Назад", 
                                command=self.go_back, width=10, height=1)
        self.back_btn.pack(side=tk.LEFT, padx=10)
    
    def browse_frames(self):
        folder = filedialog.askdirectory()
        if folder:
            self.frames_var.set(folder)
    
    def start_extraction(self):
        frames_path = self.frames_var.get()
        
        if not frames_path:
            messagebox.showerror("Ошибка", "Выберите папку для фреймов")
            return
        
        self.extract_btn.config(state=tk.DISABLED)
        self.back_btn.config(state=tk.DISABLED)
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.extract_thread, args=(frames_path,))
        thread.daemon = True
        thread.start()
    
    def extract_thread(self, frames_path):
        def update_progress(current, total, chapter, total_chapters):
            self.progress['value'] = (current / total) * 100
            self.progress_label.config(text=f"Глава {chapter}/{total_chapters}: {current}/{total} изображений")
            self.window.update_idletasks()
        
        try:
            extractor = FrameExtractor(progress_callback=update_progress)
            success, message = extractor.process_images(self.chapters_path, frames_path)
            
            if success:
                self.extraction_complete = True
                self.progress_label.config(text="Обработка завершена!")
                self.next_btn.config(state=tk.NORMAL)
                self.back_btn.config(state=tk.NORMAL)
            else:
                messagebox.showerror("Ошибка", message)
                self.extract_btn.config(state=tk.NORMAL)
                self.back_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
            self.extract_btn.config(state=tk.NORMAL)
            self.back_btn.config(state=tk.NORMAL)

    def next_window(self):
        if self.extraction_complete:
            self.window.destroy()
            ViewFramesWindow(self.parent, self.frames_var.get())
    
    def go_back(self):
        self.window.destroy()
        MainWindow(self.parent)
    
    def on_close(self):
        self.window.destroy()
        MainWindow(self.parent)

class ViewFramesWindow:
    def __init__(self, parent, frames_path):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Просмотр фреймов")
        self.window.geometry("1000x800")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.frames_path = Path(frames_path)
        self.frames = sorted(self.frames_path.glob("*.png"))
        self.current_frame_index = 0
        self.current_photo = None
        self.drag_start_index = None
        
        # Оптимизация: отложенное переименование
        self.pending_renames = []
        self.rename_timer = None
        
        self.setup_ui()
        if self.frames:
            self.load_current_frame()
        else:
            messagebox.showwarning("Предупреждение", "Фреймы не найдены")
        
    def setup_ui(self):
        # Основной контейнер с фиксированной структурой
        main_container = tk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель управления
        control_frame = tk.Frame(main_container)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Панель навигации
        nav_frame = tk.Frame(control_frame)
        nav_frame.pack(pady=5)
        
        self.prev_btn = tk.Button(nav_frame, text="← Назад", command=self.prev_frame, width=10)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.frame_info = tk.Label(nav_frame, text="Фрейм 0/0", font=("Arial", 12, "bold"))
        self.frame_info.pack(side=tk.LEFT, padx=20)
        
        self.next_btn = tk.Button(nav_frame, text="Вперед →", command=self.next_frame, width=10)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Панель действий
        action_frame1 = tk.Frame(control_frame)
        action_frame1.pack(pady=5)
        
        self.edit_btn = tk.Button(action_frame1, text="Редактировать", command=self.edit_frame, width=14)
        self.edit_btn.pack(side=tk.LEFT, padx=3)
        
        self.ocr_btn = tk.Button(action_frame1, text="Распознать текст", command=self.ocr_frame, width=16)
        self.ocr_btn.pack(side=tk.LEFT, padx=3)
        
        self.add_btn = tk.Button(action_frame1, text="Добавить фрейм", command=self.add_frame, width=14)
        self.add_btn.pack(side=tk.LEFT, padx=3)
        
        # Вторая строка действий
        action_frame2 = tk.Frame(control_frame)
        action_frame2.pack(pady=5)
        
        # КНОПКА УДАЛЕНИЯ
        self.delete_btn = tk.Button(action_frame2, text="🗑️ Удалить фрейм", command=self.delete_frame, 
                                   width=14, bg="#ff4444", fg="white", font=("Arial", 9, "bold"))
        self.delete_btn.pack(side=tk.LEFT, padx=3)
        
        self.voice_btn = tk.Button(action_frame2, text="Озвучить", command=self.voice_frame, width=12)
        self.voice_btn.pack(side=tk.LEFT, padx=3)
        
        self.back_btn = tk.Button(action_frame2, text="← Главное меню", command=self.go_back, width=14)
        self.back_btn.pack(side=tk.LEFT, padx=3)
        
        # Кнопки для перемещения вверх/вниз
        self.move_up_btn = tk.Button(action_frame2, text="↑ Вверх", command=self.move_frame_up, width=8)
        self.move_up_btn.pack(side=tk.LEFT, padx=3)
        
        self.move_down_btn = tk.Button(action_frame2, text="↓ Вниз", command=self.move_frame_down, width=8)
        self.move_down_btn.pack(side=tk.LEFT, padx=3)
        
        # Кнопка для принудительного сохранения порядка
        self.save_order_btn = tk.Button(action_frame2, text="💾 Сохранить порядок", 
                                       command=self.save_order, width=16, bg="#4CAF50", fg="white")
        self.save_order_btn.pack(side=tk.LEFT, padx=3)
        
        # Область изображения
        image_container = tk.Frame(main_container, bg="white", relief=tk.SUNKEN, bd=2)
        image_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Создаем Canvas для отображения изображения с прокруткой
        self.canvas = tk.Canvas(image_container, bg="white", highlightthickness=0)
        
        # Добавляем прокрутку
        v_scrollbar = tk.Scrollbar(image_container, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = tk.Scrollbar(image_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Упаковываем элементы прокрутки
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Создаем фрейм внутри Canvas для изображения
        self.image_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.image_frame, anchor="nw")
        
        # Метка для изображения внутри image_frame
        self.image_label = tk.Label(self.image_frame, bg="white")
        self.image_label.pack(padx=10, pady=10)
        
        # Привязываем события для обновления прокрутки
        self.image_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Нижняя панель со списком фреймов
        list_frame = tk.Frame(main_container)
        list_frame.pack(fill=tk.X)
        
        list_header = tk.Frame(list_frame)
        list_header.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(list_header, text="Список фреймов (перетащите для изменения порядка):", 
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, anchor=tk.W)
        
        # Индикатор изменений
        self.unsaved_changes_label = tk.Label(list_header, text="", fg="red", font=("Arial", 9))
        self.unsaved_changes_label.pack(side=tk.RIGHT)
        
        # Создаем Listbox с возможностью перетаскивания
        listbox_container = tk.Frame(list_frame)
        listbox_container.pack(fill=tk.X)
        
        self.frames_listbox = tk.Listbox(listbox_container, height=8, font=("Arial", 9),
                                        selectbackground="#4CAF50", selectmode=tk.SINGLE)
        
        # Добавляем скроллбар для списка
        list_scrollbar = tk.Scrollbar(listbox_container, orient=tk.VERTICAL, command=self.frames_listbox.yview)
        self.frames_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        self.frames_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязываем события для перетаскивания
        self.frames_listbox.bind('<Button-1>', self.on_listbox_click)
        self.frames_listbox.bind('<B1-Motion>', self.on_listbox_drag)
        self.frames_listbox.bind('<ButtonRelease-1>', self.on_listbox_release)
        self.frames_listbox.bind('<<ListboxSelect>>', self.on_frame_select)
        
        self.update_frames_list()
    
    def _on_frame_configure(self, event):
        """Обновляем область прокрутки когда меняется размер фрейма"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Обновляем размер окна внутри Canvas при изменении размера Canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def update_frames_list(self):
        """Обновляет список фреймов в Listbox"""
        self.frames_listbox.delete(0, tk.END)
        for i, frame_path in enumerate(self.frames):
            display_name = f"{i+1:03d}. {frame_path.name}"
            self.frames_listbox.insert(tk.END, display_name)
        
        # Обновляем состояние кнопок перемещения
        self.update_move_buttons_state()
    
    def update_move_buttons_state(self):
        """Обновляет состояние кнопок перемещения вверх/вниз"""
        if not self.frames:
            self.move_up_btn.config(state=tk.DISABLED)
            self.move_down_btn.config(state=tk.DISABLED)
            return
            
        self.move_up_btn.config(state=tk.NORMAL if self.current_frame_index > 0 else tk.DISABLED)
        self.move_down_btn.config(state=tk.NORMAL if self.current_frame_index < len(self.frames) - 1 else tk.DISABLED)
    
    def on_listbox_click(self, event):
        """Обработчик клика по Listbox для начала перетаскивания"""
        if self.frames_listbox.size() == 0:
            return
            
        # Определяем индекс элемента под курсором
        index = self.frames_listbox.nearest(event.y)
        if index >= 0:
            self.drag_start_index = index
            # Выделяем элемент сразу при клике
            self.frames_listbox.selection_clear(0, tk.END)
            self.frames_listbox.selection_set(index)
            self.current_frame_index = index
            self.load_current_frame()
    
    def on_listbox_drag(self, event):
        """Обработчик перетаскивания в Listbox"""
        if self.drag_start_index is None:
            return
            
        # Определяем индекс элемента под курсором
        current_index = self.frames_listbox.nearest(event.y)
        if current_index >= 0 and current_index != self.drag_start_index:
            # Визуально показываем перемещение
            self.frames_listbox.selection_clear(0, tk.END)
            self.frames_listbox.selection_set(current_index)
    
    def on_listbox_release(self, event):
        """Обработчик отпускания кнопки мыши после перетаскивания"""
        if self.drag_start_index is None:
            return
            
        # Определяем конечный индекс
        end_index = self.frames_listbox.nearest(event.y)
        
        if end_index >= 0 and end_index != self.drag_start_index:
            self.move_frame(self.drag_start_index, end_index)
        
        self.drag_start_index = None
    
    def move_frame(self, from_index, to_index):
        """Перемещает фрейм с одного места на другое"""
        if from_index == to_index:
            return
            
        # Перемещаем элемент в списке
        item = self.frames.pop(from_index)
        self.frames.insert(to_index, item)
        
        # Обновляем отображение
        self.update_frames_list()
        
        # Обновляем текущий индекс
        self.current_frame_index = to_index
        self.frames_listbox.selection_set(to_index)
        self.load_current_frame()
        
        # Отмечаем необходимость переименования (но не выполняем сразу)
        self.schedule_renumbering()
    
    def move_frame_up(self):
        """Перемещает текущий фрейм вверх"""
        if self.current_frame_index > 0:
            self.move_frame(self.current_frame_index, self.current_frame_index - 1)
    
    def move_frame_down(self):
        """Перемещает текущий фрейм вниз"""
        if self.current_frame_index < len(self.frames) - 1:
            self.move_frame(self.current_frame_index, self.current_frame_index + 1)
    
    def schedule_renumbering(self):
        """Планирует отложенное переименование файлов"""
        # Отменяем предыдущий таймер, если он есть
        if self.rename_timer:
            self.window.after_cancel(self.rename_timer)
        
        # Показываем индикатор несохраненных изменений
        self.unsaved_changes_label.config(text="⚠ Изменения не сохранены")
        
        # Запускаем новый таймер (переименование через 2 секунды бездействия)
        self.rename_timer = self.window.after(2000, self.execute_pending_renames)
    
    def execute_pending_renames(self):
        """Выполняет отложенное переименование файлов"""
        if not self.frames:
            return
            
        try:
            # Показываем прогресс
            self.unsaved_changes_label.config(text="💾 Сохранение...")
            self.window.update_idletasks()
            
            # Оптимизированное переименование: только необходимые файлы
            renamed_count = 0
            
            for i, frame_path in enumerate(self.frames):
                expected_name = f"frame_{i:06d}.png"
                if frame_path.name != expected_name:
                    # Создаем временное имя для избежания конфликтов
                    temp_name = f"temp_{i:06d}.png"
                    temp_path = self.frames_path / temp_name
                    
                    # Переименовываем файл
                    frame_path.rename(temp_path)
                    
                    # Обновляем путь в списке
                    self.frames[i] = temp_path
                    renamed_count += 1
            
            # Теперь переименовываем временные файлы в окончательные имена
            for i, temp_path in enumerate(self.frames):
                if temp_path.name.startswith("temp_"):
                    final_name = f"frame_{i:06d}.png"
                    final_path = self.frames_path / final_name
                    temp_path.rename(final_path)
                    self.frames[i] = final_path
            
            # Обновляем список фреймов
            self.frames = sorted(self.frames_path.glob("*.png"))
            
            # Сбрасываем индикатор
            self.unsaved_changes_label.config(text="✓ Сохранено")
            
            # Через 1.5 секунды убираем сообщение
            self.window.after(1500, lambda: self.unsaved_changes_label.config(text=""))
            
            print(f"Оптимизированное переименование: обработано {renamed_count} файлов")
            
        except Exception as e:
            print(f"Ошибка при переименовании фреймов: {e}")
            self.unsaved_changes_label.config(text="❌ Ошибка сохранения")
    
    def save_order(self):
        """Принудительное сохранение порядка"""
        self.execute_pending_renames()
    
    def delete_frame(self):
        """Удаляет текущий фрейм - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ"""
        if not self.frames:
            return
            
        frame_to_delete = self.frames[self.current_frame_index]
        
        # Подтверждение удаления
        result = messagebox.askyesno(
            "Удаление фрейма", 
            f"Вы уверены, что хотите удалить фрейм?\n{frame_to_delete.name}",
            icon='warning'
        )
        
        if not result:
            return
        
        try:
            # Удаляем файл
            frame_to_delete.unlink()
            
            # Удаляем из списка
            self.frames.pop(self.current_frame_index)
            
            # Обновляем текущий индекс
            if not self.frames:
                # Если удалили последний фрейм
                self.current_frame_index = 0
                self.image_label.config(image='', text="Фреймы не найдены")
                self.frame_info.config(text="Фрейм 0/0")
                self.unsaved_changes_label.config(text="")
            else:
                if self.current_frame_index >= len(self.frames):
                    self.current_frame_index = len(self.frames) - 1
                
                # Немедленно переименовываем только при удалении (это быстро)
                self.fast_renumber_after_delete()
                self.load_current_frame()
            
            self.update_frames_list()
            
        except Exception as e:
            print(f"Ошибка при удалении фрейма: {e}")
            messagebox.showerror("Ошибка", f"Не удалось удалить фрейм: {e}")
    
    def fast_renumber_after_delete(self):
        """Быстрое переименование после удаления - только необходимые файлы"""
        try:
            # Находим индекс, с которого нужно начать переименование
            start_index = self.current_frame_index
            
            for i in range(start_index, len(self.frames)):
                expected_name = f"frame_{i:06d}.png"
                current_path = self.frames[i]
                
                if current_path.name != expected_name:
                    new_path = self.frames_path / expected_name
                    current_path.rename(new_path)
                    self.frames[i] = new_path
            
            # Обновляем список
            self.frames = sorted(self.frames_path.glob("*.png"))
            
        except Exception as e:
            print(f"Ошибка при быстром переименовании: {e}")
    
    def load_current_frame(self):
        if not self.frames:
            self.image_label.config(text="Фреймы не найдены", font=("Arial", 14))
            return
            
        frame_path = self.frames[self.current_frame_index]
        
        try:
            # Загружаем изображение
            image = Image.open(frame_path)
            
            # Получаем размеры Canvas для масштабирования
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Если Canvas еще не отрисован, используем разумные размеры по умолчанию
            if canvas_width <= 1:
                canvas_width = 800
            if canvas_height <= 1:
                canvas_height = 500
            
            # Вычитаем отступы для области просмотра
            viewport_width = max(canvas_width - 40, 100)
            viewport_height = max(canvas_height - 40, 100)
            
            # Масштабируем изображение чтобы оно вписывалось в область просмотра
            img_width, img_height = image.size
            scale = min(viewport_width / img_width, viewport_height / img_height, 1.0)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            if scale < 1.0:
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Конвертируем в PhotoImage и сохраняем ссылку
            self.current_photo = ImageTk.PhotoImage(image)
            
            # Обновляем метку
            self.image_label.config(image=self.current_photo, text="")
            
            # Обновляем информацию
            self.frame_info.config(text=f"Фрейм {self.current_frame_index + 1}/{len(self.frames)}")
            
            # Выделяем в списке
            self.frames_listbox.selection_clear(0, tk.END)
            self.frames_listbox.selection_set(self.current_frame_index)
            self.frames_listbox.see(self.current_frame_index)
            
            # Обновляем область прокрутки
            self.image_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Обновляем состояние кнопок перемещения
            self.update_move_buttons_state()
            
        except Exception as e:
            print(f"Ошибка загрузки изображения {frame_path}: {e}")
            self.image_label.config(image="", text=f"Ошибка загрузки: {frame_path.name}")
    
    def next_frame(self):
        if self.current_frame_index < len(self.frames) - 1:
            self.current_frame_index += 1
            self.load_current_frame()
    
    def prev_frame(self):
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.load_current_frame()
    
    def on_frame_select(self, event):
        selection = self.frames_listbox.curselection()
        if selection:
            self.current_frame_index = selection[0]
            self.load_current_frame()
    
    def edit_frame(self):
        if self.frames:
            frame_path = self.frames[self.current_frame_index]
            try:
                os.startfile(frame_path)
            except:
                messagebox.showinfo("Инфо", f"Файл: {frame_path}")
    
    def ocr_frame(self):
        messagebox.showinfo("Инфо", "Функция распознавания текста будет реализована позже")
    
    def add_frame(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            # Копируем файл в папку фреймов
            import shutil
            new_frame_path = self.frames_path / f"frame_{len(self.frames):06d}.png"
            shutil.copy(file_path, new_frame_path)
            
            # Обновляем список
            self.frames = sorted(self.frames_path.glob("*.png"))
            self.update_frames_list()
            self.current_frame_index = len(self.frames) - 1
            self.load_current_frame()
    
    def voice_frame(self):
        messagebox.showinfo("Инфо", "Функция озвучки будет реализована позже")
    
    def go_back(self):
        # Сохраняем изменения перед выходом
        if self.unsaved_changes_label.cget("text") == "⚠ Изменения не сохранены":
            self.execute_pending_renames()
        self.window.destroy()
        MainWindow(self.parent)
    
    def on_close(self):
        # Сохраняем изменения перед выходом
        if self.unsaved_changes_label.cget("text") == "⚠ Изменения не сохранены":
            self.execute_pending_renames()
        self.window.destroy()
        MainWindow(self.parent)

class MangaSpeechApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Manga Speech App")
        self.root.geometry("400x300")
        
    def setup_ui(self):
        # Скрываем главное окно, показываем MainWindow
        self.root.withdraw()
        MainWindow(self.root)
    
    def run(self):
        self.setup_ui()
        self.root.mainloop()