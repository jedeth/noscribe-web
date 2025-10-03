noScribe Web - Guide d'installation technique
📋 Vue d'ensemble
noScribe Web est une application Flask qui utilise :

faster-whisper : Transcription audio optimisée CPU
pyannote.audio : Détection et diarisation des locuteurs
Ollama : Génération de comptes rendus avec LLM locaux
Traitement parallèle : Exploitation maximale des cœurs CPU
🖥️ Prérequis système
Configuration minimale
OS : Red Hat Enterprise Linux 9.4 (ou compatible : CentOS Stream 9, Rocky Linux 9, AlmaLinux 9)
CPU : 8 cœurs minimum (72 cœurs recommandés pour performances optimales)
RAM : 16 GB minimum (512 GB utilisés pour les tests, 32 GB recommandés)
Espace disque : 50 GB minimum
Python : 3.11+
FFmpeg : Pour le traitement audio
Configuration recommandée
CPU multi-cœurs (32+ cœurs)
RAM : 64 GB+
SSD pour stockage temporaire
Réseau local rapide si accès distant
📦 Installation sur Red Hat 9.4
1. Préparation du système
bash
# Mise à jour du système
sudo dnf update -y

# Installation des dépendances système
sudo dnf install -y \
    python3.11 \
    python3.11-devel \
    python3.11-pip \
    gcc \
    gcc-c++ \
    make \
    git \
    wget \
    curl \
    htop \
    vim \
    policycoreutils-python-utils

# Installation de FFmpeg via RPM Fusion
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
sudo dnf install -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm
sudo dnf install -y ffmpeg ffmpeg-devel

# Vérification
python3.11 --version
ffmpeg -version
2. Configuration du firewall
bash
# Autoriser le port 5000 (développement)
sudo firewall-cmd --permanent --add-port=5000/tcp

# Autoriser HTTP/HTTPS (production)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Recharger
sudo firewall-cmd --reload
3. Configuration SELinux
bash
# Vérifier l'état
getenforce

# Configurer les permissions (recommandé)
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1
sudo setsebool -P httpd_read_user_content 1

# Autoriser le port
sudo semanage port -a -t http_port_t -p tcp 5000

# Ou en mode permissif pour tests (NON recommandé en production)
sudo setenforce 0
4. Installation de l'application
bash
# Créer le répertoire
cd ~
mkdir -p noscribe-web
cd noscribe-web

# Créer l'environnement virtuel avec Python 3.11
python3.11 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Mettre à jour pip
pip install --upgrade pip setuptools wheel

# Installer les dépendances
pip install flask==3.0.0 \
    flask-cors==4.0.0 \
    faster-whisper==1.0.0 \
    pydub==0.25.1 \
    gunicorn==21.2.0 \
    pyyaml==6.0.1 \
    pyannote.audio==3.1.1 \
    beautifulsoup4==4.12.0 \
    requests==2.32.0
5. Configuration HuggingFace (pour pyannote)
bash
# Installer le CLI
pip install huggingface_hub

# Se connecter
huggingface-cli login
# Entrez votre token HuggingFace

# Accepter les conditions sur :
# https://huggingface.co/pyannote/speaker-diarization-3.1
# https://huggingface.co/pyannote/segmentation-3.0
# https://huggingface.co/pyannote/speaker-diarization-community-1
6. Installation d'Ollama
bash
# Télécharger et installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Vérifier l'installation
ollama --version

# Télécharger les modèles recommandés
ollama pull llama3.2:3b      # Rapide, 2 GB
ollama pull mistral-nemo     # Équilibré, 7 GB
ollama pull llama3.3:70b     # Précis, 42 GB (optionnel)

# Lister les modèles installés
ollama list

# Démarrer le service Ollama
sudo systemctl enable ollama
sudo systemctl start ollama
7. Structure des fichiers
bash
# Créer la structure
mkdir -p ~/noscribe-web/{static,models,logs}
mkdir -p /tmp/noscribe_uploads
mkdir -p /tmp/noscribe_results
mkdir -p ~/.noscribe_web/log

# Permissions
chmod 755 /tmp/noscribe_uploads
chmod 755 /tmp/noscribe_results
Copiez les fichiers :

app.py → ~/noscribe-web/app.py
static/index.html → ~/noscribe-web/static/index.html
8. Configuration système pour haute performance
bash
# Éditer /etc/security/limits.conf
sudo tee -a /etc/security/limits.conf << EOF
* soft nofile 1048576
* hard nofile 1048576
* soft nproc 1048576
* hard nproc 1048576
EOF

# Éditer /etc/sysctl.conf
sudo tee -a /etc/sysctl.conf << EOF
fs.file-max = 2097152
kernel.pid_max = 4194304
vm.swappiness = 10
vm.max_map_count = 262144
net.core.somaxconn = 65535
EOF

# Appliquer
sudo sysctl -p

# Recharger les limites (logout/login requis)
🚀 Déploiement
Mode développement
bash
cd ~/noscribe-web
source venv/bin/activate
python app.py
# Accès : http://localhost:5000
Mode production avec Gunicorn
Fichier gunicorn_config.py
python
import multiprocessing

bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 100
timeout = 7200
keepalive = 5
graceful_timeout = 30

accesslog = "/home/iarag/noscribe-web/logs/access.log"
errorlog = "/home/iarag/noscribe-web/logs/error.log"
loglevel = "info"
capture_output = True

proc_name = "noscribe-web"
preload_app = False
max_requests = 100
max_requests_jitter = 10
Service systemd
Créer /etc/systemd/system/noscribe-web.service :

ini
[Unit]
Description=noScribe Web - Transcription Audio AI
After=network.target

[Service]
Type=notify
User=iarag
Group=iarag
WorkingDirectory=/home/iarag/noscribe-web
Environment="PATH=/home/iarag/noscribe-web/venv/bin"
Environment="PYTHONUNBUFFERED=1"

LimitNOFILE=65536
LimitNPROC=65536

ExecStart=/home/iarag/noscribe-web/venv/bin/gunicorn -c gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30
Restart=on-failure
RestartSec=5s

PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
Activer et démarrer :

bash
sudo systemctl daemon-reload
sudo systemctl enable noscribe-web
sudo systemctl start noscribe-web
sudo systemctl status noscribe-web

# Logs
sudo journalctl -u noscribe-web -f
Nginx comme reverse proxy
Installer Nginx :

bash
sudo dnf install -y nginx
Créer /etc/nginx/conf.d/noscribe.conf :

nginx
upstream noscribe_backend {
    server 127.0.0.1:5000 fail_timeout=0;
}

server {
    listen 80;
    server_name votre-domaine.com;

    client_max_body_size 2G;
    client_body_timeout 7200s;

    access_log /var/log/nginx/noscribe_access.log;
    error_log /var/log/nginx/noscribe_error.log;

    location / {
        root /home/iarag/noscribe-web/static;
        index index.html;
        try_files $uri $uri/ =404;
    }

    location /api {
        proxy_pass http://noscribe_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 7200s;
        proxy_send_timeout 7200s;
        proxy_read_timeout 7200s;
        
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
Permissions SELinux pour Nginx :

bash
sudo chmod 755 /home/iarag
sudo chmod 755 /home/iarag/noscribe-web
sudo chmod 755 /home/iarag/noscribe-web/static
sudo chcon -R -t httpd_sys_content_t /home/iarag/noscribe-web/static
Activer :

bash
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
HTTPS avec Let's Encrypt
bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
🔧 Configuration avancée
Paramètres de performance
Dans app.py, ajustez selon vos ressources :

python
# Configuration CPU
SEGMENT_DURATION_MS = 60000  # Durée des segments (ms)
MAX_WORKERS = 72             # Nombre de cœurs à utiliser
CPU_THREADS = 4              # Threads par worker
Optimisation des modèles Whisper
Les modèles sont téléchargés automatiquement au premier usage dans :

~/.cache/huggingface/hub/
Pour pré-télécharger :

python
from faster_whisper import WhisperModel

# Modèles disponibles
models = ['tiny', 'base', 'small', 'medium', 'large-v3']

for model_name in models:
    print(f"Téléchargement de {model_name}...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
Nettoyage automatique des fichiers temporaires
Créer /etc/cron.daily/noscribe-cleanup :

bash
#!/bin/bash
# Nettoyer les fichiers de plus de 24h
find /tmp/noscribe_uploads -type f -mtime +1 -delete
find /tmp/noscribe_results -type f -mtime +7 -delete
Rendre exécutable :

bash
sudo chmod +x /etc/cron.daily/noscribe-cleanup
Rotation des logs
Créer /etc/logrotate.d/noscribe :

/home/iarag/noscribe-web/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 iarag iarag
    sharedscripts
    postrotate
        systemctl reload noscribe-web > /dev/null 2>&1 || true
    endscript
}
📊 Monitoring et performances
Surveillance des ressources
bash
# CPU et mémoire en temps réel
htop

# Processus Python actifs
ps aux | grep python

# Utilisation disque
df -h /tmp

# Logs applicatifs
tail -f ~/noscribe-web/logs/error.log

# Logs système
sudo journalctl -u noscribe-web -f
Tests de performance
bash
# Test de charge CPU
stress-ng --cpu 72 --timeout 60s --metrics

# Benchmark transcription
time curl -F "file=@test_1hour.mp3" \
     -F 'options={"quality":"precise","language":"fr"}' \
     http://localhost:5000/api/transcribe
Métriques attendues (72 cœurs, 512 GB RAM)
Durée audio	Mode rapide	Mode précis	Avec diarisation
10 minutes	1-2 min	3-5 min	+2 min
1 heure	5-10 min	15-30 min	+10 min
3 heures	15-30 min	45-90 min	+30 min
🐛 Débogage
Problèmes courants
Erreur : Port 5000 déjà utilisé
bash
# Trouver le processus
sudo lsof -i :5000

# Tuer le processus
sudo kill -9 <PID>
Erreur : Permission denied
bash
# Vérifier les permissions
ls -laZ /home/iarag/noscribe-web/

# Corriger SELinux
sudo restorecon -Rv /home/iarag/noscribe-web/
Ollama ne répond pas
bash
# Vérifier le service
sudo systemctl status ollama

# Redémarrer
sudo systemctl restart ollama

# Tester directement
curl http://localhost:11434/api/tags
Modèles Whisper lents
bash
# Vérifier le compute_type (doit être "int8" sur CPU)
# Dans app.py :
compute_type = 'int8'  # Le plus rapide sur CPU
Logs de débogage
bash
# Activer le mode debug (développement uniquement)
# Dans app.py :
app.run(host='0.0.0.0', port=5000, debug=True)

# Logs détaillés
export FLASK_DEBUG=1
export WERKZEUG_DEBUG_PIN=off
python app.py
🔐 Sécurité
Recommandations
Ne jamais exposer directement sur Internet sans reverse proxy
Toujours utiliser HTTPS en production
Implémenter une authentification si nécessaire
Limiter les tailles de fichiers uploadés
Nettoyer régulièrement les fichiers temporaires
Surveiller les logs pour détecter les abus
Authentification basique (optionnel)
Dans app.py, ajouter :

python
from flask_httpauth import HTTPBasicAuth
from werkzeug.security.py import generate_password_hash, check_password_hash

auth = HTTPBasicAuth()

users = {
    "admin": generate_password_hash("votre_mot_de_passe")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Protéger les routes
@app.route('/api/transcribe', methods=['POST'])
@auth.login_required
def transcribe():
    # ...
📚 API Documentation
Endpoints disponibles
GET /api/health
Vérification de l'état du serveur

Réponse:

json
{
    "status": "ok",
    "available_cores": 72,
    "configured_workers": 72,
    "compute_type": "int8",
    "device": "CPU (optimized for 512GB RAM)"
}
POST /api/transcribe
Lancer une transcription

Paramètres:

file: Fichier audio (multipart/form-data)
options: JSON avec configuration
Exemple options:

json
{
    "language": "fr",
    "quality": "precise",
    "output_format": "html",
    "start_time": "00:00:00",
    "stop_time": "",
    "speaker_detection": "auto",
    "timestamps": true,
    "segment_duration": 60000
}
POST /api/generate-summary
Générer un compte rendu

Paramètres:

json
{
    "file_id": "uuid-du-fichier",
    "model": "llama3.2:3b"
}
GET /api/download/{file_id}
Télécharger la transcription

GET /api/download-summary/{file_id}
Télécharger le compte rendu

GET /api/models
Liste des modèles Whisper disponibles

GET /api/ollama-models
Liste des modèles Ollama disponibles

🔄 Mises à jour
Mise à jour de l'application
bash
cd ~/noscribe-web
source venv/bin/activate

# Mise à jour des dépendances
pip install --upgrade flask faster-whisper pyannote.audio

# Redémarrer le service
sudo systemctl restart noscribe-web
Mise à jour des modèles Ollama
bash
ollama pull llama3.2:3b
ollama pull mistral-nemo
ollama list
📝 Notes techniques
Architecture du traitement parallèle
Découpage : L'audio est découpé en segments de 60s (configurable)
Distribution : Les segments sont distribués sur les 72 cœurs via ProcessPoolExecutor
Transcription : Chaque cœur transcrit son segment indépendamment avec faster-whisper
Fusion : Les résultats sont réassemblés dans l'ordre
Post-traitement : Application de la diarisation des locuteurs
Optimisations CPU
faster-whisper : 4x plus rapide que whisper standard
compute_type="int8" : Quantification pour réduire l'usage mémoire
VAD (Voice Activity Detection) : Filtre automatique des silences
Pas de GPU : Utilisation optimale des ressources CPU
Limitations connues
Temps de traitement proportionnel à la durée audio
Détection des locuteurs nécessite une bonne qualité audio
Fichiers très courts (< 30s) peuvent avoir des problèmes avec la diarisation
Les modèles LLM 70B+ nécessitent beaucoup de RAM
📞 Support technique
Pour les développeurs :

Repository GitHub : [à définir]
Issues : [à définir]
Documentation API : http://votre-serveur:5000/api/health
Version : 1.0.0
Dernière mise à jour : Octobre 2025
Testé sur : Red Hat Enterprise Linux 9.4, 72 cœurs, 512 GB RAM

