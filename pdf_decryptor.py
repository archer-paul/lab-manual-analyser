#!/usr/bin/env python3
"""
Déchiffreur de PDFs pour Lab Manual Analyzer
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
    Déchiffre un PDF protégé par mot de passe
    
    Args:
        input_path: PDF chiffré
        output_path: PDF déchiffré
        password: Mot de passe (essaie vide si non fourni)
        
    Returns:
        True si succès
    """
    if not PDF_AVAILABLE:
        print("❌ PyPDF2 non installé. Installez avec: pip install PyPDF2")
        return False
    
    try:
        with open(input_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            if not pdf_reader.is_encrypted:
                print("✅ PDF non chiffré - copie simple")
                # Simple copie
                with open(output_path, 'wb') as output_file:
                    output_file.write(file.read())
                return True
            
            # Essayer de déchiffrer
            print(f"🔐 PDF chiffré détecté...")
            
            # Essayer d'abord sans mot de passe (parfois ça marche)
            if pdf_reader.decrypt(""):
                print("✅ Déchiffré sans mot de passe")
            elif password and pdf_reader.decrypt(password):
                print(f"✅ Déchiffré avec le mot de passe fourni")
            else:
                # Essayer des mots de passe courants
                common_passwords = [
                    "", "password", "123456", "admin", "user", 
                    "pdf", "document", "default", "open"
                ]
                
                decrypted = False
                for pwd in common_passwords:
                    if pdf_reader.decrypt(pwd):
                        print(f"✅ Déchiffré avec mot de passe: '{pwd}'")
                        decrypted = True
                        break
                
                if not decrypted:
                    print("❌ Impossible de déchiffrer - mot de passe requis")
                    return False
            
            # Créer le PDF déchiffré
            pdf_writer = PyPDF2.PdfWriter()
            
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            print(f"✅ PDF déchiffré sauvegardé: {output_path}")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du déchiffrement: {e}")
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
        print("❌ Aucun fichier PDF trouvé")
        return
    
    print(f"🔍 Trouvé {len(pdf_files)} fichiers PDF")
    
    success_count = 0
    
    for pdf_file in pdf_files:
        print(f"\n📄 Traitement de: {pdf_file.name}")
        
        output_file = output_path / f"decrypted_{pdf_file.name}"
        
        if decrypt_pdf(pdf_file, output_file):
            success_count += 1
        else:
            print(f"⚠️  Échec pour: {pdf_file.name}")
    
    print(f"\n✅ Déchiffrement terminé: {success_count}/{len(pdf_files)} réussis")
    print(f"📁 Fichiers déchiffrés dans: {output_path}")

def main():
    """Interface en ligne de commande"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Déchiffreur de PDFs")
    parser.add_argument("input", help="Fichier PDF ou dossier à traiter")
    parser.add_argument("--output", help="Fichier ou dossier de sortie")
    parser.add_argument("--password", help="Mot de passe du PDF")
    parser.add_argument("--batch", action="store_true", help="Traiter tous les PDFs du dossier")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"❌ Fichier/dossier non trouvé: {args.input}")
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
            print(f"✅ Succès! Fichier déchiffré: {output_path}")
        else:
            print("❌ Échec du déchiffrement")

if __name__ == "__main__":
    main()
