from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from datetime import datetime, timedelta

app = FastAPI()@app.get("/")
def read_root():
    return RedirectResponse(url="/login")
DB_NAME = "kassa_v4.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT,
            role TEXT DEFAULT 'reader'
        )
    """)
    
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin123", "Администратор", "admin")
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            item_name TEXT,
            total_price REAL,
            cash_amount REAL,
            card_amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT,
            name_az TEXT,
            price REAL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        initial_products = [
            ("Черный тмин (масло) 100ml", "Qara çörəkotu yağı 100ml", 15.0),
            ("Масло оливковое специальное", "Xüsusi zeytun yağı", 12.0),
            ("Зам-зам вода 1л", "Zəm-zəm suyu 1l", 5.0),
            ("Миск (парфюмерное масло)", "Misk (ətir yağı)", 8.0),
            ("Челеби / Вода с дуа", "Çələbi / Dua ilə su", 3.0),
            ("Благовония (бахур)", "Bəxur / Ətirli tüstü", 10.0),
            ("Книга «Защита от сглаза»", "«Göz dəymədən qorunma» kitabı", 7.0),
            ("Сивак / Мисвак", "Sivak / Misvak", 2.0),
            ("Травяной сбор (чай)", "Ot çayı", 6.0),
            ("Набор медовый специальный", "Xüsusi bal dəsti", 25.0)
        ]
        cursor.executemany("INSERT INTO products (name_ru, name_az, price) VALUES (?, ?, ?)", initial_products)

    conn.commit()
    conn.close()

init_db()

COMMON_STYLE = """
<style>
    :root {
        --bg-color: #0f172a;
        --card-bg: #1e293b;
        --text-color: #ffffff;
        --border-color: #334155;
        --input-bg: #0f172a;
        --accent-color: #0284c7;
        --subtext: #94a3b8;
    }
    body.light-mode {
        --bg-color: #f8fafc;
        --card-bg: #ffffff;
        --text-color: #0f172a;
        --border-color: #cbd5e1;
        --input-bg: #f1f5f9;
        --accent-color: #0284c7;
        --subtext: #64748b;
    }
    body { font-family: -apple-system, sans-serif; background: var(--bg-color); color: var(--text-color); padding: 15px; max-width: 620px; margin: 0 auto; transition: all 0.2s ease; }
    .card { background: var(--card-bg); padding: 18px; border-radius: 12px; margin-bottom: 15px; border: 1px solid var(--border-color); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .header { display: flex; justify-content: space-between; align-items: center; }
    .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .btn-toggle { background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-color); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; text-decoration: none; }
    .btn { padding: 12px; background: var(--accent-color); color: white; border: none; border-radius: 8px; font-weight: bold; width: 100%; cursor: pointer; margin-top: 10px; font-size: 15px; }
    .btn-green { background: #16a34a; }
    .btn-install { background: #16a34a; color: white; border: none; padding: 10px; border-radius: 8px; font-weight: bold; width: 100%; cursor: pointer; margin-bottom: 15px; display: none; }
    input, select { width: 100%; padding: 10px; margin-top: 4px; margin-bottom: 10px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-color); box-sizing: border-box; font-size: 14px; }
    .flex { display: flex; gap: 10px; }
    .stat { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-color); font-size: 14px; }
    .err-banner { background: #ef4444; color: white; padding: 10px; border-radius: 8px; margin-bottom: 15px; font-weight: bold; text-align: center; }
    
    .filter-btn { padding: 6px 12px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--input-bg); color: var(--text-color); text-decoration: none; font-size: 13px; }
    .filter-btn.active { background: var(--accent-color); color: white; border-color: var(--accent-color); font-weight: bold; }
</style>
<script>
    function toggleTheme() {
        document.body.classList.toggle('light-mode');
        localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
    }
    window.addEventListener('DOMContentLoaded', () => {
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-mode');
        }
    });

    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        const btn = document.getElementById('pwaBtn');
        if (btn) btn.style.display = 'block';
    });

    function installPWA() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then(() => {
                deferredPrompt = null;
                document.getElementById('pwaBtn').style.display = 'none';
            });
        }
    }
</script>
"""

@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = "", lang: str = "ru"):
    err_msg = f"<div class='err-banner'>{error}</div>" if error else ""
    is_az = lang == "az"
    
    title = "Sistemə giriş" if is_az else "Вход в Систему"
    user_ph = "İstifadəçi adı" if is_az else "Логин"
    pass_ph = "Şifrə" if is_az else "Пароль"
    btn_txt = "Daxil ol" if is_az else "Войти"
    reg_link = "Hesabınız yoxdur? Qeydiyyat" if is_az else "Ещё нет аккаунта? Зарегистрироваться"
    pwa_txt = "📲 Tətbiq kimi quraşdırın" if is_az else "📲 Установить как приложение"

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>{title}</title>{COMMON_STYLE}</head>
    <body>
        <div class="top-bar">
            <button class="btn-toggle" onclick="toggleTheme()">🌗 Тема / Mövzu</button>
            <div>
                <a href="/login?lang=ru" class="btn-toggle" style="font-weight:{'bold' if not is_az else 'normal'}">RU</a>
                <a href="/login?lang=az" class="btn-toggle" style="font-weight:{'bold' if is_az else 'normal'}">AZ</a>
            </div>
        </div>
        
        <button id="pwaBtn" class="btn-install" onclick="installPWA()">{pwa_txt}</button>

        <div class="card" style="text-align:center;">
            <h2 style="color:#0284c7; margin-top:0;">🔐 {title}</h2>
            {err_msg}
            <form id="loginForm" action="/login?lang={lang}" method="post" onsubmit="saveUser()">
                <input type="text" id="username_inp" name="username" placeholder="{user_ph}" required autocomplete="username">
                <input type="password" id="password_inp" name="password" placeholder="{pass_ph}" required autocomplete="current-password">
                <button type="submit" class="btn">{btn_txt}</button>
            </form>
            <a href="/register?lang={lang}" style="color:#0284c7; text-decoration:none; font-size:14px; display:inline-block; margin-top:15px;">{reg_link}</a>
        </div>

        <script>
            function saveUser() {{
                localStorage.setItem('saved_user', document.getElementById('username_inp').value);
                localStorage.setItem('saved_pass', document.getElementById('password_inp').value);
            }}

            window.addEventListener('load', () => {{
                let su = localStorage.getItem('saved_user');
                let sp = localStorage.getItem('saved_pass');
                if (su && sp) {{
                    document.getElementById('username_inp').value = su;
                    document.getElementById('password_inp').value = sp;
                }}
            }});
        </script>
    </body>
    </html>
    """

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), lang: str = "ru"):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    
    if not user:
        err = "Yanlış istifadəçi adı və ya şifrə" if lang == "az" else "Неверный логин или пароль"
        return RedirectResponse(url=f"/login?error={err}&lang={lang}", status_code=303)
        
    if user['role'] == 'admin':
        return RedirectResponse(url=f"/admin?user_id={user['id']}&lang={lang}", status_code=303)
    return RedirectResponse(url=f"/kassa?user_id={user['id']}&lang={lang}", status_code=303)

@app.get("/register", response_class=HTMLResponse)
def register_page(error: str = "", lang: str = "ru"):
    err_msg = f"<div class='err-banner'>{error}</div>" if error else ""
    is_az = lang == "az"
    
    title = "Xətib Qeydiyyatı" if is_az else "Регистрация Чтеца"
    name_ph = "Adınız (məsələn: Əli)" if is_az else "Ваше Имя (например: Чтец Али)"
    user_ph = "İstifadəçi adı təyin edin" if is_az else "Придумайте Логин"
    pass_ph = "Şifrə təyin edin" if is_az else "Придумайте Пароль"
    btn_txt = "Hesab yarat" if is_az else "Создать аккаунт"
    login_link = "Artıq hesabınız var? Daxil ol" if is_az else "Уже есть аккаунт? Войти"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>{title}</title>{COMMON_STYLE}</head>
    <body>
        <div class="top-bar">
            <button class="btn-toggle" onclick="toggleTheme()">🌗 Тема / Mövzu</button>
            <div>
                <a href="/register?lang=ru" class="btn-toggle">RU</a>
                <a href="/register?lang=az" class="btn-toggle">AZ</a>
            </div>
        </div>
        <div class="card" style="text-align:center;">
            <h2 style="color:#0284c7; margin-top:0;">📝 {title}</h2>
            {err_msg}
            <form action="/register?lang={lang}" method="post">
                <input type="text" name="name" placeholder="{name_ph}" required>
                <input type="text" name="username" placeholder="{user_ph}" required>
                <input type="password" name="password" placeholder="{pass_ph}" required>
                <button type="submit" class="btn btn-green">{btn_txt}</button>
            </form>
            <a href="/login?lang={lang}" style="color:#0284c7; text-decoration:none; font-size:14px; display:inline-block; margin-top:15px;">{login_link}</a>
        </div>
    </body>
    </html>
    """

@app.post("/register")
def register(name: str = Form(...), username: str = Form(...), password: str = Form(...), lang: str = "ru"):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, 'reader')", (name, username, password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return RedirectResponse(url=f"/kassa?user_id={user_id}&lang={lang}", status_code=303)
    except sqlite3.IntegrityError:
        conn.close()
        err = "Bu istifadəçi adı artiq götürülüb" if lang == "az" else "Этот логин уже занят"
        return RedirectResponse(url=f"/register?error={err}&lang={lang}", status_code=303)

@app.get("/kassa", response_class=HTMLResponse)
def kassa_page(user_id: int, error: str = "", lang: str = "ru"):
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return RedirectResponse(url="/login")
        
    products = cursor.execute("SELECT * FROM products").fetchall()
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_txs = cursor.execute("SELECT * FROM transactions WHERE user_id = ? AND date(created_at) = ? ORDER BY id DESC", (user_id, today_str)).fetchall()
    
    total_income = sum(t["total_price"] for t in today_txs)
    total_cash = sum(t["cash_amount"] for t in today_txs)
    total_card = sum(t["card_amount"] for t in today_txs)
    reader_salary = total_income * 0.5
    transfer_to_company = total_cash - reader_salary

    is_az = lang == "az"
    prod_options = "".join([f'<option value="{p["price"]}" data-name="{p["name_az" if is_az else "name_ru"]}">{p["name_az" if is_az else "name_ru"]} — {p["price"]} AZN</option>' for p in products])
    pwa_txt = "📲 Tətbiq kimi quraşdırın" if is_az else "📲 Установить как приложение"

    tx_list = ""
    for t in today_txs:
        tx_list += f"""
        <div style="background:var(--input-bg); padding:10px; border-radius:8px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <b>{t["item_name"]}</b> — {t["total_price"]} AZN<br>
                <small style="color:var(--subtext);">💵 {'Nağd' if is_az else 'Нал'}: {t["cash_amount"]} | 💳 {'Köçürmə' if is_az else 'Перевод'}: {t["card_amount"]}</small>
            </div>
            <form action="/delete/{t['id']}?user_id={user_id}&lang={lang}" method="post" style="margin:0;">
                <button type="submit" style="background:#ef4444; padding:5px 10px; border:none; color:white; border-radius:6px; cursor:pointer;">❌</button>
            </form>
        </div>
        """

    err_banner = f"<div class='err-banner'>{error}</div>" if error else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>{'Kassa' if is_az else 'Касса'}</title>{COMMON_STYLE}</head>
    <body>
        <div class="top-bar">
            <button class="btn-toggle" onclick="toggleTheme()">🌗 Тема / Mövzu</button>
            <div>
                <a href="/kassa?user_id={user_id}&lang=ru" class="btn-toggle">RU</a>
                <a href="/kassa?user_id={user_id}&lang=az" class="btn-toggle">AZ</a>
            </div>
        </div>

        <button id="pwaBtn" class="btn-install" onclick="installPWA()">{pwa_txt}</button>

        <div class="card header">
            <h3 style="margin:0;">📖 {'Xətib' if is_az else 'Чтец'}: <span style="color:#0284c7;">{user['name']}</span></h3>
            <a href="/login?lang={lang}" style="color:#ef4444; text-decoration:none; font-weight:bold;">{'Çıxış' if is_az else 'Выйти'}</a>
        </div>

        {err_banner}

        <div class="card">
            <h3>📖 {'Seans keçirmək' if is_az else 'Провести Сеанс'}</h3>
            <form action="/add" method="post">
                <input type="hidden" name="user_id" value="{user_id}">
                <input type="hidden" name="type" value="session">
                <input type="hidden" name="item_name" value="{'Seans' if is_az else 'Сеанс'}">
                <input type="hidden" name="lang" value="{lang}">
                
                <label>{'Seansın ümumi dəyəri (AZN)' if is_az else 'Общая стоимость сеанса (AZN)'}:</label>
                <input type="number" step="0.1" name="total_price" value="0" required>
                
                <div class="flex">
                    <div style="flex:1;">
                        <label>{'Nağd ödəniş' if is_az else 'Оплата наличными'}:</label>
                        <input type="number" step="0.1" name="cash_amount" value="0" required>
                    </div>
                    <div style="flex:1;">
                        <label>{'Kartla / Köçürmə' if is_az else 'Оплата переводом'}:</label>
                        <input type="number" step="0.1" name="card_amount" value="0" required>
                    </div>
                </div>

                <button type="submit" class="btn">{'Seansı yadda saxla' if is_az else 'Сохранить сеанс'}</button>
            </form>
        </div>

        <div class="card">
            <h3>🛍️ {'Məhsul satışı' if is_az else 'Продать Товары'}</h3>
            <div class="flex">
                <select id="p_select">{prod_options}</select>
                <button type="button" onclick="addP()" style="width: auto; padding: 0 15px; background:#16a34a; border-radius:6px; color:white; border:none; cursor:pointer;">+</button>
            </div>
            <div id="cart" style="margin-bottom:10px; font-size:14px; color:var(--subtext); background:var(--input-bg); padding:8px; border-radius:6px;">{'Qəbz boşdur' if is_az else 'Чек пуст'}</div>

            <form action="/add" method="post">
                <input type="hidden" name="user_id" value="{user_id}">
                <input type="hidden" name="type" value="product">
                <input type="hidden" id="p_name" name="item_name" value="">
                <input type="hidden" id="p_total" name="total_price" value="0">
                <input type="hidden" name="lang" value="{lang}">
                
                <div class="flex">
                    <div style="flex:1;">
                        <label>{'Nağd' if is_az else 'Оплата наличными'}:</label>
                        <input type="number" step="0.1" id="p_cash" name="cash_amount" value="0" required>
                    </div>
                    <div style="flex:1;">
                        <label>{'Köçürmə' if is_az else 'Оплата переводом'}:</label>
                        <input type="number" step="0.1" id="p_card" name="card_amount" value="0" required>
                    </div>
                </div>

                <button type="submit" class="btn btn-green">{'Məhsulları sat' if is_az else 'Продать товары'}</button>
            </form>
        </div>

        <div class="card">
            <h3>📊 {'Növbənin yekunları' if is_az else 'Итоги вашей смены'}</h3>
            <div class="stat"><span>{'Ümumi gəlir' if is_az else 'Общая выручка'}:</span> <b>{total_income:.2f} AZN</b></div>
            <div class="stat"><span>{'Nağd qəbul edilib' if is_az else 'Принято наличными'}:</span> <b>{total_cash:.2f} AZN</b></div>
            <div class="stat"><span>{'Köçürmə ilə qəbul edilib' if is_az else 'Принято переводом'}:</span> <b>{total_card:.2f} AZN</b></div>
            <div class="stat"><span>{'Məvacibiniz (50%)' if is_az else 'Ваша зарплата (50%)'}:</span> <b>{reader_salary:.2f} AZN</b></div>
            <div class="stat" style="color:#16a34a; font-size:16px; margin-top:5px;">
                <span>{'Şirkətə təhvil veriləcək nağd məbləğ' if is_az else 'Сдать наличными компании'}:</span> 
                <b>{transfer_to_company:.2f} AZN</b>
            </div>
        </div>

        <div class="card">
            <h3>📝 {'Bugünkü qeydlər' if is_az else 'Записи за сегодня'}</h3>
            {tx_list if tx_list else f"<small style='color:var(--subtext);'>{'Qeyd yoxdur' if is_az else 'Записей пока нет'}</small>"}
        </div>

        <script>
            let cartItems = [];
            function addP() {{
                let sel = document.getElementById('p_select');
                let price = parseFloat(sel.value);
                let name = sel.options[sel.selectedIndex].getAttribute('data-name');
                cartItems.push({{name, price}});
                renderCart();
            }}

            function renderCart() {{
                let tot = 0;
                let names = [];
                let html = '';
                cartItems.forEach((item, i) => {{
                    tot += item.price;
                    names.push(item.name);
                    html += `<div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>${{item.name}} (${{item.price}} AZN)</span> <b onclick="cartItems.splice(${{i}},1);renderCart();" style="color:#ef4444;cursor:pointer;">❌</b></div>`;
                }});
                document.getElementById('cart').innerHTML = html || "{'Qəbz boşdur' if is_az else 'Чек пуст'}";
                document.getElementById('p_name').value = names.join(', ');
                document.getElementById('p_total').value = tot;
                document.getElementById('p_cash').value = tot;
                document.getElementById('p_card').value = 0;
            }}
        </script>
    </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
def admin_page(user_id: int, filter: str = "today", lang: str = "ru"):
    conn = get_db()
    cursor = conn.cursor()
    
    admin = cursor.execute("SELECT * FROM users WHERE id = ? AND role = 'admin'", (user_id,)).fetchone()
    if not admin:
        return RedirectResponse(url="/login")
        
    is_az = lang == "az"
    readers = cursor.execute("SELECT * FROM users WHERE role = 'reader'").fetchall()
    
    # Фильтрация по датам
    today = datetime.now()
    if filter == "week":
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif filter == "month":
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start_date = today.strftime("%Y-%m-%d")
    
    total_all_income = 0
    total_all_cash = 0
    total_all_card = 0
    
    readers_reports = ""
    for r in readers:
        txs = cursor.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND date(created_at) >= ? ORDER BY id DESC", 
            (r["id"], start_date)
        ).fetchall()
        
        inc = sum(t["total_price"] for t in txs)
        cash = sum(t["cash_amount"] for t in txs)
        card = sum(t["card_amount"] for t in txs)
        sal = inc * 0.5
        to_comp = cash - sal
        
        total_all_income += inc
        total_all_cash += cash
        total_all_card += card
        
        tx_details = "".join([f"<li style='font-size:13px; color:var(--subtext);'>{t['item_name']} — {t['total_price']} AZN ({'Nağd' if is_az else 'Нал'}: {t['cash_amount']} | {'Köçürmə' if is_az else 'Перевод'}: {t['card_amount']})</li>" for t in txs])
        
        readers_reports += f"""
        <div style="background:var(--input-bg); padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid var(--border-color);">
            <h4 style="margin:0 0 8px 0; color:#0284c7;">👤 {r['name']} (@{r['username']})</h4>
            <div style="font-size:14px; line-height:1.6;">
                {'Məxaric' if is_az else 'Выручка'}: <b>{inc:.2f} AZN</b> ({'Nağd' if is_az else 'Нал'}: {cash:.2f} | {'Köçürmə' if is_az else 'Карта'}: {card:.2f})<br>
                {'Məvacib' if is_az else 'Зарплата чтеца'} (50%): <b>{sal:.2f} AZN</b><br>
                <span style="color:#16a34a;">{'Şirkətə təhvil veriləcək nağd' if is_az else 'К сдаче в компанию'}: <b>{to_comp:.2f} AZN</b></span>
            </div>
            <details style="margin-top:8px;">
                <summary style="cursor:pointer; color:var(--subtext); font-size:13px;">{'Təfərrüatlar' if is_az else 'Детализация продаж'} ({len(txs)})</summary>
                <ul style="padding-left:18px; margin:5px 0 0 0;">
                    {tx_details if tx_details else f"<li style='font-size:13px; color:var(--subtext);'>{'Satış yoxdur' if is_az else 'Продаж нет'}</li>"}
                </ul>
            </details>
        </div>
        """

    f_today = "active" if filter == "today" else ""
    f_week = "active" if filter == "week" else ""
    f_month = "active" if filter == "month" else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>{'Admin Panel' if is_az else 'Панель Админа'}</title>{COMMON_STYLE}</head>
    <body>
        <div class="top-bar">
            <button class="btn-toggle" onclick="toggleTheme()">🌗 Тема / Mövzu</button>
            <div>
                <a href="/admin?user_id={user_id}&filter={filter}&lang=ru" class="btn-toggle">RU</a>
                <a href="/admin?user_id={user_id}&filter={filter}&lang=az" class="btn-toggle">AZ</a>
            </div>
        </div>

        <div class="card header">
            <h2 style="margin:0; color:#ef4444;">👑 {'Admin Panel' if is_az else 'Панель Админа'}</h2>
            <a href="/login?lang={lang}" style="color:#ef4444; text-decoration:none; font-weight:bold;">{'Çıxış' if is_az else 'Выйти'}</a>
        </div>

        <!-- Блок 3 ФИЛЬТРОВ -->
        <div class="card" style="display:flex; justify-content:space-around; padding:10px;">
            <a href="/admin?user_id={user_id}&filter=today&lang={lang}" class="filter-btn {f_today}">{'Bu gün' if is_az else 'Сегодня'}</a>
            <a href="/admin?user_id={user_id}&filter=week&lang={lang}" class="filter-btn {f_week}">{'Bu həftə' if is_az else 'За неделю'}</a>
            <a href="/admin?user_id={user_id}&filter=month&lang={lang}" class="filter-btn {f_month}">{'Bu ay' if is_az else 'За месяц'}</a>
        </div>

        <div class="card">
            <h3>📊 {'Ümumi nəticələr' if is_az else 'Итоги за выбранный период'}</h3>
            <div class="stat"><span>{'Klinikanın ümumi gəliri' if is_az else 'Вся выручка клиники'}:</span> <b style="color:#0284c7;">{total_all_income:.2f} AZN</b></div>
            <div class="stat"><span>{'Ümumi nağd' if is_az else 'Всего наличными'}:</span> <b>{total_all_cash:.2f} AZN</b></div>
            <div class="stat"><span>{'Ümumi köçürmə' if is_az else 'Всего переводами'}:</span> <b>{total_all_card:.2f} AZN</b></div>
            <div class="stat"><span>{'Şirkətin payı (50%)' if is_az else 'Доля компании (50%)'}:</span> <b style="color:#16a34a;">{total_all_income * 0.5:.2f} AZN</b></div>
        </div>

        <div class="card">
            <h3>👨‍⚕️ {'Xətiblər üzrə hesabat' if is_az else 'Отчёты по каждому чтецу'}</h3>
            {readers_reports if readers_reports else f"<p style='color:var(--subtext);'>{'Qeydiyyatdan keçmiş xətib yoxdur' if is_az else 'Зарегистрированных чтецов пока нет'}</p>"}
        </div>
    </body>
    </html>
    """

@app.post("/add")
def add_tx(
    user_id: int = Form(...),
    type: str = Form(...),
    item_name: str = Form(...),
    total_price: float = Form(...),
    cash_amount: float = Form(0),
    card_amount: float = Form(0),
    lang: str = Form("ru")
):
    if round(cash_amount + card_amount, 2) != round(total_price, 2):
        err = f"Сумма оплаты ({cash_amount + card_amount:.2f}) не совпадает с общей стоимостью ({total_price:.2f})!"
        if lang == "az":
            err = f"Ödəniş məbləği ({cash_amount + card_amount:.2f}) ümumi məbləğlə ({total_price:.2f}) üst-üstə düşmür!"
        return RedirectResponse(url=f"/kassa?user_id={user_id}&error={err}&lang={lang}", status_code=303)

    conn = get_db()
    conn.execute(
        "INSERT INTO transactions (user_id, type, item_name, total_price, cash_amount, card_amount) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, type, item_name, total_price, cash_amount, card_amount)
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/kassa?user_id={user_id}&lang={lang}", status_code=303)

@app.post("/delete/{tx_id}")
def delete_tx(tx_id: int, user_id: int, lang: str = "ru"):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/kassa?user_id={user_id}&lang={lang}", status_code=303)
