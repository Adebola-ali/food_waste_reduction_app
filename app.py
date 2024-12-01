# from flask import Flask, jsonify, request
# import mysql.connector
# from mysql.connector import IntegrityError

# app = Flask(__name__)

# # Database connection
# def get_db_connection():
#     return mysql.connector.connect(
#         host="localhost",
#         user="root",          # Replace with your MySQL username
#         password="bodbcfGmysql@30",  # Replace with your MySQL password
#         database="food_waste_reduction"
#     )

from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import IntegrityError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Database connection using environment variables
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# Root route
@app.route('/')
def home():
    return "Welcome to the Food Waste Reduction App!"

# Route to fetch all users with pagination
@app.route('/users', methods=['GET'])
def get_users():
    # Get query parameters
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Calculate offset and limit
    offset = (page - 1) * limit

    # Fetch total count for pagination metadata
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cursor.fetchone()['total']

    # Fetch paginated results
    cursor.execute("SELECT * FROM users LIMIT %s OFFSET %s", (limit, offset))
    users = cursor.fetchall()

    cursor.close()
    connection.close()

    # Build response
    response = {
        "total": total_users,
        "page": page,
        "limit": limit,
        "total_pages": (total_users + limit - 1) // limit,  # Round up for total pages
        "users": users
    }
    return jsonify(response)


## Route to fetch all food items with filters and pagination
@app.route('/food_items', methods=['GET'])
def get_food_items():
    # Get query parameters
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    name = request.args.get('name', default=None, type=str)
    min_quantity = request.args.get('min_quantity', default=None, type=int)
    max_quantity = request.args.get('max_quantity', default=None, type=int)
    expiry_date = request.args.get('expiry_date', default=None, type=str)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Base query
    query = "SELECT * FROM food_items WHERE 1=1"
    params = []

    # Add filters
    if name:
        query += " AND name LIKE %s"
        params.append("%" + name + "%")  # Corrected filter value
    if min_quantity:
        query += " AND quantity >= %s"
        params.append(min_quantity)
    if max_quantity:
        query += " AND quantity <= %s"
        params.append(max_quantity)
    if expiry_date:
        query += " AND expiry_date <= %s"
        params.append(expiry_date)

    # Calculate offset and limit
    offset = (page - 1) * limit
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    # Execute the query to fetch food items
    cursor.execute(query, tuple(params))
    food_items = cursor.fetchall()

    # Fetch total count for pagination metadata
    count_query = "SELECT COUNT(*) AS total FROM food_items WHERE 1=1"
    count_params = []

    # Add the same filters for the count query
    if name:
        count_query += " AND name LIKE %s"
        count_params.append("%" + name + "%")
    if min_quantity:
        count_query += " AND quantity >= %s"
        count_params.append(min_quantity)
    if max_quantity:
        count_query += " AND quantity <= %s"
        count_params.append(max_quantity)
    if expiry_date:
        count_query += " AND expiry_date <= %s"
        count_params.append(expiry_date)

    # Execute the count query
    cursor.execute(count_query, tuple(count_params))
    total_food_items = cursor.fetchone()['total']

    cursor.close()
    connection.close()

    # Build response
    response = {
        "total": total_food_items,
        "page": page,
        "limit": limit,
        "total_pages": (total_food_items + limit - 1) // limit,
        "food_items": food_items
    }
    return jsonify(response)


# Route to add a new user
@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    # Validation: Ensure required fields are present
    if not data or not all(k in data for k in ('name', 'email', 'password_hash', 'role')):
        return jsonify({"error": "Missing required fields: 'name', 'email', 'password_hash', 'role'"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (data['name'], data['email'], data['password_hash'], data['role']))
        connection.commit()
    except IntegrityError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": "User added successfully"}), 201

# Route to add a new food item
@app.route('/food_items', methods=['POST'])
def add_food_item():
    data = request.json
    # Validation: Ensure required fields are present
    if not data or not all(k in data for k in ('user_id', 'name', 'quantity', 'expiry_date')):
        return jsonify({"error": "Missing required fields: 'user_id', 'name', 'quantity', 'expiry_date'"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO food_items (user_id, name, quantity, expiry_date) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (data['user_id'], data['name'], data['quantity'], data['expiry_date']))
        connection.commit()
    except IntegrityError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": "Food item added successfully"}), 201

# Route to log a donation
@app.route('/donations', methods=['POST'])
def add_donation():
    data = request.json
    # Validation: Ensure required fields are present
    if not data or not all(k in data for k in ('food_id', 'donor_id', 'recipient_id')):
        return jsonify({"error": "Missing required fields: 'food_id', 'donor_id', 'recipient_id'"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO donations (food_id, donor_id, recipient_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (data['food_id'], data['donor_id'], data['recipient_id']))
        connection.commit()
    except IntegrityError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": "Donation logged successfully"}), 201


# Route to fetch all donations with filters and pagination
@app.route('/donations', methods=['GET'])
def get_donations():
    # Get query parameters
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    donor_id = request.args.get('donor_id', default=None, type=int)
    recipient_id = request.args.get('recipient_id', default=None, type=int)
    donation_date = request.args.get('donation_date', default=None, type=str)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Base query
    query = """
        SELECT d.donation_id, f.name AS food_item, u1.name AS donor, u2.name AS recipient, d.donation_date
        FROM donations d
        JOIN food_items f ON d.food_id = f.food_id
        JOIN users AS u1 ON d.donor_id = u1.user_id
        JOIN users AS u2 ON d.recipient_id = u2.user_id
        WHERE 1=1
    """
    params = []

    # Add filters
    if donor_id:
        query += " AND d.donor_id = %s"
        params.append(donor_id)
    if recipient_id:
        query += " AND d.recipient_id = %s"
        params.append(recipient_id)
    if donation_date:
        query += " AND DATE(d.donation_date) = %s"
        params.append(donation_date)

    # Add pagination
    offset = (page - 1) * limit
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    # Execute query to fetch donations
    cursor.execute(query, tuple(params))
    donations = cursor.fetchall()

    # Fetch total count for donations
    total_count_query = """
        SELECT COUNT(*) AS total
        FROM donations d
        JOIN food_items f ON d.food_id = f.food_id
        JOIN users AS u1 ON d.donor_id = u1.user_id
        JOIN users AS u2 ON d.recipient_id = u2.user_id
        WHERE 1=1
    """
    cursor.execute(total_count_query, tuple(params[:-2]))  # Exclude limit and offset from count query
    total_donations = cursor.fetchone()['total']

    cursor.close()
    connection.close()

    # Build response
    response = {
        "total": total_donations,
        "page": page,
        "limit": limit,
        "total_pages": (total_donations + limit - 1) // limit,
        "donations": donations
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
