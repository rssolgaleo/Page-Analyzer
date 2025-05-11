from flask import (
  Flask, render_template, request, redirect, url_for, flash
)
from dotenv import load_dotenv
import os
import validators
from urllib.parse import urlparse
from .db import get_connection
from datetime import datetime
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form.get('url')

    if not url or not validators.url(url) or len(url) > 255:
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id FROM urls WHERE name=%s', (normalized_url, )
            )

            exiting_url = cursor.fetchone()
            if exiting_url:
                flash('Страница уже существует', 'info')
                return redirect(url_for('show_url', url_id=exiting_url[0]))

            cursor.execute(
                'INSERT INTO urls (name) VALUES (%s) RETURNING id',
                (normalized_url, )
            )
            new_url_id = cursor.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('show_url', url_id=new_url_id))


@app.route('/urls')
def list_urls():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT urls.id, urls.name,
                MAX(url_checks.created_at) AS last_check,
                MAX(url_checks.status_code) AS status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id
                ORDER BY urls.id DESC
                """
            )
            urls = cursor.fetchall()
    return render_template('urls/index.html', urls=urls)


@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id, name, created_at FROM urls WHERE id = %s',
                (url_id, )
            )
            url = cursor.fetchone()

            if not url:
                return render_template('urls/404.html'), 404

            cursor.execute(
                """
                SELECT id, status_code, title, h1, description, created_at
                FROM url_checks
                WHERE url_id = %s ORDER BY created_at DESC
                """,
                (url_id, )
            )
            checks = cursor.fetchall()
    return render_template('urls/show.html', url=url, checks=checks)


@app.route('/urls/<int:url_id>/checks', methods=['GET', 'POST'])
def check_url(url_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
                row = cur.fetchone()
                if not row:
                    return render_template('urls/404.html'), 404
                url = row[0]

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        status_code = response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')

        h1 = soup.find('h1')
        title = soup.find('title')
        description_tag = soup.find('meta', attrs={'name': 'description'})

        h1_text = h1.text.strip() if h1 else None
        title_text = title.text.strip() if title else None
        if description_tag and description_tag.has_attr('content'):
            description = description_tag['content'].strip()
        else:
            description = None

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO url_checks
                    (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        url_id,
                        status_code,
                        h1_text,
                        title_text,
                        description,
                        datetime.now()
                    )
                )
                conn.commit()

        flash('Страница успешно проверена', 'success')

    except RequestException:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', url_id=url_id))
