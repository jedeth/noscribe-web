from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from faster_whisper import WhisperModel
from pydub import AudioSegment
from pyannote.audio import Pipeline
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import tempfile
import uuid
from pathlib import Path
import logging
import json
from datetime import datetime, timedelta
import yaml
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='static')
CORS(app)
logging.basicConfig(level=logging.INFO)

# Configuration
UPLOAD_FOLDER = Path('/tmp/noscribe_uploads')
RESULTS_FOLDER = Path('/tmp/noscribe_results')
CONFIG_FOLDER = Path.home() / '.noscribe_web'
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)
CONFIG_FOLDER.mkdir(exist_ok=True)

# Paramètres optimisés pour 512 Go RAM sans GPU
SEGMENT_DURATION_MS = 60000
MAX_WORKERS = min(72, mp.cpu_count())
CPU_THREADS = 4

class TranscriptionConfig:
    def __init__(self):
        self.config_file = CONFIG_FOLDER / 'config.yml'
        self.hf_token_file = CONFIG_FOLDER / 'hf_token.txt'
        self.default_config = {
            'locale': 'fr',
            'num_workers': MAX_WORKERS,
            'cpu_threads': CPU_THREADS,
            'beam_size': 5,
            'compute_type': 'int8'
        }
        self.load_config()
    
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f) or self.default_config
        else:
            self.config = self.default_config
            self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f)
    
    def get_hf_token(self):
        """Récupère le token HuggingFace"""
        if self.hf_token_file.exists():
            with open(self.hf_token_file, 'r') as f:
                return f.read().strip()
        return None

config = TranscriptionConfig()

def format_timestamp(seconds):
    """Formate les secondes en HH:MM:SS"""
    return str(timedelta(seconds=int(seconds))).split('.')[0]

def parse_timestamp(timestamp_str):
    """Convertit HH:MM:SS en millisecondes"""
    if not timestamp_str:
        return 0
    parts = timestamp_str.split(':')
    hours = int(parts[0]) if len(parts) > 0 else 0
    minutes = int(parts[1]) if len(parts) > 1 else 0
    seconds = int(parts[2]) if len(parts) > 2 else 0
    return (hours * 3600 + minutes * 60 + seconds) * 1000

def split_audio(audio_path, segment_duration_ms, start_ms=0, stop_ms=None):
    """Découpe l'audio en segments"""
    audio = AudioSegment.from_file(audio_path)
    
    if stop_ms:
        audio = audio[start_ms:stop_ms]
    else:
        audio = audio[start_ms:]
    
    segments = []
    
    for i, start in enumerate(range(0, len(audio), segment_duration_ms)):
        end = min(start + segment_duration_ms, len(audio))
        segment = audio[start:end]
        
        segment_path = UPLOAD_FOLDER / f"segment_{uuid.uuid4()}_{i}.wav"
        segment.export(segment_path, format="wav")
        
        absolute_start = (start_ms + start) / 1000
        absolute_end = (start_ms + end) / 1000
        
        segments.append({
            'path': str(segment_path),
            'index': i,
            'start_time': absolute_start,
            'end_time': absolute_end
        })
    
    return segments

def transcribe_segment(args):
    """Transcrit un segment (exécuté dans un processus séparé)"""
    segment_info, model_name, language, compute_type, cpu_threads = args
    
    try:
        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type=compute_type,
            cpu_threads=cpu_threads,
            num_workers=1
        )
        
        lang = None if language == 'auto' else language
        
        segments_result, info = model.transcribe(
            segment_info['path'],
            language=lang,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        text_parts = []
        for seg in segments_result:
            text_parts.append(seg.text.strip())
        
        full_text = " ".join(text_parts)
        
        os.remove(segment_info['path'])
        
        return {
            'index': segment_info['index'],
            'text': full_text,
            'start_time': segment_info['start_time'],
            'end_time': segment_info['end_time'],
            'timestamp': format_timestamp(segment_info['start_time'])
        }
    except Exception as e:
        logging.error(f"Erreur segment {segment_info['index']}: {str(e)}")
        return {
            'index': segment_info['index'],
            'text': f"[ERREUR: {str(e)}]",
            'start_time': segment_info['start_time'],
            'end_time': segment_info['end_time'],
            'timestamp': format_timestamp(segment_info['start_time'])
        }

def detect_speakers(audio_path, num_speakers=None):
    """Détection des locuteurs avec pyannote - officiel"""
    try:
        import torch
        from pyannote.audio import Pipeline
        
        hf_token = config.get_hf_token()
        if not hf_token:
            logging.error("Token Hugging Face non trouvé. La détection des locuteurs est désactivée.")
            logging.error("Veuillez créer un token sur https://huggingface.co/settings/tokens et l'enregistrer dans ~/.noscribe_web/hf_token.txt")
            return []

        logging.info("Chargement du pipeline de diarisation pyannote/speaker-diarization-3.1...")
        
        # Charger le pipeline officiel depuis Hugging Face
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token
        )
        
        # Forcer CPU si pas de GPU disponible ou pour la cohérence
        pipeline.to(torch.device("cpu"))
        
        logging.info("Préparation de l'audio pour la diarisation...")
        
        # Convertir l'audio en WAV mono 16kHz pour assurer la compatibilité
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)

        temp_audio_path = UPLOAD_FOLDER / f"temp_diarization_{uuid.uuid4()}.wav"
        audio.export(temp_audio_path, format="wav")
        
        logging.info(f"Analyse du fichier audio pour détecter les locuteurs...")
        
        # Exécuter la diarisation sur le fichier WAV temporaire
        diarization = pipeline(str(temp_audio_path), num_speakers=num_speakers)
        
        speaker_segments = []
        
        # Itérer sur les résultats (format Annotation de pyannote)
        # NOTE: La structure de sortie a changé, .itertracks est sur l'objet d'annotation
        for segment, _, label in diarization.annotation.itertracks(yield_label=True):
            speaker_segments.append({
                'start': segment.start,
                'end': segment.end,
                'speaker': label
            })
        
        # Nettoyer le fichier temporaire
        os.remove(temp_audio_path)

        logging.info(f"Détection terminée: {len(speaker_segments)} segments de parole trouvés")
        return speaker_segments
        
    except Exception as e:
        logging.error(f"Erreur lors de la détection des locuteurs: {str(e)}")
        if "401" in str(e):
             logging.error("Erreur d'authentification (401). Votre token Hugging Face est probablement invalide ou a expiré.")
        import traceback
        logging.error(traceback.format_exc())
        return []
def format_transcript(results, speaker_segments, add_timestamps):
    """Formate la transcription finale"""
    lines = []
    current_speaker = None
    
    for result in results:
        text = result['text']
        timestamp = result['timestamp']
        
        if add_timestamps:
            text = f"[{timestamp}] {text}"
        
        if speaker_segments:
            for seg in speaker_segments:
                if seg['start'] <= result['start_time'] <= seg['end']:
                    if current_speaker != seg['speaker']:
                        current_speaker = seg['speaker']
                        lines.append(f"\n{current_speaker}:")
                    break
        
        lines.append(text)
    
    return "\n".join(lines)

def save_as_html(path, text, filename):
    """Sauvegarde en format HTML"""
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Transcription - {filename}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #667eea; }}
        .content {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>Transcription: {filename}</h1>
    <div class="content">{text}</div>
</body>
</html>"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def save_as_vtt(path, segments):
    """Sauvegarde en format VTT"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            start = timedelta(seconds=seg['start_time'])
            end = timedelta(seconds=seg['end_time'])
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{seg['text']}\n\n")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'available_cores': mp.cpu_count(),
        'configured_workers': MAX_WORKERS,
        'compute_type': config.config['compute_type'],
        'device': 'CPU (optimized for 512GB RAM)'
    })

# Modifier la fonction process_audio dans le endpoint /api/transcribe

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    options = json.loads(request.form.get('options', '{}'))
    
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_FOLDER / f"{file_id}_{file.filename}"
    file.save(file_path)
    
    log_file = CONFIG_FOLDER / 'log' / f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(exist_ok=True)
    
    try:
        model_name = options.get('model', 'base')
        quality = options.get('quality', 'precise')
        language = options.get('language', 'fr')
        segment_duration_ms = options.get('segment_duration', SEGMENT_DURATION_MS)
        start_time = options.get('start_time', '00:00:00')
        stop_time = options.get('stop_time', '')
        speaker_detection = options.get('speaker_detection', 'none')
        add_timestamps = options.get('timestamps', False)
        
        start_ms = parse_timestamp(start_time)
        stop_ms = parse_timestamp(stop_time) if stop_time else None
        
        # IMPORTANT: Détection des locuteurs AVANT la transcription (comme noScribe)
        speaker_segments = []
        if speaker_detection != 'none':
            try:
                num_speakers = int(speaker_detection) if speaker_detection != 'auto' else None
                logging.info(f"Détection des locuteurs sur le fichier complet...")
                speaker_segments = detect_speakers(str(file_path), num_speakers)
                logging.info(f"{len(speaker_segments)} segments de locuteurs détectés")
            except Exception as e:
                logging.error(f"Erreur détection locuteurs: {str(e)}")
        
        # Ensuite la transcription parallèle
        logging.info(f"Découpage de l'audio en segments de {segment_duration_ms}ms")
        segments = split_audio(str(file_path), segment_duration_ms, start_ms, stop_ms)
        
        logging.info(f"Transcription de {len(segments)} segments sur {MAX_WORKERS} cœurs")
        
        # Préparer les arguments pour chaque segment
        args_list = [(seg, model_name, language, config.config['compute_type'], config.config['cpu_threads']) for seg in segments]
        
        results = []
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_segment = {executor.submit(transcribe_segment, args): args for args in args_list}
            
            for future in as_completed(future_to_segment):
                try:
                    result = future.result()
                    results.append(result)
                    logging.info(f"Segment {result['index']} transcrit")
                except Exception as e:
                    logging.error(f"Erreur future: {str(e)}")
        
        results.sort(key=lambda x: x['index'])
        
        # Formater avec les locuteurs détectés
        full_text = format_transcript(results, speaker_segments, add_timestamps)
        
        output_format = options.get('output_format', 'html')
        result_path = RESULTS_FOLDER / f"{file_id}_result.{output_format}"
        
        if output_format == 'html':
            save_as_html(result_path, full_text, file.filename)
        elif output_format == 'vtt':
            save_as_vtt(result_path, results)
        else:
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        os.remove(file_path)
        
        with open(log_file, 'w') as f:
            f.write(f"Transcription réussie\n")
            f.write(f"Fichier: {file.filename}\n")
            f.write(f"Segments: {len(results)}\n")
            f.write(f"Locuteurs détectés: {len(speaker_segments)}\n")
            f.write(f"Workers: {MAX_WORKERS}\n")
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'result': {
                'full_text': full_text,
                'segments': results,
                'num_segments': len(segments),
                'num_workers': MAX_WORKERS,
                'speaker_segments': len(speaker_segments)
            },
            'download_url': f'/api/download/{file_id}',
            'output_format': output_format
        })
    
    except Exception as e:
        logging.error(f"Erreur de transcription: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        with open(log_file, 'w') as f:
            f.write(f"ERREUR: {str(e)}\n")
            f.write(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<file_id>', methods=['GET'])
def download_result(file_id):
    for ext in ['html', 'vtt', 'txt']:
        result_path = RESULTS_FOLDER / f"{file_id}_result.{ext}"
        if result_path.exists():
            return send_file(result_path, as_attachment=True, download_name=f'transcription.{ext}')
    
    return jsonify({'error': 'Fichier introuvable'}), 404

@app.route('/api/models', methods=['GET'])
def list_models():
    return jsonify({
        'models': ['tiny', 'base', 'small', 'medium', 'large-v3', 'large-v3-turbo']
    })

def generate_summary_with_ollama(transcript_text, model="llama3.2:3b"):
    """Génère un compte rendu avec Ollama"""
    try:
        logging.info(f"Génération du compte rendu avec le modèle {model}...")
        
        prompt = f"""Tu es un assistant qui génère des comptes rendus structurés de réunions et d'entretiens.

Voici la transcription complète :

{transcript_text}

Génère un compte rendu structuré avec :
1. RÉSUMÉ EXÉCUTIF (2-3 phrases maximum)
2. POINTS CLÉS ABORDÉS (liste à puces)
3. DÉCISIONS PRISES (si applicable)
4. ACTIONS À ENTREPRENDRE (si mentionnées)
5. PARTICIPANTS IDENTIFIÉS (si mentionnés)

Sois concis, professionnel et structuré."""

        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            },
            timeout=600  # 10 minutes max
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('response', '')
            logging.info("Compte rendu généré avec succès")
            return summary
        else:
            raise Exception(f"Erreur Ollama: {response.status_code}")
            
    except Exception as e:
        logging.error(f"Erreur génération compte rendu: {str(e)}")
        return None

@app.route('/api/generate-summary', methods=['POST'])
def generate_summary():
    """Génère un compte rendu à partir d'une transcription existante"""
    try:
        data = request.json
        file_id = data.get('file_id')
        model = data.get('model', 'llama3.2:3b')
        
        if not file_id:
            return jsonify({'error': 'file_id requis'}), 400
        
        # Récupérer la transcription existante
        transcript_path = None
        for ext in ['txt', 'html']:
            path = RESULTS_FOLDER / f"{file_id}_result.{ext}"
            if path.exists():
                transcript_path = path
                break
        
        if not transcript_path:
            return jsonify({'error': 'Transcription introuvable'}), 404
        
        # Lire le contenu
        with open(transcript_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire le texte si c'est du HTML
        if transcript_path.suffix == '.html':
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text()
        
        # Générer le compte rendu
        summary = generate_summary_with_ollama(content, model)
        
        if not summary:
            return jsonify({'error': 'Erreur lors de la génération du compte rendu'}), 500
        
        # Sauvegarder le compte rendu
        summary_path = RESULTS_FOLDER / f"{file_id}_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"COMPTE RENDU\n")
            f.write(f"=" * 80 + "\n\n")
            f.write(summary)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'download_url': f'/api/download-summary/{file_id}'
        })
        
    except Exception as e:
        logging.error(f"Erreur: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-summary/<file_id>', methods=['GET'])
def download_summary(file_id):
    """Télécharge le compte rendu"""
    summary_path = RESULTS_FOLDER / f"{file_id}_summary.txt"
    
    if not summary_path.exists():
        return jsonify({'error': 'Compte rendu introuvable'}), 404
    
    return send_file(summary_path, as_attachment=True, download_name='compte_rendu.txt')

@app.route('/api/ollama-models', methods=['GET'])
def list_ollama_models():
    """Liste les modèles Ollama disponibles"""
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_list = [m['name'] for m in models]
            return jsonify({'models': model_list})
        return jsonify({'models': ['llama3.2:3b', 'mistral-nemo:latest']})
    except:
        return jsonify({'models': ['llama3.2:3b', 'mistral-nemo:latest']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)