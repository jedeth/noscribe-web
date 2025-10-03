# noScribe Web - Guide d'utilisation

## 📋 Présentation

noScribe Web est une application de transcription audio automatique avec intelligence artificielle. Elle permet de :
- Transcrire automatiquement vos fichiers audio/vidéo
- Détecter et identifier les différents locuteurs
- Générer automatiquement des comptes rendus structurés
- Traiter les fichiers en parallèle pour une vitesse maximale

## 🎯 Fonctionnalités principales

### 1. Transcription audio
- **Formats supportés** : MP3, WAV, M4A, MP4, AVI, et la plupart des formats audio/vidéo
- **Langues supportées** : Français, Anglais, Espagnol, Allemand, Italien, Portugais, et 60+ autres langues
- **Traitement parallèle** : Utilise tous les cœurs de votre processeur pour une transcription rapide

### 2. Détection des locuteurs
- Identification automatique des différents intervenants
- Séparation claire des prises de parole
- Détection automatique du nombre de locuteurs ou nombre fixe

### 3. Génération de comptes rendus
- Résumé exécutif automatique
- Extraction des points clés
- Identification des décisions et actions
- Plusieurs modèles d'IA disponibles selon vos besoins

## 🚀 Utilisation

### Accès à l'application

Ouvrez votre navigateur web et allez à l'adresse fournie par votre administrateur :
```
http://adresse-du-serveur:5000
```

### Étape 1 : Sélectionner votre fichier audio

1. Cliquez sur la zone de téléchargement ou glissez-déposez votre fichier
2. Les formats acceptés : MP3, WAV, M4A, MP4, etc.
3. Le nom du fichier s'affiche une fois chargé

### Étape 2 : Configurer la transcription

#### Paramètres de base

**Format de sortie**
- **HTML** (recommandé) : Format compatible avec Word, LibreOffice, et logiciels d'analyse qualitative
- **VTT** : Format sous-titres, utile pour la vidéo
- **TXT** : Texte brut simple

**Plage de temps**
- **Début** : Démarrer la transcription à un moment précis (format HH:MM:SS)
- **Fin** : Arrêter à un moment précis (laisser vide pour tout transcrire)
- Utile pour tester avec un extrait avant de lancer la transcription complète

**Langue**
- Sélectionnez la langue de l'audio
- "Détection automatique" fonctionne bien mais la langue fixe est plus rapide
- "Multilingue" si l'audio contient plusieurs langues

**Qualité**
- **Précis** (recommandé) : Meilleure qualité, temps plus long
- **Rapide** : Transcription plus rapide, peut nécessiter plus de corrections

#### Paramètres avancés

**Marquer les pauses**
- Indique les silences dans la transcription
- Format : (..) pour 2 secondes, (XX secondes pause) pour les longues pauses
- Options : aucune, 1sec+, 2sec+, 3sec+

**Détection des locuteurs**
- **Aucune** : Transcription continue sans séparation
- **Automatique** : Détecte le nombre de locuteurs automatiquement
- **2-6 locuteurs** : Fixe le nombre de personnes à identifier

**Options supplémentaires**
- ☑ **Parole simultanée** : Marque les chevauchements (//texte//)
- ☑ **Disfluences** : Transcrit les "euh", "hum", mots inachevés
- ☑ **Timestamps** : Ajoute l'horodatage [HH:MM:SS] dans le texte

**Durée des segments**
- Taille des morceaux pour le traitement parallèle
- 60 secondes recommandé (équilibre vitesse/qualité)
- Vous pouvez réduire à 30s pour des fichiers courts

### Étape 3 : Lancer la transcription

1. Cliquez sur **"Démarrer la transcription"**
2. Suivez la progression dans le journal et la barre de progression
3. La durée dépend de la taille du fichier et des paramètres choisis

**Temps de traitement estimé** (pour 1h d'audio) :
- Mode Rapide sans locuteurs : 5-10 minutes
- Mode Précis sans locuteurs : 15-30 minutes
- Avec détection des locuteurs : +5-10 minutes

### Étape 4 : Consulter et télécharger

Une fois terminé :
1. Le texte transcrit s'affiche à l'écran
2. Les statistiques apparaissent (segments, cœurs utilisés, mots)
3. Cliquez sur **"Télécharger"** pour sauvegarder le fichier

### Étape 5 : Générer un compte rendu (optionnel)

1. Sélectionnez un modèle d'IA dans la liste déroulante :
   - **Llama 3.2 3B** : Rapide, recommandé pour la plupart des cas
   - **Mistral Nemo 12B** : Bon équilibre qualité/vitesse
   - **Llama 3.3 70B** : Très précis, pour les documents importants
   - **Gemma 3 12B** : Alternative de qualité

2. Cliquez sur **"Compte rendu"**
3. Patientez pendant la génération (1-5 minutes)
4. Le compte rendu structuré s'affiche avec :
   - Résumé exécutif
   - Points clés
   - Décisions prises
   - Actions à entreprendre
5. Téléchargez le compte rendu avec **"Télécharger CR"**

## 💡 Conseils d'utilisation

### Pour une transcription de qualité

1. **Qualité audio** : Plus l'enregistrement est clair, meilleure sera la transcription
   - Évitez les enregistrements avec beaucoup de bruit de fond
   - Privilégiez un micro de qualité

2. **Testez d'abord** : 
   - Utilisez les champs Début/Fin pour transcrire 1-2 minutes
   - Vérifiez la qualité avant de lancer la transcription complète

3. **Choix du modèle** :
   - **Rapide** : Convient pour des notes personnelles, réunions informelles
   - **Précis** : Pour des entretiens, interviews, documents officiels

4. **Détection des locuteurs** :
   - Fonctionne mieux avec des voix distinctes
   - Si vous connaissez le nombre exact de personnes, indiquez-le
   - Nécessite une qualité audio correcte

### Pour un compte rendu efficace

1. **Choix du modèle LLM** :
   - Llama 3.2 3B : Rapide (30-60 secondes), bon pour réunions courtes
   - Mistral Nemo : Équilibré, recommandé usage général
   - Llama 3.3 70B : Lent (5+ minutes) mais très détaillé

2. **Relecture nécessaire** :
   - Le compte rendu est une aide, pas un remplacement
   - Vérifiez toujours les points importants
   - Ajustez selon vos besoins spécifiques

## 🔧 Résolution des problèmes courants

### La transcription est lente
- Vérifiez que le serveur n'est pas surchargé
- Essayez le mode "Rapide" au lieu de "Précis"
- Réduisez la durée des segments à 30 secondes

### Erreurs de transcription
- Vérifiez la qualité audio du fichier source
- Assurez-vous que la langue sélectionnée est correcte
- Utilisez le mode "Précis" pour plus de qualité

### La détection des locuteurs ne fonctionne pas
- Cette fonction nécessite une bonne qualité audio
- Essayez de spécifier le nombre exact de locuteurs
- Vérifiez que les voix sont suffisamment distinctes

### Le compte rendu n'est pas pertinent
- Essayez un modèle plus puissant (Llama 3.3 70B)
- Vérifiez que la transcription est correcte d'abord
- Pour les documents très spécialisés, une relecture humaine est recommandée

### Erreur "Serveur déconnecté"
- Contactez votre administrateur système
- Le service peut être en maintenance

## 📞 Support

Pour toute question ou problème :
1. Consultez d'abord ce guide
2. Contactez votre service informatique
3. Conservez les fichiers de log en cas de problème technique

## ⚖️ Confidentialité et sécurité

- Tous les traitements sont effectués localement sur votre serveur
- Aucune donnée n'est envoyée sur internet
- Les fichiers temporaires sont automatiquement supprimés après traitement
- Les transcriptions et comptes rendus sont stockés temporairement (7 jours par défaut)

## 📝 Notes importantes

- **Vérification obligatoire** : Toute transcription automatique contient des erreurs. Une relecture complète est indispensable avant utilisation officielle.
- **Confidentialité** : Ne transcrivez que des fichiers dont vous avez le droit
- **Sauvegarde** : Téléchargez vos fichiers rapidement, ils ne sont pas conservés indéfiniment