# FaceRecognizer
A simpe FaceRecognition program based on [ageitgey/face_recognition](https://github.com/ageitgey/face_recognition) project using [dlib](http://dlib.net/) library.

Featured with API using Flask, ability to add/remove face data to database, recognize faces and return dlib face encodings

Note: images will not be stored in database but the MD5 hash of the image file will to prevent storing exact same image face encodings.
# How it works

## Authorization
Authentication is required for all requests and is passed as "x-api-key" in header.

for now, keys are stored inside app.py file as list: API_KEYS

## Add
Using /add (or --source argument) you can send your image and national id (--source-national-id argument), the bot will extract the encodings of the first face in the image and stores it to the database referrenced by FaceID and national id.

This method supports batch adding mode, for this feature, you must create a csv file with "name" and "id" headers and a zip containing only image files.

For example, you have 3 image files named as, 0001.jpg, David.jpeg, John_Doe.PNG; create a zip containing these three files. save each file name and national id into csv file like this:
```csv
name,id
0001,0123456789
John_Doe,1010101010
David,9876543210
```

## Recognize
Using /recognize (or --recognize-face argument) you can send your image (--source, --tolerance and --show-distance arguments), the bot will detect the first face in the image and returs the results.

## Download Face dlib Encoding data
Using /get_encoding (or --get-encoding argument) and face national id (--source-national-id argument) you can download dlib encoding data from database by FaceIDs wraped in pickle format.

## Get Face IDs
In case you need to get track of stored FaceIDs using national id, you can use /get_face_idsand send national id to get all FaceIDs list.

## Remove Face ID from database
Using /remove_face_id you can send a FaceID and the face encoding will be removed from database.

# API

<table>
  <tr>
    <th>Path</th>
    <th>Method</th>
    <th>Params</th>
    <th>Accept</th>
  </tr>
  
  <tr>
    <td rowspan="2">/add</td>
    <td rowspan="2">POST</td>
    <td>file*</td>
    <td>.jpg | .jpeg | .png | <ins>.zip</ins></td>
  </tr>
  <tr>
    <td>national_id*</td>
    <td><strong>TEXT</strong> | <ins>.csv</ins></td>
  </tr>
  
  <tr>
    <td rowspan="3">/recognize</td>
    <td rowspan="3">POST</td>
    <td>file*</td>
    <td>.jpg | .jpeg | .png</td>
  </tr>
  <tr>
    <td>tolerance</td>
    <td><strong>FLOAT:</strong> 0.6</td>
  </tr>
  <tr>
    <td>show_distance</td>
    <td><strong>BOOL:</strong> false</td>
  </tr>
  
  <tr>
    <td>/get_encoding</td>
    <td>GET</td>
    <td>national_id*</td>
    <td><strong>TEXT</strong></td>
  </tr>
  
  <tr>
    <td>/get_face_ids</td>
    <td>GET</td>
    <td>national_id*</td>
    <td><strong>TEXT</strong></td>
  </tr>
  
  <tr>
    <td>/remove_face_id</td>
    <td>GET</td>
    <td>unique_face_id*</td>
    <td><strong>TEXT</strong></td>
  </tr>
</table>

