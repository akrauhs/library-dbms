from flask import Flask, g, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'library_secret_key'
DATABASE = 'library.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = get_db()
    with open('schema.sql', 'r') as f:
        db.executescript(f.read())
    print("Database initialized.")

def seed_db():
    db = get_db()
    existing = db.execute("SELECT COUNT(*) FROM Genres").fetchone()[0]
    if existing > 0:
        print("Database already seeded, skipping.")
        return
    db.execute("PRAGMA foreign_keys = OFF")
    db.executemany("INSERT OR IGNORE INTO Genres (name) VALUES (?)", [
        ('Fiction',),
        ('Non-Fiction',),
        ('Fantasy',),
        ('Romance',),
        ('Science Fiction',)
    ])
    db.executemany("INSERT OR IGNORE INTO Locations (name, address) VALUES (?, ?)", [
        ("Main Branch",   "123 Library Ave"),
        ("West Branch",   "456 West St"),
        ("East Branch",   "789 East Blvd"),
    ])
    db.executemany("""
        INSERT OR IGNORE INTO Members (name, email, phone)
        VALUES (?, ?, ?)
    """, [
        ("Audrey Krauhs", "akrauhs@email.com", "555-1001"),
        ("Willow Wilson", "wwilson@email.com", "555-1002"),
        ("Olivia McFarren", "omcfarren@email.com", "555-1003"),
        ("Danielle Hewitt", "dhewitt@email.com", "555-1004"),
    ])

    db.executemany("""
        INSERT OR IGNORE INTO Books
            (title, author, isbn, gid, lid, copies, available)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("Ninth House", "Leigh Bardugo", "978-0743273565", 1, 1, 3, 3),
        ("Cien años de soledad", "Gabriel García Márquez", "978-0553380163", 3, 1, 2, 2),
        ("Deep Cuts", "Holly Brickly", "978-0062316097", 4, 2, 4, 4),
        ("Red Rising", "Pierce Brown", "978-0132350884", 3, 2, 2, 2),
        ("Atmosphere", "Taylor Jenkins Reid", "978-1451648539", 5, 3, 3, 3),
        ("It's No Wonder", "Margena A. Christian", "978-0451524935", 1, 3, 5, 5),
    ])

    db.executemany("""
        INSERT OR IGNORE INTO Borrowing
            (bid, mid, borrow_date, due_date, return_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (1, 1, "2025-01-05", "2025-01-19", "2025-01-17", "returned"),
        (2, 2, "2025-01-10", "2025-01-24", None,         "overdue"),
        (3, 3, "2025-02-01", "2025-02-15", "2025-02-14", "returned"),
        (4, 4, "2025-02-10", "2025-02-24", None,         "active"),
        (5, 1, "2025-03-01", "2025-03-15", "2025-03-10", "returned"),
        (6, 2, "2025-03-05", "2025-03-19", None,         "active"),
    ])
    db.execute("""
               UPDATE Books
               SET available = copies - (
                   SELECT COUNT(*) FROM Borrowing WHERE bid = Books.bid AND status != 'returned'
               )
    """)
    db.commit()
    db.execute("PRAGMA foreign_keys = ON")
    print("Database seeded with initial data.")

@app.route('/')
def index():
    return redirect(url_for('books_index'))

@app.route('/books')
def books_index():
    db = get_db()
    books = db.execute("""
        SELECT b.*, b.title, b.author, g.name AS genre, l.name AS location,
               b.copies, b.available
        FROM Books b
        JOIN Genres g ON b.gid = g.gid
        JOIN Locations l ON b.lid = l.lid
        ORDER BY b.title
    """).fetchall()
    return render_template('books/index.html', books=books)

@app.route('/books/new', methods=['GET', 'POST'])
def books_new():
    db = get_db()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        genre_id = request.form['genre_id']
        location_id = request.form['location_id']
        copies = int(request.form['copies'])

        db.execute("""
            INSERT INTO Books (title, author, isbn, gid, lid, copies, available)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, author, isbn, genre_id, location_id, copies, copies))
        db.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('books_index'))
    
    genres = db.execute("SELECT * FROM Genres").fetchall()
    locations = db.execute("SELECT * FROM Locations").fetchall()
    return render_template('books/form.html', book=None, genres=genres, locations=locations)

@app.route('/books/<int:bid>/edit', methods=['GET', 'POST'])
def books_edit(bid):
    db = get_db()
    book = db.execute("SELECT * FROM Books WHERE bid = ?", (bid,)).fetchone()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        genre_id = request.form['genre_id']
        location_id = request.form['location_id']
        copies = int(request.form['copies'])

        db.execute("""
            UPDATE Books
            SET title = ?, author = ?, isbn = ?, gid = ?, lid = ?, copies = ?
            WHERE bid = ?
        """, (title, author, isbn, genre_id, location_id, copies, bid))
        db.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books_index'))

    genres = db.execute("SELECT * FROM Genres").fetchall()
    locations = db.execute("SELECT * FROM Locations").fetchall()
    return render_template('books/form.html', book=book, genres=genres, locations=locations)

@app.route('/books/<int:bid>/delete', methods=['GET', 'POST'])
def books_delete(bid):
    db = get_db()
    book = db.execute("SELECT * FROM Books WHERE bid = ?", (bid,)).fetchone()
    if request.method == 'POST':
        db.execute("BEGIN")
        db.execute("DELETE FROM Borrowing WHERE bid = ?", (bid,))
        db.execute("DELETE FROM Books WHERE bid = ?", (bid,))
        db.commit()
        flash('Book deleted successfully!', 'success')
        return redirect(url_for('books_index'))

    return render_template('books/delete.html', book=book)

@app.route('/reports/borrows')
def report_borrows():
    db = get_db()
    genres = db.execute("SELECT * FROM Genres").fetchall()
    locations = db.execute("SELECT * FROM Locations").fetchall()
    filters, params = [], []

    if request.args.get('from_date'):
        filters.append("borrow_date >= ?")
        params.append(request.args['from_date'])
    if request.args.get('to_date'):
        filters.append("borrow_date <= ?")
        params.append(request.args['to_date'])
    if request.args.get('gid'):
        filters.append("b.gid = ?")
        params.append(request.args['gid'])
    if request.args.get('lid'):
        filters.append("b.lid = ?")
        params.append(request.args['lid'])
    if request.args.get('status'):
        filters.append("status = ?")
        params.append(request.args['status'])
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    borrows = db.execute(f"""
        SELECT br.borrow_id, br.borrow_date, br.due_date, br.return_date, br.status, m.name AS member_name, b.title, b.author, g.name AS genre, l.name AS location, 
            ROUND(julianday(COALESCE(br.return_date, date('now'))) - julianday(br.borrow_date), 1) AS loan_days
        FROM Borrowing br
        JOIN Members m ON br.mid = m.mid
        JOIN Books b ON br.bid = b.bid
        JOIN Genres g ON b.gid = g.gid
        JOIN Locations l ON b.lid = l.lid
        {where_clause}
        ORDER BY borrow_date DESC
    """, params).fetchall()

    stats = db.execute(f"""
        SELECT
            COUNT(*) AS total_borrows,
            ROUND(AVG(julianday(COALESCE(br.return_date, date('now'))) - julianday(br.borrow_date)), 1) AS avg_loan_days,
            SUM(CASE WHEN br.status = 'returned' THEN 1 ELSE 0 END) AS total_returned,
            SUM(CASE WHEN br.status = 'overdue'  THEN 1 ELSE 0 END) AS total_overdue,
            SUM(CASE WHEN br.status = 'borrowed' THEN 1 ELSE 0 END) AS total_active,
            ROUND(100.0 * SUM(CASE WHEN br.status = 'returned' THEN 1 ELSE 0 END) / MAX(COUNT(*), 1), 1) AS return_rate
        FROM Borrowing br
        JOIN Books b ON br.bid = b.bid
        {where_clause}
    """, params).fetchone()

    return render_template('reports/borrows.html', borrows=borrows, stats=stats, genres=genres, locations=locations, args=request.args)

if __name__ == '__main__':
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True)
    print("Setup complete.")