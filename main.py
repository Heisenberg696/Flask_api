from flask import Flask, request, json, jsonify
from firebase_admin import credentials, firestore, initialize_app
from flask_cors import CORS
import functions_framework


app = Flask(__name__)
CORS(app)

client_credentials = credentials.Certificate("socialnetwork.json")
default_app = initialize_app(client_credentials)
db = firestore.client()

# collections
user_collection = db.collection("users")
post_collection = db.collection("posts")


@app.route("/register", methods=["POST"])
def register():
    if not request.json:
        return jsonify({"msg": "Please provide the required fields"}), 400
   
    student_id = request.json["student_id"]
    student_info = user_collection.document(student_id).get()
    if student_info.exists:
            return jsonify({"msg": "You already have an account"}), 400
    else:
            try:
                user_collection.document(student_id).set(request.json)
                return jsonify({"msg":"Registration successful", "data": request.json}), 201
            except:
                return jsonify({"msg": "An error occurred during registration"}), 400



@app.route("/login", methods=["POST"])
def login():
    if not request.json:
        return jsonify({"msg": "Please provide the required fields"}), 400
    elif "student_id" not in request.json:
        return jsonify({"msg": "Please provide a student ID"}), 400
    elif "password" not in request.json:
        return jsonify({"msg": "Please provide a password"}), 400
    else:
        student_id = request.json["student_id"]
        password = request.json["password"]
        student_info = user_collection.document(student_id).get()
        if student_info.exists:
            if student_info.to_dict()["password"] == password:
                return jsonify({"msg": "Login successful", "data": student_info.to_dict()}), 200
            else:
                return jsonify({"msg": "Incorrect password"}), 401
        else:
            return jsonify({"msg": "This user does not exist"}), 404
        
        
        
@app.route("/create-profile", methods=["POST"])
def create_profile():
    if not request.json:
        return jsonify({"message": "Please fill the form"}), 400
    
    required_fields = ["student_id", "name", "email", "Date of Birth","Year group","Major","Residency","Best food","Best Movie"]
    for field in required_fields:
        if field not in request.json:
            return jsonify({"error": f"{field} is required"}), 400

    student_id = request.json["student_id"]
    student_document = user_collection.document(student_id).get()

    try:    
        if student_document.exists:
            user_collection.document(student_id).update(request.json)
            return jsonify({"message":"Profile created successfully", "data": request.json}), 201
        else:
            return jsonify({"message": f'User with ID {student_id} does not exist'})
    except:
        return jsonify({"message":"There was an error creating profile"}), 400
    

@app.route("/edit-profile/<student_id>", methods=["PATCH"])
def edit_profile(student_id):
    if not request.data:
        return jsonify({"error": "Request body is empty"}), 400

    try:
        updated_student_data = json.loads(request.data)
    except json.JSONDecodeError:
        return jsonify({"error": "Request body is not valid JSON"}), 400

    student_info = user_collection.document(student_id).get()

    if student_info.exists:
        user_collection.document(student_id).update(updated_student_data)
        return jsonify({"message": f'Student with ID {student_id} has been updated', "data": updated_student_data}), 200
    else:
        return jsonify({"error": f'Student with ID {student_id} does not exist'}), 400


@app.route("/view-profile/<student_id>", methods=["GET"])
def view_profile(student_id):
    try:
        student_info = user_collection.document(student_id).get()
        if student_info.exists:
            return jsonify({"msg": f'User with ID {student_id} has been retrieved', "data": student_info.to_dict()}), 200
        else:
            return jsonify({'msg': f'User with ID {student_id} does not exist'}), 404
    except Exception as e:
        return jsonify({'msg': f'An error occurred: {str(e)}'}), 500
    


@app.route("/create-post", methods=["POST"])
def create_post():
    if not request.data:
        return jsonify({"error": "Request body is empty"}), 400

    title = request.json["title"]
    description = request.json["description"]

    post_data = {
        "avatar": "https://pngtree.com/freepng/gray-silhouette-avatar_6404679.html",
        "title": title,
        "description": description,
        "date": firestore.SERVER_TIMESTAMP
    }

    try:
        post_collection.add(post_data)
        return jsonify({"message": "Post created successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"There was an error creating the post: {str(e)}"}), 400
    
@app.route("/feed", methods=["GET"])
def get_feed():
    try:
        # Query the posts collection and order by timestamp in descending order
        posts_doc = post_collection.order_by("timestamp", direction=firestore.Query.DESCENDING).get()
        # Get the first 10 posts
        posts = [post.to_dict() for post in posts_doc[:10]]
        return jsonify({"posts": posts}), 200
    except:
        return jsonify({"msg":"An error occurred while retrieving posts"}), 400
    

@functions_framework.http
def social_network_api(request):
    if request.method == 'POST' and request.path == '/create-profile':
        return create_profile()
    elif request.method == 'POST' and request.path == "/create-post":
        return create_post()

    # elif request.method == 'POST' and request.path == "/login":
    #     # return login()
    # elif request.method == 'POST' and request.path == "/register":
    #     return register()
    else:
        internal_ctx = app.test_request_context(path=request.full_path, method=request.method)
        internal_ctx.request.data = request.data
        internal_ctx.request.headers = request.headers
        internal_ctx.push()
        return_value = app.full_dispatch_request()
        internal_ctx.pop()
        return return_value
    
if __name__ == "__main__":
    app.run(debug = True)