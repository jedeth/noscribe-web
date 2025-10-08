
#!/usr/bin/env python3
"""Patch pour pyannote.audio 4.0 - DiarizeOutput"""

with open('app.py', 'r') as f:
    lines = f.readlines()

# Trouver et remplacer la section problématique
in_section = False
new_lines = []
skip_until_except = False

for i, line in enumerate(lines):
    # Détecter le début de la section à remplacer
    if '# Convertir le résultat en format utilisable' in line and 'speaker_segments = []' in lines[i+2] if i+2 < len(lines) else False:
        in_section = True
        # Ajouter le nouveau code
        new_lines.append('        # Convertir le résultat en format utilisable\n')
        new_lines.append('        # Compatible avec pyannote.audio 4.0+ (DiarizeOutput)\n')
        new_lines.append('        speaker_segments = []\n')
        new_lines.append('        \n')
        new_lines.append('        # Explorer l\'objet pour comprendre son API (debug)\n')
        new_lines.append('        logging.info(f"Type de diarization: {type(diarization)}")\n')
        new_lines.append('        \n')
        new_lines.append('        try:\n')
        new_lines.append('            # pyannote 4.0+ : DiarizeOutput wrapper\n')
        new_lines.append('            # Les segments sont dans l\'attribut speaker_diarization\n')
        new_lines.append('            if hasattr(diarization, \'speaker_diarization\'):\n')
        new_lines.append('                logging.info("Utilisation de diarization.speaker_diarization")\n')
        new_lines.append('                annotation = diarization.speaker_diarization\n')
        new_lines.append('                \n')
        new_lines.append('                # L\'annotation a la méthode itertracks()\n')
        new_lines.append('                for turn, _, speaker in annotation.itertracks(yield_label=True):\n')
        new_lines.append('                    speaker_segments.append({\n')
        new_lines.append('                        \'start\': turn.start,\n')
        new_lines.append('                        \'end\': turn.end,\n')
        new_lines.append('                        \'speaker\': f"SPEAKER_{speaker}"\n')
        new_lines.append('                    })\n')
        new_lines.append('            \n')
        new_lines.append('            # pyannote 3.x : Annotation directe avec itertracks\n')
        new_lines.append('            elif hasattr(diarization, \'itertracks\'):\n')
        new_lines.append('                logging.info("Utilisation de diarization.itertracks() (v3.x)")\n')
        new_lines.append('                for turn, _, speaker in diarization.itertracks(yield_label=True):\n')
        new_lines.append('                    speaker_segments.append({\n')
        new_lines.append('                        \'start\': turn.start,\n')
        new_lines.append('                        \'end\': turn.end,\n')
        new_lines.append('                        \'speaker\': f"SPEAKER_{speaker}"\n')
        new_lines.append('                    })\n')
        new_lines.append('            \n')
        new_lines.append('            else:\n')
        new_lines.append('                logging.error("API pyannote non reconnue")\n')
        new_lines.append('                logging.error(f"Attributs disponibles: {[a for a in dir(diarization) if not a.startswith(\'_\')]}")\n')
        new_lines.append('        \n')
        new_lines.append('        except Exception as e:\n')
        new_lines.append('            logging.error(f"Erreur lors de l\'extraction des segments: {e}")\n')
        new_lines.append('            import traceback\n')
        new_lines.append('            logging.error(traceback.format_exc())\n')
        skip_until_except = True
        continue
    
    # Sauter les lignes de l'ancienne section jusqu'au prochain except qui n'est pas dans notre nouveau code
    if skip_until_except:
        # Chercher la ligne "# Nettoyer" ou "try:" qui suit notre section
        if '# Nettoyer' in line or ('try:' in line and 'os.remove' in lines[i+1] if i+1 < len(lines) else False):
            skip_until_except = False
            new_lines.append(line)
        continue
    
    new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print("✓ Patch appliqué pour pyannote.audio 4.0")
print("  Redémarrez app.py")
