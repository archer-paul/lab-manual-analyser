#!/usr/bin/env python3
"""
Générateur de PDF pour les synthèses Lab Manual Analyzer
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

# Import pour génération PDF
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFSynthesisGenerator:
    """Générateur de synthèses PDF"""
    
    def __init__(self):
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab non installé. Installez avec: pip install reportlab")
        
        # Styles
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Crée des styles personnalisés"""
        # Titre principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=20,
            textColor=colors.darkblue,
            alignment=TA_CENTER
        ))
        
        # Titre de section
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkred,
            borderWidth=1,
            borderColor=colors.darkred,
            borderPadding=5
        ))
        
        # Sous-titre
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        ))
        
        # Texte normal avec justification
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['Normal'],
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
        
        # Liste
        self.styles.add(ParagraphStyle(
            name='ListItem',
            parent=self.styles['Normal'],
            leftIndent=20,
            spaceAfter=4
        ))
        
        # Étapes numérotées
        self.styles.add(ParagraphStyle(
            name='StepItem',
            parent=self.styles['Normal'],
            leftIndent=20,
            spaceAfter=6,
            borderWidth=0.5,
            borderColor=colors.lightgrey,
            borderPadding=3
        ))
    
    def generate_pdf_synthesis(self, synthesis: Dict, output_path: Path, manual_name: str = "Manuel"):
        """
        Génère un PDF de synthèse
        
        Args:
            synthesis: Données de synthèse
            output_path: Chemin de sortie du PDF
            manual_name: Nom du manuel
        """
        try:
            # Créer le document PDF
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch
            )
            
            # Contenu du document
            story = []
            
            # Page de titre
            self.add_title_page(story, manual_name)
            
            # Table des matières
            story.append(PageBreak())
            self.add_table_of_contents(story, synthesis)
            
            # Contenu principal
            story.append(PageBreak())
            self.add_main_content(story, synthesis)
            
            # Construire le PDF
            doc.build(story)
            
            logger.info(f"PDF généré avec succès: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération PDF: {e}")
            return False
    
    def add_title_page(self, story, manual_name: str):
        """Ajoute la page de titre"""
        # Logo ou titre principal
        title = Paragraph("FICHE DE SYNTHÈSE", self.styles['MainTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Nom du manuel
        manual_title = Paragraph(f"<b>{manual_name}</b>", self.styles['Title'])
        story.append(manual_title)
        story.append(Spacer(1, 0.3*inch))
        
        # Sous-titre
        subtitle = Paragraph("Manuel d'Instrument de Laboratoire", self.styles['Heading2'])
        story.append(subtitle)
        story.append(Spacer(1, 1*inch))
        
        # Informations de génération
        info_data = [
            ["Date de génération:", datetime.now().strftime('%d/%m/%Y à %H:%M')],
            ["Générateur:", "Lab Manual Analyzer"],
            ["Format:", "Synthèse automatique"]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        story.append(info_table)
    
    def add_table_of_contents(self, story, synthesis: Dict):
        """Ajoute la table des matières"""
        story.append(Paragraph("TABLE DES MATIÈRES", self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        toc_items = [
            "1. Résumé Exécutif",
            "2. Informations Générales", 
            "3. Procédures d'Analyse",
            "4. Maintenance Préventive",
            "5. Spécifications Techniques",
            "6. Guide Rapide"
        ]
        
        for item in toc_items:
            story.append(Paragraph(item, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    
    def add_main_content(self, story, synthesis: Dict):
        """Ajoute le contenu principal"""
        
        # 1. Résumé exécutif
        if "resume_executif" in synthesis:
            story.append(Paragraph("1. RÉSUMÉ EXÉCUTIF", self.styles['SectionTitle']))
            story.append(Paragraph(synthesis["resume_executif"], self.styles['BodyJustified']))
            story.append(Spacer(1, 0.3*inch))
        
        # 2. Informations générales
        if "informations_generales" in synthesis:
            story.append(Paragraph("2. INFORMATIONS GÉNÉRALES", self.styles['SectionTitle']))
            info = synthesis["informations_generales"]
            
            info_data = [
                ["Instrument:", info.get('nom_instrument', 'Non identifié')],
                ["Fabricant:", info.get('fabricant', 'Non identifié')],
                ["Type:", info.get('type_instrument', 'Non identifié')],
                ["Applications:", ', '.join(info.get('applications_principales', ['Non spécifiées']))]
            ]
            
            info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 0.3*inch))
        
        # 3. Procédures d'analyse
        if "procedures_analyses" in synthesis and synthesis["procedures_analyses"]:
            story.append(Paragraph("3. PROCÉDURES D'ANALYSE", self.styles['SectionTitle']))
            
            for i, proc in enumerate(synthesis["procedures_analyses"], 1):
                # Titre de la procédure
                proc_title = f"3.{i} {proc.get('nom_analyse', 'Analyse non nommée')}"
                story.append(Paragraph(proc_title, self.styles['SubTitle']))
                
                # Informations de base
                story.append(Paragraph(f"<b>Type d'échantillon:</b> {proc.get('type_echantillon', 'Non spécifié')}", self.styles['Normal']))
                story.append(Paragraph(f"<b>Durée totale:</b> {proc.get('duree_totale', 'Non spécifiée')}", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                # Préparation de l'échantillon
                if proc.get('preparation_echantillon'):
                    story.append(Paragraph("<b>Préparation de l'échantillon:</b>", self.styles['Normal']))
                    for step in proc['preparation_echantillon']:
                        story.append(Paragraph(f"• {step}", self.styles['ListItem']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Procédure détaillée
                if proc.get('procedure_detaillee'):
                    story.append(Paragraph("<b>Procédure détaillée:</b>", self.styles['Normal']))
                    for j, step in enumerate(proc['procedure_detaillee'], 1):
                        story.append(Paragraph(f"{j}. {step}", self.styles['StepItem']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Matériels et réactifs
                if proc.get('materiels_reactifs'):
                    story.append(Paragraph("<b>Matériels et réactifs:</b>", self.styles['Normal']))
                    for item in proc['materiels_reactifs']:
                        story.append(Paragraph(f"• {item}", self.styles['ListItem']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Précautions
                if proc.get('precautions_critiques'):
                    story.append(Paragraph("<b>⚠️ Précautions critiques:</b>", self.styles['Normal']))
                    for precaution in proc['precautions_critiques']:
                        story.append(Paragraph(f"⚠️ {precaution}", self.styles['ListItem']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Interprétation
                if proc.get('interpretation_resultats'):
                    story.append(Paragraph(f"<b>Interprétation des résultats:</b> {proc['interpretation_resultats']}", self.styles['BodyJustified']))
                
                story.append(Spacer(1, 0.2*inch))
        
        # 4. Maintenance préventive
        if "maintenance_preventive" in synthesis and synthesis["maintenance_preventive"]:
            story.append(Paragraph("4. MAINTENANCE PRÉVENTIVE", self.styles['SectionTitle']))
            
            for i, maint in enumerate(synthesis["maintenance_preventive"], 1):
                maint_title = f"4.{i} {maint.get('type_maintenance', 'Maintenance non nommée')}"
                story.append(Paragraph(maint_title, self.styles['SubTitle']))
                
                story.append(Paragraph(f"<b>Fréquence:</b> {maint.get('frequence_recommandee', 'Non spécifiée')}", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                if maint.get('procedure_complete'):
                    story.append(Paragraph("<b>Procédure:</b>", self.styles['Normal']))
                    for j, step in enumerate(maint['procedure_complete'], 1):
                        story.append(Paragraph(f"{j}. {step}", self.styles['StepItem']))
                    story.append(Spacer(1, 0.1*inch))
                
                if maint.get('materiels_necessaires'):
                    story.append(Paragraph("<b>Matériels nécessaires:</b>", self.styles['Normal']))
                    for item in maint['materiels_necessaires']:
                        story.append(Paragraph(f"• {item}", self.styles['ListItem']))
                
                story.append(Spacer(1, 0.2*inch))
        
        # 5. Spécifications techniques
        if "specifications_techniques" in synthesis and synthesis["specifications_techniques"]:
            story.append(Paragraph("5. SPÉCIFICATIONS TECHNIQUES", self.styles['SectionTitle']))
            
            for spec_cat in synthesis["specifications_techniques"]:
                story.append(Paragraph(spec_cat.get('categorie', 'Catégorie non nommée'), self.styles['SubTitle']))
                
                if spec_cat.get('parametres'):
                    # Créer un tableau pour les spécifications
                    spec_data = [["Paramètre", "Valeur", "Unité"]]
                    for param in spec_cat['parametres']:
                        spec_data.append([
                            param.get('nom', 'Paramètre'),
                            param.get('valeur', 'Non spécifiée'),
                            param.get('unite', '')
                        ])
                    
                    spec_table = Table(spec_data, colWidths=[2*inch, 2*inch, 1*inch])
                    spec_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(spec_table)
                    story.append(Spacer(1, 0.2*inch))
        
        # 6. Guide rapide
        if "guide_rapide" in synthesis:
            story.append(Paragraph("6. GUIDE RAPIDE", self.styles['SectionTitle']))
            guide = synthesis["guide_rapide"]
            
            if guide.get('demarrage_quotidien'):
                story.append(Paragraph("6.1 Démarrage quotidien", self.styles['SubTitle']))
                for step in guide['demarrage_quotidien']:
                    story.append(Paragraph(f"• {step}", self.styles['ListItem']))
                story.append(Spacer(1, 0.1*inch))
            
            if guide.get('arret_quotidien'):
                story.append(Paragraph("6.2 Arrêt quotidien", self.styles['SubTitle']))
                for step in guide['arret_quotidien']:
                    story.append(Paragraph(f"• {step}", self.styles['ListItem']))
                story.append(Spacer(1, 0.1*inch))
            
            if guide.get('troubleshooting'):
                story.append(Paragraph("6.3 Dépannage courant", self.styles['SubTitle']))
                for issue in guide['troubleshooting']:
                    story.append(Paragraph(f"• {issue}", self.styles['ListItem']))

def main():
    """Test du générateur PDF"""
    # Exemple de synthèse pour test
    test_synthesis = {
        "informations_generales": {
            "nom_instrument": "Cytomètre BD FACSCalibur",
            "fabricant": "BD Biosciences",
            "type_instrument": "Cytomètre en flux",
            "applications_principales": ["Analyse cellulaire", "Immunophénotypage", "Comptage cellulaire"]
        },
        "resume_executif": "Le BD FACSCalibur est un cytomètre en flux polyvalent conçu pour l'analyse et le tri de cellules individuelles. Il permet l'immunophénotypage, le comptage cellulaire et l'analyse de la viabilité cellulaire avec une précision élevée.",
        "procedures_analyses": [
            {
                "nom_analyse": "Immunophénotypage lymphocytaire",
                "type_echantillon": "Sang total",
                "duree_totale": "45 minutes",
                "preparation_echantillon": [
                    "Prélever 5ml de sang sur tube EDTA",
                    "Maintenir à température ambiante"
                ],
                "procedure_detaillee": [
                    "Allumer l'instrument et vérifier l'alignement",
                    "Préparer les tubes de marquage avec les anticorps",
                    "Ajouter 100µl de sang dans chaque tube",
                    "Incuber 15 minutes à l'obscurité",
                    "Lyser les globules rouges avec FACS Lyse",
                    "Centrifuger et laver",
                    "Acquérir au cytomètre"
                ],
                "materiels_reactifs": [
                    "Anticorps monoclonaux fluorescents",
                    "FACS Lyse",
                    "PBS",
                    "Tubes 5ml"
                ],
                "precautions_critiques": [
                    "Maintenir la chaîne du froid",
                    "Protéger de la lumière",
                    "Vérifier l'expiration des réactifs"
                ],
                "interpretation_resultats": "Analyser les populations par gating séquentiel sur FSC/SSC puis marquages spécifiques"
            }
        ]
    }
    
    generator = PDFSynthesisGenerator()
    output_path = Path("test_synthesis.pdf")
    
    success = generator.generate_pdf_synthesis(test_synthesis, output_path, "Test Manuel")
    
    if success:
        print(f"✅ PDF de test généré: {output_path}")
    else:
        print("❌ Erreur lors de la génération du PDF")

if __name__ == "__main__":
    main()
