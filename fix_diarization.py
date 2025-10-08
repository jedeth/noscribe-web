#!/usr/bin/env python3
"""Patch rapide pour corriger l'API pyannote.audio 4.0"""

import re

with open('app.py', 'r') as f:
    content = f.read()

# Chercher et remplacer la section problématique
old_code = """        # Convertir le résultat en format utilisable
        speaker_segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': f"SPEAKER_{speaker}"
            })"""

new_code = """        # Convertir le résultat en format utilisable
        # Compatible avec pyannote.audio 4.0+ (DiarizeOutput)
        speaker_segments = []
        
        # Explorer l'objet pour comprendre son API
        logging.info(f"Type de diarization: {type(diarization)}")
        logging.info(f"Attributs: {[a for a in dir(diarization) if not a.startswith('_')][:10]}")
        
        try:
            # Essayer plusieurs méthodes selon la version de pyannote
            if hasattr(diarization, 'segments'):
                # pyannote 4.0+ : DiarizeOutput avec attribut segments
                logging.info("Utilisation de diarization.segments")
                for segment in diarization.segments:
                    speaker_segments.append({
                        'start': segment.start,
                        'end': segment.end,
                        'speaker': f"SPEAKER_{segment.speaker}"
                    })
            elif hasattr(diarization, 'itertracks'):
                # pyannote 3.x : Annotation avec méthode itertracks
                logging.info("Utilisation de diarization.itertracks()")
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    speaker_segments.append({
                        'start': turn.start,
                        'end': turn.end,
                        'speaker': f"SPEAKER_{speaker}"
                    })
            else:
                # Fallback : itération directe
                logging.info("Utilisation de l'itération directe")
                for item in diarization:
                    # L'item peut être un tuple (segment, track, label) ou un objet
                    if isinstance(item, tuple) and len(item) == 3:
                        segment, track, label = item
                        speaker_segments.append({
                            'start': segment.start,
                            'end': segment.end,
                            'speaker': f"SPEAKER_{label}"
                        })
                    elif hasattr(item, 'start') and hasattr(item, 'end'):
                        speaker_segments.append({
                            'start': item.start,
                            'end': item.end,
                            'speaker': f"SPEAKER_{getattr(item, 'speaker', 'UNKNOWN')}"
                        })
        except Exception as e:
            logging.error(f"Erreur lors de l'extraction des segments: {e}")
            import traceback
            logging.error(traceback.format_exc())"""

content = content.replace(old_code, new_code)

with open('app.py', 'w') as f:
    f.write(content)

print("✓ Patch appliqué avec succès")
print("  Redémarrez app.py pour tester")