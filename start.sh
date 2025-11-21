# Сборка образа
docker build -t manga-speach-app .

# Запуск контейнера
#docker run -it --rm manga-speach-app #--volume ${pwd}/:/app
docker run -it -v ./:/app --rm manga-speach-app