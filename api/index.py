from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import uuid  # Import UUID module
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB connection string
uri = os.getenv('MONGODB_URI')

# Initialize MongoDB client and connect to the 'test' database
client = MongoClient(uri)
db = client.EmployeeDatabase  # Connect to the 'test' database
collection = db.DepartmentCollection  # Replace with your actual collection name

# Helper function to convert ObjectId to string
def convert_objectid(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
    return doc

@app.route('/api', methods=['GET'])
def get_department():
    # Query to retrieve all documents from the collection
    data = collection.find()  # Retrieves all documents
    result = [convert_objectid(doc) for doc in data]  # Convert ObjectId to string
    return jsonify(result)

@app.route('/api', methods=['POST'])
def add_data():
    # Get the data from the request body
    data = request.get_json()

    # Validate department_name
    department_name = data.get("department_name")
    if not department_name:
        return jsonify({"error": "Department name is required"}), 400

    # Check if a department with the same name already exists
    existing_department = collection.find_one({"department_name": department_name})
    if existing_department:
        return jsonify({"error": "Department name already exists"}), 409  # 409 Conflict

    # Generate a unique department_id
    data["department_id"] = str(uuid.uuid4())  # Assign a unique UUID

    # Insert the data into MongoDB
    result = collection.insert_one(data)

    # Return a response with the inserted document ID and generated department_id
    return jsonify({
        "message": "Data added successfully",
        "department_id": data["department_id"],
        "_id": str(result.inserted_id)
    }), 201


# @app.route('/api', methods=['POST'])
# def add_data():
#     # Get the data from the request body
#     data = request.get_json()  # Get data as a dictionary
    
#     # Insert the data into MongoDB
#     result = collection.insert_one(data)  # Insert data into the collection
    
#     # Return a response with the inserted document ID
#     return jsonify({"message": "Data added successfully", "_id": str(result.inserted_id)}), 201

@app.route('/api/department', methods=['DELETE'])
def delete_department():
    # Get the department name from the request body
    data = request.get_json()
    department_name = data.get('department_name')
    
    if not department_name:
        return jsonify({"error": "department_name is required"}), 400

    # Delete the department with the specified department_name
    result = collection.delete_one({"department_name": department_name})
    
    if result.deleted_count > 0:
        return jsonify({"message": f"Department '{department_name}' deleted successfully"}), 200
    else:
        return jsonify({"error": f"Department '{department_name}' not found"}), 404
        
@app.route('/api/department/add_employee', methods=['POST'])
def add_employee():
    # Get the data from the request body
    data = request.get_json()

    # Extract department_name and employee details from the request
    department_name = data.get('department_name')
    new_employee = data.get('employee')

    if not department_name or not new_employee:
        return jsonify({"error": "Both department_name and employee data are required"}), 400

    # Generate a unique employee_id using UUID
    new_employee['employee_id'] = str(uuid.uuid4())  # Assign a unique ID

    # Remove 'id' field if it's empty
    if 'id' in new_employee and not new_employee['id']:
        del new_employee['id']

    # Update the department by adding the new employee to the employees array
    result = collection.update_one(
        {"department_name": department_name},  # Find department by name
        {"$push": {"employees": new_employee}}  # Add the new employee to the employees array
    )

    if result.matched_count > 0:
        if result.modified_count > 0:
            return jsonify({
                "message": "Employee added successfully",
                "employee_id": new_employee['employee_id']  # Return generated employee_id
            }), 200
        else:
            return jsonify({"message": "No changes made"}), 200
    else:
        return jsonify({"error": f"Department '{department_name}' not found"}), 404

# @app.route('/api/department/add_employee', methods=['POST'])
# def add_employee():
#     # Get the data from the request body
#     data = request.get_json()

#     # Extract department_name and employee details from the request
#     department_name = data.get('department_name')
#     new_employee = data.get('employee')

#     if not department_name or not new_employee:
#         return jsonify({"error": "Both department_name and employee data are required"}), 400

#     # Update the department by adding the new employee to the employees array
#     result = collection.update_one(
#         {"department_name": department_name},  # Find department by name
#         {"$push": {"employees": new_employee}}  # Add the new employee to the employees array
#     )

#     if result.matched_count > 0:
#         if result.modified_count > 0:
#             return jsonify({"message": "Employee added successfully"}), 200
#         else:
#             return jsonify({"message": "Employee already exists or no changes made"}), 200
#     else:
#         return jsonify({"error": f"Department '{department_name}' not found"}), 404

@app.route('/api/department/employees', methods=['GET'])
def get_employees():
    # Get the department name from the query parameters
    department_name = request.args.get('department_name')
    
    if not department_name:
        return jsonify({"error": "department_name is required"}), 400

    # Query the department by department_name
    department = collection.find_one({"department_name": department_name}, {"employees": 1, "_id": 0})

    if department:
        employees = department.get("employees", [])
        return jsonify({"employees": employees}), 200
    else:
        return jsonify({"error": f"Department '{department_name}' not found"}), 404

@app.route('/api/department/employee', methods=['GET'])
def get_employee_by_name():
    # Get the department_name and employee_name from the query parameters
    department_name = request.args.get('department_name')
    employee_name = request.args.get('employee_name')

    if not department_name or not employee_name:
        return jsonify({"error": "Both department_name and employee_name are required"}), 400

    # Query the department by department_name
    department = collection.find_one({"department_name": department_name}, {"employees": 1, "_id": 0})

    if not department:
        return jsonify({"error": f"Department '{department_name}' not found"}), 404

    # Filter the employee from the employees array
    employees = department.get("employees", [])
    employee = next((emp for emp in employees if emp.get("name") == employee_name), None)

    if employee:
        return jsonify({"employee": employee}), 200
    else:
        return jsonify({"error": f"Employee named '{employee_name}' not found in department '{department_name}'"}), 404

@app.route('/api/department/employee/update', methods=['PUT'])
def update_employee_name_email():
    # Get the data from the request body
    data = request.get_json()

    department_name = data.get('department_name')
    employee_name = data.get('employee_name')  # Current name of the employee
    updated_name = data.get('updated_name')    # New name for the employee
    updated_email = data.get('updated_email')  # New email for the employee

    # Validate the inputs
    if not department_name or not employee_name:
        return jsonify({"error": "department_name and employee_name are required"}), 400

    if not updated_name and not updated_email:
        return jsonify({"error": "At least one of updated_name or updated_email is required"}), 400

    # Build the update fields dynamically
    update_fields = {}
    if updated_name:
        update_fields["employees.$.name"] = updated_name
    if updated_email:
        update_fields["employees.$.email"] = updated_email

    # Update the specific employee within the department
    result = collection.update_one(
        {
            "department_name": department_name,
            "employees.name": employee_name  # Match department and employee name
        },
        {
            "$set": update_fields  # Update the specified fields
        }
    )

    # Handle the result
    if result.matched_count == 0:
        return jsonify({
            "error": f"Employee '{employee_name}' not found in department '{department_name}'"
        }), 404

    return jsonify({
        "message": f"Employee '{employee_name}' updated successfully",
        "updated_fields": update_fields
    }), 200

@app.route('/api/department/employee/status', methods=['PUT'])
def update_employee_status():
    # Get the data from the request body
    data = request.get_json()

    department_name = data.get('department_name')  # Department name
    employee_name = data.get('employee_name')      # Employee name
    new_status = data.get('status')               # New status ('Active' or 'Inactive')

    # Validate inputs
    if not department_name or not employee_name or not new_status:
        return jsonify({"error": "department_name, employee_name, and status are required"}), 400

    if new_status not in ['Active', 'Inactive']:
        return jsonify({"error": "status must be either 'Active' or 'Inactive'"}), 400

    # Update the employee's status
    result = collection.update_one(
        {
            "department_name": department_name,
            "employees.name": employee_name  # Match the department and employee name
        },
        {
            "$set": {"employees.$.status": new_status}  # Update the employee's status
        }
    )

    # Handle the result
    if result.matched_count == 0:
        return jsonify({
            "error": f"Employee '{employee_name}' not found in department '{department_name}'"
        }), 404

    return jsonify({
        "message": f"Employee '{employee_name}' status updated to '{new_status}' successfully"
    }), 200

@app.route('/api/employee/move', methods=['PUT'])
def move_employee_to_new_department():
    # Get the data from the request body
    data = request.get_json()

    # Data fields from the request
    current_department_name = data.get('current_department_name')
    employee_name = data.get('employee_name')
    new_department_name = data.get('new_department_name')
    new_location = data.get('new_location')

    # Validate inputs
    if not current_department_name or not employee_name or not new_department_name or not new_location:
        return jsonify({"error": "current_department_name, employee_name, new_department_name, and new_location are required"}), 400

    # Find the employee in the current department and update their department and location
    result = collection.update_one(
        {
            "department_name": current_department_name,
            "employees.name": employee_name  # Match the employee's name in the current department
        },
        {
            "$set": {
                "employees.$.department_name": new_department_name,  # Update department
                "employees.$.location": new_location  # Update employee location
            }
        }
    )

    # If no employee is found, return an error
    if result.matched_count == 0:
        return jsonify({
            "error": f"Employee '{employee_name}' not found in department '{current_department_name}'"
        }), 404

    # Move the employee to the new department by adding them to the new department's employees list
    move_result = collection.update_one(
        {
            "department_name": new_department_name
        },
        {
            "$push": {
                "employees": {
                    "name": employee_name,
                    "location": new_location,
                    # You can retain other fields like employee_id, email, etc., if needed
                }
            }
        }
    )

    # If moving the employee to the new department is unsuccessful, return an error
    if move_result.modified_count == 0:
        return jsonify({
            "error": f"Unable to move employee '{employee_name}' to department '{new_department_name}'"
        }), 500

    return jsonify({
        "message": f"Employee '{employee_name}' successfully moved to department '{new_department_name}' and located at '{new_location}'"
    }), 200

if __name__ == '__main__':
    app.run()
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'
