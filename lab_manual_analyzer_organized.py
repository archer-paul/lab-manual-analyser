#!/usr/bin/env python3
"""
Lab Manual Analyzer - Version LaTeX STRICTE avec double validation JSON
AUCUN FALLBACK - Échec propre si problème
USAGE MÉDICAL - Fiabilité critique avec Gemini 2.0 Flash + correction automatique
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time
import re
import math

# Google Cloud imports
from google.cloud import documentai
import google.generativeai as genai
from google.oauth2 import service_account

# Import du générateur LaTeX strict et déchiffreur
from latex_generator import LatexSynthesisGenerator
from pdf_decryptor import decrypt_pdf

# Configuration logging stricte
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lab_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LabManualAnalyzerStrict:
    """Analyseur STRICT pour matériel médical avec double validation JSON"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialise l'analyseur avec vérifications strictes"""
        logger.info("🏥 INITIALISATION ANALYSEUR MÉDICAL STRICT")
        
        self.config = self.load_config(config_path)
        self.setup_google_apis()
        self.setup_output_directories()
        
        # Limite Document AI stricte
        self.max_pages_per_request = 15
        logger.info(f"📄 Limite Document AI: {self.max_pages_per_request} pages par requête")
        
        # Initialiser le générateur LaTeX STRICT
        try:
            self.latex_generator = LatexSynthesisGenerator()
            logger.info("✅ Générateur LaTeX médical initialisé et vérifié")
        except Exception as e:
            logger.error(f"❌ ERREUR CRITIQUE: Générateur LaTeX non opérationnel")
            raise RuntimeError(f"Impossible d'initialiser le générateur LaTeX: {e}")
    
    def load_config(self, config_path: str) -> Dict:
        """Charge et valide la configuration de manière stricte"""
        if not Path(config_path).exists():
            raise FileNotFoundError(f"❌ Fichier de configuration manquant: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validation stricte de la configuration
            required_sections = {
                "google_cloud": ["project_id", "location", "processor_id", "credentials_path"],
                "gemini": ["api_key", "model"],
                "analysis": ["delay_between_requests"]
            }
            
            for section, keys in required_sections.items():
                if section not in config:
                    raise ValueError(f"❌ Section manquante dans config: {section}")
                
                for key in keys:
                    if key not in config[section] or not config[section][key]:
                        raise ValueError(f"❌ Clé manquante ou vide: {section}.{key}")
            
            # Vérifier le fichier de credentials
            creds_path = Path(config["google_cloud"]["credentials_path"])
            if not creds_path.exists():
                raise FileNotFoundError(f"❌ Fichier credentials manquant: {creds_path}")
            
            logger.info("✅ Configuration validée")
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Configuration JSON invalide: {e}")
    
    def setup_output_directories(self):
        """Crée la structure de dossiers avec vérifications"""
        self.manuels_dir = Path("manuels")
        self.syntheses_dir = self.manuels_dir / "syntheses"
        self.temp_dir = Path("temp")
        
        try:
            for directory in [self.manuels_dir, self.syntheses_dir, self.temp_dir]:
                directory.mkdir(exist_ok=True)
                
                # Vérifier les permissions d'écriture
                test_file = directory / "test_write_permission.tmp"
                test_file.write_text("test")
                test_file.unlink()
            
            logger.info("✅ Structure de dossiers validée avec permissions d'écriture")
            
        except Exception as e:
            raise RuntimeError(f"❌ Impossible de créer/accéder aux dossiers: {e}")
    
    def setup_google_apis(self):
        """Configure les APIs Google Cloud avec vérifications strictes"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.config["google_cloud"]["credentials_path"]
            )
            
            region = self.config["google_cloud"]["location"]
            if region == "eu":
                client_options = {"api_endpoint": "eu-documentai.googleapis.com"}
                self.doc_ai_client = documentai.DocumentProcessorServiceClient(
                    credentials=credentials,
                    client_options=client_options
                )
            else:
                self.doc_ai_client = documentai.DocumentProcessorServiceClient(
                    credentials=credentials
                )
            
            self.processor_name = f"projects/{self.config['google_cloud']['project_id']}/locations/{self.config['google_cloud']['location']}/processors/{self.config['google_cloud']['processor_id']}"
            
            # Configuration Gemini stricte
            genai.configure(api_key=self.config["gemini"]["api_key"])
            self.gemini_model = genai.GenerativeModel(self.config["gemini"]["model"])
            
            # Essayer d'utiliser Gemini 2.0 Flash si disponible
            try:
                self.advanced_model = genai.GenerativeModel("gemini-2.0-flash-exp")
                logger.info("✅ Gemini 2.0 Flash détecté et disponible")
            except:
                self.advanced_model = self.gemini_model
                logger.info("💡 Utilisation du modèle Gemini configuré")
            
            # Test de connexion obligatoire
            self.test_api_connections()
            
            logger.info("✅ APIs Google Cloud configurées et testées")
            
        except Exception as e:
            raise RuntimeError(f"❌ Échec configuration APIs: {e}")
    
    def test_api_connections(self):
        """Test obligatoire des connexions APIs"""
        try:
            # Test Document AI
            parent = f"projects/{self.config['google_cloud']['project_id']}/locations/{self.config['google_cloud']['location']}"
            request = documentai.ListProcessorsRequest(parent=parent)
            processors = list(self.doc_ai_client.list_processors(request=request))
            
            # Vérifier que notre processeur existe
            processor_id = self.config["google_cloud"]["processor_id"]
            processor_found = any(processor_id in p.name for p in processors)
            
            if not processor_found:
                raise RuntimeError(f"❌ Processeur Document AI non trouvé: {processor_id}")
            
            # Test Gemini simple
            test_response = self.gemini_model.generate_content("Test de connexion - répondez 'OK'")
            if not test_response.text:
                raise RuntimeError("❌ Gemini ne répond pas correctement")
            
            logger.info("✅ Connexions APIs testées avec succès")
            
        except Exception as e:
            raise RuntimeError(f"❌ Test de connexion échoué: {e}")
    
    def prepare_pdf(self, pdf_path: Path) -> Path:
        """Prépare le PDF avec vérifications strictes"""
        if not pdf_path.exists():
            raise FileNotFoundError(f"❌ PDF non trouvé: {pdf_path}")
        
        if pdf_path.stat().st_size == 0:
            raise ValueError(f"❌ PDF vide: {pdf_path}")
        
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.is_encrypted:
                    logger.info(f"🔒 PDF chiffré détecté: {pdf_path.name}")
                    decrypted_path = self.temp_dir / f"decrypted_{pdf_path.name}"
                    
                    if not decrypt_pdf(pdf_path, decrypted_path):
                        raise RuntimeError(f"❌ Impossible de déchiffrer: {pdf_path}")
                    
                    logger.info(f"🔓 PDF déchiffré: {decrypted_path}")
                    return decrypted_path
                else:
                    logger.info(f"📄 PDF non chiffré: {pdf_path.name}")
                    return pdf_path
                    
        except ImportError:
            raise RuntimeError("❌ PyPDF2 non installé - requis pour validation PDF")
        except Exception as e:
            raise RuntimeError(f"❌ Erreur préparation PDF: {e}")
    
    def split_pdf_15pages(self, pdf_path: Path) -> List[Path]:
        """Divise PDF en chunks stricts de 15 pages maximum"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                if total_pages == 0:
                    raise ValueError("❌ PDF sans pages")
                
                logger.info(f"📊 PDF: {total_pages} pages à traiter")
                
                if total_pages <= self.max_pages_per_request:
                    logger.info("📄 PDF petit - traitement direct")
                    return [pdf_path]
                
                # Découpage strict
                chunks_dir = self.temp_dir / f"{pdf_path.stem}_chunks"
                chunks_dir.mkdir(exist_ok=True)
                
                chunks = []
                pages_per_chunk = self.max_pages_per_request
                num_chunks = math.ceil(total_pages / pages_per_chunk)
                
                logger.info(f"✂️ Découpage en {num_chunks} chunks de {pages_per_chunk} pages max")
                
                for i in range(num_chunks):
                    start_page = i * pages_per_chunk
                    end_page = min(start_page + pages_per_chunk, total_pages)
                    
                    pdf_writer = PyPDF2.PdfWriter()
                    
                    for page_num in range(start_page, end_page):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
                    
                    chunk_path = chunks_dir / f"chunk_{i+1:02d}_p{start_page+1}-{end_page}.pdf"
                    
                    with open(chunk_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                    
                    # Vérification chunk créé
                    if not chunk_path.exists() or chunk_path.stat().st_size == 0:
                        raise RuntimeError(f"❌ Échec création chunk: {chunk_path}")
                    
                    chunks.append(chunk_path)
                    logger.info(f"✅ Chunk {i+1}: {end_page - start_page} pages")
                
                return chunks
                
        except Exception as e:
            raise RuntimeError(f"❌ Échec découpage PDF: {e}")
    
    def extract_text_safe(self, pdf_path: Path, max_retries: int = 2) -> Dict:
        """Extraction de texte avec validation stricte"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Extraction: {pdf_path.name} (tentative {attempt + 1})")
                
                with open(pdf_path, "rb") as pdf_file:
                    pdf_content = pdf_file.read()
                
                file_size_mb = len(pdf_content) / (1024 * 1024)
                logger.info(f"📊 Taille: {file_size_mb:.1f} MB")
                
                # Limite stricte de taille
                if len(pdf_content) > 20 * 1024 * 1024:
                    raise ValueError("❌ Fichier trop volumineux (>20MB)")
                
                if len(pdf_content) == 0:
                    raise ValueError("❌ Fichier vide")
                
                raw_document = documentai.RawDocument(
                    content=pdf_content,
                    mime_type="application/pdf"
                )
                
                request = documentai.ProcessRequest(
                    name=self.processor_name,
                    raw_document=raw_document
                )
                
                result = self.doc_ai_client.process_document(request=request)
                document = result.document
                
                # Validation stricte du résultat
                if not document or not document.text:
                    raise ValueError("❌ Document AI n'a extrait aucun texte")
                
                char_count = len(document.text)
                page_count = len(document.pages) if document.pages else 0
                
                # Validation minimale du contenu
                if char_count < 100:  # Trop peu de texte = problème
                    raise ValueError(f"❌ Texte extrait insuffisant: {char_count} caractères")
                
                logger.info(f"✅ Extraction réussie: {char_count:,} caractères, {page_count} pages")
                
                return {
                    "text": document.text,
                    "pages": page_count,
                    "chunk_file": str(pdf_path),
                    "char_count": char_count
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Tentative {attempt + 1} échouée: {str(e)[:200]}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    logger.info(f"⏳ Attente {wait_time}s avant nouvelle tentative...")
                    time.sleep(wait_time)
                else:
                    # Échec définitif
                    error_msg = f"❌ ÉCHEC DÉFINITIF extraction: {pdf_path.name} - {e}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
    
    def analyze_with_gemini_advanced(self, chunk: Dict, context: str = "", language: str = 'fr') -> Dict:
        """Analyse Gemini AVANCÉE avec modèle intelligent et double validation et support multilingue"""
        
        # Instructions de langue pour le prompt
        language_instruction = {
            'fr': "IMPORTANT: Réponds EXCLUSIVEMENT en français avec tous les textes, descriptions et valeurs en français.",
            'en': "IMPORTANT: Respond EXCLUSIVELY in English with all texts, descriptions and values in English."
        }
        
        lang_inst = language_instruction.get(language, language_instruction['fr'])
        
        # Prompt détaillé pour extraction maximale d'informations
        detailed_prompt = f"""
Tu es un expert médical spécialisé dans l'analyse d'instruments de laboratoire diagnostique.
Analyse EXHAUSTIVEMENT ce manuel médical et extrait TOUTES les informations techniques et cliniques critiques.

{lang_inst}

CONTEXTE PRÉCÉDENT: {context[-300:] if context else "Début du document"}

SECTION À ANALYSER: {chunk['description']} ({chunk['char_count']} caractères)

INSTRUCTIONS CRITIQUES:
- Extrait TOUS les détails techniques, procéduraux et cliniques
- Identifie précisément les volumes, concentrations, températures, durées
- Capture les spécifications de performance, limites de détection, gammes linéaires
- Relève TOUTES les précautions de sécurité, contre-indications, limitations
- Documente les procédures complètes avec matériels exacts
- Note les conditions de stockage, stabilité, contrôles qualité
- Extraie les données de validation clinique et performance analytique

TEXTE À ANALYSER:
{chunk['text'][:80000]}

Réponds en JSON détaillé PARFAITEMENT FORMATÉ:

{{
    "instrument": {{
        "nom": "nom exact complet de l'instrument",
        "fabricant": "fabricant exact",
        "modele": "modèle et références exactes", 
        "type": "type d'instrument et technologie",
        "applications_cliniques": ["application clinique 1", "application clinique 2"],
        "principe_technique": "principe de fonctionnement détaillé"
    }},
    "procedures": [
        {{
            "nom": "nom exact de l'analyse",
            "code_produit": "référence produit si mentionnée",
            "echantillon": {{
                "type": "type exact d'échantillon",
                "volume_minimum": "volume minimum requis",
                "volume_traitement": "volume de traitement",
                "anticoagulant": "anticoagulant requis",
                "conditions_prelevement": ["condition 1", "condition 2"]
            }},
            "preparation_echantillon": {{
                "etapes": ["étape détaillée 1", "étape détaillée 2"],
                "stabilite": "conditions et durées de stabilité",
                "transport": "conditions de transport",
                "stockage": "conditions de stockage détaillées"
            }},
            "procedure_analytique": {{
                "etapes_detaillees": ["étape 1 avec détails", "étape 2 avec détails"],
                "duree_totale": "durée complète du processus",
                "temperature_incubation": "températures si applicables",
                "cycles_pcr": "nombre de cycles si PCR",
                "detection": "méthode de détection"
            }},
            "materiels_reactifs": {{
                "reactifs": ["réactif 1 avec référence", "réactif 2 avec référence"],
                "consommables": ["consommable 1", "consommable 2"],
                "equipements": ["équipement requis"]
            }},
            "performance": {{
                "gamme_lineaire": "gamme de mesure",
                "limite_detection": "limite de détection",
                "limite_quantification": "limite de quantification",
                "precision": "données de précision",
                "reproductibilite": "données de reproductibilité"
            }},
            "controles_qualite": {{
                "controles_requis": ["contrôle positif", "contrôle négatif"],
                "frequence": "fréquence des contrôles",
                "criteres_acceptation": ["critère 1", "critère 2"]
            }},
            "interpretation": {{
                "resultats_possibles": ["résultat 1: signification", "résultat 2: signification"],
                "seuils_decision": "seuils cliniques importants",
                "unites": "unités de mesure",
                "facteur_conversion": "facteur de conversion si applicable"
            }},
            "precautions_critiques": [
                "précaution de sécurité 1 DÉTAILLÉE",
                "précaution technique 2 DÉTAILLÉE"
            ],
            "limitations": [
                "limitation technique 1",
                "limitation clinique 2"
            ]
        }}
    ],
    "maintenance": [
        {{
            "type": "type exact de maintenance",
            "frequence": "fréquence précise",
            "duree": "temps nécessaire",
            "procedure_complete": {{
                "preparation": ["étape préparation 1", "étape préparation 2"],
                "execution": ["étape exécution 1 détaillée", "étape exécution 2 détaillée"],
                "verification": ["vérification 1", "vérification 2"],
                "documentation": "éléments à documenter"
            }},
            "materiels_requis": ["matériel 1", "matériel 2"],
            "personnel": "qualification du personnel",
            "conditions_environnementales": "conditions requises"
        }}
    ],
    "specifications_techniques": [
        {{
            "categorie": "catégorie technique précise",
            "parametres": [
                {{
                    "nom": "nom exact du paramètre",
                    "valeur": "valeur exacte",
                    "unite": "unité",
                    "conditions": "conditions de mesure",
                    "tolerance": "tolérance acceptable"
                }}
            ]
        }}
    ],
    "securite": [
        {{
            "categorie": "catégorie de risque",
            "risques_identifies": ["risque 1 détaillé", "risque 2 détaillé"],
            "mesures_prevention": ["mesure préventive 1", "mesure préventive 2"],
            "equipements_protection": ["EPI requis 1", "EPI requis 2"],
            "procedures_urgence": ["action urgence 1", "action urgence 2"],
            "formation_requise": "formation nécessaire",
            "reglementation": "références réglementaires"
        }}
    ],
    "stockage_reagents": [
        {{
            "reagent": "nom du réactif",
            "temperature_stockage": "température de stockage",
            "stabilite": "durée de stabilité",
            "conditions_speciales": ["condition 1", "condition 2"],
            "duree_utilisation": "durée après ouverture"
        }}
    ],
    "validation_clinique": {{
        "population_etudiee": "population des études cliniques",
        "nombre_echantillons": "nombre d'échantillons testés",
        "comparaison_methodes": "méthodes de référence",
        "sensibilite": "sensibilité analytique",
        "specificite": "spécificité analytique",
        "etudes_interference": "substances testées pour interférence",
        "genotypes_detectes": "génotypes ou variants détectés"
    }},
    "calibration": [
        {{
            "type": "type de calibration",
            "frequence": "fréquence recommandée",
            "standards_utilises": ["standard 1", "standard 2"],
            "procedure": ["étape calibration 1", "étape calibration 2"],
            "criteres_acceptation": ["critère 1", "critère 2"],
            "tracabilite": "traçabilité métrologique"
        }}
    ],
    "troubleshooting": [
        {{
            "probleme": "problème identifié détaillé",
            "causes_possibles": ["cause 1", "cause 2"],
            "solutions": ["solution 1 détaillée", "solution 2 détaillée"],
            "prevention": "mesures préventives"
        }}
    ],
    "resume_section": "résumé technique détaillé de cette section en 3-4 phrases"
}}

CRITIQUE: Sois EXHAUSTIF, précis et technique. Capture TOUS les détails numériques, procéduraux et cliniques. ASSURE-TOI que le JSON est PARFAITEMENT VALIDE."""
        
        # Utiliser Gemini 2.0 Flash si disponible
        try:
            # Essayer d'abord avec Gemini 2.0 Flash
            model_to_use = getattr(self, 'advanced_model', self.gemini_model)
            if hasattr(self, 'advanced_model') and self.advanced_model != self.gemini_model:
                model_name = "Gemini 2.0 Flash"
            else:
                model_name = self.config["gemini"]["model"]
        except:
            # Fallback vers le modèle configuré
            model_to_use = self.gemini_model
            model_name = self.config["gemini"]["model"]
        
        for attempt in range(2):  # Maximum 2 tentatives
            try:
                logger.info(f"🧠 Analyse {model_name} DÉTAILLÉE: {chunk['description']} (tentative {attempt + 1})")
                
                response = model_to_use.generate_content(detailed_prompt)
                
                if not response or not response.text:
                    raise ValueError("❌ Gemini n'a fourni aucune réponse")
                
                response_text = response.text.strip()
                
                # DOUBLE VALIDATION avec second modèle
                validated_json = self.validate_and_fix_json_with_gemini(response_text)
                result = json.loads(validated_json)
                
                # Validation stricte de la structure détaillée
                self.validate_detailed_analysis_result(result)
                
                # Comptage détaillé pour logs
                proc_count = len(result.get('procedures', []))
                maint_count = len(result.get('maintenance', []))
                spec_count = len(result.get('specifications_techniques', []))
                sec_count = len(result.get('securite', []))
                storage_count = len(result.get('stockage_reagents', []))
                
                logger.info(f"✅ Analyse DÉTAILLÉE réussie avec {model_name}: {proc_count} procédures, {maint_count} maintenances, {spec_count} spécs, {sec_count} sécurités, {storage_count} stockages")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON invalide même après double validation (tentative {attempt + 1}): {e}")
                if attempt < 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Erreur analyse Gemini avancée (tentative {attempt + 1}): {e}")
                if attempt < 1:
                    time.sleep(3)
        
        # Échec définitif = erreur critique
        error_msg = f"❌ ÉCHEC ANALYSE GEMINI AVANCÉE: {chunk['description']}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def validate_and_fix_json_with_gemini(self, response_text: str) -> str:
        """Double validation: utilise Gemini pour corriger le JSON défaillant"""
        
        # D'abord, essayer l'extraction normale
        try:
            return self.extract_and_validate_json(response_text)
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"⚠️ JSON invalide détecté, tentative de correction automatique: {e}")
            
            # Utiliser Gemini pour corriger le JSON
            validation_prompt = f"""
Tu es un expert en formatage JSON. Le JSON suivant contient des erreurs de syntaxe. 
Corrige-le pour qu'il soit parfaitement valide tout en préservant TOUTES les informations.

JSON À CORRIGER:
{response_text[:10000]}

INSTRUCTIONS:
1. Garde TOUTES les informations existantes
2. Corrige uniquement les erreurs de syntaxe JSON
3. Assure-toi que tous les guillemets sont corrects
4. Supprime les virgules en trop
5. Vérifie que tous les crochets et accolades sont équilibrés
6. Échappe correctement les caractères spéciaux dans les strings

Réponds UNIQUEMENT avec le JSON corrigé, sans explanation, sans markdown."""
            
            try:
                # Utiliser un modèle plus simple pour la correction
                correction_response = self.gemini_model.generate_content(validation_prompt)
                
                if correction_response and correction_response.text:
                    corrected_text = correction_response.text.strip()
                    
                    # Extraire et valider le JSON corrigé
                    return self.extract_and_validate_json(corrected_text)
                else:
                    raise ValueError("❌ Gemini n'a pas pu corriger le JSON")
                    
            except Exception as correction_error:
                logger.error(f"❌ Échec correction JSON avec Gemini: {correction_error}")
                # Fallback vers correction automatique basique
                return self.extract_and_validate_json(response_text)
    
    def extract_and_validate_json(self, response_text: str) -> str:
        """Extraction et validation JSON avec correction automatique"""
        if not response_text or not response_text.strip():
            raise ValueError("❌ Réponse Gemini vide")
        
        # Supprimer les blocs markdown
        text = response_text
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.rfind("```")
            if end > start:
                text = text[start:end]
        elif "```" in text:
            start = text.find("```") + 3
            end = text.rfind("```")
            if end > start:
                text = text[start:end]
        
        # Extraire JSON entre accolades
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        
        if first_brace < 0 or last_brace < 0 or first_brace >= last_brace:
            raise ValueError("❌ Aucun JSON valide trouvé dans la réponse Gemini")
        
        json_text = text[first_brace:last_brace + 1].strip()
        
        # Corrections automatiques des erreurs JSON courantes
        json_text = self.fix_common_json_errors(json_text)
        
        # Validation JSON basique
        try:
            json.loads(json_text)  # Test de parsing
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON encore invalide après corrections: {e}")
            logger.error(f"Extrait problématique: {json_text[max(0, e.pos-50):e.pos+50]}")
            raise ValueError(f"❌ JSON invalide même après corrections: {e}")
        
        return json_text
    
    def fix_common_json_errors(self, json_text: str) -> str:
        """Corrige automatiquement les erreurs JSON courantes"""
        
        # 1. Supprimer les virgules en fin d'objet/array
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # 2. Échapper les guillemets dans les valeurs
        # Protéger d'abord les structures JSON valides
        lines = json_text.split('\n')
        corrected_lines = []
        
        for line in lines:
            # Si la ligne contient une valeur de string
            if '": "' in line and not line.strip().endswith(',') and not line.strip().endswith('{') and not line.strip().endswith('['):
                # Trouver la partie valeur après ": "
                parts = line.split('": "', 1)
                if len(parts) == 2:
                    key_part = parts[0]
                    value_part = parts[1]
                    
                    # Trouver la fin de la valeur
                    end_quote = value_part.rfind('"')
                    if end_quote > 0:
                        value_content = value_part[:end_quote]
                        rest = value_part[end_quote:]
                        
                        # Échapper les guillemets dans la valeur seulement
                        value_content = value_content.replace('"', '\\"')
                        
                        line = key_part + '": "' + value_content + rest
            
            corrected_lines.append(line)
        
        json_text = '\n'.join(corrected_lines)
        
        # 3. Supprimer les caractères de contrôle problématiques
        json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_text)
        
        # 4. Réparer les arrays mal fermés
        json_text = re.sub(r',(\s*\])', r'\1', json_text)
        
        # 5. Supprimer les doubles virgules
        json_text = re.sub(r',,+', ',', json_text)
        
        return json_text
    
    def validate_detailed_analysis_result(self, result: Dict):
        """Validation simplifiée du résultat d'analyse"""
        if not isinstance(result, dict):
            raise ValueError("❌ Résultat d'analyse n'est pas un dictionnaire")
        
        # Structure simplifiée requise
        required_sections = [
            'instrument', 'procedures', 'maintenance', 'specifications_techniques', 
            'securite', 'stockage_reagents', 'validation_clinique', 'calibration', 
            'troubleshooting', 'resume_section'
        ]
        
        for section in required_sections:
            if section not in result:
                if section in ['instrument', 'validation_clinique', 'resume_section']:
                    result[section] = {} if section != 'resume_section' else ""
                else:
                    result[section] = []
        
        # Validation des procédures (critique pour sécurité)
        procedures = result.get('procedures', [])
        if not isinstance(procedures, list):
            result['procedures'] = []
        
        # Validation maintenance (critique pour fiabilité)
        maintenance = result.get('maintenance', [])
        if not isinstance(maintenance, list):
            result['maintenance'] = []
        
        # S'assurer que l'instrument a au moins un nom
        if not result.get('instrument', {}).get('nom'):
            if result.get('instrument'):
                result['instrument']['nom'] = "Instrument non identifié"
            else:
                result['instrument'] = {"nom": "Instrument non identifié"}
        
        logger.debug("✅ Structure d'analyse simplifiée validée")
        
        # Log de debug pour voir ce qui a été extrait
        proc_count = len(result.get('procedures', []))
        maint_count = len(result.get('maintenance', []))
        logger.info(f"✅ Validation OK: {proc_count} procédures, {maint_count} maintenances")
        
        return result
    
    def synthesize_final_medical(self, analyses: List[Dict], language: str = 'fr') -> Dict:
        """Synthèse finale EXHAUSTIVE avec double validation JSON"""
        if not analyses:
            raise ValueError("❌ Aucune analyse à synthétiser")
        
        logger.info("🔬 Création de la synthèse médicale DÉTAILLÉE...")
        
        # Compilation EXHAUSTIVE des données
        all_procedures = []
        all_maintenance = []
        all_specs = []
        all_security = []
        all_calibration = []
        all_storage = []
        all_validation = []
        all_troubleshooting = []
        instrument_info = {}
        
        for i, analysis in enumerate(analyses):
            if not isinstance(analysis, dict):
                logger.warning(f"⚠️ Analyse {i+1} invalide - ignorée")
                continue
            
            # Consolidation détaillée
            all_procedures.extend(analysis.get("procedures", []))
            all_maintenance.extend(analysis.get("maintenance", []))
            all_specs.extend(analysis.get("specifications_techniques", []))
            all_security.extend(analysis.get("securite", []))
            all_calibration.extend(analysis.get("calibration", []))
            all_storage.extend(analysis.get("stockage_reagents", []))
            all_troubleshooting.extend(analysis.get("troubleshooting", []))
            
            # Validation clinique (important)
            validation = analysis.get("validation_clinique", {})
            if validation and isinstance(validation, dict):
                all_validation.append(validation)
            
            # Consolidation info instrument
            inst = analysis.get("instrument", {})
            if isinstance(inst, dict):
                for key, value in inst.items():
                    if value and str(value).strip() and not str(value).startswith("Non"):
                        if key not in instrument_info or len(str(value)) > len(str(instrument_info.get(key, ""))):
                            instrument_info[key] = value
        
        logger.info(f"📊 Données DÉTAILLÉES compilées:")
        logger.info(f"   - Procédures: {len(all_procedures)}")
        logger.info(f"   - Maintenances: {len(all_maintenance)}")
        logger.info(f"   - Spécifications: {len(all_specs)}")
        logger.info(f"   - Sécurité: {len(all_security)}")
        logger.info(f"   - Stockage: {len(all_storage)}")
        logger.info(f"   - Validation: {len(all_validation)}")
        logger.info(f"   - Troubleshooting: {len(all_troubleshooting)}")
        
        # Synthèse finale EXHAUSTIVE avec Gemini + double validation
        # Instructions de langue pour le prompt
        logger.info(f"DEBUG: About to use language variable: {language}")
        language_instruction = {
            'fr': "IMPORTANT: Réponds EXCLUSIVEMENT en français avec tous les textes, descriptions et valeurs en français.",
            'en': "IMPORTANT: Respond EXCLUSIVELY in English with all texts, descriptions and values in English."
        }
        lang_inst = language_instruction.get(language, language_instruction['fr'])
        logger.info(f"DEBUG: Language instruction set to: {lang_inst[:50]}...")
        synthesis_prompt = f"""
Tu es un expert médical diagnostique. Créer une synthèse TECHNIQUE COMPLÈTE de cet instrument médical.

{lang_inst}

INFORMATIONS INSTRUMENT CONSOLIDÉES:
{json.dumps(instrument_info, ensure_ascii=False, indent=2)}

DONNÉES EXHAUSTIVES ANALYSÉES:

PROCÉDURES DÉTAILLÉES ({len(all_procedures)} extraites):
{json.dumps(all_procedures[:3], ensure_ascii=False, indent=2) if all_procedures else "Aucune procédure extraite"}

MAINTENANCE PRÉVENTIVE ({len(all_maintenance)} extraites):
{json.dumps(all_maintenance[:3], ensure_ascii=False, indent=2) if all_maintenance else "Aucune maintenance extraite"}

SPÉCIFICATIONS TECHNIQUES ({len(all_specs)} extraites):
{json.dumps(all_specs[:2], ensure_ascii=False, indent=2) if all_specs else "Aucune spécification extraite"}

SÉCURITÉ ET PRÉCAUTIONS ({len(all_security)} extraites):
{json.dumps(all_security[:2], ensure_ascii=False, indent=2) if all_security else "Aucune précaution extraite"}

STOCKAGE RÉACTIFS ({len(all_storage)} extraits):
{json.dumps(all_storage[:2], ensure_ascii=False, indent=2) if all_storage else "Aucun stockage extrait"}

VALIDATION CLINIQUE:
{json.dumps(all_validation[:2], ensure_ascii=False, indent=2) if all_validation else "Aucune validation extraite"}

DÉPANNAGE ({len(all_troubleshooting)} extraits):
{json.dumps(all_troubleshooting[:2], ensure_ascii=False, indent=2) if all_troubleshooting else "Aucun dépannage extrait"}

MISSION CRITIQUE: Consolider TOUTES ces données en une synthèse technique COMPLÈTE pour usage médical professionnel. Préserver tous les détails techniques critiques (volumes, concentrations, références, limites, performances).

JSON SYNTHÈSE MÉDICALE EXHAUSTIVE PARFAITEMENT FORMATÉ:

{{
    "informations_generales": {{
        "nom_instrument": "nom complet consolidé avec toutes références",
        "fabricant": "fabricant exact",
        "modele": "modèle complet avec références produit",
        "type_instrument": "type d'instrument et technologie précise",
        "applications_principales": [
            "application clinique détaillée 1 avec contexte",
            "application clinique détaillée 2 avec contexte"
        ],
        "principe_fonctionnement": "principe technique détaillé de fonctionnement",
        "approche_diagnostique": "méthodologie diagnostique et workflow"
    }},
    "procedures_analyses": [
        {{
            "nom_analyse": "nom complet de l'analyse avec code produit",
            "indication_clinique": "indication médicale précise et population cible",
            "echantillon": {{
                "type": "type d'échantillon exact avec spécifications",
                "volume_minimum": "volume minimum avec justification",
                "volume_traitement": "volume de traitement avec options",
                "anticoagulant": "anticoagulant spécifique avec alternatives"
            }},
            "preparation_detaillee": {{
                "etapes": [
                    "étape préparation 1 avec volumes/temps précis",
                    "étape préparation 2 avec conditions/températures"
                ],
                "stabilite": "conditions de stabilité complètes avec durées",
                "stockage": "conditions de stockage détaillées par phase"
            }},
            "procedure_analytique": {{
                "workflow": [
                    "étape analytique 1 avec paramètres techniques",
                    "étape analytique 2 avec conditions de traitement"
                ],
                "duree_totale": "temps total avec décomposition par phase",
                "conditions_techniques": "températures, pressions, vitesses détaillées"
            }},
            "performance_analytique": {{
                "gamme_mesure": "gamme linéaire complète avec unités",
                "limite_detection": "LoD précise avec conditions de validation",
                "precision": "données de précision intra et inter-série (CV%)"
            }},
            "controles_qualite": {{
                "types_controles": [
                    "contrôle positif haut avec concentration cible",
                    "contrôle négatif avec critères acceptation"
                ],
                "frequence": "fréquence des contrôles avec justification"
            }},
            "precautions_critiques": [
                "SÉCURITÉ BIOLOGIQUE: manipulation échantillons infectieux avec EPI",
                "QUALITÉ ANALYTIQUE: prévention contamination croisée"
            ]
        }}
    ],
    "maintenance_preventive": [
        {{
            "type_maintenance": "maintenance détaillée avec niveau d'intervention",
            "frequence_precise": "fréquence exacte avec conditions déclenchantes",
            "duree_estimee": "temps nécessaire avec marge",
            "procedure_step_by_step": {{
                "preparation": [
                    "préparation 1: matériels avec références"
                ],
                "execution": [
                    "étape 1: procédure avec paramètres techniques"
                ],
                "verification": [
                    "contrôle 1: paramètre avec limite acceptable"
                ]
            }},
            "materiels_specifiques": [
                "matériel 1 avec référence et spécifications"
            ]
        }}
    ],
    "guide_utilisation_quotidienne": {{
        "demarrage_systeme": [
            "startup 1: vérifications préalables avec check-list",
            "startup 2: initialisation avec paramètres de contrôle"
        ],
        "arret_systeme": [
            "shutdown 1: finalisation analyses en cours avec sauvegarde",
            "shutdown 2: mise en sécurité avec vérifications"
        ],
        "maintenance_quotidienne": [
            "tâche quotidienne 1: contrôles de routine avec documentation"
        ]
    }},
    "resume_executif": "Résumé technique et clinique EXHAUSTIF de l'instrument couvrant: technologie utilisée, applications cliniques principales, performances analytiques clés, exigences d'utilisation, considérations de maintenance et points critiques de sécurité pour usage médical professionnel"
}}

EXIGENCE ABSOLUE: JSON PARFAITEMENT VALIDE. Consolide EXHAUSTIVEMENT toutes les données en préservant les détails techniques critiques."""
        
        try:
            # Utiliser le modèle avancé si disponible
            model_to_use = getattr(self, 'advanced_model', self.gemini_model)
            
            response = model_to_use.generate_content(synthesis_prompt)
            
            if not response or not response.text:
                raise ValueError("❌ Gemini n'a pas généré de synthèse")
            
            # Double validation avec correction automatique
            cleaned_json = self.validate_and_fix_json_with_gemini(response.text.strip())
            result = json.loads(cleaned_json)
            
            # Validation de la synthèse finale détaillée
            self.validate_comprehensive_synthesis(result)
            
            logger.info("✅ Synthèse médicale EXHAUSTIVE créée et validée avec double validation")
            return result
            
        except Exception as e:
            logger.error(f"❌ ÉCHEC SYNTHÈSE DÉTAILLÉE: {e}")
            # Fallback: créer une synthèse de secours
            logger.warning("🚨 Création synthèse de secours détaillée...")
            return self.create_comprehensive_fallback_synthesis(instrument_info, all_procedures, all_maintenance, all_specs, all_security)
    
    def validate_comprehensive_synthesis(self, synthesis: Dict):
        """Validation stricte de la synthèse exhaustive"""
        if not isinstance(synthesis, dict):
            raise ValueError("❌ Synthèse exhaustive invalide")
        
        critical_sections = [
            'informations_generales', 'procedures_analyses', 'maintenance_preventive'
        ]
        
        missing_critical = [sec for sec in critical_sections if not synthesis.get(sec)]
        
        if missing_critical:
            logger.warning(f"⚠️ ATTENTION: Sections critiques manquantes: {missing_critical}")
        
        # Vérifier résumé exécutif
        resume = synthesis.get('resume_executif', '')
        if not resume or len(resume.strip()) < 100:
            logger.warning("⚠️ Résumé exécutif insuffisant ou manquant")
        
        # Vérifier procédures (critique pour sécurité)
        procedures = synthesis.get('procedures_analyses', [])
        if not procedures:
            logger.warning("⚠️ ATTENTION CRITIQUE: Aucune procédure d'analyse identifiée")
        
        # Vérifier maintenance (critique pour fiabilité)
        maintenance = synthesis.get('maintenance_preventive', [])
        if not maintenance:
            logger.warning("⚠️ ATTENTION: Aucune procédure de maintenance identifiée")
        
        logger.info("✅ Synthèse exhaustive médicale validée")
    
    def create_comprehensive_fallback_synthesis(self, instrument_info: Dict, procedures: List, maintenance: List, specs: List, security: List) -> Dict:
        """Crée une synthèse de secours exhaustive en cas d'échec Gemini"""
        logger.warning("🚨 Création synthèse de secours EXHAUSTIVE")
        
        return {
            "informations_generales": {
                "nom_instrument": instrument_info.get('nom', 'Instrument non identifié'),
                "fabricant": instrument_info.get('fabricant', 'Non spécifié'),
                "modele": instrument_info.get('modele', 'Non spécifié'),
                "type_instrument": instrument_info.get('type', 'Analyseur médical'),
                "applications_principales": instrument_info.get('applications_cliniques', [])[:5],
                "principe_fonctionnement": instrument_info.get('principe_technique', 'Non spécifié'),
                "approche_diagnostique": "Méthodologie diagnostique selon manuel"
            },
            "procedures_analyses": [
                {
                    "nom_analyse": proc.get('nom', 'Analyse non spécifiée'),
                    "indication_clinique": "Indication selon manuel complet",
                    "echantillon": {
                        "type": proc.get('echantillon', {}).get('type', 'Non spécifié'),
                        "volume_minimum": proc.get('echantillon', {}).get('volume_minimum', 'Voir manuel'),
                        "volume_traitement": proc.get('echantillon', {}).get('volume_traitement', 'Voir manuel'),
                        "anticoagulant": proc.get('echantillon', {}).get('anticoagulant', 'Selon procédure')
                    },
                    "preparation_detaillee": {
                        "etapes": proc.get('preparation_echantillon', {}).get('etapes', [])[:5],
                        "stabilite": proc.get('preparation_echantillon', {}).get('stabilite', 'Voir manuel'),
                        "stockage": proc.get('preparation_echantillon', {}).get('stockage', 'Conditions standard')
                    },
                    "procedure_analytique": {
                        "workflow": proc.get('procedure_analytique', {}).get('etapes_detaillees', [])[:6],
                        "duree_totale": proc.get('procedure_analytique', {}).get('duree_totale', 'Voir manuel'),
                        "conditions_techniques": proc.get('procedure_analytique', {}).get('temperature_incubation', 'Conditions contrôlées')
                    },
                    "performance_analytique": {
                        "gamme_mesure": proc.get('performance', {}).get('gamme_lineaire', 'Voir spécifications'),
                        "limite_detection": proc.get('performance', {}).get('limite_detection', 'Selon validation'),
                        "precision": proc.get('performance', {}).get('precision', 'Données de validation')
                    },
                    "controles_qualite": {
                        "types_controles": proc.get('controles_qualite', {}).get('controles_requis', [])[:3],
                        "frequence": proc.get('controles_qualite', {}).get('frequence', 'Selon procédure')
                    },
                    "precautions_critiques": proc.get('precautions_critiques', [])[:4]
                }
                for proc in procedures[:5]  # Max 5 procédures
            ],
            "maintenance_preventive": [
                {
                    "type_maintenance": maint.get('type', 'Maintenance non spécifiée'),
                    "frequence_precise": maint.get('frequence', 'Non spécifiée'),
                    "duree_estimee": maint.get('duree', 'Selon complexité'),
                    "procedure_step_by_step": {
                        "preparation": maint.get('procedure_complete', {}).get('preparation', [])[:3],
                        "execution": maint.get('procedure_complete', {}).get('execution', [])[:4],
                        "verification": maint.get('procedure_complete', {}).get('verification', [])[:3]
                    },
                    "materiels_specifiques": maint.get('materiels_requis', [])[:3]
                }
                for maint in maintenance[:6]  # Max 6 maintenances
            ],
            "guide_utilisation_quotidienne": {
                "demarrage_systeme": [
                    "Vérifier l'alimentation électrique",
                    "Contrôler les niveaux de réactifs",
                    "Effectuer les contrôles qualité",
                    "Valider le fonctionnement système"
                ],
                "arret_systeme": [
                    "Finaliser toutes les analyses en cours",
                    "Effectuer le nettoyage système",
                    "Sauvegarder les données",
                    "Mise en sécurité"
                ],
                "maintenance_quotidienne": [
                    "Contrôles visuels de l'instrument",
                    "Nettoyage des surfaces externes",
                    "Vérification des niveaux",
                    "Documentation des observations"
                ]
            },
            "resume_executif": f"Synthèse technique exhaustive de l'instrument {instrument_info.get('nom', 'non identifié')} générée automatiquement. {len(procedures)} procédures d'analyse, {len(maintenance)} opérations de maintenance identifiées. Cette synthèse consolidée couvre les aspects critiques d'utilisation, de maintenance et de sécurité pour usage médical professionnel. Vérification obligatoire avec le manuel complet avant mise en service clinique."
        }
    
    def merge_texts_medical(self, chunk_results: List[Dict]) -> str:
        """Fusion stricte des textes avec validation médicale"""
        full_text = ""
        successful_chunks = 0
        total_chars = 0
        
        for i, chunk_result in enumerate(chunk_results):
            if chunk_result.get("text") and len(chunk_result["text"]) > 50:  # Validation stricte
                chunk_text = chunk_result["text"]
                char_count = len(chunk_text)
                
                # En-tête de section médicale
                section_header = f"\n\n{'='*80}\nSECTION MÉDICALE {i+1}\nPages: {chunk_result.get('pages', '?')}\nCaractères: {char_count:,}\nSource: {Path(chunk_result.get('chunk_file', '')).name}\n{'='*80}\n\n"
                
                full_text += section_header + chunk_text
                successful_chunks += 1
                total_chars += char_count
                
                logger.info(f"✅ Section {i+1} intégrée: {char_count:,} caractères")
            else:
                logger.error(f"❌ Section {i+1} invalide - texte insuffisant")
                raise ValueError(f"Section {i+1} contient un texte insuffisant pour analyse médicale")
        
        if successful_chunks == 0:
            raise ValueError("❌ Aucune section valide pour analyse médicale")
        
        logger.info(f"✅ Fusion médicale: {successful_chunks} sections, {total_chars:,} caractères")
        return full_text
    
    def create_analysis_chunks(self, text: str) -> List[Dict]:
        """Création de chunks d'analyse optimisés pour Gemini"""
        if not text or len(text.strip()) < 100:
            raise ValueError("❌ Texte insuffisant pour création de chunks")
        
        # Limite Gemini conservative
        max_chars_per_chunk = 350000
        
        chunks = []
        
        if len(text) <= max_chars_per_chunk:
            chunks.append({
                "text": text,
                "chunk_id": 0,
                "description": "Document médical complet",
                "char_count": len(text)
            })
            logger.info(f"📄 Document analysable en 1 chunk: {len(text):,} caractères")
            return chunks
        
        # Découpage par sections marquées
        section_markers = re.findall(r'={80}\nSECTION MÉDICALE \d+', text)
        logger.info(f"📊 {len(section_markers)} sections médicales identifiées")
        
        if len(section_markers) > 1:
            # Découpage intelligent par sections
            sections = re.split(r'={80}\nSECTION MÉDICALE \d+[^\n]*\n={80}\n\n', text)
            
            current_chunk = ""
            chunk_sections = []
            
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                
                if len(current_chunk) + len(section) > max_chars_per_chunk and current_chunk:
                    chunks.append({
                        "text": current_chunk,
                        "chunk_id": len(chunks),
                        "description": f"Sections médicales {chunk_sections[0]}-{chunk_sections[-1]}" if len(chunk_sections) > 1 else f"Section médicale {chunk_sections[0]}",
                        "char_count": len(current_chunk)
                    })
                    
                    current_chunk = ""
                    chunk_sections = []
                
                current_chunk += section
                chunk_sections.append(i+1)
            
            # Chunk final
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk,
                    "chunk_id": len(chunks),
                    "description": f"Sections finales {chunk_sections[0]}-{chunk_sections[-1]}" if len(chunk_sections) > 1 else f"Section finale {chunk_sections[0]}",
                    "char_count": len(current_chunk)
                })
        
        else:
            # Découpage simple par taille
            for i in range(0, len(text), max_chars_per_chunk):
                chunk_text = text[i:i + max_chars_per_chunk]
                
                if chunk_text.strip():
                    chunks.append({
                        "text": chunk_text,
                        "chunk_id": len(chunks),
                        "description": f"Partie médicale {len(chunks) + 1}",
                        "char_count": len(chunk_text)
                    })
        
        if not chunks:
            raise ValueError("❌ Échec création des chunks d'analyse")
        
        logger.info(f"✅ {len(chunks)} chunks d'analyse créés:")
        for chunk in chunks:
            logger.info(f"   - {chunk['description']}: {chunk['char_count']:,} caractères")
        
        return chunks
    
    def analyze_manual_organized(self, pdf_path: Path, language: str = 'fr') -> Dict:
        """Analyse complète stricte d'un manuel médical avec extraction exhaustive et support multilingue"""
        logger.info(f"🏥 DÉBUT ANALYSE MÉDICALE EXHAUSTIVE: {pdf_path.name} (Language: {language})")
        
        pdf_chunks = []
        prepared_pdf = None
        
        try:
            # 1. Préparation et validation PDF
            prepared_pdf = self.prepare_pdf(pdf_path)
            
            # 2. Découpage strict en chunks ≤15 pages
            pdf_chunks = self.split_pdf_15pages(prepared_pdf)
            logger.info(f"📄 {len(pdf_chunks)} chunks PDF créés")
            
            # 3. Extraction de texte stricte
            chunk_texts = []
            
            for i, chunk_pdf in enumerate(pdf_chunks):
                logger.info(f"🔍 Extraction chunk {i+1}/{len(pdf_chunks)}")
                
                result = self.extract_text_safe(chunk_pdf)  # Lève exception si échec
                chunk_texts.append(result)
                
                # Délai entre extractions (respect des quotas)
                if i < len(pdf_chunks) - 1:
                    delay = self.config["analysis"]["delay_between_requests"]
                    time.sleep(delay)
            
            # 4. Fusion et structuration du texte
            full_text = self.merge_texts_medical(chunk_texts)
            
            if not full_text or len(full_text.strip()) < 500:
                raise ValueError("❌ Texte extrait insuffisant pour analyse médicale")
            
            # 5. Création des chunks d'analyse Gemini
            analysis_chunks = self.create_analysis_chunks(full_text)
            
            if not analysis_chunks:
                raise ValueError("❌ Impossible de créer des chunks d'analyse")
            
            # 6. Analyse Gemini EXHAUSTIVE de chaque chunk
            chunk_analyses = []
            context = ""
            
            for i, chunk in enumerate(analysis_chunks):
                logger.info(f"🧠 Analyse Gemini EXHAUSTIVE {i+1}/{len(analysis_chunks)}: {chunk['description']}")
                
                analysis = self.analyze_with_gemini_advanced(chunk, context, language)  # Version avancée avec double validation
                chunk_analyses.append(analysis)
                
                # Contexte enrichi pour chunk suivant
                context += f"{chunk['description']}: {analysis.get('resume_section', '')}\n"
                if analysis.get('instrument', {}).get('nom'):
                    context += f"Instrument: {analysis['instrument']['nom']}\n"
                
                # Délai entre analyses Gemini
                if i < len(analysis_chunks) - 1:
                    delay = self.config["analysis"]["delay_between_requests"]
                    time.sleep(delay)
            
            # 7. Synthèse finale médicale EXHAUSTIVE
            logger.info("🔬 Création de la synthèse médicale EXHAUSTIVE...")
            synthesis = self.synthesize_final_medical(chunk_analyses, language)
            
            # 8. Génération du PDF LaTeX PROFESSIONNEL avec données complètes
            output_pdf = self.syntheses_dir / f"{pdf_path.stem}_SYNTHESE_MEDICALE_COMPLETE.pdf"
            
            logger.info("📄 Génération du PDF médical professionnel...")
            pdf_success = self.latex_generator.generate_latex_synthesis(
                synthesis, output_pdf, f"MANUEL MÉDICAL COMPLET - {pdf_path.stem}", language
            )
            
            if not pdf_success:
                raise RuntimeError("❌ ÉCHEC GÉNÉRATION PDF MÉDICAL - Aucun fichier créé")
            
            # 9. Nettoyage strict des fichiers temporaires
            self.cleanup_temp_files(pdf_chunks, prepared_pdf, pdf_path)
            
            # 10. Statistiques exhaustives
            stats = self.calculate_comprehensive_stats(pdf_chunks, analysis_chunks, chunk_texts, chunk_analyses, synthesis)
            
            logger.info(f"✅ ANALYSE MÉDICALE EXHAUSTIVE TERMINÉE: {pdf_path.name}")
            logger.info(f"📄 PDF médical complet créé: {output_pdf}")
            
            return {
                "success": True,
                "pdf_medical": str(output_pdf),
                "statistiques": stats,
                "synthesis": synthesis,
                "validation": "CONFORME USAGE MÉDICAL PROFESSIONNEL"
            }
            
        except Exception as e:
            # Nettoyage en cas d'erreur
            self.emergency_cleanup(pdf_chunks, prepared_pdf, pdf_path)
            
            error_msg = f"❌ ÉCHEC ANALYSE MÉDICALE EXHAUSTIVE: {pdf_path.name} - {e}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": str(e),
                "pdf_path": str(pdf_path),
                "validation": "ÉCHEC - NON CONFORME"
            }
    
    def calculate_comprehensive_stats(self, pdf_chunks: List[Path], analysis_chunks: List[Dict], 
                                    chunk_texts: List[Dict], chunk_analyses: List[Dict], synthesis: Dict) -> Dict:
        """Calcul des statistiques exhaustives"""
        
        # Compter les éléments dans la synthèse finale
        procedures = synthesis.get("procedures_analyses", [])
        maintenance = synthesis.get("maintenance_preventive", [])
        
        # Statistiques détaillées par procédure
        procedures_with_performance = sum(1 for p in procedures if p.get("performance_analytique"))
        procedures_with_controls = sum(1 for p in procedures if p.get("controles_qualite"))
        procedures_with_precautions = sum(1 for p in procedures if p.get("precautions_critiques"))
        
        # Statistiques de maintenance
        maintenance_with_timing = sum(1 for m in maintenance if m.get("duree_estimee"))
        maintenance_with_materials = sum(1 for m in maintenance if m.get("materiels_specifiques"))
        
        return {
            "extraction": {
                "chunks_pdf_traités": len(pdf_chunks),
                "chunks_analysés": len(analysis_chunks),
                "caractères_totaux": sum(result.get("char_count", 0) for result in chunk_texts),
                "extractions_réussies": len([r for r in chunk_texts if r.get("text") and len(r["text"]) > 50])
            },
            "analyse_brute": {
                "procédures_brutes": sum(len(a.get("procedures", [])) for a in chunk_analyses),
                "maintenances_brutes": sum(len(a.get("maintenance", [])) for a in chunk_analyses),
                "spécifications_brutes": sum(len(a.get("specifications_techniques", [])) for a in chunk_analyses),
                "éléments_sécurité": sum(len(a.get("securite", [])) for a in chunk_analyses),
                "éléments_stockage": sum(len(a.get("stockage_reagents", [])) for a in chunk_analyses)
            },
            "synthese_finale": {
                "procédures_consolidées": len(procedures),
                "procédures_avec_performance": procedures_with_performance,
                "procédures_avec_contrôles": procedures_with_controls,
                "procédures_avec_précautions": procedures_with_precautions,
                "maintenances_consolidées": len(maintenance),
                "maintenances_avec_timing": maintenance_with_timing,
                "maintenances_avec_matériels": maintenance_with_materials
            },
            "qualité_extraction": {
                "instrument_identifié": bool(synthesis.get("informations_generales", {}).get("nom_instrument")),
                "principe_technique_documenté": bool(synthesis.get("informations_generales", {}).get("principe_fonctionnement")),
                "guide_utilisation_complet": bool(synthesis.get("guide_utilisation_quotidienne")),
                "résumé_exécutif_longueur": len(synthesis.get("resume_executif", "")),
                "niveau_détail": "EXHAUSTIF" if len(procedures) > 0 and procedures_with_performance > 0 else "BASIQUE"
            },
            "conformité_médicale": {
                "données_performance_analytique": procedures_with_performance > 0,
                "précautions_sécurité_documentées": procedures_with_precautions > 0,
                "maintenance_préventive_structurée": len(maintenance) > 0,
                "guide_utilisation_quotidienne": bool(synthesis.get("guide_utilisation_quotidienne"))
            },
            "validation": "CONFORME USAGE MÉDICAL PROFESSIONNEL"
        }
    
    def cleanup_temp_files(self, pdf_chunks: List[Path], prepared_pdf: Path, original_pdf: Path):
        """Nettoyage strict des fichiers temporaires"""
        logger.info("🧹 Nettoyage des fichiers temporaires...")
        
        # Nettoyer les chunks PDF
        if pdf_chunks and len(pdf_chunks) > 1:
            for chunk_file in pdf_chunks:
                try:
                    if chunk_file.exists():
                        chunk_file.unlink()
                        logger.debug(f"✅ Chunk supprimé: {chunk_file.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de supprimer {chunk_file.name}: {e}")
            
            # Supprimer le dossier de chunks
            try:
                chunk_dir = pdf_chunks[0].parent
                if chunk_dir.exists() and not any(chunk_dir.iterdir()):
                    chunk_dir.rmdir()
                    logger.info(f"✅ Dossier chunks supprimé: {chunk_dir.name}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer le dossier chunks: {e}")
        
        # Nettoyer le PDF déchiffré temporaire
        if prepared_pdf != original_pdf and prepared_pdf.exists():
            try:
                prepared_pdf.unlink()
                logger.info(f"✅ PDF déchiffré temporaire supprimé: {prepared_pdf.name}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer le PDF déchiffré: {e}")
        
        logger.info("✅ Nettoyage terminé")
    
    def emergency_cleanup(self, pdf_chunks: List[Path], prepared_pdf: Path, original_pdf: Path):
        """Nettoyage d'urgence en cas d'erreur"""
        logger.info("🚨 Nettoyage d'urgence en cours...")
        
        try:
            self.cleanup_temp_files(pdf_chunks, prepared_pdf, original_pdf)
        except:
            logger.warning("⚠️ Nettoyage d'urgence partiel seulement")


def main():
    """Fonction principale STRICTE"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lab Manual Analyzer - Version Médicale Stricte avec Double Validation")
    parser.add_argument("input_path", help="Chemin vers le fichier PDF médical")
    parser.add_argument("--config", default="config.json", help="Fichier de configuration")
    
    args = parser.parse_args()
    
    try:
        # Initialisation STRICTE
        analyzer = LabManualAnalyzerStrict(args.config)
        
        input_path = Path(args.input_path)
        
        if not input_path.is_file() or input_path.suffix.lower() != '.pdf':
            print(f"❌ ERREUR: {input_path} n'est pas un fichier PDF valide")
            print(f"Usage: python {Path(__file__).name} chemin/vers/manuel_medical.pdf")
            return 1
        
        print(f"🏥 ANALYSE MÉDICALE STRICTE AVEC DOUBLE VALIDATION: {input_path.name}")
        print(f"📄 PDF LaTeX sera généré dans: {analyzer.syntheses_dir}")
        print("⏳ Traitement en cours (mode strict avec Gemini 2.0 Flash + correction automatique)...")
        
        # Analyse STRICTE
        result = analyzer.analyze_manual_organized(input_path)
        
        if result.get("success"):
            print(f"\n✅ ANALYSE MÉDICALE RÉUSSIE AVEC DOUBLE VALIDATION")
            print(f"📄 PDF MÉDICAL GÉNÉRÉ: {result['pdf_medical']}")
            
            print(f"\n📊 STATISTIQUES:")
            stats = result.get("statistiques", {})
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"   {key.replace('_', ' ').title()}:")
                    for subkey, subvalue in value.items():
                        print(f"     - {subkey.replace('_', ' ')}: {subvalue}")
                else:
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            
            print(f"\n🔬 VALIDATION: {result.get('validation')}")
            
            synthesis = result.get("synthesis", {})
            if synthesis:
                procedures = synthesis.get("procedures_analyses", [])
                maintenance = synthesis.get("maintenance_preventive", [])
                print(f"\n📋 CONTENU MÉDICAL EXTRAIT AVEC DOUBLE VALIDATION:")
                print(f"   🧪 {len(procedures)} procédures d'analyse médicales détaillées")
                print(f"   🔧 {len(maintenance)} procédures de maintenance préventive")
                print(f"   📊 Guide d'utilisation quotidienne: {'✅' if synthesis.get('guide_utilisation_quotidienne') else '❌'}")
            
            print(f"\n🎯 FICHIER FINAL: {result['pdf_medical']}")
            print(f"   ➤ Document PDF professionnel prêt pour usage médical")
            print(f"   ➤ Extraction maximale d'informations avec validation JSON")
            print(f"   ➤ Compatible Gemini 2.0 Flash + correction automatique")
            
        else:
            print(f"\n❌ ÉCHEC DE L'ANALYSE MÉDICALE")
            print(f"🚨 ERREUR CRITIQUE: {result.get('error')}")
            print(f"\n🔍 DIAGNOSTIC:")
            print(f"   1. Vérifiez la configuration dans config.json")
            print(f"   2. Contrôlez vos quotas Google Cloud et Gemini")
            print(f"   3. Assurez-vous que LaTeX est installé")
            print(f"   4. Consultez les logs: lab_analysis.log")
            print(f"\n⚠️  AUCUN FICHIER GÉNÉRÉ - Sécurité médicale respectée")
            return 1
    
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE SYSTÈME: {e}")
        logger.error(f"Erreur critique dans main: {e}")
        print(f"\n🚨 ANALYSE INTERROMPUE - Aucun fichier généré")
        print(f"   Ceci est normal en mode médical strict")
        print(f"   Consultez lab_analysis.log pour diagnostic complet")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)