#!/bin/bash
# Script de test rapide pour diagnostiquer le problème HuggingFace
# Usage: bash quick_test.sh

echo "════════════════════════════════════════════════════════"
echo "  DIAGNOSTIC HUGGINGFACE POUR PYANNOTE"
echo "════════════════════════════════════════════════════════"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd ~/noscribe-web
source venv/bin/activate 2>/dev/null

# Test 1 : Token existe ?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1 : Recherche du token"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOKEN=""

if [ -f ~/.noscribe_web/hf_token.txt ]; then
    TOKEN=$(cat ~/.noscribe_web/hf_token.txt | tr -d '\n\r ')
    echo -e "${GREEN}✓${NC} Token trouvé dans ~/.noscribe_web/hf_token.txt"
    echo "  Longueur : ${#TOKEN} caractères"
    echo "  Début : ${TOKEN:0:10}..."
elif [ -f ~/.cache/huggingface/token ]; then
    TOKEN=$(cat ~/.cache/huggingface/token | tr -d '\n\r ')
    echo -e "${GREEN}✓${NC} Token trouvé dans ~/.cache/huggingface/token"
    echo "  Longueur : ${#TOKEN} caractères"
    echo "  Début : ${TOKEN:0:10}..."
else
    echo -e "${RED}✗${NC} AUCUN TOKEN TROUVÉ"
    echo ""
    echo "SOLUTION :"
    echo "  1. Créez un token sur : https://huggingface.co/settings/tokens"
    echo "  2. Exécutez : huggingface-cli login"
    echo "  3. OU créez : ~/.noscribe_web/hf_token.txt"
    echo ""
    exit 1
fi

# Test 2 : Format du token
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2 : Validation du format"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $TOKEN =~ ^hf_[a-zA-Z0-9]{32,}$ ]]; then
    echo -e "${GREEN}✓${NC} Format valide (hf_...)"
else
    echo -e "${RED}✗${NC} Format suspect"
    echo "  Le token devrait commencer par 'hf_' et faire ~40 caractères"
    echo ""
    echo "SOLUTION : Recréez un nouveau token"
fi

# Test 3 : Import Python
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3 : Import pyannote.audio"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "from pyannote.audio import Pipeline; print('OK')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} pyannote.audio importé avec succès"
else
    echo -e "${RED}✗${NC} Erreur d'import"
    echo ""
    echo "SOLUTION :"
    echo "  pip install --upgrade pyannote.audio torch"
    exit 1
fi

# Test 4 : Token valide sur HuggingFace
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4 : Validation du token sur HuggingFace"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << PYEOF
import sys
try:
    from huggingface_hub import HfApi
    api = HfApi()
    user_info = api.whoami(token="$TOKEN")
    print(f"✓ Token valide - Utilisateur : {user_info['name']}")
    sys.exit(0)
except Exception as e:
    print(f"✗ Token invalide ou expiré")
    print(f"  Erreur : {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}PROBLÈME DÉTECTÉ${NC}"
    echo ""
    echo "SOLUTION :"
    echo "  1. Allez sur : https://huggingface.co/settings/tokens"
    echo "  2. Créez un NOUVEAU token (type 'Read')"
    echo "  3. Exécutez : huggingface-cli login"
    echo ""
    exit 1
fi

# Test 5 : Accès aux modèles
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5 : Accès aux modèles pyannote"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << PYEOF
import sys
try:
    from huggingface_hub import model_info
    
    models = [
        "pyannote/speaker-diarization-3.1",
        "pyannote/segmentation-3.0",
        "pyannote/wespeaker-voxceleb-resnet34-LM"
    ]
    
    for model_id in models:
        try:
            info = model_info(model_id, token="$TOKEN")
            print(f"✓ Accès OK : {model_id}")
        except Exception as e:
            print(f"✗ Pas d'accès : {model_id}")
            print(f"  Erreur : {str(e)[:80]}")
            print(f"  URL : https://huggingface.co/{model_id}")
            sys.exit(1)
    
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Erreur : {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}PROBLÈME D'ACCÈS AUX MODÈLES${NC}"
    echo ""
    echo "SOLUTION :"
    echo "  Acceptez les licences sur ces pages :"
    echo "  1. https://huggingface.co/pyannote/speaker-diarization-3.1"
    echo "  2. https://huggingface.co/pyannote/segmentation-3.0"
    echo "  3. https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM"
    echo ""
    echo "  Cliquez sur 'Agree and access repository' sur chaque page"
    echo ""
    exit 1
fi

# Test 6 : Chargement du pipeline
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 6 : Chargement du pipeline (peut prendre 1-5 min)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << PYEOF
import sys
try:
    from pyannote.audio import Pipeline
    print("  Téléchargement et chargement des modèles...")
    
    # Essayer avec le nouveau paramètre
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token="$TOKEN"
        )
    except TypeError:
        # Fallback pour anciennes versions
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token="$TOKEN"
        )
    
    print("✓ Pipeline chargé avec succès !")
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Erreur de chargement : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}ÉCHEC DU CHARGEMENT${NC}"
    echo ""
    echo "Causes possibles :"
    echo "  - Connexion internet instable"
    echo "  - Premier téléchargement (réessayez)"
    echo "  - Espace disque insuffisant"
    echo ""
    exit 1
fi

# Succès !
echo ""
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}✓✓✓ TOUS LES TESTS RÉUSSIS ✓✓✓${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "La diarisation avec pyannote.audio est fonctionnelle !"
echo ""
echo "Prochaines étapes :"
echo "  1. Mettez à jour la fonction detect_speakers() dans app.py"
echo "  2. Redémarrez : python app.py"
echo "  3. Testez avec un fichier audio"
echo ""