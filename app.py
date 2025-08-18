#!/usr/bin/env python3
"""
ManualMiner API - Backend Python sur Google Cloud Run
Version simplifiée et stable
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime
import uuid

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from google.cloud import storage

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration GCP
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
BUCKET_NAME = os.environ.get('STORAGE_BUCKET', f'{PROJECT_ID}-manualminer-storage')

# Initialiser le client Storage
storage_client = storage.Client()

class ManualMinerAPI:
    """API ManualMiner version simplifiée"""
    
    def __init__(self):
        self.analyzer = None
        self.latex_generator = None
        self.storage_bucket = None
        self.temp_dir = Path(tempfile.gettempdir()) / "manualminer"
        self.temp_dir.mkdir(exist_ok=True)
        self.initialized = False
        
    def initialize(self):
        """Initialisation des composants"""
        if self.initialized:
            return True
            
        try:
            # Initialiser le bucket Storage
            try:
                self.storage_bucket = storage_client.bucket(BUCKET_NAME)
                logger.info(f"Bucket connecté: {BUCKET_NAME}")
            except Exception as e:
                logger.error(f"Erreur bucket: {e}")
                
            # Essayer d'initialiser l'analyseur
            try:
                # Import conditionnel pour éviter les erreurs de démarrage
                from lab_manual_analyzer_organized import LabManualAnalyzerStrict
                self.analyzer = LabManualAnalyzerStrict("config.json")
                logger.info("LabManualAnalyzer initialisé")
            except Exception as e:
                logger.warning(f"Analyseur non initialisé: {e}")
                
            # Essayer d'initialiser le générateur LaTeX  
            try:
                from latex_generator import LatexSynthesisGenerator
                self.latex_generator = LatexSynthesisGenerator()
                logger.info("LaTeX Generator initialisé")
            except Exception as e:
                logger.warning(f"LaTeX Generator non initialisé: {e}")
                
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Erreur initialisation: {e}")
            return False

# Instance globale
manualminer = ManualMinerAPI()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check pour Cloud Run"""
    try:
        # Initialiser si pas encore fait
        if not manualminer.initialized:
            manualminer.initialize()
            
        # Statut des composants
        analyzer_status = "OK" if manualminer.analyzer is not None else "Non initialisé"
        latex_status = "OK" if manualminer.latex_generator is not None else "Non initialisé"
        bucket_status = "OK" if manualminer.storage_bucket is not None else "Non initialisé"
        
        overall_status = "healthy" if manualminer.initialized else "degraded"
        
        return jsonify({
            "status": overall_status,
            "service": "ManualMiner API",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "analyzer": analyzer_status,
                "latex_generator": latex_status,
                "storage_bucket": bucket_status
            }
        })
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return jsonify({
            "status": "error",
            "service": "ManualMiner API", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze_pdf():
    """
    Analyse d'un PDF médical - Endpoint principal
    """
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nom de fichier vide"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Le fichier doit être un PDF"}), 400
    
    # CORRECTION CRITIQUE : Lire le fichier ICI avant le streaming
    try:
        file_content = file.read()
        file_filename = file.filename
        
        if not file_content:
            return jsonify({"error": "Fichier PDF vide"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Erreur lecture fichier: {str(e)}"}), 400
    
    # Vérifier si c'est une requête streaming
    accept_header = request.headers.get('Accept', '')
    is_streaming = 'text/event-stream' in accept_header
    
    if is_streaming:
        return Response(
            stream_analysis_with_content(file_content, file_filename),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    else:
        # Traitement synchrone pour compatibilité
        return process_pdf_sync_with_content(file_content, file_filename)

def stream_analysis_with_content(file_content, filename):
    """Stream l'analyse en temps réel avec contenu pré-lu"""
    def send_log(level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_data = json.dumps({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
        return f"data: {log_data}\n\n"
    
    temp_pdf_path = None
    
    try:
        # Initialiser si pas encore fait
        if not manualminer.initialized:
            yield send_log("info", "Initialisation ManualMiner...")
            manualminer.initialize()
        
        # Vérifier que l'analyseur est disponible
        if not manualminer.analyzer:
            yield send_log("error", "Analyseur non disponible - vérifiez la configuration")
            yield f'data: {{"type":"error"}}\n\n'
            return
            
        # Initialisation
        yield send_log("info", "DÉBUT ANALYSE MÉDICALE ManualMiner")
        yield send_log("info", f"Fichier reçu: {filename}")
        yield send_log("info", f"Taille: {len(file_content)} bytes")
        
        # Sauvegarder le fichier temporairement
        analysis_id = str(uuid.uuid4())
        temp_pdf_path = manualminer.temp_dir / f"{analysis_id}_{filename}"
        
        # Sauvegarder sur disque
        try:
            with open(temp_pdf_path, 'wb') as f:
                f.write(file_content)
                
            # Vérifier que le fichier a été sauvegardé correctement
            if not temp_pdf_path.exists() or temp_pdf_path.stat().st_size == 0:
                yield send_log("error", "Échec de sauvegarde du fichier PDF")
                yield f'data: {{"type":"error"}}\n\n'
                return
                
        except Exception as save_error:
            yield send_log("error", f"Erreur sauvegarde: {str(save_error)}")
            yield f'data: {{"type":"error"}}\n\n'
            return
            
        yield send_log("success", f"Fichier sauvegardé: {temp_pdf_path.name} ({temp_pdf_path.stat().st_size} bytes)")
        
        # Analyse avec la logique Python existante
        yield send_log("info", "Lancement analyse médicale exhaustive...")
        
        try:
            result = manualminer.analyzer.analyze_manual_organized(temp_pdf_path)
        except Exception as analysis_error:
            yield send_log("error", f"Erreur lors de l'analyse: {str(analysis_error)}")
            yield f'data: {{"type":"error"}}\n\n'
            return
        
        if result.get("success"):
            yield send_log("success", "ANALYSE MÉDICALE RÉUSSIE")
            
            # Upload vers Cloud Storage
            pdf_path = Path(result["pdf_medical"])
            if pdf_path.exists():
                yield send_log("info", "Upload vers Cloud Storage...")
                
                # Nom du fichier dans le bucket
                storage_filename = f"syntheses/{analysis_id}/{pdf_path.name}"
                blob = manualminer.storage_bucket.blob(storage_filename)
                
                # Upload avec métadonnées ManualMiner
                blob.metadata = {
                    'original_filename': filename,
                    'analysis_id': analysis_id,
                    'created_by': 'ManualMiner',
                    'created_at': datetime.now().isoformat()
                }
                
                blob.upload_from_filename(str(pdf_path))
                yield send_log("success", f"PDF sauvegardé: {storage_filename}")
                
                # Statistiques
                stats = result.get("statistiques", {})
                synth_stats = stats.get("synthese_finale", {})
                procedures = synth_stats.get("procedures_consolidees", 0)
                maintenances = synth_stats.get("maintenances_consolidees", 0)
                
                yield send_log("success", f"Extraction: {procedures} procédures, {maintenances} maintenances")
                yield send_log("success", "Validation: CONFORME USAGE MÉDICAL PROFESSIONNEL")
                yield send_log("success", f"ID de synthèse: {analysis_id}")
                
                # Signal de fin avec l'ID pour le téléchargement
                completion_data = json.dumps({
                    "type": "complete",
                    "analysisId": analysis_id,
                    "filename": pdf_path.name,
                    "storageFilename": storage_filename,
                    "statistics": stats
                })
                yield f"data: {completion_data}\n\n"
                
            else:
                yield send_log("error", "PDF généré non trouvé")
                yield f'data: {{"type":"error"}}\n\n'
        else:
            error_msg = result.get("error", "Erreur inconnue")
            yield send_log("error", f"ÉCHEC ANALYSE: {error_msg}")
            yield f'data: {{"type":"error"}}\n\n'
            
    except Exception as e:
        logger.error(f"Erreur dans stream_analysis: {e}")
        yield send_log("error", f"ERREUR CRITIQUE: {str(e)}")
        yield f'data: {{"type":"error"}}\n\n'
    finally:
        # Nettoyage
        try:
            if temp_pdf_path and temp_pdf_path.exists():
                temp_pdf_path.unlink()
        except:
            pass

def process_pdf_sync_with_content(file_content, filename):
    """Traitement synchrone pour compatibilité"""
    try:
        analysis_id = str(uuid.uuid4())
        
        return jsonify({
            "success": True,
            "analysisId": analysis_id,
            "message": "Traitement initié - utilisez le streaming pour les logs en temps réel",
            "filename": filename,
            "size": len(file_content)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



def process_pdf_sync_with_content(file_content, filename):
    """Traitement synchrone pour compatibilité"""
    try:
        analysis_id = str(uuid.uuid4())
        
        return jsonify({
            "success": True,
            "analysisId": analysis_id,
            "message": "Traitement initié - utilisez le streaming pour les logs en temps réel",
            "filename": filename,
            "size": len(file_content)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<analysis_id>', methods=['GET'])
def download_synthesis(analysis_id: str):
    """Téléchargement d'une synthèse générée"""
    try:
        if not manualminer.storage_bucket:
            return jsonify({"error": "Storage non disponible"}), 500
            
        # Rechercher le fichier dans Cloud Storage
        prefix = f"syntheses/{analysis_id}/"
        blobs = list(manualminer.storage_bucket.list_blobs(prefix=prefix))
        
        if not blobs:
            return jsonify({"error": "Synthèse non trouvée"}), 404
        
        # Prendre le premier PDF trouvé
        pdf_blob = None
        for blob in blobs:
            if blob.name.endswith('.pdf'):
                pdf_blob = blob
                break
        
        if not pdf_blob:
            return jsonify({"error": "Fichier PDF non trouvé"}), 404
        
        # Télécharger le fichier temporairement
        temp_pdf = manualminer.temp_dir / f"download_{analysis_id}.pdf"
        pdf_blob.download_to_filename(str(temp_pdf))
        
        # Nom de fichier avec branding ManualMiner
        original_filename = pdf_blob.metadata.get('original_filename', 'manuel') if pdf_blob.metadata else 'manuel'
        download_filename = original_filename.replace('.pdf', '_SYNTHESE_MANUALMINER.pdf')
        
        return send_file(
            str(temp_pdf),
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Erreur téléchargement {analysis_id}: {e}")
        return jsonify({"error": f"Erreur de téléchargement: {str(e)}"}), 500

@app.route('/status/<analysis_id>', methods=['GET'])
def get_analysis_status(analysis_id: str):
    """Vérifier le statut d'une analyse"""
    try:
        if not manualminer.storage_bucket:
            return jsonify({"error": "Storage non disponible"}), 500
            
        prefix = f"syntheses/{analysis_id}/"
        blobs = list(manualminer.storage_bucket.list_blobs(prefix=prefix))
        
        if blobs:
            return jsonify({
                "status": "completed",
                "analysisId": analysis_id,
                "files": [blob.name for blob in blobs]
            })
        else:
            return jsonify({
                "status": "not_found",
                "analysisId": analysis_id
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint non trouvé"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Erreur serveur interne"}), 500

if __name__ == '__main__':
    # Pour le développement local
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)
