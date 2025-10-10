#!/usr/bin/env python3
"""Supprime les paramètres non supportés et augmente la fusion"""

with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = 0

for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue
    
    # Supprimer les lignes min_duration_on/off
    if "diarization_params['min_duration_on']" in line:
        skip_next = 1  # Sauter aussi la ligne suivante
        continue
    
    if "min_duration_on: 0.8s" in line or "min_duration_off: 0.8s" in line:
        continue
    
    if 'logging.info("Paramètres anti-sur-segmentation:")' in line:
        skip_next = 2
        continue
    
    # Changer le seuil de fusion
    if 'MERGE_THRESHOLD = 1.5' in line:
        new_lines.append('            MERGE_THRESHOLD = 2.0  # Fusion agressive\n')
        continue
    
    new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print("✓ Paramètres non supportés supprimés")
print("✓ MERGE_THRESHOLD augmenté à 2.0s")
print("  Redémarrez: python app.py")