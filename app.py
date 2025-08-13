from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
import csv
import os
from pyodbc import IntegrityError

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# =============================
# Database Connection
# =============================
server = 'DESKTOP-Q664GNP\\SQLEXPRESS'
database = 'trade-order'
driver = '{ODBC Driver 11 for SQL Server}'
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

def get_db_connection():
    return pyodbc.connect(connection_string)

# =============================
# Export Orders to CSV
# =============================
def export_user_orders(user_id, orders, columns):
    filename = f'orders_user_{user_id}.csv'
    export_folder = r"D:\myorders"
    os.makedirs(export_folder, exist_ok=True)
    csv_path = os.path.join(export_folder, filename)
    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(orders)

# =============================
# Routes
# =============================
@app.route('/')
def home():
    return redirect(url_for('login'))

# ----------------- Register -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Customers (Name, Email, PasswordHash) VALUES (?, ?, ?)",
                           (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except IntegrityError:
            return render_template('register.html', error="⚠️ This email is already registered.")
    return render_template('register.html')

# ----------------- User Login -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CustomerID, Name, PasswordHash, IsAdmin FROM Customers WHERE Email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password_input):
            if user[3] == 0:
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['is_admin'] = False
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Admins must login through the Admin Login page.")
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

# ----------------- Admin Login -----------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CustomerID, Name, PasswordHash, IsAdmin FROM Customers WHERE Email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password_input):
            if user[3] == 1:
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['is_admin'] = True
                return redirect(url_for('admin'))
            else:
                return render_template('admin_login.html', error="You are not an admin.")
        else:
            return render_template('admin_login.html', error="Invalid credentials.")
    return render_template('admin_login.html')

# ----------------- Logout -----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------- Customer Dashboard -----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.OrderID, o.Quantity, o.BuyPrice, o.SellPrice, o.Status, o.OrderDate, p.ProductName
        FROM Orders o
        JOIN Products p ON o.ProductID = p.ProductID
        WHERE o.CustomerID = ?
    """, (session['user_id'],))
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    orders = [dict(zip(columns, row)) for row in rows]
    conn.close()

    export_user_orders(session['user_id'], orders, columns)
    return render_template('dashboard.html', customer_name=session['user_name'], orders=orders)

# ----------------- Add Order -----------------
@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = request.form['quantity']
        buy_price = request.form['buy_price']
        sell_price = request.form.get('sell_price') or None
        status = request.form['status']

        cursor.execute("""
            INSERT INTO Orders (CustomerID, ProductID, Quantity, BuyPrice, SellPrice, Status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session['user_id'], product_id, quantity, buy_price, sell_price, status))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT ProductID, ProductName FROM Products")
    products = cursor.fetchall()
    conn.close()

    return render_template('add_order.html', products=products)

# ----------------- Edit Order -----------------
@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        quantity = request.form['quantity']
        buy_price = request.form['buy_price']
        sell_price = request.form.get('sell_price') or None
        status = request.form['status']

        cursor.execute("""
            UPDATE Orders
            SET Quantity = ?, BuyPrice = ?, SellPrice = ?, Status = ?
            WHERE OrderID = ? AND CustomerID = ?
        """, (quantity, buy_price, sell_price, status, order_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    cursor.execute("""
        SELECT OrderID, ProductID, Quantity, BuyPrice, SellPrice, Status
        FROM Orders
        WHERE OrderID = ? AND CustomerID = ?
    """, (order_id, session['user_id']))
    order = cursor.fetchone()

    cursor.execute("SELECT ProductID, ProductName FROM Products")
    products = cursor.fetchall()
    conn.close()

    return render_template('edit_order.html', order=order, products=products)

# ----------------- Delete Order -----------------
@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Orders WHERE OrderID = ? AND CustomerID = ?", (order_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# ----------------- Admin Dashboard -----------------
@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.OrderID, c.Name, p.ProductName, o.Quantity, o.BuyPrice, o.SellPrice, o.Status, o.OrderDate
        FROM Orders o
        JOIN Customers c ON o.CustomerID = c.CustomerID
        JOIN Products p ON o.ProductID = p.ProductID
        ORDER BY o.OrderDate DESC
    """)
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in rows]
    conn.close()

    return render_template('admin_dashboard.html', data=data)

# ----------------- Download CSV -----------------
@app.route('/download_orders')
def download_orders():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    filename = f'orders_user_{session["user_id"]}.csv'
    filepath = os.path.join(r"D:\myorders", filename)

    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return "No CSV file found. Please add an order first."

# =============================
# Run App
# =============================
if __name__ == '__main__':
    app.run(debug=True)
