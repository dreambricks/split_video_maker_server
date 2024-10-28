from flask import Flask, request, send_from_directory, jsonify, render_template, abort
import os
import uuid
from werkzeug.utils import secure_filename, send_file
from video_stacker import stack_videos_vertically_with_loop

app = Flask(__name__)
UPLOAD_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Limite de 500MB por upload

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_videos', methods=['POST'])
def upload_videos():
    if 'video1' not in request.files or 'video2' not in request.files:
        return jsonify({'error': 'Por favor, envie dois vídeos.'}), 400

    video1 = request.files['video1']
    video2 = request.files['video2']

    if video1.filename == '' or video2.filename == '':
        return jsonify({'error': 'Um dos arquivos não foi enviado corretamente.'}), 400

    video1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video1.filename))
    video2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video2.filename))
    video1.save(video1_path)
    video2.save(video2_path)

    output_filename = f"out_{uuid.uuid4()}.mp4"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

    stack_videos_vertically_with_loop(video1_path, video2_path, output_path)

    return jsonify({'filename': f'{output_filename}'}), 200


@app.route('/videos/<filename>')
def serve_video(filename):

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(file_path):
        abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
