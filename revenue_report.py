# ============================================================
# HOTFIX — DATA-210: Quarterly Revenue Report Wrong Totals
# Priority: P0 | SLA: 15 minutes | Reporter: CFO Office
# ============================================================
#
# The quarterly revenue report sent to the board showed wrong totals.
# The SQL query double-counts orders that have multiple line items.
#
# 3 line items get counted 3 times in the revenue total.
#
# ============================================================

import sqlite3

def setup_db():
    conn = sqlite3.connect(':memory:')
    conn.executescript('''
        CREATE TABLE orders (id INTEGER PRIMARY KEY, amount DECIMAL, quarter TEXT);
        CREATE TABLE order_items (order_id INTEGER, product TEXT, qty INTEGER);
        INSERT INTO orders VALUES (1, 100.00, 'Q1'), (2, 200.00, 'Q1'), (3, 150.00, 'Q2');
        INSERT INTO order_items VALUES (1, 'Widget', 2), (1, 'Gadget', 1);
        INSERT INTO order_items VALUES (2, 'Widget', 3);
        INSERT INTO order_items VALUES (3, 'Gadget', 1), (3, 'Bolt', 5), (3, 'Nut', 10);
    ''')
    return conn

def get_quarterly_revenue(conn):
    # Order 1 has 2 items -> counted as 200 instead of 100
    # Order 3 has 3 items -> counted as 450 instead of 150
    cursor = conn.execute('''
        SELECT o.quarter, SUM(o.amount) as total_revenue
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        GROUP BY o.quarter
    ''')
    return {row[0]: row[1] for row in cursor.fetchall()}

# Expected: Q1 = 300.00 (100 + 200), Q2 = 150.00
# Actual (buggy): Q1 = 500.00 (200 + 200 + 100), Q2 = 450.00 (150 * 3)
if __name__ == '__main__':
    conn = setup_db()
    result = get_quarterly_revenue(conn)
    print(f"Q1 Revenue: {result.get('Q1')} (expected 300.00)")
    print(f"Q2 Revenue: {result.get('Q2')} (expected 150.00)")
