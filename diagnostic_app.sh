#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "  DIAGNOSTIC COMPLET NOSCRIBE WEB"
echo "════════════════════════════════════════════════════════"
echo ""

# Test 1 : Dossiers temporaires
echo "━━━ Test 1 : Dossiers temporaires ━━━"
if [ -d /tmp/noscribe_uploads ]; then
    echo "✓ /tmp/noscribe_uploads existe"
    ls -ld /tmp/noscribe_uploads
else
    echo "✗ /tmp/noscribe_uploads n'existe pas"
    echo "  Création..."
    mkdir -p /tmp/noscribe_uploads
    chmod 755 /tmp/noscribe_uploads
fi

if [ -d /tmp/noscribe_results ]; then
    echo "✓ /tmp/noscribe_results existe"
    ls -ld /tmp/noscribe_results
else
    echo "✗ /tmp/noscribe_results n'existe pas"
    echo "  Création..."
    mkdir -p /tmp/noscribe_results
    chmod 755 /tmp/noscribe_results
fi

# Test 2 : Backend Flask répond
echo ""
echo "━━━ Test 2 : Backend Flask ━━━"
HEALTH=$(curl -s http://localhost:5000/api/health 2>&1)
if [ $? -eq 0 ]; then
    echo "✓ Backend Flask répond"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "✗ Backend Flask ne répond pas"
    echo "  Vérifiez que python app.py est lancé"
fi

# Test 3 : Fichier audio de test
echo ""
echo "━━━ Test 3 : Création fichier de test ━━━"
if command -v ffmpeg &> /dev/null; then
    echo "Génération d'un fichier audio de test..."
    ffmpeg -f lavfi -i "sine=frequency=1000:duration=3" -y test_audio.wav 2>/dev/null
    if [ -f test_audio.wav ]; then
        echo "✓ test_audio.wav créé ($(du -h test_audio.wav | cut -f1))"
    fi
else
    echo "⚠ ffmpeg non disponible, utilisez votre propre fichier audio"
fi

# Test 4 : Upload via API
echo ""
echo "━━━ Test 4 : Upload via API ━━━"
if [ -f test_audio.wav ]; then
    echo "Upload de test_audio.wav via API..."
    RESULT=$(curl -s -X POST http://localhost:5000/api/transcribe \
      -F "file=@test_audio.wav" \
      -F 'options={"language":"fr","quality":"fast","speaker_detection":"none","timestamps":false,"segment_duration":60000}' \
      2>&1)
    
    if echo "$RESULT" | grep -q "success"; then
        echo "✓ Upload et transcription réussis !"
        echo "$RESULT" | python3 -m json.tool 2>/dev/null | head -20
    else
        echo "✗ Erreur lors de l'upload"
        echo "$RESULT" | head -20
    fi
else
    echo "⚠ Pas de fichier de test disponible"
fi

# Test 5 : Vérifier les processus Python
echo ""
echo "━━━ Test 5 : Processus Python actifs ━━━"
ps aux | grep -E "python.*app.py" | grep -v grep || echo "✗ Aucun processus Flask trouvé"

echo ""
echo "════════════════════════════════════════════════════════"
echo "  FIN DU DIAGNOSTIC"
echo "════════════════════════════════════════════════════════"
DIAGEOF
sour    