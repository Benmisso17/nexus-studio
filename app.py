from flask import Flask, render_template, request, redirect, session
import libsql_client

app = Flask(__name__)
app.secret_key = 'nexus_secret_key_2026'

TURSO_URL = "https://ben-misso-benmisso.aws-eu-central-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTM4MTQxNTgsImlkIjoiMDFhMTg4ZWYtODcwMS03MDc3LWI0NTEtMjMzNzNhMjg1MTY3Iiwia2lkIjoiNVBZY3ZfY3BqS09jdUFPaFhYT2pkVld2bUhBd18tMnlabS1teGtSNjVqOCIsInJpZCI6ImY3MmM5YjQ5LTQxYWUtNDI0MS05OGYzLWQzOGU0NjU4M2UxZSJ9.fRNKY_Hf89WsNPkoLQ1_rDDLAisuYiEuaam2ukh9dJgONZ4QborbJpAqoHIM1Fz2vZRV3iOSBI70etkix_aoBQ"

def init_db():
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        client.execute("""
            CREATE TABLE IF NOT EXISTS studio_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT, icon TEXT, image_url TEXT, title TEXT, description TEXT, tags TEXT
            )
        """)
        try: client.execute("ALTER TABLE studio_projects ADD COLUMN image_url TEXT")
        except: pass
        
        client.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, message TEXT
            )
        """)

def get_projects():
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        result = client.execute("SELECT id, icon, image_url, title, description, tags FROM studio_projects")
        return [{"id": r[0], "icon": r[1], "image_url": r[2], "title": r[3], "description": r[4], "tags": r[5].split(",") if r[5] else []} for r in result.rows]

def get_messages():
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        result = client.execute("SELECT id, name, email, message FROM messages ORDER BY id DESC")
        return [{"id": r[0], "name": r[1], "email": r[2], "message": r[3]} for r in result.rows]

@app.route('/')
def home():
    init_db()
    return render_template('index.html', projects=get_projects())

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name, email, message = request.form['name'], request.form['email'], request.form['message']
        with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
            client.execute("INSERT INTO messages (name, email, message) VALUES (?, ?, ?)", (name, email, message))
        return "<body style='background:#0a0512;color:white;font-family:sans-serif;text-align:center;padding-top:20%;'><h2>تم إرسال رسالتك بنجاح! شكراً لتواصلك.</h2><div><a href='/' style='color:#06b6d4;text-decoration:none;'>العودة للرئيسية</a></div></body>"
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form['password'] == 'misso12345':
        session['logged_in'] = True
        return redirect('/admin')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'): return redirect('/login')
    if request.method == 'POST':
        icon, image_url, title, description, tags = request.form['icon'], request.form.get('image_url', ''), request.form['title'], request.form['description'], request.form['tags']
        with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
            client.execute("INSERT INTO studio_projects (icon, image_url, title, description, tags) VALUES (?, ?, ?, ?, ?)", (icon, image_url, title, description, tags))
        return redirect('/')
    return render_template('admin.html')

@app.route('/manage')
def manage():
    if not session.get('logged_in'): return redirect('/login')
    return render_template('manage.html', projects=get_projects())

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('logged_in'): return redirect('/login')
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        client.execute("DELETE FROM studio_projects WHERE id = ?", (id,))
    return redirect('/manage')

# --- مسارات الرسائل الجديدة ---
@app.route('/messages')
def messages():
    if not session.get('logged_in'): return redirect('/login')
    return render_template('messages.html', messages=get_messages())

@app.route('/delete_message/<int:id>')
def delete_message(id):
    if not session.get('logged_in'): return redirect('/login')
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        client.execute("DELETE FROM messages WHERE id = ?", (id,))
    return redirect('/messages')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
