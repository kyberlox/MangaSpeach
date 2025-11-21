import requests
from bs4 import BeautifulSoup
import os
import sys
from urllib.parse import urljoin
import time


def download_image(session, url, filepath, referer=None):
    """Скачивает и сохраняет изображение с обработкой ошибок"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    if referer:
        headers['Referer'] = referer

    try:
        response = session.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Успешно скачано: {filepath}")
        return True
    except Exception as e:
        print(f"Ошибка при скачивании {url}: {e}")
        return False


def download_chapter(session, url="https://v2.mangahub.one/read/502268", chapter_num=40, download_path="./static"):
    """Скачивает все изображения одной главы"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при загрузке страницы главы {chapter_num}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'lxml')

    # Создаем папку для главы
    chapter_folder = os.path.join(download_path, f"chapter_{chapter_num:03d}")
    os.makedirs(chapter_folder, exist_ok=True)

    # Ищем все изображения в reader-scan
    images = soup.find_all('reader-scan', class_='reader-viewer-scan')

    print(f"Найдено {len(images)} изображений в главе {chapter_num}")

    for idx, scan in enumerate(images, 1):
        img_tag = scan.find('img', class_='reader-viewer-img')
        if img_tag:
            # Пробуем разные источники изображений
            img_sources = []

            # Добавляем src если есть
            if img_tag.get('src'):
                img_src = img_tag['src']
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                img_sources.append(img_src)

            # Добавляем data-src если есть
            if img_tag.get('data-src'):
                data_src = img_tag['data-src']
                if data_src.startswith('//'):
                    data_src = 'https:' + data_src
                # Добавляем только если это другой URL
                if data_src not in img_sources:
                    img_sources.append(data_src)

            filename = f"page_{idx:03d}.jpg"
            filepath = os.path.join(chapter_folder, filename)

            # Пробуем скачать из всех доступных источников
            downloaded = False
            for img_url in img_sources:
                print(f"Попытка скачать: {img_url}")
                if download_image(session, img_url, filepath, referer=url):
                    downloaded = True
                    break
                time.sleep(0.5)  # Небольшая задержка между попытками

            if not downloaded:
                print(f"Не удалось скачать изображение {idx} для главы {chapter_num}")

    # Ищем ссылку на следующую главу - исправленный поиск
    next_chapter_url = None

    # Способ 1: Ищем в блоке с классом reader-alert
    reader_alert = soup.find('div', class_='reader-alert')
    if reader_alert:
        next_link = reader_alert.find('a', class_='btn btn-secondary')
        if next_link and 'Следующая глава' in next_link.get_text():
            next_chapter_url = next_link.get('href')

    # Способ 2: Ищем любую ссылку с текстом "Следующая глава"
    if not next_chapter_url:
        all_links = soup.find_all('a')
        for link in all_links:
            if 'Следующая глава' in link.get_text():
                next_chapter_url = link.get('href')
                break

    if next_chapter_url:
        print(f"Найдена ссылка на следующую главу: {next_chapter_url}")
    else:
        print("Ссылка на следующую главу не найдена")

    return next_chapter_url


def download_manga_chapter(start_url, chapters, download_path):
    """Основная функция для скачивания глав манги"""
    # Создаем сессию
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    current_url = start_url
    base_url = '/'.join(start_url.split('/')[:3])  # Получаем базовый URL

    for chapter_num in range(1, chapters + 1):
        print(f"\n=== Скачивание главы {chapter_num} ===")
        print(f"URL: {current_url}")

        next_chapter = download_chapter(session, current_url, chapter_num, download_path)

        if next_chapter and chapter_num < chapters:
            # Преобразуем относительную ссылку в абсолютную
            if next_chapter.startswith('http'):
                current_url = next_chapter
            else:
                current_url = urljoin(base_url, next_chapter)
            print(f"Переход к следующей главе: {current_url}")
        else:
            if chapter_num < chapters:
                print(f"Не удалось найти следующую главу. Загрузка завершена.")
            break

        # Задержка между главами
        time.sleep(1)

    print("\nЗагрузка завершена!")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python3 get_images.py <start_url> <chapters> <download_path>")
        print("Пример: python3 get_images.py \"https://example.com/manga/123\" 3 \"./downloads\"")
        sys.exit(1)

    start_url = sys.argv[1]
    chapters = int(sys.argv[2])
    download_path = sys.argv[3]

    # Создаем основную папку для загрузки
    os.makedirs(download_path, exist_ok=True)

    download_manga_chapter(start_url, chapters, download_path)