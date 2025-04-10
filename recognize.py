# -*- coding: utf-8 -*-
from __future__ import print_function
import csv
import hashlib
import pickle
import time
import click
import os
import re
import face_recognition.api as face_recognition
import PIL.Image
import numpy as np
import sqlite3


conn = sqlite3.connect("face_database.sqlite", check_same_thread=False)
c = conn.cursor()

check_query = "SELECT name FROM main.sqlite_master WHERE name='raw_data';"
raw_database_query = """
create table raw_data
(
    id          integer not null
        constraint raw_data_pk
            primary key autoincrement,
    raw_data    BLOB    not null,
    md5         TEXT    not null,
    basename    TEXT    not null,
    national_id TEXT    not null
);"""

c.execute(check_query)
if c.fetchone() is None:
    c.execute(raw_database_query)
    conn.commit()


def get_encoding_by_national_id(target_national_id):
    known_names, known_face_encodings, known_md5s, national_ids = get_known_names_from_database()
    encodings = []
    for known_face_encoding, national_id in zip(known_face_encodings, national_ids):
        if national_id == target_national_id:
            encodings.append(known_face_encoding)
    if len(encodings) > 0:
        return True, encodings
    else:
        return False, "Encoding not found."


def get_known_names_from_database():
    known_names = []
    known_face_encodings = []
    known_md5s = []
    national_ids = []
    cmd = "SELECT r.basename, r.md5, r.raw_data, r.national_id FROM raw_data as r"
    c.execute(cmd)
    rows = c.fetchall()
    if rows:
        for row in rows:
            basename, md5, raw_data, national_id = row[0],row[1],pickle.loads(row[2]), row[3]
            known_names.append(basename)
            known_face_encodings.append(raw_data)
            known_md5s.append(md5)
            national_ids.append(national_id)
    return known_names, known_face_encodings, known_md5s, national_ids

def add_to_dict(data, key, value):
    data.setdefault(key, [])
    if value not in data[key]:
        data[key].append(value)

def batch_add_face_to_database(folder_path, national_ids_path):
    data = {}
    if os.path.isdir(folder_path):
        national_ids = get_national_ids_from_csv(national_ids_path)
        image_files = image_files_in_folder(folder_path)
        if len(image_files) == len(national_ids) and len(image_files) > 0:
            for file_path in image_files:
                basename = os.path.splitext(os.path.basename(file_path))[0]
                try:
                    add_to_dict(data, national_ids[basename], add_face_to_database(file_path, national_ids[basename]))
                except:
                    return False, {"result":False, "message":"Couldn't find any file named {} inside provided ZIP.".format(basename)}
            return True, {"result":data,"message":"Operation completed successfully."}
        else:
            return False, {"result":None, "message":"Files count are not matched with provided csv filenames."}

    else:
        result = [add_face_to_database(folder_path, national_ids_path)]
        data[national_ids_path] = result
        return True, {"result":data, "message":"Operation completed successfully."}


def get_national_ids_from_csv(path):
    name_id_dict = {}
    try:
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name_id_dict[row["name"]] = row["id"]
            f.close()
        return name_id_dict
    except:
        return None

def get_face_id_from_national_id(national_id):
    cmd = f"""SELECT r.id from raw_data as r WHERE r.national_id ==  '{national_id}'"""
    c.execute(cmd)
    face_ids = []
    rows = c.fetchall()
    if rows:
        for row in rows:
            face_ids.append(row[0])
    return True, {"national_id":national_id,"unique_face_ids":face_ids}

def remove_data_with_face_id(face_id):
    try:
        cmd = f"""SELECT id FROM raw_data WHERE id = {face_id}"""
        c.execute(cmd)
        row = c.fetchone()
        if row is not None:
            cmd = f"""DELETE FROM raw_data WHERE id = {face_id}"""
            c.execute(cmd)
            conn.commit()
            c.execute("VACUUM")
            return True, "Face has been removed from database."
        else:
            return False, "Face has NOT been removed from database."
    except Exception as e:
        return False, e

def add_face_to_database(image_path, national_id):
    st = time.time()
    msg = ""
    known_names, known_face_encodings, known_md5s, national_ids = get_known_names_from_database()
    f = open(image_path, "rb")
    file_content = f.read()
    f.close()
    file_md5 = hashlib.md5(file_content).hexdigest()
    if file_md5 not in known_md5s:
        if national_id in national_ids:
            if national_ids.count(national_id) < 10:
                msg += f"Stored FaceIDs for this national_id: {national_ids.count(national_id)+1}. "
            else:
                msg += "This national_id has reached maximum FaceID limits."
                return {"success":False, "message":msg}
        basename = os.path.splitext(os.path.basename(image_path))[0]
        img = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(img)
        if len(encodings) > 1:
            msg += "Warning: More than 1 face detected in the provided image."
        if len(encodings) == 0:
            msg += "Warning: No face detected in the provided image."
        else:
            cmd = """
            INSERT INTO raw_data (raw_data, md5, basename, national_id)
            VALUES (?, ?, ?, ?)
            """
            print(f"Inserting into database... Done in {time.time() - st:.2f}s")
            c.execute(cmd, (pickle.dumps(encodings[0]), file_md5, basename, national_id))
            conn.commit()
            auto_increment_id = c.lastrowid
            known_names.append(basename)
            known_face_encodings.append(encodings[0])
            return {"success":True,"message":msg + "Face encoding has been stored.", "unique_face_id":auto_increment_id}
    else:
        cmd = f"""SELECT r.id FROM raw_data AS r WHERE r.md5 = '{file_md5}'"""
        c.execute(cmd)
        auto_increment_id = c.fetchone()[0]
        return {"success":False,"message":msg + "This file is already encoded in the database.", "unique_face_id":auto_increment_id}


def print_result(filename, name, distance,start_time, show_distance=False):
    if show_distance:
        print("{},{},{},{}".format(filename, name, f"{(1-distance)*100:.2f}%" if distance is not None else distance, f"{time.time()-start_time:.2f}s"))
    else:
        print("{},{},{}".format(filename, name, f"{time.time()-start_time:.2f}s"))


def test_image(image_to_check, national_ids, known_face_encodings, tolerance=0.6, show_distance=False):
    unknown_image = face_recognition.load_image_file(image_to_check)
    if max(unknown_image.shape) > 1000:
        pil_img = PIL.Image.fromarray(unknown_image)
        pil_img.thumbnail((1000, 1000), PIL.Image.LANCZOS)
        unknown_image = np.array(pil_img)
    unknown_encodings = face_recognition.face_encodings(unknown_image)
    for unknown_encoding in unknown_encodings:
        distances = face_recognition.face_distance(known_face_encodings, unknown_encoding)
        result = list(distances <= tolerance)
        best_match_index = list(distances).index(distances.min())
        if True in result:
            return True, {"national_id": national_ids[best_match_index], "match":f"{(1-distances[best_match_index])*100:.2f}"}
        else:
            return False, "Couldn't find face in database."
    if not unknown_encodings:
        return False, "No face is detected in provided image."


def image_files_in_folder(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]

def recognize(image_to_check, tolerance, show_distance):
    known_names, known_face_encodings, known_md5s, national_ids = get_known_names_from_database()
    print("Started!")
    start_time = time.time()
    return test_image(image_to_check, national_ids, known_face_encodings, tolerance, show_distance)


if __name__ == "__main__":
    @click.command()
    @click.option('--recognize-face', default='',
                  help='provide source file/folder to recognize')
    @click.option('--source', default='',
                  help='the source file/folder which will be added to database')
    @click.option('--get-encoding', default='',
                  help='provide national id to get dlib encoding information')
    @click.option('--source-national-id', default='',
                  help='the source file/folder national id. (must be provided in csv (name,id) if --source is a folder with same size)')
    @click.option('--tolerance', default=0.5,
                  help='Tolerance for face comparisons. Default is 0.5. Lower this if you get multiple matches for the same person.')
    @click.option('--show-distance', default=False, type=bool,
                  help='Output face distance. Useful for tweaking tolerance setting.')
    def main(recognize_face, source, source_national_id, get_encoding, tolerance, show_distance):
        if source != '':
            if source_national_id != '':
                return batch_add_face_to_database(source, source_national_id)
            else:
                msg = "--source and --source-national-id must be provided together."
                print(msg)
                return False, msg
        elif source_national_id != '':
            msg = "--source and --source-national-id must be provided together."
            print(msg)
            return False, msg
        elif get_encoding != '':
            return get_encoding_by_national_id(get_encoding)
        elif recognize_face != '':
            return recognize(recognize_face, tolerance, show_distance)
        else:
            print("use --help")
    main()
