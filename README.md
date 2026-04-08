# Foodgram – сервис для публикации рецептов

Foodgram — это платформа, где пользователи могут делиться рецептами, подписываться на других авторов, добавлять рецепты в избранное и формировать список покупок. Проект включает фронтенд на React, бэкенд на Django Rest Framework и полностью контейнеризирован.

## Стек технологий

- **Backend:** Django 3.2, Django REST Framework (DRF), Djoser (аутентификация), PostgreSQL
- **Frontend:** React, Nginx
- **Инфраструктура:** Docker, Docker Compose, Gunicorn
- **Дополнительно:** Base64-кодирование изображений, пагинация, фильтрация, генерация коротких ссылок, скачивание списка покупок в TXT.

## Как развернуть проект в Docker

### Требования

- Установленные Docker и Docker Compose на сервере или локальной машине.
- Клонированный репозиторий проекта.

### Шаги по развертыванию

1. Перейдите в папку `infra` (в ней находится `docker-compose.yml`):
   ```bash
   cd infra
Создайте файл .env в папке infra со следующими переменными (пример):

env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=strong_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=секретный_ключ_джанго
DEBUG=False
DOMAIN=foodgramnight.viewdns.net
Запустите контейнеры:

bash
docker-compose up -d
При первом запуске контейнер frontend соберет статические файлы и завершится, а контейнеры db, backend, nginx продолжат работу.

Выполните миграции и создайте суперпользователя (один раз):

bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
Соберите статику бэкенда (если не автоматизировано):

bash
docker-compose exec backend python manage.py collectstatic --no-input
Проект будет доступен по адресу вашего сервера (например, https://foodgramnight.viewdns.net), а документация API — по адресу https://foodgramnight.viewdns.net/api/docs/ (или http://localhost/api/docs/ при локальном запуске).

Как наполнить базу данных начальными данными
Вы можете загрузить тестовые ингредиенты, теги и рецепты с помощью фикстур.

Фикстуры
Скопируйте файлы фикстур (например, ingredients.json, tags.json) в папку data/ на сервере или локально.

Загрузите их в контейнер backend и примените:

bash
docker cp data/ingredients.json <backend_container_id>:/app/ingredients.json
docker-compose exec backend python manage.py loaddata ingredients.json
Аналогично для тегов и других моделей.

Либо используйте административную панель Django (доступна по /admin/) для ручного ввода.

Как открыть документацию API
После запуска проекта документация в формате ReDoc (или Swagger UI) доступна по адресу:

https://foodgramnight.viewdns.net/api/docs/

при локальном запуске: http://localhost/api/docs/

Документация генерируется автоматически из кода и описывает все эндпоинты, методы, форматы запросов и ответов.

Примеры запросов и ответов
Регистрация пользователя
POST /api/users/

json
{
  "email": "user@example.com",
  "username": "cooker",
  "first_name": "Иван",
  "last_name": "Петров",
  "password": "securepass123"
}
Ответ (201 Created):

json
{
  "email": "user@example.com",
  "id": 42,
  "username": "cooker",
  "first_name": "Иван",
  "last_name": "Петров",
  "avatar": null,
  "is_subscribed": false
}
Получение короткой ссылки на рецепт
GET /api/recipes/1/get-link/ (требуется авторизация)
Ответ (200 OK):

json
{
  "short-link": "https://foodgramnight.viewdns.net/s/Ab3XyZ/"
}
Добавление рецепта в корзину покупок
POST /api/recipes/1/shopping_cart/ (авторизация)
Ответ (201 Created):

json
{
  "id": 1,
  "name": "Оливье",
  "image": "https://.../olivier.jpg",
  "cooking_time": 45
}
Скачивание списка покупок
GET /api/recipes/download_shopping_cart/ (авторизация)
Ответ (200 OK) – текстовый файл:

text
Огурцы - 3 (шт)
Картофель - 5 (шт)
Майонез - 200 (г)
Авторство
Проект выполнен в рамках учебного курса (Яндекс.Практикум) студентом Харо Александром.

GitHub: https://github.com/VioletNightt

Адрес развёрнутого проекта: https://foodgramnight.viewdns.net