#!/usr/bin/env python3
"""
Déchiffreur de PDFs pour ManualMiner
Version sans emojis pour usage professionnel
"""

import os
from pathlib import Path
import logging

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

def decrypt_pdf(input_path: Path, output_path: Path, password: str = "") -> bool:
    """
    Déchiffre un PDF protégé par mot de passe et répare les PDFs corrompus
    
    Args:
        input_path: PDF chiffré/corrompu
        output_path: PDF déchiffré/réparé
        password: Mot de passe (essaie vide si non fourni)
        
    Returns:
        True si succès
    """
    if not PDF_AVAILABLE:
        logger.error("PyPDF2 non installé. Installez avec: pip install PyPDF2")
        return False
    
    try:
        # Essayer d'abord avec strict=False pour gérer les PDFs mal formés
        with open(input_path, 'rb') as file:
            try:
                # Tentative avec strict=False pour les PDFs mal formés
                pdf_reader = PyPDF2.PdfReader(file, strict=False)
            except Exception as e:
                logger.warning(f"Erreur lecture PDF avec strict=False: {e}")
                # Essayer avec strict=True
                file.seek(0)
                pdf_reader = PyPDF2.PdfReader(file, strict=True)
            
            if not pdf_reader.is_encrypted:
                logger.info("PDF non chiffré - copie simple")
                # Simple copie
                file.seek(0)  # Retour au début du fichier
                with open(output_path, 'wb') as output_file:
                    output_file.write(file.read())
                return True
            
            # Essayer de déchiffrer
            logger.info(f"PDF chiffré détecté...")
            
            # Essayer d'abord sans mot de passe (parfois ça marche)
            if pdf_reader.decrypt(""):
                logger.info("Déchiffré sans mot de passe")
            elif password and pdf_reader.decrypt(password):
                logger.info(f"Déchiffré avec le mot de passe fourni")
            else:
                # Essayer des mots de passe courants
                common_passwords = [
                    "", "password", "123456", "admin", "user", 
                    "pdf", "document", "default", "open"
                ]
                
                decrypted = False
                for pwd in common_passwords:
                    if pdf_reader.decrypt(pwd):
                        logger.info(f"Déchiffré avec mot de passe: '{pwd}'")
                        decrypted = True
                        break
                
                if not decrypted:
                    logger.error("Impossible de déchiffrer - mot de passe requis")
                    return False
            
            # Créer le PDF déchiffré avec gestion d'erreur robuste
            pdf_writer = PyPDF2.PdfWriter()
            
            total_pages = len(pdf_reader.pages)
            successful_pages = 0
            
            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)
                    successful_pages += 1
                except Exception as page_error:
                    logger.warning(f"Erreur page {page_num + 1}: {page_error}")
                    # Continuer avec les autres pages
                    continue
            
            if successful_pages == 0:
                logger.error("Aucune page n'a pu être traitée")
                return False
            
            # Sauvegarder le PDF traité
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            if successful_pages < total_pages:
                logger.warning(f"PDF partiellement traité: {successful_pages}/{total_pages} pages")
            else:
                logger.info(f"PDF traité avec succès: {successful_pages} pages")
            
            logger.info(f"PDF sauvegardé: {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement PDF: {e}")
        # Essayer une copie directe en cas d'échec total
        try:
            logger.info("Tentative de copie directe du fichier...")
            with open(input_path, 'rb') as src, open(output_path, 'wb') as dst:
                dst.write(src.read())
            logger.info("Copie directe réussie")
            return True
        except Exception as copy_error:
            logger.error(f"Échec copie directe: {copy_error}")
            return False

def batch_decrypt_pdfs(input_dir: str, output_dir: str = None):
    """
    Déchiffre tous les PDFs d'un dossier
    
    Args:
        input_dir: Dossier source
        output_dir: Dossier destination (optionnel)
    """
    input_path = Path(input_dir)
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    else:
        output_path = input_path / "decrypted"
        output_path.mkdir(exist_ok=True)
    
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("Aucun fichier PDF trouvé")
        return
    
    logger.info(f"Trouvé {len(pdf_files)} fichiers PDF")
    
    success_count = 0
    
    for pdf_file in pdf_files:
        logger.info(f"Traitement de: {pdf_file.name}")
        
        output_file = output_path / f"decrypted_{pdf_file.name}"
        
        if decrypt_pdf(pdf_file, output_file):
            success_count += 1
        else:
            logger.warning(f"Échec pour: {pdf_file.name}")
    
    logger.info(f"Déchiffrement terminé: {success_count}/{len(pdf_files)} réussis")
    logger.info(f"Fichiers déchiffrés dans: {output_path}")

def main():
    """Interface en ligne de commande"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Déchiffreur de PDFs ManualMiner")
    parser.add_argument("input", help="Fichier PDF ou dossier à traiter")
    parser.add_argument("--output", help="Fichier ou dossier de sortie")
    parser.add_argument("--password", help="Mot de passe du PDF")
    parser.add_argument("--batch", action="store_true", help="Traiter tous les PDFs du dossier")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Fichier/dossier non trouvé: {args.input}")
        return
    
    if args.batch or input_path.is_dir():
        # Mode batch
        batch_decrypt_pdfs(str(input_path), args.output)
    else:
        # Fichier unique
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.parent / f"decrypted_{input_path.name}"
        
        success = decrypt_pdf(input_path, output_path, args.password or "")
        
        if success:
            print(f"Succès! Fichier déchiffré: {output_path}")
        else:
            print("Échec du déchiffrement")

if __name__ == "__main__":
    main()
