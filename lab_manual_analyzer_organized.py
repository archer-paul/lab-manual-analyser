#!/usr/bin/env python3
"""
Lab Manual Analyzer - Version organisée avec dossier synthèses
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

# Import du générateur PDF et déchiffreur
from pdf_generator import PDFSynthesisGenerator
from pdf_decryptor import decrypt_pdf

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lab_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LabManualAnalyzerOrganized:
    def __init__(self, config_path: str = "config.json"):
        """Initialise l'analyseur avec organisation des fichiers"""
        self.config = self.load_config(config_path)
        self.setup_google_apis()
        self.setup_output_directories()
        
        # Limite réelle - 15 pages max pour Document AI
        self.max_pages_per_request = 15
        logger.info(f"Limite Document AI: {self.max_pages_per_request} pages par requête")
        
        # Initialiser le générateur PDF
        try:
            self.pdf_generator = PDFSynthesisGenerator()
            self.pdf_available = True
        except ImportError:
            logger.warning("ReportLab non installé - génération Markdown uniquement")
            self.pdf_available = False
    
    def load_config(self, config_path: str) -> Dict:
        """Charge la configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logger.error(f"Fichier de configuration non trouvé: {config_path}")
            raise
    
    def setup_output_directories(self):
        """Crée la structure de dossiers organisée"""
        # Dossiers principaux
        self.manuels_dir = Path("manuels")
        self.syntheses_dir = self.manuels_dir / "syntheses"
        self.logs_dir = Path("logs")
        self.temp_dir = Path("temp")
        
        # Créer les dossiers s'ils n'existent pas
        for directory in [self.manuels_dir, self.syntheses_dir, self.logs_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)
        
        logger.info(f"Structure de dossiers organisée:")
        logger.info(f"  - PDFs source: {self.manuels_dir}")
        logger.info(f"  - Synthèses: {self.syntheses_dir}")
        logger.info(f"  - Logs: {self.logs_dir}")
        logger.info(f"  - Temporaire: {self.temp_dir}")
    
    def setup_google_apis(self):
        """Configure les APIs Google Cloud"""
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
        
        # Configuration Gemini
        genai.configure(api_key=self.config["gemini"]["api_key"])
        self.gemini_model = genai.GenerativeModel(self.config["gemini"]["model"])
    
    def prepare_pdf(self, pdf_path: Path) -> Path:
        """Prépare le PDF (déchiffrement si nécessaire)"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.is_encrypted:
                    logger.info(f"PDF chiffré détecté: {pdf_path.name}")
                    
                    # Sauvegarder dans le dossier temp
                    decrypted_path = self.temp_dir / f"decrypted_{pdf_path.name}"
                    
                    if decrypt_pdf(pdf_path, decrypted_path):
                        logger.info(f"PDF déchiffré: {decrypted_path}")
                        return decrypted_path
                    else:
                        logger.error(f"Impossible de déchiffrer: {pdf_path}")
                        return pdf_path
                else:
                    return pdf_path
                    
        except ImportError:
            logger.warning("PyPDF2 non disponible")
            return pdf_path
        except Exception as e:
            logger.warning(f"Erreur vérification PDF: {e}")
            return pdf_path
    
    def split_pdf_15pages(self, pdf_path: Path) -> List[Path]:
        """Divise un PDF en chunks de 15 pages dans le dossier temp"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                logger.info(f"PDF total: {total_pages} pages")
                
                if total_pages <= self.max_pages_per_request:
                    logger.info("PDF petit - pas de découpage nécessaire")
                    return [pdf_path]
                
                # Créer un dossier pour les chunks dans temp
                chunks_dir = self.temp_dir / f"{pdf_path.stem}_chunks"
                chunks_dir.mkdir(exist_ok=True)
                
                chunks = []
                pages_per_chunk = self.max_pages_per_request
                num_chunks = math.ceil(total_pages / pages_per_chunk)
                
                logger.info(f"Découpage en {num_chunks} chunks de {pages_per_chunk} pages max")
                
                for i in range(num_chunks):
                    start_page = i * pages_per_chunk
                    end_page = min(start_page + pages_per_chunk, total_pages)
                    
                    # Créer le chunk
                    pdf_writer = PyPDF2.PdfWriter()
                    
                    for page_num in range(start_page, end_page):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
                    
                    # Sauvegarder le chunk dans temp
                    chunk_path = chunks_dir / f"chunk_{i+1:02d}_p{start_page+1}-{end_page}.pdf"
                    
                    with open(chunk_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                    
                    chunks.append(chunk_path)
                    logger.info(f"Chunk créé: {chunk_path.name} ({end_page - start_page} pages)")
                
                return chunks
                
        except Exception as e:
            logger.error(f"Erreur découpage: {e}")
            return [pdf_path]
    
    def extract_text_safe(self, pdf_path: Path, max_retries: int = 2) -> Dict:
        """Extraction sécurisée avec limite 15 pages"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Extraction: {pdf_path.name} (tentative {attempt + 1})")
                
                with open(pdf_path, "rb") as pdf_file:
                    pdf_content = pdf_file.read()
                
                file_size_mb = len(pdf_content) / (1024 * 1024)
                logger.info(f"  Taille: {file_size_mb:.1f} MB")
                
                if len(pdf_content) > 20 * 1024 * 1024:
                    return {"error": "Fichier trop volumineux", "text": ""}
                
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
                
                char_count = len(document.text)
                page_count = len(document.pages) if document.pages else 0
                
                logger.info(f"  Succès: {char_count:,} caractères, {page_count} pages")
                
                return {
                    "text": document.text,
                    "pages": page_count,
                    "chunk_file": str(pdf_path),
                    "char_count": char_count
                }
                
            except Exception as e:
                logger.warning(f"  Tentative {attempt + 1} échouée: {str(e)[:100]}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    logger.info(f"  Attente {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"  Échec définitif: {pdf_path.name}")
                    return {"error": str(e), "text": "", "chunk_file": str(pdf_path)}
    
    def merge_and_structure_texts(self, chunk_results: List[Dict]) -> str:
        """Fusion et structuration intelligente des textes"""
        full_text = ""
        successful_chunks = 0
        total_chars = 0
        
        for i, chunk_result in enumerate(chunk_results):
            if "error" not in chunk_result and chunk_result.get("text"):
                chunk_text = chunk_result.get("text", "")
                char_count = len(chunk_text)
                
                # En-tête de section claire
                section_header = f"\n\n{'='*60}\nSECTION {i+1} - CHUNK {i+1}\nPages: {chunk_result.get('pages', '?')}\nCaractères: {char_count:,}\n{'='*60}\n\n"
                
                full_text += section_header + chunk_text
                
                successful_chunks += 1
                total_chars += char_count
                logger.info(f"  Section {i+1}: {char_count:,} caractères intégrés")
            else:
                error_msg = chunk_result.get('error', 'aucun texte')
                logger.warning(f"  Section {i+1}: {error_msg[:50]}...")
        
        logger.info(f"Fusion terminée:")
        logger.info(f"  {successful_chunks}/{len(chunk_results)} sections réussies")
        logger.info(f"  {total_chars:,} caractères au total")
        
        return full_text
    
    def create_gemini_chunks(self, text: str) -> List[Dict]:
        """Crée des chunks optimaux pour Gemini"""
        if not text.strip():
            return []
        
        # Limite conservative pour Gemini
        max_chars_per_chunk = 400000
        
        chunks = []
        
        if len(text) <= max_chars_per_chunk:
            chunks.append({
                "text": text,
                "chunk_id": 0,
                "description": "Document complet",
                "char_count": len(text)
            })
            logger.info(f"Document analysable en 1 chunk ({len(text):,} caractères)")
            return chunks
        
        # Découpage par sections marquées
        section_markers = re.findall(r'={60}\nSECTION \d+', text)
        logger.info(f"Trouvé {len(section_markers)} sections marquées")
        
        if len(section_markers) > 1:
            # Découpage par sections
            sections = re.split(r'={60}\nSECTION \d+[^\n]*\n={60}\n\n', text)
            
            current_chunk = ""
            chunk_sections = []
            
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                
                if len(current_chunk) + len(section) > max_chars_per_chunk and current_chunk:
                    chunks.append({
                        "text": current_chunk,
                        "chunk_id": len(chunks),
                        "description": f"Sections {chunk_sections[0]}-{chunk_sections[-1]}" if len(chunk_sections) > 1 else f"Section {chunk_sections[0]}",
                        "char_count": len(current_chunk)
                    })
                    
                    current_chunk = ""
                    chunk_sections = []
                
                current_chunk += section
                chunk_sections.append(i+1)
            
            # Dernier chunk
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
                        "description": f"Partie {len(chunks) + 1}",
                        "char_count": len(chunk_text)
                    })
        
        logger.info(f"{len(chunks)} chunks d'analyse créés:")
        for chunk in chunks:
            logger.info(f"  - {chunk['description']}: {chunk['char_count']:,} caractères")
        
        return chunks
    
    def analyze_with_gemini_15p(self, chunk: Dict, context: str = "") -> Dict:
        """Analyse Gemini optimisée pour chunks 15 pages"""
        
        # Prompt optimisé et plus court
        prompt = f"""
Analyse ce manuel d'instrument de laboratoire médical. Extrait toutes les informations utiles.

CONTEXTE: {context[-500:] if context else "Début"}

SECTION: {chunk['description']}

CONTENU À ANALYSER:
{chunk['text'][:70000]}

Réponds en JSON strict:

{{
    "instrument": {{
        "nom": "nom instrument complet",
        "fabricant": "fabricant",
        "modele": "modèle",
        "type": "type appareil"
    }},
    "procedures": [
        {{
            "nom": "nom procédure",
            "echantillon": "type échantillon",
            "preparation": ["préparation 1", "préparation 2"],
            "execution": ["étape 1", "étape 2", "étape 3"],
            "materiels": ["matériel 1", "matériel 2"],
            "duree": "durée",
            "precautions": ["précaution 1", "précaution 2"],
            "controles": ["contrôle qualité"],
            "resultats": "interprétation"
        }}
    ],
    "maintenance": [
        {{
            "nom": "type maintenance",
            "frequence": "fréquence",
            "etapes": ["étape 1", "étape 2"],
            "materiels": ["matériel"],
            "duree": "temps"
        }}
    ],
    "specifications": [
        {{
            "categorie": "catégorie",
            "parametre": "paramètre",
            "valeur": "valeur",
            "unite": "unité",
            "conditions": "conditions"
        }}
    ],
    "securite": [
        {{
            "risque": "type risque",
            "prevention": ["mesure 1", "mesure 2"],
            "equipements": ["EPI"],
            "urgence": ["action urgence"]
        }}
    ],
    "calibration": [
        {{
            "type": "type calibration",
            "frequence": "fréquence",
            "procedure": ["étape 1", "étape 2"],
            "standards": ["standard utilisé"]
        }}
    ],
    "resume": "résumé en 2-3 phrases"
}}

Important: JSON uniquement, sois précis, n'invente rien.
"""
        
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Gemini: {chunk['description']} (tentative {attempt + 1})")
                
                response = self.gemini_model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Nettoyage JSON robuste
                cleaned_json = self.extract_clean_json(response_text)
                
                # Parsing et validation
                result = json.loads(cleaned_json)
                
                # Assurer la structure minimale
                defaults = {
                    "instrument": {},
                    "procedures": [],
                    "maintenance": [],
                    "specifications": [],
                    "securite": [],
                    "calibration": [],
                    "resume": ""
                }
                
                for key, default_value in defaults.items():
                    if key not in result:
                        result[key] = default_value
                
                proc_count = len(result.get('procedures', []))
                maint_count = len(result.get('maintenance', []))
                spec_count = len(result.get('specifications', []))
                
                logger.info(f"  Succès: {proc_count} procédures, {maint_count} maintenances, {spec_count} spécifications")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"  JSON invalide (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.warning(f"  Erreur Gemini (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        # Fallback
        logger.error(f"  Échec définitif: {chunk['description']}")
        return {
            "instrument": {},
            "procedures": [],
            "maintenance": [],
            "specifications": [],
            "securite": [],
            "calibration": [],
            "resume": f"Erreur analyse: {chunk['description']}"
        }
    
    def extract_clean_json(self, response_text: str) -> str:
        """Extrait et nettoie le JSON de la réponse Gemini"""
        
        # Supprimer blocs markdown
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.rfind("```")
            if end > start:
                response_text = response_text[start:end]
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            if end > start:
                response_text = response_text[start:end]
        
        # Extraire entre { et }
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        
        if first_brace >= 0 and last_brace > first_brace:
            response_text = response_text[first_brace:last_brace + 1]
        
        return response_text.strip()
    
    def synthesize_final_15p(self, analyses: List[Dict]) -> Dict:
        """Synthèse finale pour version 15 pages"""
        
        # Compilation des données
        all_procedures = []
        all_maintenance = []
        all_specs = []
        all_security = []
        all_calibration = []
        instrument_info = {}
        
        for analysis in analyses:
            all_procedures.extend(analysis.get("procedures", []))
            all_maintenance.extend(analysis.get("maintenance", []))
            all_specs.extend(analysis.get("specifications", []))
            all_security.extend(analysis.get("securite", []))
            all_calibration.extend(analysis.get("calibration", []))
            
            # Consolider infos instrument
            inst = analysis.get("instrument", {})
            for key, value in inst.items():
                if value and str(value).strip():
                    if key not in instrument_info or len(str(value)) > len(str(instrument_info.get(key, ""))):
                        instrument_info[key] = value
        
        logger.info(f"Données compilées:")
        logger.info(f"  - Procédures: {len(all_procedures)}")
        logger.info(f"  - Maintenances: {len(all_maintenance)}")
        logger.info(f"  - Spécifications: {len(all_specs)}")
        logger.info(f"  - Sécurité: {len(all_security)}")
        logger.info(f"  - Calibrations: {len(all_calibration)}")
        
        # Synthèse finale concentrée
        synthesis_prompt = f"""
Synthèse finale de ce manuel d'instrument de laboratoire.

INSTRUMENT: {json.dumps(instrument_info, ensure_ascii=False)}

DONNÉES COLLECTÉES:
- {len(all_procedures)} procédures
- {len(all_maintenance)} maintenances  
- {len(all_specs)} spécifications
- {len(all_security)} consignes sécurité
- {len(all_calibration)} calibrations

EXEMPLES:
Procédures: {json.dumps(all_procedures[:3], ensure_ascii=False) if all_procedures else "Aucune"}

JSON de synthèse finale:

{{
    "informations_generales": {{
        "nom_instrument": "nom consolidé",
        "fabricant": "fabricant",
        "modele": "modèle",
        "type_instrument": "type",
        "applications_principales": ["application clinique 1", "application 2"]
    }},
    "procedures_analyses": [
        {{
            "nom_analyse": "analyse consolidée",
            "type_echantillon": "échantillon",
            "preparation_echantillon": ["préparation 1", "préparation 2"],
            "procedure_detaillee": ["étape 1", "étape 2", "étape 3"],
            "materiels_reactifs": ["matériel 1", "matériel 2"],
            "duree_totale": "durée",
            "precautions_critiques": ["précaution critique"],
            "controles_qualite": ["contrôle qualité"],
            "interpretation_resultats": "interprétation"
        }}
    ],
    "maintenance_preventive": [
        {{
            "type_maintenance": "maintenance consolidée",
            "frequence_recommandee": "fréquence",
            "procedure_complete": ["étape 1", "étape 2"],
            "materiels_necessaires": ["matériel"],
            "points_verification": ["vérification"]
        }}
    ],
    "specifications_techniques": [
        {{
            "categorie": "catégorie technique",
            "parametres": [
                {{
                    "nom": "paramètre",
                    "valeur": "valeur",
                    "unite": "unité"
                }}
            ]
        }}
    ],
    "calibration_qualite": [
        {{
            "type_calibration": "calibration",
            "frequence": "fréquence",
            "procedure": ["étape calibration"],
            "standards_requis": ["standards"]
        }}
    ],
    "guide_rapide": {{
        "demarrage_quotidien": ["démarrage 1", "démarrage 2"],
        "arret_quotidien": ["arrêt 1", "arrêt 2"],
        "troubleshooting": ["problème courant et solution"]
    }},
    "resume_executif": "résumé en 3-4 phrases de l'instrument"
}}

Consolide intelligemment, élimine doublons.
"""
        
        try:
            response = self.gemini_model.generate_content(synthesis_prompt)
            cleaned_json = self.extract_clean_json(response.text.strip())
            result = json.loads(cleaned_json)
            
            logger.info("Synthèse finale créée avec succès")
            return result
            
        except Exception as e:
            logger.error(f"Erreur synthèse finale: {e}")
            return {
                "error": f"Erreur synthèse: {str(e)}",
                "donnees_brutes": {
                    "procedures_count": len(all_procedures),
                    "maintenance_count": len(all_maintenance),
                    "specs_count": len(all_specs),
                    "instrument": instrument_info
                }
            }
    
    def analyze_manual_organized(self, pdf_path: Path) -> Dict:
        """Analyse complète avec organisation des fichiers"""
        logger.info(f"ANALYSE ORGANISÉE: {pdf_path.name}")
        
        try:
            # 1. Préparation
            prepared_pdf = self.prepare_pdf(pdf_path)
            
            # 2. Découpage 15 pages
            pdf_chunks = self.split_pdf_15pages(prepared_pdf)
            logger.info(f"{len(pdf_chunks)} chunks de 15 pages créés")
            
            # 3. Extraction sécurisée
            chunk_texts = []
            
            for i, chunk_pdf in enumerate(pdf_chunks):
                logger.info(f"Extraction chunk {i+1}/{len(pdf_chunks)}")
                
                result = self.extract_text_safe(chunk_pdf)
                chunk_texts.append(result)
                
                # Délai entre extractions
                if i < len(pdf_chunks) - 1:
                    time.sleep(self.config["analysis"]["delay_between_requests"])
            
            # 4. Fusion structurée
            full_text = self.merge_and_structure_texts(chunk_texts)
            
            if not full_text.strip():
                return {"error": "Aucun texte extrait de l'ensemble du document"}
            
            # 5. Chunks Gemini
            analysis_chunks = self.create_gemini_chunks(full_text)
            
            if not analysis_chunks:
                return {"error": "Impossible de créer des chunks d'analyse"}
            
            # 6. Analyse Gemini
            chunk_analyses = []
            context = ""
            
            for i, chunk in enumerate(analysis_chunks):
                logger.info(f"Analyse Gemini {i+1}/{len(analysis_chunks)}")
                
                analysis = self.analyze_with_gemini_15p(chunk, context)
                chunk_analyses.append(analysis)
                
                # Contexte pour chunk suivant
                context += f"{chunk['description']}: {analysis.get('resume', '')}\n"
                
                # Délai entre analyses
                if i < len(analysis_chunks) - 1:
                    time.sleep(self.config["analysis"]["delay_between_requests"])
            
            # 7. Synthèse finale
            logger.info("Synthèse finale...")
            synthesis = self.synthesize_final_15p(chunk_analyses)
            
            # 8. Fichiers de sortie ORGANISÉS
            output_base = self.syntheses_dir / pdf_path.stem
            
            # PDF de synthèse dans le dossier synthèses
            if self.pdf_available and "error" not in synthesis:
                pdf_output = Path(str(output_base) + "_SYNTHESE.pdf")
                success = self.pdf_generator.generate_pdf_synthesis(
                    synthesis, pdf_output, f"SYNTHÈSE - {pdf_path.stem}"
                )
                if success:
                    logger.info(f"PDF synthèse généré: {pdf_output}")
            
            # JSON détaillé dans le dossier synthèses
            json_output = Path(str(output_base) + "_ANALYSE_COMPLETE.json")
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": {
                        "fichier_source": str(pdf_path),
                        "limite_pages": self.max_pages_per_request,
                        "chunks_pdf": len(pdf_chunks),
                        "chunks_analyse": len(analysis_chunks),
                        "caracteres_total": len(full_text),
                        "date_analyse": datetime.now().isoformat(),
                        "version": "Organized v1.0"
                    },
                    "extraction_chunks": [
                        {
                            "chunk": i+1,
                            "caracteres": result.get("char_count", 0),
                            "pages": result.get("pages", 0),
                            "statut": "succès" if "error" not in result else "échec",
                            "erreur": result.get("error")
                        }
                        for i, result in enumerate(chunk_texts)
                    ],
                    "analyses_detaillees": chunk_analyses,
                    "synthese_finale": synthesis,
                    "statistiques": {
                        "extractions_reussies": len([r for r in chunk_texts if "error" not in r]),
                        "procedures_totales": sum(len(a.get("procedures", [])) for a in chunk_analyses),
                        "maintenances_totales": sum(len(a.get("maintenance", [])) for a in chunk_analyses),
                        "specifications_totales": sum(len(a.get("specifications", [])) for a in chunk_analyses),
                        "calibrations_totales": sum(len(a.get("calibration", [])) for a in chunk_analyses)
                    }
                }, f, indent=2, ensure_ascii=False)
            
            #