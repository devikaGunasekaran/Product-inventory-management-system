from flask import Flask, render_template, request, redirect, url_for,flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key" 

# ✅ MySQL Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="2025",
    database="product_manage"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def index():
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    cursor.execute("SELECT * FROM suppliers")
    suppliers = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_id, p.product_name, p.price, p.quantity_in_stock, 
               c.category_id, c.category_name, s.supplier_id, s.supplier_name 
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
    """)
    products = cursor.fetchall()

    cursor.execute("""
        SELECT sa.sale_id, sa.product_id, sa.quantity_sold, sa.sale_date, 
               p.product_name, (sa.quantity_sold * p.price) AS total_amount
        FROM sales sa
        JOIN products p ON sa.product_id = p.product_id
    """)
    sales = cursor.fetchall()

    return render_template("index.html", categories=categories, suppliers=suppliers, products=products, sales=sales)

# ✅ CRUD: Categories
@app.route('/add_category', methods=['POST'])
def add_category():
    category_name = request.form['category_name']
    cursor.execute("INSERT INTO categories (category_name) VALUES (%s)", (category_name,))
    db.commit()
    return redirect(url_for('index'))

@app.route('/update_category/<int:category_id>', methods=['POST'])
def update_category(category_id):
    category_name = request.form['category_name']
    cursor.execute("UPDATE categories SET category_name = %s WHERE category_id = %s", (category_name, category_id))
    db.commit()
    return redirect(url_for('index'))

@app.route('/delete_category/<int:category_id>')
def delete_category(category_id):
    cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
    db.commit()
    return redirect(url_for('index'))

# ✅ CRUD: Suppliers
@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    supplier_name = request.form['supplier_name']
    email = request.form['email']
    contact_number = request.form['contact_number']
    address = request.form['address']
    
    cursor.execute("""
        INSERT INTO suppliers (supplier_name, email, contact_number, address) 
        VALUES (%s, %s, %s, %s)
    """, (supplier_name, email, contact_number, address))
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/update_supplier/<int:supplier_id>', methods=['POST'])
def update_supplier(supplier_id):
    supplier_name = request.form['supplier_name']
    email = request.form['email']
    contact_number = request.form['contact_number']
    address = request.form['address']

    cursor.execute("""
        UPDATE suppliers 
        SET supplier_name = %s, email = %s, contact_number = %s, address = %s 
        WHERE supplier_id = %s
    """, (supplier_name, email, contact_number, address, supplier_id))
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/delete_supplier/<int:supplier_id>')
def delete_supplier(supplier_id):
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE supplier_id = %s", (supplier_id,))
    product_result = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) as count FROM sales 
        JOIN products ON sales.product_id = products.product_id 
        WHERE products.supplier_id = %s
    """, (supplier_id,))
    sales_result = cursor.fetchone()

    if product_result['count'] > 0 or sales_result['count'] > 0:
        flash("❌ Supplier cannot be deleted as there are products or sales associated with it!", "error")
    else:
        cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s", (supplier_id,))
        db.commit()
        flash("✅ Supplier deleted successfully!", "success")

    return redirect(url_for('index'))

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        print("Received form data:", request.form.to_dict())  # Debugging

        product_name = request.form.get('product_name')
        price = request.form.get('price')
        quantity_in_stock = request.form.get('quantity_in_stock')
        category_id = request.form.get('category_id')
        supplier_id = request.form.get('supplier_id')

        # Ensure all required fields are present
        if not all([product_name, price, quantity_in_stock, category_id, supplier_id]):
            flash("❌ All fields are required!", "error")
            return redirect(url_for('index'))

        # Ensure IDs are integers
        try:
            category_id = int(category_id)
            supplier_id = int(supplier_id)
            price = float(price)
            quantity_in_stock = int(quantity_in_stock)
        except ValueError:
            flash("❌ Invalid data format!", "error")
            return redirect(url_for('index'))

        # Insert product
        sql_query = """
            INSERT INTO products (product_name, price, quantity_in_stock, category_id, supplier_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (product_name, price, quantity_in_stock, category_id, supplier_id)
        
        cursor.execute(sql_query, values)
        db.commit()

        print("✅ Product inserted successfully!")  # Debugging success
        flash("✅ Product added successfully!", "success")
        return redirect(url_for('index'))

    except Exception as e:
        print(f"❌ Error inserting product: {e}")  # Debugging error
        db.rollback()  # Undo changes if insertion fails
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    product_name = request.form['product_name']
    price = request.form['price']
    quantity_in_stock = request.form['quantity_in_stock']
    category_name = request.form['category_name']
    supplier_name = request.form['supplier_name']

    # Fetch category_id based on category_name
    cursor.execute("SELECT category_id FROM categories WHERE category_name = %s", (category_name,))
    category = cursor.fetchone()

    # Fetch supplier_id based on supplier_name
    cursor.execute("SELECT supplier_id FROM suppliers WHERE supplier_name = %s", (supplier_name,))
    supplier = cursor.fetchone()

    # Handle invalid category or supplier names
    if not category or not supplier:
        flash("❌ Invalid category or supplier selected!", "error")
        return redirect(url_for('index'))

    category_id = category['category_id']
    supplier_id = supplier['supplier_id']

    # Update product with resolved category_id and supplier_id
    cursor.execute("""
        UPDATE products 
        SET product_name=%s, price=%s, quantity_in_stock=%s, category_id=%s, supplier_id=%s 
        WHERE product_id=%s
    """, (product_name, price, quantity_in_stock, category_id, supplier_id, product_id))
    db.commit()

    flash("✅ Product updated successfully!", "success")
    return redirect(url_for('index'))

@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
    db.commit()
    return redirect(url_for('index'))

# ✅ CRUD: Sales
@app.route('/add_sale', methods=['POST'])
def add_sale():
    product_id = request.form['product_id']
    quantity_sold = int(request.form['quantity_sold'])

   
    cursor.execute("SELECT price, quantity_in_stock FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    if product and product['quantity_in_stock'] >= quantity_sold:
        total_amount = float(product['price']) * quantity_sold
        sale_date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO sales (product_id, quantity_sold, sale_date, total_amount)
            VALUES (%s, %s, %s, %s)
        """, (product_id, quantity_sold, sale_date, total_amount))

        # Reduce stock
        new_quantity = product['quantity_in_stock'] - quantity_sold
        cursor.execute("UPDATE products SET quantity_in_stock = %s WHERE product_id = %s", (new_quantity, product_id))

        db.commit()

    return redirect(url_for('index'))

@app.route('/update_sale/<int:sale_id>', methods=['POST'])
def update_sale(sale_id):
    new_product_id = request.form['product_id']
    new_quantity_sold = int(request.form['quantity_sold'])

    
    cursor.execute("SELECT product_id, quantity_sold FROM sales WHERE sale_id = %s", (sale_id,))
    old_sale = cursor.fetchone()

    if old_sale:
        old_product_id = old_sale['product_id']
        old_quantity_sold = old_sale['quantity_sold']

        
        cursor.execute("UPDATE products SET quantity_in_stock = quantity_in_stock + %s WHERE product_id = %s",
                       (old_quantity_sold, old_product_id))

        
        cursor.execute("UPDATE products SET quantity_in_stock = quantity_in_stock - %s WHERE product_id = %s",
                       (new_quantity_sold, new_product_id))

        
        cursor.execute("UPDATE sales SET product_id = %s, quantity_sold = %s, sale_date = %s WHERE sale_id = %s",
                       (new_product_id, new_quantity_sold, datetime.now(), sale_id))
        db.commit()

    return redirect(url_for('index'))


@app.route('/delete_sale/<int:sale_id>')
def delete_sale(sale_id):
    cursor.execute("SELECT product_id, quantity_sold FROM sales WHERE sale_id = %s", (sale_id,))
    sale = cursor.fetchone()

    if sale:
        product_id = sale['product_id']
        quantity_sold = sale['quantity_sold']

        
        cursor.execute("UPDATE products SET quantity_in_stock = quantity_in_stock + %s WHERE product_id = %s",
                       (quantity_sold, product_id))

        cursor.execute("DELETE FROM sales WHERE sale_id = %s", (sale_id,))
        db.commit()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
