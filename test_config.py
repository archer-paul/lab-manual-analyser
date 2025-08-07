#!/usr/bin/env python3
"""
Test de configuration simplifié pour le script batch
"""

import json
import os
from pathlib import Path
import sys

def test_config_simple():
    """Test simplifié qui retourne 0 si OK, 1 si erreur"""
    
    try:
        # Vérifier config.json
        if not Path("config.json").exists():
            return 1
        
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Vérifier les clés essentielles
        required_keys = [
            ("google_cloud", "project_id"),
            ("google_cloud", "processor_id"), 
            ("google_cloud", "credentials_path"),
            ("gemini", "api_key")
        ]
        
        for section, key in required_keys:
            if section not in config:
                return 1
            if key not in config[section]:
                return 1
            value = config[section][key]
            if not value or str(value).startswith("YOUR_"):
                return 1
        
        # Vérifier le fichier de credentials
        creds_path = Path(config["google_cloud"]["credentials_path"])
        if not creds_path.exists():
            return 1
        
        # Test rapide Google Cloud
        try:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path)
            )
        except Exception:
            return 1
        
        # Test rapide Gemini
        try:
            import google.generativeai as genai
            genai.configure(api_key=config["gemini"]["api_key"])
            model = genai.GenerativeModel(config["gemini"]["model"])
            
            # Test très simple
            response = model.generate_content("Test")
            if not response.text:
                return 1
                
        except Exception:
            return 1
        
        return 0  # Tout OK
        
    except Exception:
        return 1  # Erreur

if __name__ == "__main__":
    exit_code = test_config_simple()
    sys.exit(exit_code)
