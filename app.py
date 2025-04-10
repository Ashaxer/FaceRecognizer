# -*- coding: utf-8 -*-
import io
import pickle
import os
from flask import Flask, request, jsonify, send_file
from recognize import recognize, batch_add_face_to_database, get_encoding_by_national_id, get_face_id_from_national_id, remove_data_with_face_id
import zipfile
from werkzeug.utils import secure_filename
from functools import wraps

API_KEYS = ["Test_API-key", "anonymous"]


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key or api_key not in API_KEYS:
            return jsonify({"success":False,"message": "Access Denied: Invalid API key or not provided."}), 401
        return func(*args, **kwargs)
    return wrapper


app = Flask(__name__)
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}
ALLOWED_ZIP_EXTENSIONS = {'zip'}
ALLOWED_NATIONAL_ID_EXTENSIONS = {'txt', 'csv'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, subfolder):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(folder_path, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(folder_path, filename)
    file.save(file_path)
    return file_path

def create_unique_folder(base_folder):
    folder_path = base_folder
    counter = 1
    while os.path.exists(folder_path):
        folder_path = f"{base_folder}_{counter}"
        counter += 1
    os.makedirs(folder_path)
    return folder_path

@app.route('/recognize', methods=['POST'])
@require_api_key
def recognize_face():
    try:
        file = request.files.get('file')
        if not file or not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({"success":False,"message": "Invalid image file or not provided."}), 400
        tolerance = request.form.get('tolerance', 0.6, type=float)
        show_distance = request.form.get('show_distance', False, type=bool)

        file_path = save_file(file, 'recognize')
        result = recognize(file_path, tolerance, show_distance)
        if result[0]:
            return jsonify({"success": result[0],"data":result[1]}), 200
        else:
            return jsonify({"success": result[0],"message":result[1]}), 400

    except Exception as e:
        return jsonify({"success":False,"message": str(e)}), 500

@app.route('/add', methods=['POST'])
@require_api_key
def add():
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"success":False,"message": "file is not provided."}), 400

        file_extension = file.filename.rsplit('.', 1)[1].lower()

        if file_extension in ALLOWED_IMAGE_EXTENSIONS:
            national_id = request.form.get('national_id')
            if not national_id:
                return jsonify({"success":False,"message": "national_id is not provided."}), 400
            file_path = save_file(file, 'images')
        elif file_extension in ALLOWED_ZIP_EXTENSIONS:
            national_id_file = request.files.get('national_id')
            if not national_id_file or not allowed_file(national_id_file.filename, ALLOWED_NATIONAL_ID_EXTENSIONS):
                return jsonify({"success":False,"message": "Invalid csv file or not provided."}), 400
            zip_path = save_file(file, 'zips')
            extract_folder = os.path.splitext(zip_path)[0]
            extract_folder = create_unique_folder(extract_folder)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            file_path = extract_folder
        else:
            return jsonify({"success":False,"message": "Wrong file format, only ZIP and JPEG/PNG is accepted."}), 400

        if file_extension in ALLOWED_ZIP_EXTENSIONS:
            national_id_path = save_file(national_id_file, 'national_ids')
        else:
            national_id_path = national_id
        result = batch_add_face_to_database(file_path, national_id_path)
        return jsonify({"success": result[0],"data":result[1]}), 200

    except Exception as e:
        return jsonify({"success":False,"message": str(e)}), 500


@app.route('/get_encoding', methods=['GET'])
@require_api_key
def get_encoding():
    try:
        national_id = request.args.get('national_id')
        if not national_id:
            return jsonify({"success":False,"message": "national_id is not provided."}), 400

        result = get_encoding_by_national_id(national_id)
        if result[0] is False:
            return jsonify({"success": result[0],"data":result[1]}), 400
        else:
            pickle_file = io.BytesIO()
            pickle.dump(result[1], pickle_file)
            pickle_file.seek(0)

            return send_file(
                pickle_file,
                as_attachment=True,
                download_name=f"{national_id}_encodings.dlib.pkl",
                mimetype='application/octet-stream'
            ), 200

    except Exception as e:
        return jsonify({"success":False, "message": str(e)}), 500


@app.route('/get_face_ids', methods=['GET'])
@require_api_key
def get_face_ids():
    national_id = request.args.get('national_id')
    try:
        if not national_id:
            return jsonify({"success":False,"message": "national_id is not provided."}), 400
        result = get_face_id_from_national_id(national_id)
        if result[0] is False:
            return jsonify({"success": result[0],"message":result[1]}), 400
        else:
            return jsonify({"success": result[0],"data":result[1]}), 200
    except Exception as e:
        return jsonify({"success":False, "message": str(e)}), 500


@app.route('/remove_face_id', methods=['GET'])
@require_api_key
def remove_face_id():
    unique_face_id = request.args.get('unique_face_id')
    try:
        if not unique_face_id:
            return jsonify({"success":False,"message": "unique_face_id is not provided."}), 400
        result = remove_data_with_face_id(unique_face_id)
        if result[0] is False:
            return jsonify({"success": result[0],"message":result[1]}), 400
        else:
            return jsonify({"success": result[0],"message":result[1]}), 200
    except Exception as e:
        return jsonify({"success":False, "message": str(e)}), 500
@app.route('/')
def home():
    return jsonify({"success":True,"message": "FaceRecognition server is running."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
