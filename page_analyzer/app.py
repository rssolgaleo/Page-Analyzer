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
        flash('Invalid URL', 'danger')
        return render_template('index.html')

    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id FROM urls WHERE name=%s', (normalized_url, )
            )

            exiting_url = cursor.fetchone()
            if exiting_url:
                flash('URL already exists', 'error')
                return redirect(url_for('show_url', url_id=exiting_url[0]))

            cursor.execute(
                'INSERT INTO urls (name) VALUES (%s) RETURNING id',
                (normalized_url, )
            )
            new_url_id = cursor.fetchone()[0]
            flash('URL added successfully', 'success')
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

            cursor.execute(
                """
                SELECT id, status_code, created_at FROM url_checks
                WHERE url_id = %s ORDER BY created_at DESC
                """,
                (url_id, )
            )
            checks = cursor.fetchall()

    if not url:
        flash('URL not found', 'error')
        return redirect(url_for('list_urls'))
    return render_template('urls/show.html', url=url, checks=checks)


@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
                row = cur.fetchone()
                if not row:
                    flash('URL не найден', 'danger')
                    return redirect(url_for('list_urls'))
                url = row[0]

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        status_code = response.status_code

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO url_checks (url_id, status_code, created_at)
                    VALUES (%s, %s, %s)
                    ''',
                    (url_id, status_code, datetime.now())
                )
                conn.commit()

        flash('Проверка успешно выполнена', 'success')

    except RequestException:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', url_id=url_id))
