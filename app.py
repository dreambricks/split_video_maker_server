import os
import uuid
import zipfile
import time
from flask import Flask, request, send_file, jsonify, render_template, abort
from werkzeug.utils import secure_filename
from video_stacker import stack_videos_vertically_with_loop
import traceback

app = Flask(__name__)
UPLOAD_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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

    output_filename = f"out_{uuid.uuid4()}.mp4"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

    try:
        stack_videos_vertically_with_loop(video1_path, video2_path, output_path)
        processed_videos.append(output_filename)
    except Exception as e:
        print(f"Erro ao processar os vídeos: {str(e)}")
        print(traceback.format_exc())
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
        print(f"Erro ao remover arquivos: {str(e)}")
        print(traceback.format_exc())
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
        print(f"Erro ao criar o arquivo ZIP: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Erro ao criar o arquivo ZIP: {str(e)}'}), 500

    return send_file(zip_path, as_attachment=True)

@app.route('/videos/<filename>')
def serve_video(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(file_path):
        abort(404)

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)
