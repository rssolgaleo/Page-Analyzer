### Hexlet tests and linter status:
[![Actions Status](https://github.com/rssolgaleo/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/rssolgaleo/python-project-83/actions)


[![Демонстрация](https://img.shields.io/badge/Веб--приложение-🔗-blue)](https://page-analyzer-qc7t.onrender.com)


# Анализатор страниц

Это учебное веб-приложение, которое позволяет добавлять сайты и запускать их базовую SEO-проверку.  
После добавления сайт можно проверить: приложение выполнит HTTP-запрос, проанализирует HTML-контент и извлечёт мета-данные (title, h1, description).

---

## Возможности

- Добавление и хранение списка сайтов
- Проверка доступности сайта (HTTP status code)
- Извлечение мета-данных: `<title>`, `<h1>`, `<meta name="description">`
- История проверок для каждого сайта
- Валидация и нормализация URL
- Уведомления через flash-сообщения
- Обработка ошибок (404 и других)

---

## Стек технологий

| Категория             | Используемое решение             |
|-----------------------|----------------------------------|
| Язык программирования | Python 3                         |
| Веб-фреймворк         | Flask                            |
| HTTP-клиент           | requests                         |
| HTML-парсер           | BeautifulSoup4                   |
| База данных           | PostgreSQL                       |
| Работа с БД           | psycopg                          |
| Менеджер пакетов      | uv                               |
| Деплой                | Render.com (PaaS)                |
| UI и стили            | Bootstrap 5                      |

---

## Установка и запуск

```bash
uv sync           # Установка зависимостей
make dev          # Запуск локального сервера в режиме отладки
make start        # Запуск приложения в продакшене
make build        # Сборка проекта для деплоя