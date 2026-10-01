import os
import random
from datetime import datetime, timedelta
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DB", "ecommerce_db")


def get_connection():
    # First connect without DB to ensure DB exists
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;")
    conn.close()

    # Reconnect targeting the database
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor
    )


def build_schema(cursor):
    """Creates a complex relational eCommerce schema."""
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    tables = [
        "inventory_logs", "product_reviews", "payments", 
        "order_items", "orders", "discounts", "products", 
        "categories", "customers"
    ]
    for tbl in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {tbl};")

    # 1. Categories (Hierarchical parent-child)
    cursor.execute("""
    CREATE TABLE categories (
        category_id INT AUTO_INCREMENT PRIMARY KEY,
        category_name VARCHAR(50) NOT NULL,
        parent_id INT NULL,
        FOREIGN KEY (parent_id) REFERENCES categories(category_id) ON DELETE SET NULL
    );
    """)

    # 2. Customers
    cursor.execute("""
    CREATE TABLE customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        city VARCHAR(50) DEFAULT 'New York',
        country VARCHAR(50) DEFAULT 'USA',
        loyalty_tier ENUM('Bronze', 'Silver', 'Gold', 'Platinum') DEFAULT 'Bronze',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Products
    cursor.execute("""
    CREATE TABLE products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        category_id INT NULL,
        category_name VARCHAR(50) NOT NULL,
        product_name VARCHAR(100) NOT NULL,
        sku VARCHAR(30) UNIQUE,
        cost_price DECIMAL(10, 2) NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        stock_quantity INT DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
    );
    """)

    # 4. Discounts / Coupon codes
    cursor.execute("""
    CREATE TABLE discounts (
        discount_id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(20) UNIQUE NOT NULL,
        discount_pct DECIMAL(5, 2) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE
    );
    """)

    # 5. Orders
    cursor.execute("""
    CREATE TABLE orders (
        order_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT NOT NULL,
        discount_id INT NULL,
        order_date DATETIME NOT NULL,
        status ENUM('completed', 'shipped', 'pending', 'cancelled', 'refunded') DEFAULT 'pending',
        shipping_fee DECIMAL(10, 2) DEFAULT 0.00,
        total_amount DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
        FOREIGN KEY (discount_id) REFERENCES discounts(discount_id) ON DELETE SET NULL
    );
    """)

    # 6. Order Items
    cursor.execute("""
    CREATE TABLE order_items (
        item_id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    );
    """)

    # 7. Payments
    cursor.execute("""
    CREATE TABLE payments (
        payment_id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        payment_method ENUM('Credit Card', 'PayPal', 'Apple Pay', 'Bank Transfer') NOT NULL,
        payment_status ENUM('success', 'failed', 'refunded') DEFAULT 'success',
        transaction_reference VARCHAR(64) UNIQUE NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        paid_at DATETIME NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
    );
    """)

    # 8. Product Reviews
    cursor.execute("""
    CREATE TABLE product_reviews (
        review_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        customer_id INT NOT NULL,
        rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
        review_title VARCHAR(120),
        review_body TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
    );
    """)

    # 9. Inventory Logs (Tracking stock in and out)
    cursor.execute("""
    CREATE TABLE inventory_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        change_quantity INT NOT NULL,
        reason ENUM('restock', 'order_sale', 'damaged', 'customer_return') NOT NULL,
        logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("✓ Schema initialized successfully.")


def seed_data(cursor):
    """Populates existing base records alongside extended complex datasets."""

    # 1. Categories
    cursor.execute("""
    INSERT INTO categories (category_id, category_name, parent_id) VALUES
    (1, 'Electronics', NULL),
    (2, 'Kitchen', NULL),
    (3, 'Office Supplies', NULL),
    (4, 'Audio & Accessories', 1),
    (5, 'Computer Peripherals', 1),
    (6, 'Coffee & Tea', 2);
    """)

    # 2. Discounts
    cursor.execute("""
    INSERT INTO discounts (discount_id, code, discount_pct, is_active) VALUES
    (1, 'WELCOME10', 10.00, TRUE),
    (2, 'SAVE20', 20.00, TRUE),
    (3, 'VIP25', 25.00, TRUE),
    (4, 'EXPIRED50', 50.00, FALSE);
    """)

    # 3. Base Customers (Original 5) + 45 Extended Customers
    initial_customers = [
        (1, 'Alice', 'Smith', 'alice.smith@example.com', 'New York', 'USA', 'Platinum', '2024-01-15 08:30:00'),
        (2, 'Bob', 'Johnson', 'bob.johnson@example.com', 'Toronto', 'Canada', 'Gold', '2024-02-10 11:20:00'),
        (3, 'Charlie', 'Brown', 'charlie.brown@example.com', 'Chicago', 'USA', 'Silver', '2024-02-22 14:15:00'),
        (4, 'Diana', 'Prince', 'diana.prince@example.com', 'London', 'UK', 'Bronze', '2024-03-01 09:45:00'),
        (5, 'Evan', 'Wright', 'evan.wright@example.com', 'Berlin', 'Germany', 'Bronze', '2024-03-12 16:00:00'),
    ]

    first_names = ['Liam', 'Emma', 'Noah', 'Olivia', 'James', 'Sophia', 'Lucas', 'Mia', 'Benjamin', 'Amelia']
    last_names = ['Miller', 'Davis', 'Wilson', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee']
    cities = ['Austin', 'Seattle', 'San Francisco', 'Boston', 'Denver', 'Miami', 'Atlanta', 'Sydney', 'Tokyo']
    tiers = ['Bronze', 'Silver', 'Gold', 'Platinum']

    more_customers = []
    for cid in range(6, 51):
        f = random.choice(first_names)
        l = random.choice(last_names)
        email = f"{f.lower()}.{l.lower()}{cid}@example.com"
        created = datetime.now() - timedelta(days=random.randint(40, 500))
        more_customers.append((
            cid, f, l, email, random.choice(cities),
            random.choice(['USA', 'Canada', 'UK', 'Australia']),
            random.choice(tiers),
            created.strftime('%Y-%m-%d %H:%M:%S')
        ))

    cursor.executemany("""
    INSERT INTO customers (customer_id, first_name, last_name, email, city, country, loyalty_tier, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, initial_customers + more_customers)

    # 4. Products (Original 6 + 10 Additional)
    initial_products = [
        (101, 5, 'Electronics', 'Ergonomic Mechanical Keyboard', 'KB-ERG-101', 65.00, 129.99, 45),
        (102, 4, 'Electronics', 'Wireless Noise-Canceling Headphones', 'HP-WNC-102', 110.00, 199.50, 28),
        (103, 5, 'Electronics', 'Ultra-Wide Gaming Monitor 34"', 'MON-UW-103', 280.00, 449.00, 12),
        (104, 6, 'Kitchen', 'Ceramic Pour-Over Coffee Dripper', 'KIT-CD-104', 11.50, 24.95, 120),
        (105, 6, 'Kitchen', 'Gooseneck Temperature Kettle', 'KIT-GK-105', 38.00, 68.50, 35),
        (106, 3, 'Office Supplies', 'Adjustable Standing Desk Mat', 'OFF-DM-106', 20.00, 45.00, 75),
    ]

    extra_products = [
        (107, 5, 'Electronics', 'Wireless Vertical Ergonomic Mouse', 'MOU-VERT-107', 22.00, 49.99, 80),
        (108, 4, 'Electronics', 'Desktop USB Condenser Microphone', 'MIC-USB-108', 42.00, 89.99, 40),
        (109, 5, 'Electronics', '4K High-Res Streaming Webcam', 'CAM-4K-109', 55.00, 119.00, 25),
        (110, 6, 'Kitchen', 'Stainless Steel Manual Burr Grinder', 'KIT-GR-110', 18.00, 39.50, 95),
        (111, 6, 'Kitchen', 'AeroPress Coffee Maker Kit', 'KIT-AP-111', 19.00, 42.00, 60),
        (112, 3, 'Office Supplies', 'Dual Monitor Arm Mount', 'OFF-MA-112', 30.00, 74.99, 30),
        (113, 3, 'Office Supplies', 'Cable Management Under-Desk Tray', 'OFF-CT-113', 9.00, 22.50, 110),
        (114, 5, 'Electronics', 'Aluminium Laptop Stand (Foldable)', 'LAP-ST-114', 14.00, 34.99, 85),
        (115, 6, 'Kitchen', 'Double-Walled Espresso Glasses (Set of 4)', 'KIT-GL-115', 8.50, 19.99, 150),
        (116, 4, 'Electronics', 'Bluetooth Bookshelf Speakers (Pair)', 'SPK-BT-116', 75.00, 159.00, 18),
    ]

    cursor.executemany("""
    INSERT INTO products (product_id, category_id, category_name, product_name, sku, cost_price, price, stock_quantity)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, initial_products + extra_products)

    # 5. Base Orders (Original 7) + Order Items
    cursor.execute("""
    INSERT INTO orders (order_id, customer_id, discount_id, order_date, status, shipping_fee, total_amount) VALUES
    (1001, 1, 1, '2024-04-01 10:15:00', 'completed', 0.00, 329.49),
    (1002, 2, NULL, '2024-04-03 12:40:00', 'completed', 10.00, 449.00),
    (1003, 1, NULL, '2024-04-10 17:25:00', 'completed', 0.00, 93.45),
    (1004, 3, 2, '2024-04-15 08:50:00', 'shipped', 5.00, 129.99),
    (1005, 4, NULL, '2024-04-18 14:10:00', 'pending', 15.00, 717.00),
    (1006, 5, NULL, '2024-04-20 16:30:00', 'cancelled', 0.00, 68.50),
    (1007, 2, 1, '2024-05-02 11:05:00', 'completed', 0.00, 154.94);
    """)

    cursor.execute("""
    INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price) VALUES
    (1, 1001, 101, 1, 129.99),
    (2, 1001, 102, 1, 199.50),
    (3, 1002, 103, 1, 449.00),
    (4, 1003, 104, 1, 24.95),
    (5, 1003, 105, 1, 68.50),
    (6, 1004, 101, 1, 129.99),
    (7, 1005, 102, 1, 199.50),
    (8, 1005, 103, 1, 449.00),
    (9, 1005, 106, 1, 45.00),
    (10, 1006, 105, 1, 68.50),
    (11, 1007, 101, 1, 129.99),
    (12, 1007, 104, 1, 24.95);
    """)

    # 6. Generate 60+ Realistic New Orders & Line Items
    prod_lookup = {
        p[0]: float(p[6]) for p in (initial_products + extra_products)
    }
    
    order_id_seq = 1008
    item_id_seq = 13
    extended_orders = []
    extended_items = []
    payments = []
    inventory_logs = []

    statuses = ['completed', 'completed', 'completed', 'shipped', 'pending', 'refunded', 'cancelled']
    methods = ['Credit Card', 'PayPal', 'Apple Pay', 'Bank Transfer']

    # Initial payments for first 7 orders
    for o_id, amt, dt in [
        (1001, 329.49, '2024-04-01 10:16:00'),
        (1002, 449.00, '2024-04-03 12:41:00'),
        (1003, 93.45, '2024-04-10 17:26:00'),
        (1004, 129.99, '2024-04-15 08:52:00'),
        (1007, 154.94, '2024-05-02 11:06:00'),
    ]:
        payments.append((
            o_id, random.choice(methods), 'success', f"TXN-{o_id}-{random.randint(1000, 9999)}", amt, dt
        ))

    for cust_id in range(1, 51):
        # 1 to 3 orders per customer
        for _ in range(random.randint(1, 3)):
            num_items = random.randint(1, 3)
            picked_products = random.sample(list(prod_lookup.keys()), num_items)
            subtotal = 0.0

            for pid in picked_products:
                qty = random.randint(1, 2)
                u_price = prod_lookup[pid]
                subtotal += (u_price * qty)
                extended_items.append((item_id_seq, order_id_seq, pid, qty, u_price))
                
                # Add inventory log
                inventory_logs.append((
                    pid, -qty, 'order_sale',
                    (datetime.now() - timedelta(days=random.randint(1, 120))).strftime('%Y-%m-%d %H:%M:%S')
                ))
                item_id_seq += 1

            status = random.choice(statuses)
            discount_id = random.choice([None, 1, 2, 3])
            disc_mult = 0.90 if discount_id == 1 else (0.80 if discount_id == 2 else 1.0)
            shipping = 0.00 if subtotal > 150 else 9.99
            final_total = round((subtotal * disc_mult) + shipping, 2)
            
            o_date = datetime.now() - timedelta(days=random.randint(2, 180), hours=random.randint(1, 12))
            date_str = o_date.strftime('%Y-%m-%d %H:%M:%S')

            extended_orders.append((
                order_id_seq, cust_id, discount_id, date_str, status, shipping, final_total
            ))

            if status in ['completed', 'shipped']:
                payments.append((
                    order_id_seq, random.choice(methods), 'success',
                    f"TXN-{order_id_seq}-{random.randint(1000, 9999)}", final_total, date_str
                ))
            elif status == 'refunded':
                payments.append((
                    order_id_seq, random.choice(methods), 'refunded',
                    f"TXN-{order_id_seq}-{random.randint(1000, 9999)}", final_total, date_str
                ))

            order_id_seq += 1

    cursor.executemany("""
    INSERT INTO orders (order_id, customer_id, discount_id, order_date, status, shipping_fee, total_amount)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, extended_orders)

    cursor.executemany("""
    INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price)
    VALUES (%s, %s, %s, %s, %s);
    """, extended_items)

    cursor.executemany("""
    INSERT INTO payments (order_id, payment_method, payment_status, transaction_reference, amount, paid_at)
    VALUES (%s, %s, %s, %s, %s, %s);
    """, payments)

    # 7. Reviews
    reviews_data = [
        (101, 1, 5, "Best mechanical keyboard!", "Crisp click and excellent wrist posture."),
        (102, 1, 4, "Great noise cancelling", "Battery lasts long, but earcups get a bit warm."),
        (103, 2, 5, "Insane screen real estate", "Super smooth refresh rate for games and coding."),
        (104, 3, 4, "Classic coffee dripper", "Reliable and easy to clean every morning."),
        (105, 5, 2, "Kettle lid was sticky", "Heats water fast, but lid was difficult to remove."),
    ]
    for _ in range(40):
        reviews_data.append((
            random.choice(list(prod_lookup.keys())),
            random.randint(1, 50),
            random.randint(1, 5),
            "Verified Purchase Review",
            "Item functioned as advertised in the technical specifications.",
            (datetime.now() - timedelta(days=random.randint(5, 140))).strftime('%Y-%m-%d %H:%M:%S')
        ))

    # Handle varying tuple lengths gracefully
    for r in reviews_data:
        if len(r) == 5:
            cursor.execute("""
            INSERT INTO product_reviews (product_id, customer_id, rating, review_title, review_body)
            VALUES (%s, %s, %s, %s, %s);
            """, r)
        else:
            cursor.execute("""
            INSERT INTO product_reviews (product_id, customer_id, rating, review_title, review_body, created_at)
            VALUES (%s, %s, %s, %s, %s, %s);
            """, r)

    # 8. Add Restock logs
    for p_id in prod_lookup.keys():
        inventory_logs.append((
            p_id, random.randint(50, 100), 'restock',
            (datetime.now() - timedelta(days=random.randint(150, 200))).strftime('%Y-%m-%d %H:%M:%S')
        ))

    cursor.executemany("""
    INSERT INTO inventory_logs (product_id, change_quantity, reason, logged_at)
    VALUES (%s, %s, %s, %s);
    """, inventory_logs)

    print(f"✓ Seeded 50 customers, 16 products, {order_id_seq - 1001} orders, payments, reviews, and logs.")


def main():
    print(f"Connecting to MySQL ({DB_HOST}:{DB_PORT}/{DB_NAME})...")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            build_schema(cursor)
            seed_data(cursor)
        conn.commit()
        print("🎉 Database successfully seeded and ready for your SQL Agent!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error occurred during migration: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    main()