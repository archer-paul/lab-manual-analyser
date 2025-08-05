#!/usr/bin/env python3
"""
Script de setup automatique pour Lab Manual Analyzer
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou supérieur requis")
        return False
    print(f"✅ Python {sys.version} détecté")
    return True

def install_requirements():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dépendances installées avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances: {e}")
        return False

def create_directories():
    """Crée les dossiers nécessaires"""
    directories = [
        "manuels",
        "output",
        "logs",
        "credentials"
    ]
    
    print("📁 Création des dossiers...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   - {directory}/")
    
    print("✅ Dossiers créés")

def create_config_if_needed():
    """Crée le fichier de configuration si nécessaire"""
    config_path = Path("config.json")
    
    if config_path.exists():
        print("✅ Fichier config.json existant trouvé")
        return
    
    print("📝 Création du fichier de configuration...")
    
    default_config = {
        "google_cloud": {
            "project_id": "YOUR_PROJECT_ID",
            "location": "us",
            "processor_id": "YOUR_LAYOUT_PROCESSOR_ID", 
            "credentials_path": "credentials/service-account.json"
        },
        "gemini": {
            "api_key": "YOUR_GEMINI_API_KEY",
            "model": "gemini-1.5-pro"
        },
        "analysis": {
            "max_pages_per_chunk": 50,
            "overlap_pages": 5,
            "delay_between_requests": 2,
            "max_tokens_per_request": 1000000
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print("✅ Fichier config.json créé")
    print("⚠️  IMPORTANT: Vous devez remplir config.json avec vos clés API")

def create_example_script():
    """Crée un script d'exemple d'utilisation"""
    example_script = '''#!/usr/bin/env python3
"""
Exemple d'utilisation de Lab Manual Analyzer
"""

from lab_manual_analyzer import LabManualAnalyzer
from pathlib import Path

def main():
    # Initialisation de l'analyseur
    analyzer = LabManualAnalyzer("config.json")
    
    # Exemple 1: Analyser un seul manuel
    manuel_path = Path("manuels/mon_manuel.pdf")
    if manuel_path.exists():
        print("Analyse du manuel...")
        result = analyzer.analyze_manual(manuel_path)
        
        if result.get("success"):
            print(f"✅ Analyse réussie!")
            print(f"Synthèse: {result['synthesis_file']}")
        else:
            print(f"❌ Erreur: {result.get('error')}")
    
    # Exemple 2: Analyser tous les manuels d'un dossier
    print("Analyse du dossier manuels/...")
    analyzer.analyze_directory("manuels")

if __name__ == "__main__":
    main()
'''
    
    with open("exemple_utilisation.py", 'w') as f:
        f.write(example_script)
    
    print("✅ Script d'exemple créé: exemple_utilisation.py")

def create_readme():
    """Crée un fichier README"""
    readme_content = '''# Lab Manual Analyzer

Analyseur automatique de manuels d'instruments de laboratoire utilisant Google Cloud Document AI et Gemini.

## Installation

1. Exécutez le setup:
```bash
python setup.py
```

2. Configurez vos APIs dans `config.json`:
   - Project ID Google Cloud
   - Processor ID Document AI (Layout Parser)
   - Clé API Gemini
   - Chemin vers le fichier de service account

## Configuration Google Cloud

### 1. Document AI Layout Parser
```bash
# Activer l'API Document AI
gcloud services enable documentai.googleapis.com

# Créer un processeur Layout Parser
gcloud documentai processors create \\
  --display-name="Lab Manual Parser" \\
  --type="LAYOUT_PARSER_PROCESSOR" \\
  --location=us
```

### 2. Service Account
```bash
# Créer un service account
gcloud iam service-accounts create lab-analyzer \\
  --display-name="Lab Manual Analyzer"

# Donner les permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\
  --member="serviceAccount:lab-analyzer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \\
  --role="roles/documentai.apiUser"

# Créer une clé
gcloud iam service-accounts keys create credentials/service-account.json \\
  --iam-account=lab-analyzer@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Utilisation

### Analyser un seul manuel:
```bash
python lab_manual_analyzer.py chemin/vers/manuel.pdf
```

### Analyser un dossier:
```bash
python lab_manual_analyzer.py manuels/
```

## Structure des fichiers générés

- `manuel_synthese.md`: Fiche de synthèse lisible
- `manuel_analyse_complete.json`: Données structurées complètes
- `rapport_analyse_globale.json`: Rapport pour analyse de dossier

## Fonctionnalités

- ✅ Extraction intelligente de la structure du document
- ✅ Découpage adaptatif pour les longs documents
- ✅ Identification automatique des procédures d'analyse
- ✅ Extraction des étapes de maintenance
- ✅ Spécifications techniques
- ✅ Guide rapide d'utilisation
- ✅ Synthèse exécutive

## Troubleshooting

### Document trop volumineux
- Limite Document AI: 20MB
- Utilisez un outil de compression PDF si nécessaire

### Erreurs d'API
- Vérifiez vos quotas Google Cloud
- Augmentez le délai entre requêtes dans config.json

### Qualité d'extraction
- Assurez-vous que le PDF contient du texte (pas seulement des images)
- Pour les PDF scannés, utilisez d'abord un OCR
'''
    
    with open("README.md", 'w') as f:
        f.write(readme_content)
    
    print("✅ README.md créé")

def create_test_script():
    """Crée un script de test de configuration"""
    test_script = '''#!/usr/bin/env python3
"""
Script de test de configuration
"""

import json
import os
from pathlib import Path

def test_config():
    """Teste la configuration"""
    print("🔍 Test de la configuration...")
    
    # Vérifier config.json
    if not Path("config.json").exists():
        print("❌ config.json manquant")
        return False
    
    try:
        with open("config.json") as f:
            config = json.load(f)
        
        # Vérifier les clés obligatoires
        required_keys = [
            "google_cloud.project_id",
            "google_cloud.processor_id", 
            "google_cloud.credentials_path",
            "gemini.api_key"
        ]
        
        for key_path in required_keys:
            keys = key_path.split(".")
            value = config
            for key in keys:
                value = value.get(key)
            
            if not value or value.startswith("YOUR_"):
                print(f"❌ {key_path} non configuré")
                return False
        
        print("✅ config.json valide")
        
        # Vérifier le fichier de credentials
        creds_path = Path(config["google_cloud"]["credentials_path"])
        if not creds_path.exists():
            print(f"❌ Fichier de credentials manquant: {creds_path}")
            return False
        
        print("✅ Fichier de credentials trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return False

def test_apis():
    """Teste les connexions aux APIs"""
    print("🔍 Test des connexions APIs...")
    
    try:
        # Test Document AI
        from google.cloud import documentai
        from google.oauth2 import service_account
        
        with open("config.json") as f:
            config = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_file(
            config["google_cloud"]["credentials_path"]
        )
        
        client = documentai.DocumentProcessorServiceClient(credentials=credentials)
        print("✅ Connexion Document AI OK")
        
        # Test Gemini
        import google.generativeai as genai
        genai.configure(api_key=config["gemini"]["api_key"])
        
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content("Test de connexion")
        print("✅ Connexion Gemini OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion API: {e}")
        return False

def main():
    print("🧪 Test de configuration Lab Manual Analyzer\\n")
    
    config_ok = test_config()
    if not config_ok:
        print("\\n❌ Configuration invalide. Corrigez config.json")
        return
    
    apis_ok = test_apis()
    if not apis_ok:
        print("\\n❌ Problème de connexion aux APIs")
        return
    
    print("\\n✅ Configuration complète et fonctionnelle!")
    print("Vous pouvez maintenant utiliser Lab Manual Analyzer")

if __name__ == "__main__":
    main()
'''
    
    with open("test_config.py", 'w') as f:
        f.write(test_script)
    
    print("✅ Script de test créé: test_config.py")

def main():
    """Setup principal"""
    print("🚀 Setup Lab Manual Analyzer\n")
    
    # Vérifications
    if not check_python_version():
        return
    
    # Installation
    create_directories()
    
    if not install_requirements():
        return
    
    create_config_if_needed()
    create_example_script()
    create_test_script()
    create_readme()
    
    print("\n✅ Setup terminé!")
    print("\n📋 Prochaines étapes:")
    print("1. Configurez vos APIs dans config.json")
    print("2. Placez votre service account dans credentials/")
    print("3. Testez avec: python test_config.py")
    print("4. Placez vos manuels dans le dossier manuels/")
    print("5. Lancez l'analyse: python lab_manual_analyzer.py manuels/")

if __name__ == "__main__":
    main()
