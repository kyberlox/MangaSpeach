from modules import download_manga_chapter
from modules import FrameExtractor

# url = input("Введите URL первой главы: ")
# chapters = int(input("Введите количество глав: "))
# download_manga_chapter(url, chapters, "./static")

FrameExtractor().process_images()