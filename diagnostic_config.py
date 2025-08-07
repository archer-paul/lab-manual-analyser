#!/usr/bin/env python3
"""
Diagnostic détaillé de la configuration
"""

import json
import os
from pathlib import Path
import sys

def test_config_detailed():
    """Test détaillé de la configuration"""
    print("=" * 60)
    print("DIAGNOSTIC DÉTAILLÉ DE CONFIGURATION")
    print("=" * 60)
    print()
    
    # 1. Vérifier l'existence de config.json
    print("1. VÉRIFICATION DU FICHIER CONFIG.JSON")
    print("-" * 40)
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ ERREUR: config.json n'existe pas")
        print("   Solution: Exécutez python setup.py")
        return False
    
    print("✅ config.json trouvé")
    
    # 2. Charger et analyser config.json
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ config.json lu avec succès")
    except Exception as e:
        print(f"❌ ERREUR lecture config.json: {e}")
        return False
    
    print()
    print("2. VÉRIFICATION DE LA STRUCTURE DE CONFIGURATION")
    print("-" * 40)
    
    # Vérifier la structure
    required_sections = {
        "google_cloud": ["project_id", "location", "processor_id", "credentials_path"],
        "gemini": ["api_key", "model"],
        "analysis": ["max_pages_per_chunk", "delay_between_requests"]
    }
    
    config_ok = True
    
    for section, keys in required_sections.items():
        if section not in config:
            print(f"❌ Section manquante: {section}")
            config_ok = False
            continue
        
        print(f"✅ Section {section} présente")
        
        for key in keys:
            if key not in config[section]:
                print(f"   ❌ Clé manquante: {section}.{key}")
                config_ok = False
            elif not config[section][key] or str(config[section][key]).startswith("YOUR_"):
                print(f"   ❌ Valeur non configurée: {section}.{key} = {config[section][key]}")
                config_ok = False
            else:
                # Masquer les clés sensibles
                if "key" in key.lower() or "id" in key.lower():
                    masked_value = str(config[section][key])[:8] + "..." if len(str(config[section][key])) > 8 else "***"
                    print(f"   ✅ {section}.{key} = {masked_value}")
                else:
                    print(f"   ✅ {section}.{key} = {config[section][key]}")
    
    if not config_ok:
        print("\n❌ CONFIGURATION INCOMPLÈTE")
        return False
    
    # 3. Vérifier le fichier de service account
    print()
    print("3. VÉRIFICATION DU SERVICE ACCOUNT")
    print("-" * 40)
    
    creds_path = Path(config["google_cloud"]["credentials_path"])
    if not creds_path.exists():
        print(f"❌ ERREUR: Fichier service account non trouvé: {creds_path}")
        print("   Vérifiez que le fichier existe et que le chemin est correct")
        return False
    
    print(f"✅ Fichier service account trouvé: {creds_path}")
    
    # Vérifier que c'est un JSON valide
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        required_creds_fields = ["type", "project_id", "private_key", "client_email"]
        for field in required_creds_fields:
            if field not in creds_data:
                print(f"   ❌ Champ manquant dans service account: {field}")
                return False
        
        print("✅ Structure du service account valide")
        print(f"   Project ID: {creds_data.get('project_id', 'N/A')}")
        print(f"   Client email: {creds_data.get('client_email', 'N/A')}")
        
    except Exception as e:
        print(f"❌ ERREUR lecture service account: {e}")
        return False
    
    # 4. Test des connexions
    print()
    print("4. TEST DES CONNEXIONS API")
    print("-" * 40)
    
    # Test Google Cloud
    try:
        from google.cloud import documentai
        from google.oauth2 import service_account
        
        credentials = service_account.Credentials.from_service_account_file(
            config["google_cloud"]["credentials_path"]
        )
        
        region = config["google_cloud"]["location"]
        if region == "eu":
            client_options = {"api_endpoint": "eu-documentai.googleapis.com"}
            doc_ai_client = documentai.DocumentProcessorServiceClient(
                credentials=credentials,
                client_options=client_options
            )
        else:
            doc_ai_client = documentai.DocumentProcessorServiceClient(
                credentials=credentials
            )
        
        # Tester en listant les processeurs
        parent = f"projects/{config['google_cloud']['project_id']}/locations/{config['google_cloud']['location']}"
        
        try:
            request = documentai.ListProcessorsRequest(parent=parent)
            response = doc_ai_client.list_processors(request=request)
            processors = list(response)
            
            print("✅ Connexion Google Cloud Document AI réussie")
            print(f"   Nombre de processeurs trouvés: {len(processors)}")
            
            # Vérifier si notre processeur existe
            processor_id = config["google_cloud"]["processor_id"]
            processor_found = False
            
            for processor in processors:
                if processor_id in processor.name:
                    processor_found = True
                    print(f"   ✅ Processeur trouvé: {processor.display_name}")
                    print(f"      Type: {processor.type_}")
                    print(f"      État: {processor.state.name}")
                    break
            
            if not processor_found:
                print(f"   ❌ Processeur {processor_id} non trouvé")
                print("   Processeurs disponibles:")
                for processor in processors:
                    print(f"      - {processor.display_name} ({processor.name.split('/')[-1]})")
                return False
                
        except Exception as e:
            print(f"❌ ERREUR Document AI: {e}")
            return False
        
    except ImportError as e:
        print(f"❌ ERREUR import Google Cloud: {e}")
        print("   Exécutez: pip install google-cloud-documentai")
        return False
    
    # Test Gemini
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=config["gemini"]["api_key"])
        model = genai.GenerativeModel(config["gemini"]["model"])
        
        # Test simple
        response = model.generate_content("Test de connexion - répondez juste 'OK'")
        
        print("✅ Connexion Gemini AI réussie")
        print(f"   Modèle: {config['gemini']['model']}")
        print(f"   Réponse test: {response.text[:50]}...")
        
    except Exception as e:
        print(f"❌ ERREUR Gemini AI: {e}")
        print("   Vérifiez votre clé API Gemini")
        return False
    
    # 5. Résumé final
    print()
    print("5. RÉSUMÉ FINAL")
    print("-" * 40)
    print("✅ CONFIGURATION COMPLÈTE ET FONCTIONNELLE")
    print()
    print("Votre système est prêt à analyser des manuels de laboratoire!")
    print()
    print("Prochaines étapes:")
    print("1. Placez vos PDFs dans le dossier 'manuels/'")
    print("2. Exécutez: python lab_manual_analyzer_organized.py manuels/votre_manuel.pdf")
    print("3. Ou utilisez: lancer_analyse.bat")
    
    return True

def main():
    """Fonction principale"""
    try:
        success = test_config_detailed()
        if success:
            print("\n🎉 DIAGNOSTIC RÉUSSI!")
        else:
            print("\n❌ DIAGNOSTIC ÉCHOUÉ - Configuration à corriger")
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        print("\nContactez le support technique avec cette erreur")

if __name__ == "__main__":
    main()
