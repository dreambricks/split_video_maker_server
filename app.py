import json
import os
import uuid
import zipfile
import time
from flask import Flask, request, send_file, jsonify, render_template, abort
from werkzeug.utils import secure_filename
from logging_config import setup_logging
import logging
from video_stacker import stack_videos_vertically_with_loop
import traceback
from utils import generate_datetime_filename, generate_random_string
import threading


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSING_FOLDER = 'processing'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(PROCESSING_FOLDER):
    os.makedirs(PROCESSING_FOLDER)

# Set up logging configuration
setup_logging()
logger = logging.getLogger("SplitVideoMaker")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSING_FOLDER'] = PROCESSING_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # Limite de 10GB por upload

# Listas para armazenar os arquivos "source" e vídeos processados
source_files = []
processed_videos = []


@app.route('/alive')
def alive():
    return 'alive'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get-job-code')
def get_job_code():
    job_code = generate_random_string(10)
    job_code_dir = os.path.join(UPLOAD_FOLDER, job_code)
    os.makedirs(job_code_dir)
    job_code_proc_dir = os.path.join(app.config['PROCESSING_FOLDER'], job_code)
    os.makedirs(job_code_proc_dir)
    return jsonify({"job_code": job_code})


# Endpoint to handle secondary file upload
@app.route('/upload-secondary', methods=['POST'])
def upload_secondary():
    secondary_file = request.files['file']
    job_code = request.form.get('job_code')
    secondary_file_path = os.path.join(UPLOAD_FOLDER, job_code, secondary_file.filename)
    secondary_file.save(secondary_file_path)  # Save the secondary file

    return jsonify({"file_path": secondary_file_path, "job_code": job_code})


# Endpoint to handle primary file uploads, with a secondary file path
@app.route('/upload', methods=['POST'])
def upload_primary():
    primary_file = request.files['file']
    secondary_file_path = request.form.get('secondary_file_path')  # Get path of secondary file
    job_code = request.form.get('job_code')

    # Save primary file
    primary_file_path = os.path.join(UPLOAD_FOLDER, job_code, primary_file.filename)
    primary_file.save(primary_file_path)

    # Create a status file for tracking processing progress
    job_code_proc_dir = os.path.join(app.config['PROCESSING_FOLDER'], job_code)
    status_path = os.path.join(job_code_proc_dir, primary_file.filename + ".status")

    # Create a job file with details about the work
    job_path = os.path.join(job_code_proc_dir, "job_" + primary_file.filename + ".json")

    video1_basename, _ = os.path.splitext(os.path.basename(primary_file_path))
    video2_basename, _ = os.path.splitext(os.path.basename(secondary_file_path))
    output_filename = generate_datetime_filename(f"out_{video1_basename}_{video2_basename}", "mp4")
    output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], job_code, output_filename)
    output_link = f"videos/{job_code}/{output_filename}"

    # Simulate processing both files
    #process_files(primary_file_path, primary_file_size, secondary_file_path, secondary_file_size)
    #threading.Thread(target=dummy_process_file, args=(primary_file_path, secondary_file_path, status_path)).start()
    threading.Thread(target=stack_videos_vertically_with_loop,
                     args=(primary_file_path, secondary_file_path, output_file_path,
                           status_path, job_path, output_link)).start()

    return jsonify({"file": primary_file.filename})


@app.route('/progress/<job_code>/<filename>')
def progress(job_code, filename):
    """Check processing progress of a specific file."""
    status_path = os.path.join(app.config['PROCESSING_FOLDER'], job_code, filename + ".status")
    if os.path.exists(status_path):
        with open(status_path, 'r') as f:
            progress = f.read()
        return jsonify({"processing_progress": progress}), 200
    return jsonify({"processing_progress": "100"}), 200  # Return 100 if processing is complete

@app.route('/details/<job_code>/<filename>')
def details(job_code, filename):
    """Check processing progress of a specific file."""
    details_path = os.path.join(app.config['PROCESSING_FOLDER'], job_code, "job_" + filename + ".json")
    if os.path.exists(details_path):
        with open(details_path, 'r') as f:
            job_details = json.load(f)
            return jsonify({
                "video1": job_details['video1'],
                "video2": job_details['video2'],
                "out_video": job_details['out_video'],
            }), 200
    #return jsonify({"processing_progress": "100"}), 200  # Return 100 if processing is complete

    # Return a link to the processed primary file
    return jsonify({'error': f"details file doesn't exist: {str(details_path)}"}), 500


@app.route('/upload_videos', methods=['POST'])
def upload_videos():
    video1 = request.files['video1']
    video2 = request.files['video2']

    if video1.filename == '' or video2.filename == '':
        return jsonify({'error': 'Um dos arquivos não foi enviado corretamente.'}), 400

    video1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video1.filename))
    video2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video2.filename))
    video1.save(video1_path)
    video2.save(video2_path)

    source_files.extend([video1_path, video2_path])

    video1_basename, _ = os.path.splitext(os.path.basename(video1_path))
    video2_basename, _ = os.path.splitext(os.path.basename(video2_path))
    output_filename = generate_datetime_filename(f"out_{video1_basename}_{video2_basename}", "mp4")
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

    try:
        stack_videos_vertically_with_loop(video1_path, video2_path, output_path)
        processed_videos.append(output_filename)
    except Exception as e:
        logger.error(f"Erro ao processar os vídeos: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Erro ao processar os vídeos: {str(e)}'}), 500

    # Retorna a URL direta para o vídeo processado
    return jsonify({'video_url': f'/videos/{output_filename}'}), 200


@app.route('/finalize_uploads', methods=['POST'])
def finalize_uploads():
    """Rota para excluir todos os arquivos 'source' após o upload e processamento."""
    try:
        for file_path in source_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        source_files.clear()  # Limpa a lista após remover os arquivos
        return jsonify({'message': 'Arquivos source removidos com sucesso.'}), 200
    except Exception as e:
        logger.error(f"Erro ao remover arquivos: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Erro ao remover arquivos: {str(e)}'}), 500


@app.route('/download_zip')
def download_zip():
    if not processed_videos:
        return jsonify({'error': 'Nenhum vídeo processado disponível para download.'}), 400

    zip_filename = f"videos_{uuid.uuid4()}.zip"
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

    # Cria o ZIP com os vídeos processados
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for filename in processed_videos:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                zipf.write(file_path, filename)
    except Exception as e:
        logger.error(f"Erro ao criar o arquivo ZIP: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Erro ao criar o arquivo ZIP: {str(e)}'}), 500

    return send_file(zip_path, as_attachment=True)


@app.route('/videos/<job_code>/<filename>')
def serve_video(job_code, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], job_code, filename)
    if not os.path.isfile(file_path):
        abort(404)

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    #context = ('static/fullchain.pem', 'static/privkey.pem')
    #app.run(host='0.0.0.0', ssl_context=context)
    app.run()

