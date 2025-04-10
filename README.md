# FaceRecognizer
A simpe FaceRecognition program based on [ageitgey/face_recognition](https://github.com/ageitgey/face_recognition) project using [dlib](http://dlib.net/) library.
Featured with API using Flask, ability to add/remove face data to database, recognize faces and return dlib face encodings

# API

<table>
  <tr>
    <th>Path</th>
    <th>Method</th>
    <th>Params</th>
    <th>Accept</th>
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
    <td rowspan="2">/add</td>
    <td rowspan="2">POST</td>
    <td>file*</td>
    <td>.jpg | .jpeg | .png | <u>.zip</u></td>
  </tr>
  <tr>
    <td>national_id*</td>
    <td><strong>TEXT</strong> | <u>.zip</u></td>
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


Authentication is required for all requests and is passed as "x-api-key" in header
