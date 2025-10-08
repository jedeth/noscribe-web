#!/usr/bin/env python3
"""Patch pour améliorer la qualité de la diarisation"""

with open('app.py', 'r') as f:
    content = f.read()

# Chercher et ajouter les paramètres après la création du pipeline
search_pattern = """        # Paramètres de diarisation
        diarization_params = {}"""

replacement = """        # Paramètres de diarisation
        diarization_params = {}
        
        # Paramètres optimisés pour réduire la sur-segmentation
        pipeline.instantiate({
            'segmentation': {
                'min_duration_on': 0.8,    # Ignore segments < 0.8s
                'min_duration_off': 0.8    # Ignore pauses < 0.8s  
            },
            'clustering': {
                'method': 'centroid',
                'min_cluster_size': 20,    # Clusters plus stables
                'threshold': 0.75          # Haute similarité requise
            }
        })
        
        logging.info("Paramètres anti-sur-segmentation appliqués")"""

if search_pattern in content:
    content = content.replace(search_pattern, replacement, 1)
    print("✓ Paramètres de pipeline ajoutés")
else:
    print("⚠ Pattern non trouvé, modification manuelle requise")

# Augmenter le seuil de fusion
content = content.replace('MERGE_THRESHOLD = 1.0', 'MERGE_THRESHOLD = 1.5')

with open('app.py', 'w') as f:
    f.write(content)

print("✓ Patch appliqué - Redémarrez app.py")