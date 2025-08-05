# Analyseur de Manuels de Laboratoire

**[English version of README](README.md)**

Système d'analyse automatisé pour les manuels d'instruments de laboratoire utilisant Google Cloud Document AI et Gemini AI. Cet outil extrait les procédures, protocoles de maintenance, spécifications techniques et consignes de sécurité des manuels PDF pour générer des documents de synthèse complets.

## Fonctionnalités

- **Traitement PDF Automatisé**: Gère les PDF chiffrés et documents de plusieurs centaines de pages
- **Extraction de Texte Intelligente**: Utilise Google Cloud Document AI avec capacités OCR
- **Analyse par IA**: Exploite Gemini AI pour identifier et structurer les informations
- **Synthèse Complète**: Génère des résumés PDF professionnels et rapports JSON détaillés
- **Sortie Organisée**: Organise automatiquement les résultats dans des répertoires structurés

## Informations Extraites

Le système identifie et extrait:

- **Informations Générales**: Nom de l'instrument, fabricant, modèle, applications
- **Procédures d'Analyse**: Protocoles étape par étape avec matériels et précautions
- **Maintenance Préventive**: Plannings, procédures et points de vérification
- **Spécifications Techniques**: Paramètres de performance et exigences environnementales
- **Consignes de Sécurité**: Évaluations des risques et mesures de protection
- **Procédures de Calibration**: Contrôle qualité et exigences de standards

## Prérequis

### Google Cloud Platform
1. **Projet Google Cloud** avec facturation activée
2. **API Document AI** activée
3. **Processeur OCR Document AI** créé
4. **Compte de Service** avec rôle Document AI API User
5. **Clé JSON du compte de service** téléchargée

### Gemini AI
- **Clé API Gemini** depuis Google AI Studio

### Dépendances Python
- Python 3.8 ou supérieur
- Dépendances listées dans `requirements.txt`

## Installation

1. **Cloner le dépôt**
```bash
git clone https://github.com/votreutilisateur/lab-manual-analyzer.git
cd lab-manual-analyzer
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Exécuter le script de setup**
```bash
python setup.py
```

4. **Configurer les APIs**
   - Placer votre fichier JSON de compte de service dans `credentials/`
   - Mettre à jour `config.json` avec vos détails de projet

5. **Tester la configuration**
```bash
python test_config.py
```

## Démarrage Rapide

1. **Placer les manuels PDF** dans le répertoire `manuels/`
2. **Lancer l'analyse**:
```bash
python lab_manual_analyzer_organized.py manuels/votre_manuel.pdf
```
3. **Trouver les résultats** dans `manuels/syntheses/`

## Configuration

Éditer `config.json` avec vos paramètres Google Cloud et Gemini:

```json
{
  "google_cloud": {
    "project_id": "votre-project-id",
    "location": "eu",
    "processor_id": "votre-processor-id",
    "credentials_path": "credentials/service-account.json"
  },
  "gemini": {
    "api_key": "votre-cle-gemini-api",
    "model": "gemini-1.5-pro"
  },
  "analysis": {
    "max_pages_per_chunk": 15,
    "delay_between_requests": 2
  }
}
```

## Structure de Sortie

```
manuels/
├── votre_manuel.pdf              # PDF source
└── syntheses/
    ├── votre_manuel_SYNTHESE.pdf      # Résumé professionnel
    └── votre_manuel_ANALYSE_COMPLETE.json  # Analyse détaillée
```

## Utilisation Avancée

### Traitement par Lots
```bash
# Traiter tous les PDF du répertoire
for pdf in manuels/*.pdf; do
    python lab_manual_analyzer_organized.py "$pdf"
done
```

### Configuration Personnalisée
```bash
python lab_manual_analyzer_organized.py manuel.pdf --config config_personnalise.json
```

## Détails Techniques

### Pipeline de Traitement de Document
1. **Préparation PDF**: Déchiffrement automatique si protégé par mot de passe
2. **Découpage Intelligent**: Divise les gros documents (>15 pages) pour les limites API
3. **Extraction OCR**: Utilise Document AI pour extraction de texte robuste
4. **Analyse IA**: Gemini AI identifie et structure les informations
5. **Génération de Synthèse**: Crée des sorties PDF professionnelles et JSON

### Limites API et Coûts
- **Document AI**: 15 pages par requête, ~1$ pour 1000 pages
- **Gemini**: ~7$ par 1M de tokens, manuel typique coûte 1-2$
- **Temps de Traitement**: 5-20 minutes par manuel selon la taille

## Dépannage

### Problèmes Courants

**Erreur "PAGE_LIMIT_EXCEEDED"**
- S'assurer que le processeur Document AI est correctement configuré
- Vérifier que les chunks font ≤15 pages

**Erreurs de Parsing JSON**
- Augmenter le délai entre requêtes dans la config
- Vérifier les quotas API Gemini

**Aucun Texte Extrait**
- Vérifier que le PDF n'est pas corrompu ou uniquement composé d'images
- Vérifier les permissions du compte de service

### Fichiers de Support
- Consulter `lab_analysis.log` pour les logs détaillés
- Revoir la sortie de `test_config.py` pour les problèmes de configuration

## Contribution

1. Fork le dépôt
2. Créer une branche de fonctionnalité
3. Faire les modifications avec tests appropriés
4. Soumettre une pull request

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour les détails.

## Citation

Si vous utilisez cet outil dans une recherche académique, veuillez citer:

```
Lab Manual Analyzer: Analyse Automatisée de Documentation d'Instruments de Laboratoire
[Vos détails ici]
```

## Remerciements

- Google Cloud Document AI pour les capacités OCR
- Google Gemini AI pour l'analyse intelligente de texte
- ReportLab pour la génération PDF