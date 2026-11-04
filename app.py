from flask import Flask, render_template, request, redirect, session, flash
import libsql_client

app = Flask(__name__)
app.secret_key = 'nexus_secret_key_2026'

TURSO_URL = "https://ben-misso-benmisso.aws-eu-central-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTM4MTQxNTgsImlkIjoiMDFhMTg4ZWYtODcwMS03MDc3LWI0NTEtMjMzNzNhMjg1MTY3Iiwia2lkIjoiNVBZY3ZfY3BqS09jdUFPaFhYT2pkVld2bUhBd18tMnlabS1teGtSNjVqOCIsInJpZCI6ImY3MmM5YjQ5LTQxYWUtNDI0MS05OGYzLWQzOGU0NjU4M2UxZSJ9.fRNKY_Hf89WsNPkoLQ1_rDDLAisuYiEuaam2ukh9dJgONZ4QborbJpAqoHIM1Fz2vZRV3iOSBI70etkix_aoBQ"

def init_db():
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        # جدول المشاريع
        client.execute("""
            CREATE TABLE IF NOT EXISTS studio_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT, icon TEXT, image_url TEXT, title TEXT, description TEXT, tags TEXT
            )
        """)
        try: client.execute("ALTER TABLE studio_projects ADD COLUMN image_url TEXT")
        except: pass
        
        # جدول رسائل التواصل الجديد
        client.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, message TEXT
            )
        """)

def get_projects():
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        result = client.execute("SELECT id, icon, image_url, title, description, tags FROM studio_projects")
        projects = []
        for row in result.rows:
            projects.append({"id": row[0], "icon": row[1], "image_url": row[2], "title": row[3], "description": row[4], "tags": row[5].split(",") if row[5] else []})
        return projects

@app.route('/')
def home():
    init_db()
    projects_data = get_projects()
    return render_template('index.html', projects=projects_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
            client.execute("INSERT INTO messages (name, email, message) VALUES (?, ?, ?)", (name, email, message))
        return "<body style='background:#0a0512;color:white;font-family:sans-serif;text-align:center;padding-top:20%;'><h2>تم إرسال رسالتك بنجاح! شكراً لتواصلك.</h2><div><a href='/' style='color:#06b6d4;text-decoration:none;'>العودة للرئيسية</a></div></body>"
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == 'misso12345':
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
    projects_data = get_projects()
    return render_template('manage.html', projects=projects_data)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('logged_in'): return redirect('/login')
    with libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN) as client:
        client.execute("DELETE FROM studio_projects WHERE id = ?", (id,))
    return redirect('/manage')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
