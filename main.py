from flask import Flask, render_template, request, session, redirect
import sqlite3 as sql
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.secret_key = 'x]0nzPop[XP~8)42r?#%'


def init_db():
    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT,
                full_name TEXT,
                allergies TEXT,
                preferences TEXT,
                class TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance (
                user_id INTEGER PRIMARY KEY,
                amount REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subscription_type TEXT,
                start_date DATE,
                end_date DATE,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                purchase_type TEXT,
                amount REAL,
                description TEXT,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week INTEGER,
                meal_type TEXT,
                dish_name TEXT,
                description TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_of_week INTEGER,
                meal_type TEXT,
                date DATE,
                status TEXT,
                week_offset INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dish_name TEXT,
                rating INTEGER,
                comment TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                quantity REAL,
                unit TEXT,
                min_quantity REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dish_name TEXT,
                quantity_available INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                quantity REAL,
                unit TEXT,
                price REAL,
                reason TEXT,
                priority TEXT DEFAULT 'normal',
                status TEXT DEFAULT 'pending',
                created_by INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')

        cursor.execute("SELECT id FROM users WHERE username = 'student'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, class, allergies, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('student', 'student', 'student', 'Тестовый Студент', '10А', 'Нет', 'Нет'))

        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, class, allergies, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin', 'admin', 'Администратор', '', '', ''))

        cursor.execute("SELECT id FROM users WHERE username = 'cook'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, class, allergies, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('cook', 'cook', 'cook', 'Повар', '', '', ''))

        cursor.execute('''
            INSERT OR IGNORE INTO balance (user_id, amount)
            SELECT id, 500 FROM users WHERE role = 'student'
        ''')

        cursor.execute('''
            INSERT OR IGNORE INTO balance (user_id, amount)
            SELECT id, 1000 FROM users WHERE role IN ('admin', 'cook')
        ''')

        cursor.execute("SELECT COUNT(*) FROM menu_dishes")
        if cursor.fetchone()[0] == 0:
            days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
            breakfasts = [
                'Омлет с сыром', 'Овсяная каша', 'Гречневая каша',
                'Рисовая каша', 'Блины со сметаной'
            ]
            lunches = [
                'Суп куриный', 'Борщ', 'Солянка',
                'Щи', 'Гороховый суп'
            ]

            for i in range(5):
                cursor.execute('''
                    INSERT INTO menu_dishes (day_of_week, meal_type, dish_name, description)
                    VALUES (?, 'breakfast', ?, 'Вкусный завтрак')
                ''', (i, breakfasts[i]))

                cursor.execute('''
                    INSERT INTO menu_dishes (day_of_week, meal_type, dish_name, description)
                    VALUES (?, 'lunch', ?, 'Горячий обед')
                ''', (i, lunches[i]))

        cursor.execute("SELECT COUNT(*) FROM inventory")
        if cursor.fetchone()[0] == 0:
            test_inventory = [
                ('Мука', 10.5, 'кг', 2.0),
                ('Сахар', 5.0, 'кг', 1.0),
                ('Молоко', 20.0, 'л', 5.0),
                ('Яйца', 100, 'шт', 30),
                ('Картофель', 50.0, 'кг', 10.0),
                ('Курица', 15.0, 'кг', 3.0),
                ('Морковь', 8.0, 'кг', 2.0),
                ('Лук', 6.0, 'кг', 1.5),
            ]

            for item in test_inventory:
                cursor.execute('''
                    INSERT INTO inventory (item_name, quantity, unit, min_quantity)
                    VALUES (?, ?, ?, ?)
                ''', item)

        cursor.execute("SELECT COUNT(*) FROM dishes")
        if cursor.fetchone()[0] == 0:
            test_dishes = [
                ('Омлет с сыром', 25),
                ('Овсяная каша', 30),
                ('Суп куриный', 40),
                ('Борщ', 35),
            ]

            for dish in test_dishes:
                cursor.execute('''
                    INSERT INTO dishes (dish_name, quantity_available)
                    VALUES (?, ?)
                ''', dish)

        db.commit()
        print("База данных успешно инициализирована!")

    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        db.rollback()

    finally:
        db.close()


@app.route('/')
def index():
    user = session.get('user')
    if not user:
        return redirect('/login_user_help/')

    if user['role'] == 'student':
        return redirect('/menu/')
    elif user['role'] == 'cook':
        return redirect('/cook_menu/')
    elif user['role'] == 'admin':
        return redirect('/admin_stats/')
    elif user['role'] == 'manager':
        return redirect('/menu/')

    return redirect('/menu/')



@app.route('/menu/', methods=['GET', 'POST'])
def menu():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')

    if request.method == 'POST':
        action = request.form.get('action')
        day = request.form.get('day')
        meal_type = request.form.get('meal_type')
        week_offset = int(request.form.get('week_offset', 0))

        db = sql.connect('db_for_project.db')
        cursor = db.cursor()

        if action == 'pay':
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
            selected_date = start_of_week + timedelta(days=int(day))

            cursor.execute('''SELECT amount FROM balance WHERE user_id = ?''', (user['id'],))
            balance_row = cursor.fetchone()
            balance = balance_row[0] if balance_row else 0

            price = 50

            if balance >= price:
                cursor.execute('''UPDATE balance SET amount = amount - ? WHERE user_id = ?''',
                               (price, user['id']))

                cursor.execute('''
                    INSERT INTO meal_payments (user_id, day_of_week, meal_type, date, status, week_offset)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user['id'], day, meal_type, selected_date.strftime('%Y-%m-%d'), 'paid', week_offset))

                db.commit()

        elif action == 'attend':
            today = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT id FROM meal_payments 
                WHERE user_id = ? AND date = ? AND meal_type = ? 
                AND status = 'paid'
                ORDER BY id DESC LIMIT 1
            ''', (user['id'], today, meal_type))

            payment_id = cursor.fetchone()

            if payment_id:
                cursor.execute('''
                    UPDATE meal_payments 
                    SET status = 'attended' 
                    WHERE id = ?
                ''', (payment_id[0],))
                db.commit()

        db.close()
        week_offset_param = f"?week_offset={week_offset}" if week_offset != 0 else ""
        return redirect(f'/menu/{week_offset_param}')

    week_offset = request.args.get('week_offset', default=0, type=int)

    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_dates = [(start_of_week + timedelta(days=i)).strftime('%d.%m') for i in range(5)]
    week_dates_full = [(start_of_week + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]
    week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']

    week_start_str = start_of_week.strftime('%d.%m')
    week_end_str = (start_of_week + timedelta(days=4)).strftime('%d.%m.%Y')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()
    cursor.execute('''
        SELECT day_of_week, meal_type, dish_name, description 
        FROM menu_dishes 
        ORDER BY day_of_week, meal_type
    ''')

    menu_dishes = {}
    for row in cursor.fetchall():
        day, meal_type, dish_name, description = row
        if day not in menu_dishes:
            menu_dishes[day] = {}
        menu_dishes[day][meal_type] = {'name': dish_name, 'description': description}

    cursor.execute('''
        SELECT day_of_week, meal_type, status 
        FROM meal_payments 
        WHERE user_id = ? AND week_offset = ?
    ''', (user['id'], week_offset))

    meal_statuses = {}
    for row in cursor.fetchall():
        day, meal_type, status = row
        if day not in meal_statuses:
            meal_statuses[day] = {}
        meal_statuses[day][meal_type] = status

    cursor.execute('''SELECT amount FROM balance WHERE user_id = ?''', (user['id'],))
    balance_row = cursor.fetchone()
    balance = balance_row[0] if balance_row else 0

    db.close()

    table_data = []
    for day_idx in range(5):
        is_today = (week_dates_full[day_idx] == today_str)

        day_data = {
            'date': week_dates[day_idx],
            'date_full': week_dates_full[day_idx],
            'day_name': week_days[day_idx],
            'breakfast_status': meal_statuses.get(day_idx, {}).get('breakfast', 'unpaid'),
            'lunch_status': meal_statuses.get(day_idx, {}).get('lunch', 'unpaid'),
            'breakfast_dish': menu_dishes.get(day_idx, {}).get('breakfast',
                                                               {'name': 'Не указано', 'description': ''}),
            'lunch_dish': menu_dishes.get(day_idx, {}).get('lunch', {'name': 'Не указано', 'description': ''}),
            'is_today': is_today,
            'day_index': day_idx
        }
        table_data.append(day_data)

    return render_template('menu.html', user=user, table_data=table_data,
                           balance=balance, today=today, week_offset=week_offset,
                           week_start_str=week_start_str, week_end_str=week_end_str,
                           today_str=today_str)


@app.route('/cook_menu/')
def cook_menu():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    tomorrow_weekday = tomorrow.weekday()

    if tomorrow_weekday >= 5:
        days_until_monday = (7 - today.weekday()) % 7
        next_monday = today + timedelta(days=days_until_monday)
        tomorrow = next_monday
        tomorrow_weekday = 0

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    cursor.execute('''
        SELECT day_of_week, meal_type, dish_name, description 
        FROM menu_dishes 
        ORDER BY day_of_week, meal_type
    ''')

    menu_dishes = {}
    for row in cursor.fetchall():
        day, meal_type, dish_name, description = row
        if day not in menu_dishes:
            menu_dishes[day] = {}
        menu_dishes[day][meal_type] = {'name': dish_name, 'description': description}

    cursor.execute('''
        SELECT meal_type, COUNT(*) as count
        FROM meal_payments
        WHERE day_of_week = ? AND date = ? AND status IN ('paid', 'attended')
        GROUP BY meal_type
    ''', (tomorrow_weekday, tomorrow.strftime('%Y-%m-%d')))

    tomorrow_orders = {}
    for row in cursor.fetchall():
        meal_type, count = row
        tomorrow_orders[meal_type] = count

    cursor.execute('''
        SELECT meal_type, COUNT(*) as count
        FROM meal_payments
        WHERE date = ? AND status = 'attended'
        GROUP BY meal_type
    ''', (today.strftime('%Y-%m-%d'),))

    today_stats = {}
    for row in cursor.fetchall():
        meal_type, count = row
        today_stats[meal_type] = count

    db.close()

    week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
    table_data = []

    start_of_week = today - timedelta(days=today.weekday())

    for day_idx in range(5):
        current_date = start_of_week + timedelta(days=day_idx)
        is_today = (current_date.date() == today.date())
        is_tomorrow = (current_date.date() == tomorrow.date())

        day_data = {
            'day_name': week_days[day_idx],
            'date': current_date.strftime('%d.%m'),
            'date_full': current_date.strftime('%Y-%m-%d'),
            'breakfast_dish': menu_dishes.get(day_idx, {}).get('breakfast',
                                                               {'name': 'Завтрак', 'description': 'Не указано'}),
            'lunch_dish': menu_dishes.get(day_idx, {}).get('lunch', {'name': 'Обед', 'description': 'Не указано'}),
            'is_today': is_today,
            'is_tomorrow': is_tomorrow
        }
        table_data.append(day_data)

    return render_template('cook_menu.html',
                           user=user,
                           table_data=table_data,
                           tomorrow_orders=tomorrow_orders,
                           today_stats=today_stats,
                           tomorrow_date=tomorrow.strftime('%d.%m.%Y'),
                           today_date=today.strftime('%d.%m.%Y'))


@app.route('/edit_menu/', methods=['GET', 'POST'])
def edit_menu():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] not in ['manager', 'cook']:
        return redirect('/menu/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            day = request.form.get('day')
            meal_type = request.form.get('meal_type')
            dish_name = request.form.get('dish_name')
            description = request.form.get('description')

            cursor.execute('''
                SELECT id FROM menu_dishes WHERE day_of_week = ? AND meal_type = ?
            ''', (day, meal_type))

            existing = cursor.fetchone()

            if existing:
                cursor.execute('''
                    UPDATE menu_dishes SET dish_name = ?, description = ?
                    WHERE day_of_week = ? AND meal_type = ?
                ''', (dish_name, description, day, meal_type))
            else:
                cursor.execute('''
                    INSERT INTO menu_dishes (day_of_week, meal_type, dish_name, description)
                    VALUES (?, ?, ?, ?)
                ''', (day, meal_type, dish_name, description))

            db.commit()

    cursor.execute('''
        SELECT day_of_week, meal_type, dish_name, description 
        FROM menu_dishes 
        ORDER BY day_of_week, meal_type
    ''')

    menu_dishes = {}
    for row in cursor.fetchall():
        day, meal_type, dish_name, description = row
        if day not in menu_dishes:
            menu_dishes[day] = {}
        menu_dishes[day][meal_type] = {'name': dish_name, 'description': description}

    db.close()

    week_days = [
        {'id': 0, 'name': 'Понедельник'},
        {'id': 1, 'name': 'Вторник'},
        {'id': 2, 'name': 'Среда'},
        {'id': 3, 'name': 'Четверг'},
        {'id': 4, 'name': 'Пятница'}
    ]

    return render_template('edit_menu.html', user=user, menu_dishes=menu_dishes, week_days=week_days)


@app.route('/login_user_help/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        user = session.get('user')
        if user['role'] == 'student':
            return redirect('/menu/')
        elif user['role'] == 'cook':
            return redirect('/cook_menu/')
        elif user['role'] == 'admin':
            return redirect('/admin_stats/')
        return redirect('/menu/')

    if request.method == 'POST':
        user_name = request.form.get("user_name", "").strip()
        password = request.form.get("password1", "").strip()

        password_hash = hashlib.md5(password.encode()).hexdigest()

        db = sql.connect('db_for_project.db')
        cursor = db.cursor()

        try:
            special_users = {
                'admin': 'admin',
                'cook': 'cook',
                'qwer': 'qwer',
                'student': 'student'
            }

            if user_name in special_users and password == special_users[user_name]:
                print(f"Попытка входа как {user_name}")
                cursor.execute("SELECT * FROM users WHERE username = ?", (user_name,))
                user_data = cursor.fetchone()

                if user_data:
                    print(f"Найден существующий {user_name}: {user_data}")
                    user = {
                        'id': user_data[0],
                        'username': user_data[1],
                        'role': user_data[3] if user_data[3] != 'student' else 'student',
                        'full_name': user_data[4],
                        'allergies': user_data[5],
                        'preferences': user_data[6],
                        'class': user_data[7]
                    }
                else:
                    print(f"Создаем нового {user_name}")

                    if user_name == 'admin':
                        params = ('admin', 'admin', 'admin', 'Администратор', '', '', '')
                    elif user_name == 'cook':
                        params = ('cook', 'cook', 'cook', 'Повар', '', '', '')
                    elif user_name == 'qwer':
                        params = ('qwer', 'qwer', 'student', 'Тестовый Ученик QWER', '10Б', 'Нет', 'Нет')
                    elif user_name == 'student':
                        params = ('student', 'student', 'student', 'Тестовый Студент', '10А', 'Нет', 'Нет')

                    cursor.execute('''
                        INSERT INTO users (username, password_hash, role, full_name, class, allergies, preferences)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', params)
                    db.commit()

                    if user_name in ['student', 'qwer']:
                        new_user_id = cursor.lastrowid
                        cursor.execute('INSERT OR IGNORE INTO balance (user_id, amount) VALUES (?, 500)',
                                       (new_user_id,))
                        db.commit()

                    cursor.execute("SELECT * FROM users WHERE username = ?", (user_name,))
                    user_data = cursor.fetchone()
                    user = {
                        'id': user_data[0],
                        'username': user_data[1],
                        'role': user_data[3] if user_data[3] != 'student' else 'student',
                        'full_name': user_data[4],
                        'allergies': user_data[5],
                        'preferences': user_data[6],
                        'class': user_data[7]
                    }

                session['user'] = user
                db.close()
                print(f"{user_name} вошел: {user}")

                # Редирект в зависимости от роли
                if user['role'] == 'admin':
                    return redirect('/admin_stats/')
                elif user['role'] == 'cook':
                    return redirect('/cook_menu/')
                else:
                    return redirect('/menu/')

            query = """SELECT id FROM users WHERE username = ? AND password_hash = ?"""
            cursor.execute(query, (user_name, password_hash))
            id_result = cursor.fetchone()

            if id_result and id_result[0] > 0:
                query = '''SELECT * FROM users WHERE username = ? AND password_hash = ?'''
                cursor.execute(query, (user_name, password_hash))  # Используем хэш
                user_data = cursor.fetchone()
                user = {
                    'id': user_data[0],
                    'username': user_data[1],
                    'role': 'student' if user_data[3] == 'student' else user_data[3],
                    'full_name': user_data[4],
                    'allergies': user_data[5],
                    'preferences': user_data[6],
                    'class': user_data[7]
                }
                session['user'] = user
                db.close()
                return redirect('/menu/')
            else:
                db.close()
                return render_template('login_user_help.html', id='error')

        except Exception as e:
            print(f"Ошибка при входе: {e}")
            db.close()
            return render_template('login_user_help.html', id='error')

    return render_template('login_user_help.html', id='')


@app.route('/reg_user_help/', methods=['GET', 'POST'])
def reg_user():
    user = session.get('user')
    if 'user' in session:
        return redirect('/')
    if request.method == 'POST':
        full_name = request.form.get("full_name", "")
        class1 = request.form.get("class", "")
        allergy = request.form.get("allergy", "")
        login = request.form.get("login", "")
        pass1 = request.form.get("password1", "")
        pass2 = request.form.get("password2", "")
        preferences = request.form.get("preferences", "")
        password1 = hashlib.md5(pass1.encode())
        password2 = password1.hexdigest()
        db = sql.connect('db_for_project.db')
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (login,))
        if not all([full_name, class1, allergy, login, pass1, pass2, preferences]):
            return render_template('reg_user_help.html', ret='Неполн')
        elif pass1 != pass2:
            return render_template('reg_user_help.html', ret='Ошибка')
        else:
            role = 'student'
            query = """INSERT INTO users (full_name, class, allergies, username, password_hash, preferences, role) VALUES (?, ?, ?, ?, ?, ?, ?)"""
            cursor.execute(query, (full_name, class1, allergy, login, password2, preferences, role))
            db.commit()

            cursor.execute("SELECT id FROM users WHERE username = ?", (login,))
            new_user_id = cursor.fetchone()[0]
            cursor.execute("INSERT OR IGNORE INTO balance (user_id, amount) VALUES (?, 0)", (new_user_id,))
            db.commit()

            return render_template('reg_user_help.html', ret='Успех')
    return render_template('reg_user_help.html')


@app.route('/profile/')
def profile():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')

    balance = 0
    if user['role'] == 'student':
        try:
            db = sql.connect('db_for_project.db')
            cursor = db.cursor()
            cursor.execute('''SELECT amount FROM balance WHERE user_id = ?''', (user['id'],))
            balance_row = cursor.fetchone()
            if balance_row:
                balance = balance_row[0]
            db.close()
        except:
            balance = 0

    return render_template('profile.html', user=user, balance=balance)


@app.route('/exit/')
def exit():
    session.clear()
    return redirect('/login_user_help/')


@app.route('/student_payment/', methods=['GET', 'POST'])
def student_payment():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'student':
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'deposit':
            amount = request.form.get('amount', '')
            if amount:
                amount = int(amount)
                db = sql.connect('db_for_project.db')
                cursor = db.cursor()

                cursor.execute('''UPDATE balance SET amount = amount + ? WHERE user_id = ?''',
                               (amount, user['id']))

                cursor.execute('''
                    INSERT INTO purchase_history (user_id, purchase_type, amount, description)
                    VALUES (?, ?, ?, ?)
                ''', (user['id'], 'deposit', amount, f'Пополнение баланса на {amount} протокоинов'))

                db.commit()
                db.close()

    return redirect('/student_subscription/')


@app.route('/cook_mark_attendance/', methods=['GET', 'POST'])
def cook_mark_attendance():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    today = datetime.now().strftime('%Y-%m-%d')
    db = sql.connect('db_for_project.db')
    cursor = db.cursor()


    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        meal_type = request.form.get('meal_type', '')

        if student_id and meal_type:
            if student_id.isdigit():
                cursor.execute('''SELECT id FROM users WHERE id = ? AND role = "student"''', (student_id,))
            else:
                cursor.execute('''SELECT id FROM users WHERE full_name LIKE ? AND role = "student"''',
                               (f'%{student_id}%',))

            student = cursor.fetchone()

            if student:
                user_id = student[0]
                cursor.execute('''
                    SELECT mp.id FROM meal_payments mp
                    WHERE mp.user_id = ? AND mp.date = ? AND mp.meal_type = ? AND mp.status = 'paid'
                    ORDER BY mp.id DESC LIMIT 1
                ''', (user_id, today, meal_type))

                payment = cursor.fetchone()

                if payment:
                    cursor.execute('''UPDATE meal_payments SET status = 'attended' WHERE id = ?''',
                                   (payment[0],))
                    db.commit()
                else:
                    cursor.execute('''
                        INSERT INTO meal_payments (user_id, day_of_week, meal_type, date, status)
                        VALUES (?, ?, ?, ?, 'attended')
                    ''', (user_id, datetime.now().weekday(), meal_type, today))
                    db.commit()

    cursor.execute('''
        SELECT id, full_name, class 
        FROM users 
        WHERE role = 'student' 
        ORDER BY class, full_name
    ''')
    all_students = cursor.fetchall()

    students_list = []
    for student in all_students:
        students_list.append({
            'id': student[0],
            'name': student[1],
            'class': student[2]
        })

    cursor.execute('''
        SELECT 
            COUNT(CASE WHEN meal_type='breakfast' AND status='paid' THEN 1 END) as breakfast_paid,
            COUNT(CASE WHEN meal_type='breakfast' AND status='attended' THEN 1 END) as breakfast_attended,
            COUNT(CASE WHEN meal_type='lunch' AND status='paid' THEN 1 END) as lunch_paid,
            COUNT(CASE WHEN meal_type='lunch' AND status='attended' THEN 1 END) as lunch_attended
        FROM meal_payments 
        WHERE date = ?
    ''', (today,))

    stats_row = cursor.fetchone()
    stats = {
        'breakfast_paid': stats_row[0] if stats_row else 0,
        'breakfast_attended': stats_row[1] if stats_row else 0,
        'lunch_paid': stats_row[2] if stats_row else 0,
        'lunch_attended': stats_row[3] if stats_row else 0
    }

    cursor.execute('''
        SELECT 
            mp.id as payment_id,
            u.id as student_id,
            u.full_name as student_name,
            u.class,
            mp.meal_type,
            mp.status
        FROM meal_payments mp
        JOIN users u ON mp.user_id = u.id
        WHERE mp.date = ? AND mp.status IN ('paid', 'attended')
        ORDER BY u.class, u.full_name, mp.meal_type
    ''', (today,))

    paid_meals = []
    for row in cursor.fetchall():
        paid_meals.append({
            'payment_id': row[0],
            'student_id': row[1],
            'student_name': row[2],
            'class': row[3],
            'meal_type': row[4],
            'status': row[5]
        })

    db.close()

    return render_template('cook_attendance_mark.html',
                           user=user,
                           today_date=datetime.now().strftime('%d.%m.%Y'),
                           stats=stats,
                           paid_meals=paid_meals,
                           all_students=students_list)


@app.route('/cook_mark_single/<int:payment_id>')
def cook_mark_single(payment_id):
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    cursor.execute('''UPDATE meal_payments SET status = 'attended' WHERE id = ?''',
                   (payment_id,))
    db.commit()
    db.close()

    return redirect('/cook_mark_attendance/')


@app.route('/admin_allergies/')
def admin_allergies():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()
    cursor.execute(
        '''SELECT full_name, class, allergies, preferences FROM users WHERE role = 'student' ORDER BY class, full_name''')
    all_students = cursor.fetchall()

    total_students = len(all_students)

    with_allergies = 0
    for student in all_students:
        if student[2] and student[2].lower() != 'нет' and student[2].strip():
            with_allergies += 1


    with_preferences = 0
    for student in all_students:
        if student[3] and student[3].lower() != 'нет' and student[3].strip():
            with_preferences += 1


    allergy_dict = {}
    for student in all_students:
        if student[2] and student[2].lower() != 'нет':
            allergies = student[2].split(',')
            for allergy in allergies:
                allergy = allergy.strip().lower()
                if allergy:
                    if allergy not in allergy_dict:
                        allergy_dict[allergy] = {'count': 0, 'students': []}
                    allergy_dict[allergy]['count'] += 1
                    allergy_dict[allergy]['students'].append(student[0])

    common_allergies = []
    for allergy, data in allergy_dict.items():
        common_allergies.append({
            'name': allergy.capitalize(),
            'count': data['count'],
            'students': data['students']
        })

    common_allergies.sort(key=lambda x: x['count'], reverse=True)

    preference_dict = {}
    for student in all_students:
        if student[3] and student[3].lower() != 'нет':
            preferences = student[3].split(',')
            for preference in preferences:
                preference = preference.strip().lower()
                if preference:
                    if preference not in preference_dict:
                        preference_dict[preference] = {'count': 0, 'students': []}
                    preference_dict[preference]['count'] += 1
                    preference_dict[preference]['students'].append(student[0])

    common_preferences = []
    for preference, data in preference_dict.items():
        common_preferences.append({
            'name': preference.capitalize(),
            'count': data['count'],
            'students': data['students']
        })

    common_preferences.sort(key=lambda x: x['count'], reverse=True)

    students_list = []
    for student in all_students:
        students_list.append({
            'full_name': student[0],
            'class': student[1],
            'allergies': student[2] if student[2] else 'Нет',
            'preferences': student[3] if student[3] else 'Нет'
        })

    db.close()

    return render_template('admin_allergies.html',
                           user=user,
                           total_students=total_students,
                           with_allergies=with_allergies,
                           with_preferences=with_preferences,
                           common_allergies=common_allergies[:10],
                           common_preferences=common_preferences[:10],
                           all_students=students_list)


@app.route('/student_reviews/', methods=['GET', 'POST'])
def student_reviews():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'student':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if request.method == 'POST':
        dish_name = request.form.get('dish_name', '')
        rating = request.form.get('rating', '')
        comment = request.form.get('comment', '')

        if dish_name and rating:
            cursor.execute('''INSERT INTO reviews (user_id, dish_name, rating, comment) VALUES (?, ?, ?, ?)''',
                           (user['id'], dish_name, rating, comment))
            db.commit()

    cursor.execute('''SELECT dish_name, rating, comment, date FROM reviews WHERE user_id = ? ORDER BY date DESC''',
                   (user['id'],))
    reviews = cursor.fetchall()
    db.close()

    return render_template('student_reviews.html', user=user, reviews=reviews)


@app.route('/student_edit_profile/', methods=['GET', 'POST'])
def student_edit_profile():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'student':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if request.method == 'POST':
        allergies = request.form.get('allergies', '')
        preferences = request.form.get('preferences', '')

        cursor.execute('''UPDATE users SET allergies = ?, preferences = ? WHERE id = ?''',
                       (allergies, preferences, user['id']))
        db.commit()

        user['allergies'] = allergies
        user['preferences'] = preferences
        session['user'] = user

    db.close()
    return render_template('student_edit_profile.html', user=user)






@app.route('/cook_inventory/')
def cook_inventory():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM inventory''')
    inventory = cursor.fetchall()
    cursor.execute('''SELECT * FROM dishes''')
    dishes = cursor.fetchall()
    db.close()

    return render_template('cook_inventory.html', user=user, inventory=inventory, dishes=dishes)


@app.route('/cook_purchase/', methods=['GET', 'POST'])
def cook_purchase():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if request.method == 'POST':
        item_name = request.form.get('item_name', '')
        quantity = request.form.get('quantity', '')
        price = request.form.get('price', '')

        if item_name and quantity and price:
            cursor.execute(
                '''INSERT INTO purchase_requests (item_name, quantity, price, created_by) VALUES (?, ?, ?, ?)''',
                (item_name, quantity, price, user['id']))
            db.commit()

    cursor.execute('''SELECT * FROM purchase_requests WHERE created_by = ? ORDER BY created_date DESC''', (user['id'],))
    requests = cursor.fetchall()
    db.close()

    return render_template('cook_purchase.html', user=user, requests=requests)


@app.route('/admin_stats/')
def admin_stats():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM meal_payments WHERE status IN ('paid', 'attended')")
    total_meals = cursor.fetchone()[0] or 0
    total_revenue = total_meals * 50

    cursor.execute("SELECT COUNT(*) FROM meal_payments WHERE status='attended'")
    attendance_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM purchase_requests WHERE status='pending'")
    pending_requests = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    total_students = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN meal_type='breakfast' AND status IN ('paid', 'attended') THEN 1 END) as breakfast_paid,
            COUNT(CASE WHEN meal_type='breakfast' AND status='attended' THEN 1 END) as breakfast_attended,
            COUNT(CASE WHEN meal_type='lunch' AND status IN ('paid', 'attended') THEN 1 END) as lunch_paid,
            COUNT(CASE WHEN meal_type='lunch' AND status='attended' THEN 1 END) as lunch_attended
        FROM meal_payments
    """)

    stats = cursor.fetchone()
    breakfast_paid = stats[0] if stats else 0
    breakfast_attended = stats[1] if stats else 0
    lunch_paid = stats[2] if stats else 0
    lunch_attended = stats[3] if stats else 0

    breakfast_revenue = breakfast_paid * 50
    lunch_revenue = lunch_paid * 50

    db.close()

    return render_template('admin_stats.html',
                           user=user,
                           total_revenue=total_revenue,
                           total_meals=total_meals,
                           attendance_count=attendance_count,
                           pending_requests=pending_requests,
                           total_students=total_students,
                           breakfast_paid=breakfast_paid,
                           breakfast_attended=breakfast_attended,
                           breakfast_revenue=breakfast_revenue,
                           lunch_paid=lunch_paid,
                           lunch_attended=lunch_attended,
                           lunch_revenue=lunch_revenue)


@app.route('/admin_purchase/')
def admin_purchase():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM purchase_requests ORDER BY status, created_date DESC''')
    requests = cursor.fetchall()
    db.close()

    return render_template('admin_purchase.html', user=user, requests=requests)


@app.route('/admin_approve/<int:req_id>')
def admin_approve(req_id):
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()
    cursor.execute('''UPDATE purchase_requests SET status='approved' WHERE id=?''', (req_id,))
    db.commit()
    db.close()

    return redirect('/admin_purchase/')


@app.route('/admin_reject/<int:req_id>')
def admin_reject(req_id):
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()
    cursor.execute('''UPDATE purchase_requests SET status='rejected' WHERE id=?''', (req_id,))
    db.commit()
    db.close()

    return redirect('/admin_purchase/')


@app.route('/admin_report/')
def admin_report():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM meal_payments WHERE status IN ('paid', 'attended')")
    total_meals = cursor.fetchone()[0] or 0
    total_revenue = total_meals * 50

    cursor.execute("SELECT COUNT(*) FROM meal_payments WHERE meal_type='breakfast' AND status='attended'")
    breakfast_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM meal_payments WHERE meal_type='lunch' AND status='attended'")
    lunch_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(rating) FROM reviews")
    avg_rating = cursor.fetchone()[0] or 0

    db.close()

    return render_template('admin_report.html',
                           user=user,
                           total_revenue=total_revenue,
                           total_meals=total_meals,
                           breakfast_count=breakfast_count,
                           lunch_count=lunch_count,
                           avg_rating=avg_rating)


@app.route('/admin_reviews/')
def admin_reviews():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()
    cursor.execute('''SELECT r.dish_name, r.rating, r.comment, u.full_name, r.date 
                     FROM reviews r 
                     JOIN users u ON r.user_id = u.id 
                     ORDER BY r.date DESC''')
    reviews = cursor.fetchall()
    db.close()

    return render_template('admin_reviews.html', user=user, reviews=reviews)

@app.route('/cook_inventory_manage/', methods=['GET', 'POST'])
def cook_inventory_manage():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_product':
            item_name = request.form.get('item_name', '')
            quantity = request.form.get('quantity', '')
            unit = request.form.get('unit', '')
            min_quantity = request.form.get('min_quantity', '')

            if item_name and quantity and unit:
                cursor.execute('''
                    INSERT INTO inventory (item_name, quantity, unit, min_quantity)
                    VALUES (?, ?, ?, ?)
                ''', (item_name, quantity, unit, min_quantity or 0))
                db.commit()

        elif action == 'update_product':
            product_id = request.form.get('product_id', '')
            quantity = request.form.get('quantity', '')
            min_quantity = request.form.get('min_quantity', '')

            if product_id and quantity:
                cursor.execute('''
                    UPDATE inventory SET quantity = ?, min_quantity = ?
                    WHERE id = ?
                ''', (quantity, min_quantity or 0, product_id))
                db.commit()

        elif action == 'delete_product':
            product_id = request.form.get('product_id', '')
            if product_id:
                cursor.execute('DELETE FROM inventory WHERE id = ?', (product_id,))
                db.commit()

        elif action == 'add_dish':
            dish_name = request.form.get('dish_name', '')
            quantity_available = request.form.get('quantity_available', '')

            if dish_name and quantity_available:
                cursor.execute('''
                    INSERT INTO dishes (dish_name, quantity_available)
                    VALUES (?, ?)
                ''', (dish_name, quantity_available))
                db.commit()

        elif action == 'update_dish':
            dish_id = request.form.get('dish_id', '')
            quantity_available = request.form.get('quantity_available', '')

            if dish_id and quantity_available:
                cursor.execute('''
                    UPDATE dishes SET quantity_available = ?
                    WHERE id = ?
                ''', (quantity_available, dish_id))
                db.commit()

        elif action == 'delete_dish':
            dish_id = request.form.get('dish_id', '')
            if dish_id:
                cursor.execute('DELETE FROM dishes WHERE id = ?', (dish_id,))
                db.commit()

    cursor.execute('''SELECT * FROM inventory ORDER BY item_name''')
    inventory = cursor.fetchall()

    cursor.execute('''SELECT * FROM dishes ORDER BY dish_name''')
    dishes = cursor.fetchall()

    cursor.execute('''
        SELECT DISTINCT dish_name 
        FROM menu_dishes 
        WHERE dish_name != 'Завтрак' AND dish_name != 'Обед' 
        AND dish_name != 'Не указано'
        ORDER BY dish_name
    ''')
    menu_dishes = cursor.fetchall()

    menu_dishes_list = [dish[0] for dish in menu_dishes]

    db.close()

    return render_template('cook_inventory_manage.html',
                           user=user,
                           inventory=inventory,
                           dishes=dishes,
                           menu_dishes=menu_dishes_list)



@app.route('/cook_purchase_request/', methods=['GET', 'POST'])
def cook_purchase_request():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_request':
            item_name = request.form.get('item_name', '')
            quantity = request.form.get('quantity', '')
            unit = request.form.get('unit', '')
            price = request.form.get('price', '')
            reason = request.form.get('reason', '')
            priority = request.form.get('priority', 'normal')

            if item_name and quantity and unit:
                cursor.execute('''
                    INSERT INTO purchase_requests 
                    (item_name, quantity, unit, price, reason, priority, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (item_name, quantity, unit, price or 0, reason, priority, user['id']))
                db.commit()

    cursor.execute('''
        SELECT id, item_name, quantity, unit, min_quantity 
        FROM inventory 
        WHERE min_quantity > 0 AND quantity <= min_quantity
        ORDER BY item_name
    ''')
    low_stock_items = cursor.fetchall()

    cursor.execute('''
        SELECT id, item_name, quantity, unit, price, reason, priority, status, created_date 
        FROM purchase_requests 
        WHERE created_by = ? 
        ORDER BY created_date DESC
    ''', (user['id'],))
    user_requests = cursor.fetchall()

    cursor.execute('SELECT DISTINCT item_name, unit FROM inventory ORDER BY item_name')
    all_products = cursor.fetchall()

    db.close()

    return render_template('cook_purchase_request.html',
                           user=user,
                           low_stock_items=low_stock_items,
                           user_requests=user_requests,
                           all_products=all_products)


@app.route('/cook_purchase_request/<int:request_id>', methods=['POST'])
def update_purchase_request(request_id):
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'cook':
        return redirect('/')

    action = request.form.get('action')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if action == 'delete':
        cursor.execute('SELECT created_by FROM purchase_requests WHERE id = ?', (request_id,))
        request_owner = cursor.fetchone()

        if request_owner and request_owner[0] == user['id']:
            cursor.execute('DELETE FROM purchase_requests WHERE id = ?', (request_id,))
            db.commit()

    elif action == 'update':
        quantity = request.form.get('quantity', '')
        price = request.form.get('price', '')
        reason = request.form.get('reason', '')
        priority = request.form.get('priority', 'normal')

        cursor.execute('SELECT created_by FROM purchase_requests WHERE id = ?', (request_id,))
        request_owner = cursor.fetchone()

        if request_owner and request_owner[0] == user['id'] and quantity:
            cursor.execute('''
                UPDATE purchase_requests 
                SET quantity = ?, price = ?, reason = ?, priority = ?
                WHERE id = ?
            ''', (quantity, price or 0, reason, priority, request_id))
            db.commit()

    db.close()
    return redirect('/cook_purchase_request/')


@app.route('/student_subscription/', methods=['GET', 'POST'])
def student_subscription():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'student':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    cursor.execute('''SELECT amount FROM balance WHERE user_id = ?''', (user['id'],))
    balance_row = cursor.fetchone()
    balance = balance_row[0] if balance_row else 0

    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT * FROM subscriptions 
        WHERE user_id = ? AND status = 'active' AND end_date >= ?
        ORDER BY end_date DESC LIMIT 1
    ''', (user['id'], today))

    active_subscription = cursor.fetchone()

    cursor.execute('''
        UPDATE subscriptions 
        SET status = 'expired' 
        WHERE user_id = ? AND end_date < ? AND status = 'active'
    ''', (user['id'], today))
    db.commit()

    subscription_end_date = None
    if active_subscription:
        subscription_end_date = active_subscription[4]
        try:
            sub_date = datetime.strptime(subscription_end_date, '%Y-%m-%d')
            subscription_end_date = sub_date.strftime('%d.%m.%Y')
        except:
            pass

    cursor.execute('''
        SELECT 
            purchase_date,
            purchase_type,
            amount,
            description
        FROM purchase_history 
        WHERE user_id = ? 
        ORDER BY purchase_date DESC LIMIT 20
    ''', (user['id'],))

    purchases_data = cursor.fetchall()

    purchases = []
    for purchase in purchases_data:
        purchases.append({
            'date': purchase[0][:10] if purchase[0] else '',
            'type': purchase[1],
            'amount': purchase[2],
            'description': purchase[3]
        })

    subscriptions = [
        {'type': 'week', 'name': 'Абонемент на 5 дней', 'price': 450,
         'description': 'Питание на неделю (5 рабочих дней) со скидкой 10%'},
        {'type': 'two_weeks', 'name': 'Абонемент на 10 дней', 'price': 850,
         'description': 'Питание на 2 недели со скидкой 15%'},
    ]

    error = None
    message = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'buy_subscription':
            subscription_type = request.form.get('subscription_type', '')

            if subscription_type == 'week':
                price = 450
                required_working_days = 5
                description = "Абонемент на 5 дней"
            elif subscription_type == 'two_weeks':
                price = 850
                required_working_days = 10
                description = "Абонемент на 10 дней"
            else:
                error = "Неверный тип абонемента"
                db.close()
                return render_template('balance.html',
                                       user=user,
                                       balance=balance,
                                       subscriptions=subscriptions,
                                       active_subscription=active_subscription,
                                       subscription_end_date=subscription_end_date,
                                       purchases=purchases,
                                       error=error)

            if balance >= price:
                try:
                    cursor.execute('''UPDATE balance SET amount = amount - ? WHERE user_id = ?''',
                                   (price, user['id']))

                    start_date = datetime.now().strftime('%Y-%m-%d')

                    added_working_days = 0
                    current_date = datetime.now().date()
                    end_date_obj = None

                    dates_to_create = []

                    while added_working_days < required_working_days:
                        if current_date.weekday() < 5:
                            added_working_days += 1
                            dates_to_create.append(current_date)
                            end_date_obj = current_date
                        current_date += timedelta(days=1)

                    end_date = end_date_obj.strftime('%Y-%m-%d') if end_date_obj else start_date

                    cursor.execute('''
                        INSERT INTO subscriptions (user_id, subscription_type, start_date, end_date, status)
                        VALUES (?, ?, ?, ?, 'active')
                    ''', (user['id'], subscription_type, start_date, end_date))

                    cursor.execute('''
                        INSERT INTO purchase_history (user_id, purchase_type, amount, description)
                        VALUES (?, 'subscription', ?, ?)
                    ''', (user['id'], price, description))


                    current_week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())

                    for meal_date in dates_to_create:
                        for meal_type in ['breakfast', 'lunch']:

                            cursor.execute('''
                                SELECT id, status FROM meal_payments 
                                WHERE user_id = ? AND date = ? AND meal_type = ?
                            ''', (user['id'], meal_date, meal_type))
                            record = cursor.fetchone()

                            if record:
                                if record[1] == 'unpaid':
                                    cursor.execute('''
                                        UPDATE meal_payments 
                                        SET status = 'paid' 
                                        WHERE id = ?
                                    ''', (record[0],))
                            else:
                                day_of_week = meal_date.weekday()
                                start_of_week_for_date = meal_date - timedelta(days=day_of_week)
                                week_offset = (start_of_week_for_date - current_week_start).days // 7

                                cursor.execute('''
                                    INSERT INTO meal_payments (user_id, day_of_week, meal_type, date, status, week_offset)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (user['id'], day_of_week, meal_type, meal_date, 'paid', week_offset))

                    db.commit()

                    if end_date_obj:
                        end_date_formatted = end_date_obj.strftime('%d.%m.%Y')
                    else:
                        end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d.%m.%Y')

                    message = f"Абонемент успешно приобретен! Действует до {end_date_formatted}. Все приемы пищи на {required_working_days} рабочих дней оплачены."

                except Exception as e:
                    db.rollback()
                    error = f"Ошибка при создании абонемента: {str(e)}"
                    db.close()
                    return render_template('balance.html',
                                           user=user,
                                           balance=balance,
                                           subscriptions=subscriptions,
                                           active_subscription=active_subscription,
                                           subscription_end_date=subscription_end_date,
                                           purchases=purchases,
                                           error=error)

                cursor.execute('''SELECT amount FROM balance WHERE user_id = ?''', (user['id'],))
                balance_row = cursor.fetchone()
                balance = balance_row[0] if balance_row else 0

                cursor.execute('''
                    SELECT * FROM subscriptions 
                    WHERE user_id = ? AND status = 'active' AND end_date >= ?
                    ORDER BY end_date DESC LIMIT 1
                ''', (user['id'], today))

                active_subscription = cursor.fetchone()
                if active_subscription:
                    sub_date = datetime.strptime(active_subscription[4], '%Y-%m-%d')
                    subscription_end_date = sub_date.strftime('%d.%m.%Y')

                cursor.execute('''
                    SELECT 
                        purchase_date,
                        purchase_type,
                        amount,
                        description
                    FROM purchase_history 
                    WHERE user_id = ? 
                    ORDER BY purchase_date DESC LIMIT 20
                ''', (user['id'],))

                purchases_data = cursor.fetchall()
                purchases = []
                for purchase in purchases_data:
                    purchases.append({
                        'date': purchase[0][:10] if purchase[0] else '',
                        'type': purchase[1],
                        'amount': purchase[2],
                        'description': purchase[3]
                    })

            else:
                error = "Недостаточно средств на балансе"

    db.close()

    return render_template('balance.html',
                           user=user,
                           balance=balance,
                           subscriptions=subscriptions,
                           active_subscription=active_subscription,
                           subscription_end_date=subscription_end_date,
                           purchases=purchases,
                           error=error,
                           message=message)


@app.route('/admin_purchase_manage/', methods=['GET', 'POST'])
def admin_purchase_manage():
    if 'user' not in session:
        return redirect('/login_user_help/')
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect('/')

    db = sql.connect('db_for_project.db')
    cursor = db.cursor()

    if request.method == 'POST':
        request_id = request.form.get('request_id', '')
        action = request.form.get('action', '')

        if action == 'approve':
            cursor.execute('''
                UPDATE purchase_requests 
                SET status = 'approved' 
                WHERE id = ?
            ''', (request_id,))
            db.commit()

        elif action == 'reject':
            cursor.execute('''
                UPDATE purchase_requests 
                SET status = 'rejected'
                WHERE id = ?
            ''', (request_id,))
            db.commit()

    cursor.execute('''
        SELECT pr.id, pr.item_name, pr.quantity, pr.unit, pr.price, 
               pr.reason, pr.priority, pr.status, pr.created_date,
               u.full_name as creator_name
        FROM purchase_requests pr
        JOIN users u ON pr.created_by = u.id
        ORDER BY 
            CASE priority 
                WHEN 'high' THEN 1 
                WHEN 'normal' THEN 2 
                WHEN 'low' THEN 3 
            END,
            pr.created_date DESC
    ''')
    all_requests = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM purchase_requests WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(price * quantity) FROM purchase_requests WHERE status = 'pending'")
    total_cost = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM purchase_requests WHERE status = 'approved'")
    approved_count = cursor.fetchone()[0] or 0

    db.close()

    return render_template('admin_purchase_manage.html',
                           user=user,
                           all_requests=all_requests,
                           pending_count=pending_count,
                           total_cost=total_cost,
                           approved_count=approved_count)
if __name__ == '__main__':
    init_db()
    app.run(debug=True)