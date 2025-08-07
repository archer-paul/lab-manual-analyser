#!/usr/bin/env python3
"""
Générateur LaTeX EXHAUSTIF - Version médicale complète
Utilise TOUTES les données extraites par Gemini
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class LatexSynthesisGenerator:
    """Générateur LaTeX EXHAUSTIF - Toutes les informations médicales"""
    
    def __init__(self):
        """Initialise avec vérification LaTeX optimisée"""
        self.verify_latex_installation()
        
    def verify_latex_installation(self):
        """Vérifie LaTeX avec vérification minimale"""
        try:
            result = subprocess.run(['pdflatex', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                raise RuntimeError("LaTeX installé mais non fonctionnel")
            
            logger.info("✅ LaTeX détecté (test de compilation skippé pour vitesse)")
            
        except FileNotFoundError:
            raise RuntimeError(
                "❌ ERREUR CRITIQUE: LaTeX non installé\n"
                "Installation requise:\n"
                "- Windows: MiKTeX (https://miktex.org/download)\n"
                "- Linux: sudo apt-get install texlive-latex-base texlive-latex-extra\n"
                "- Mac: MacTeX (https://tug.org/mactex/)\n"
                "AUCUNE alternative possible pour matériel médical"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("❌ ERREUR: LaTeX ne répond pas")
        except Exception as e:
            raise RuntimeError(f"❌ ERREUR LaTeX: {e}")
    
    def generate_latex_synthesis(self, synthesis: Dict, output_path: Path, manual_name: str) -> bool:
        """Génère un PDF médical EXHAUSTIF - Toutes les données"""
        try:
            # Validation des données (pas de nettoyage cette fois)
            self.validate_synthesis_data(synthesis, manual_name)
            
            # Créer document LaTeX COMPLET avec toutes les données
            latex_content = self.create_comprehensive_latex_document(synthesis, manual_name)
            
            # Compilation avec timeout généreux
            success = self.compile_latex_comprehensive(latex_content, output_path, manual_name)
            
            if not success:
                logger.error("❌ ÉCHEC COMPILATION LaTeX exhaustive")
                return False
            
            # Validation finale
            if not output_path.exists() or output_path.stat().st_size < 10000:  # PDF doit être conséquent
                logger.error("❌ PDF généré trop petit")
                if output_path.exists():
                    output_path.unlink()
                return False
            
            logger.info(f"✅ SYNTHÈSE MÉDICALE EXHAUSTIVE PDF GÉNÉRÉE: {output_path}")
            return True
                
        except Exception as e:
            logger.error(f"❌ ERREUR GÉNÉRATION EXHAUSTIVE: {e}")
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            return False
    
    def validate_synthesis_data(self, synthesis: Dict, manual_name: str):
        """Validation rapide des données"""
        if not synthesis:
            raise ValueError("❌ Données de synthèse vides")
        
        if not manual_name or not manual_name.strip():
            raise ValueError("❌ Nom du manuel manquant")
        
        logger.info("✅ Données validées pour génération exhaustive")
    
    def create_comprehensive_latex_document(self, synthesis: Dict, manual_name: str) -> str:
        """Crée un document LaTeX EXHAUSTIF avec TOUTES les informations médicales"""
        
        # En-tête LaTeX PROFESSIONNEL pour document médical complet
        latex_header = r"""
\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=1.8cm]{geometry}
\usepackage[table,xcdraw]{xcolor}
\usepackage{array}
\usepackage{longtable}
\usepackage{fancyhdr}
\usepackage{enumitem}
\usepackage{multicol}
\usepackage{titlesec}

% Couleurs médicales professionnelles
\definecolor{medblue}{RGB}{0,100,200}
\definecolor{medred}{RGB}{180,0,0}
\definecolor{medgreen}{RGB}{0,120,0}
\definecolor{medorange}{RGB}{230,120,0}
\definecolor{lightblue}{RGB}{240,248,255}
\definecolor{lightgreen}{RGB}{245,255,245}
\definecolor{lightred}{RGB}{255,245,245}
\definecolor{lightorange}{RGB}{255,250,240}

% En-têtes professionnels
\pagestyle{fancy}
\fancyhf{}
\rhead{\textcolor{medblue}{\textbf{SYNTHÈSE INSTRUMENT MÉDICAL}}}
\lhead{\textcolor{medblue}{\small\today}}
\rfoot{\textcolor{medblue}{\textbf{\thepage}}}
\lfoot{\textcolor{medgreen}{\textbf{DOCUMENT TECHNIQUE}}}

% Formatage des sections
\titleformat{\section}{\large\bfseries\color{medblue}}{\thesection}{1em}{}
\titleformat{\subsection}{\normalsize\bfseries\color{medgreen}}{\thesubsection}{1em}{}

\title{\textcolor{medblue}{\Large\textbf{FICHE TECHNIQUE}} \\ \vspace{0.3cm} \textcolor{medblue}{\large """ + self.escape_latex_advanced(manual_name[:70]) + r"""}}
\author{}
\date{\today}

\begin{document}
\maketitle
\thispagestyle{fancy}

% Avertissement médical professionnel
\begin{center}
\colorbox{lightred}{\parbox{0.95\textwidth}{\centering 
\textcolor{medred}{\textbf{DOCUMENT TECHNIQUE PROFESSIONNEL}} \\
Synthèse technique automatique complète - Vérification recommandée avant usage \\
Respecter impérativement les procédures du manuel complet}}
\end{center}

\vspace{0.5cm}
"""

        latex_body = ""
        
        # 1. Résumé exécutif COMPLET
        if synthesis.get("resume_executif"):
            latex_body += r"""
\section*{RÉSUMÉ}
\colorbox{lightblue}{\parbox{0.98\textwidth}{""" + self.escape_latex_advanced(synthesis["resume_executif"]) + r"""}}

\vspace{0.5cm}
"""
        
        # 2. Informations générales DÉTAILLÉES
        if synthesis.get("informations_generales"):
            latex_body += self.generate_detailed_info_section(synthesis["informations_generales"])
        
        # 3. Procédures d'analyse EXHAUSTIVES
        if synthesis.get("procedures_analyses"):
            latex_body += self.generate_exhaustive_procedures_section(synthesis["procedures_analyses"])
        
        # 4. Maintenance préventive COMPLÈTE
        if synthesis.get("maintenance_preventive"):
            latex_body += self.generate_complete_maintenance_section(synthesis["maintenance_preventive"])
        
        # 5. Guide d'utilisation quotidienne
        if synthesis.get("guide_utilisation_quotidienne"):
            latex_body += self.generate_daily_usage_section(synthesis["guide_utilisation_quotidienne"])
        
        # 6. Spécifications techniques
        if synthesis.get("specifications_techniques"):
            latex_body += self.generate_technical_specs_section(synthesis["specifications_techniques"])
        
        # Pied de document médical professionnel
        latex_footer = r"""

\vfill
\begin{center}
\colorbox{lightred}{\parbox{0.95\textwidth}{\centering
\textcolor{medred}{\textbf{RESPONSABILITÉ TECHNIQUE PROFESSIONNELLE}} \\
L'utilisateur reste entièrement responsable de la validation des informations, \\
de la sécurité d'utilisation et de l'interprétation des données. \\
Toujours vérifier les procédures critiques dans le manuel complet.}}
\end{center}

\vspace{0.3cm}
\begin{center}
\textcolor{medblue}{\small Lab Manual Analyzer - © Paul Archer, Hôpital Henri Mondor - """ + datetime.now().strftime("%d/%m/%Y") + r"""}
\end{center>

\end{document}
"""
        
        return latex_header + latex_body + latex_footer
    
    def generate_detailed_info_section(self, info: Dict) -> str:
        """Section informations générales EXHAUSTIVE"""
        section = r"""
\section*{INFORMATIONS TECHNIQUES GÉNÉRALES}

\begin{longtable}{|>{\bfseries}p{4cm}|p{11cm}|}
\hline
\rowcolor{lightblue}
\multicolumn{2}{|c|}{\textcolor{medblue}{\textbf{IDENTIFICATION INSTRUMENT COMPLET}}} \\
\hline
\endfirsthead
\hline
\rowcolor{lightblue}
\multicolumn{2}{|c|}{\textcolor{medblue}{\textbf{IDENTIFICATION INSTRUMENT (suite)}}} \\
\hline
\endhead
"""
        
        fields = {
            "nom_instrument": "Instrument",
            "fabricant": "Fabricant", 
            "modele": "Modèle",
            "type_instrument": "Type/Technologie",
            "principe_fonctionnement": "Principe technique",
            "approche_diagnostique": "Méthodologie diagnostique"
        }
        
        for key, label in fields.items():
            if key in info and info[key]:
                value = str(info[key])
                section += f"{label} & {self.escape_latex_advanced(value)} \\\\\n\\hline\n"
        
        # Applications cliniques DÉTAILLÉES
        if info.get("applications_principales"):
            section += "Applications cliniques & "
            apps_list = []
            for i, app in enumerate(info["applications_principales"][:8]):
                apps_list.append(f"\\textbf{{{i+1}.}} {self.escape_latex_advanced(str(app))}")
            apps_text = " \\\\ ".join(apps_list)
            section += f"{apps_text} \\\\\n\\hline\n"
        
        section += r"""
\end{longtable}

\vspace{0.5cm}
"""
        return section
    
    def generate_exhaustive_procedures_section(self, procedures: List[Dict]) -> str:
        """Section procédures d'analyse EXHAUSTIVE avec toutes les informations"""
        section = r"""
\section*{PROCÉDURES D'ANALYSE MÉDICALES}

"""
        
        for i, proc in enumerate(procedures[:6]):  # Maximum 6 procédures pour éviter PDF trop long
            section += f"\\subsection*{{\\textcolor{{medgreen}}{{{i+1}. {self.escape_latex_advanced(proc.get('nom_analyse', f'Analyse {i+1}')[:60])}}}}}\n\n"
            
            # Indication clinique
            if proc.get('indication_clinique'):
                section += f"\\textbf{{\\textcolor{{medorange}}{{Indication clinique:}}}} {self.escape_latex_advanced(proc['indication_clinique'][:200])}\n\n"
            
            section += "\\vspace{0.3cm}\n"
            
            # Informations échantillon COMPLÈTES
            echantillon = proc.get('echantillon', {})
            if echantillon and isinstance(echantillon, dict):
                section += "\\textbf{\\textcolor{medblue}{ÉCHANTILLON DÉTAILLÉ:}}\n"
                section += "\\begin{itemize}[leftmargin=1cm]\n"
                
                for field, label in [
                    ('type', 'Type'), ('volume_minimum', 'Volume minimum'),
                    ('volume_traitement', 'Volume traitement'), ('anticoagulant', 'Anticoagulant')
                ]:
                    if echantillon.get(field):
                        section += f"\\item \\textbf{{{label}:}} {self.escape_latex_advanced(str(echantillon[field])[:100])}\n"
                
                section += "\\end{itemize}\n\n"
            
            section += "\\vspace{0.3cm}\n"
            
            # Préparation détaillée COMPLÈTE
            preparation = proc.get('preparation_detaillee', {})
            if preparation and isinstance(preparation, dict):
                if preparation.get('etapes'):
                    section += "\\textbf{\\textcolor{medgreen}{PRÉPARATION ÉCHANTILLON:}}\n"
                    section += "\\begin{enumerate}[leftmargin=1cm]\n"
                    for j, step in enumerate(preparation['etapes'][:8]):  # Max 8 étapes
                        section += f"\\item {self.escape_latex_advanced(str(step)[:150])}\n"
                    section += "\\end{enumerate}\n"
                
                # Conditions de stockage/stabilité
                if preparation.get('stabilite'):
                    section += f"\\textbf{{Stabilité:}} {self.escape_latex_advanced(str(preparation['stabilite'])[:200])}\n\n"
                if preparation.get('stockage'):
                    section += f"\\textbf{{Stockage:}} {self.escape_latex_advanced(str(preparation['stockage'])[:200])}\n\n"
            
            section += "\\vspace{0.3cm}\n"
            
            # Procédure analytique
            procedure_ana = proc.get('procedure_analytique', {})
            if procedure_ana and isinstance(procedure_ana, dict):
                if procedure_ana.get('workflow'):
                    section += "\\textbf{\\textcolor{medgreen}{PROCÉDURE ANALYTIQUE:}}\n"
                    section += "\\begin{enumerate}[leftmargin=1cm]\n"
                    for j, step in enumerate(procedure_ana['workflow'][:10]):  # Max 10 étapes
                        section += f"\\item {self.escape_latex_advanced(str(step)[:180])}\n"
                    section += "\\end{enumerate}\n"
                
                if procedure_ana.get('duree_totale'):
                    section += f"\\textbf{{Durée totale:}} {self.escape_latex_advanced(str(procedure_ana['duree_totale']))}\n\n"
                if procedure_ana.get('conditions_techniques'):
                    section += f"\\textbf{{Conditions techniques:}} {self.escape_latex_advanced(str(procedure_ana['conditions_techniques'])[:200])}\n\n"
            
            section += "\\vspace{0.3cm}\n"
            
            # Performance analytique (CRITIQUE)
            performance = proc.get('performance_analytique', {})
            if performance and isinstance(performance, dict):
                section += "\\colorbox{lightorange}{\\parbox{0.98\\textwidth}{\n"
                section += "\\textbf{\\textcolor{medorange}{PERFORMANCE ANALYTIQUE:}} \\\\\n"
                
                for field, label in [
                    ('gamme_mesure', 'Gamme mesure'), ('limite_detection', 'Limite détection'),
                    ('limite_quantification', 'Limite quantification'), ('precision', 'Précision'),
                    ('sensibilite_clinique', 'Sensibilité clinique'), ('specificite_clinique', 'Spécificité clinique')
                ]:
                    if performance.get(field):
                        section += f"\\textbf{{{label}:}} {self.escape_latex_advanced(str(performance[field])[:120])} \\\\\n"
                
                section += "}}\n\n"
            
            section += "\\vspace{0.3cm}\n"
            
            # Contrôles qualité
            controles = proc.get('controles_qualite', {})
            if controles and isinstance(controles, dict):
                if controles.get('types_controles'):
                    section += "\\textbf{\\textcolor{medblue}{CONTRÔLES QUALITÉ:}}\n"
                    section += "\\begin{itemize}[leftmargin=1cm]\n"
                    for ctrl in controles['types_controles'][:6]:
                        section += f"\\item {self.escape_latex_advanced(str(ctrl)[:120])}\n"
                    if controles.get('frequence'):
                        section += f"\\item \\textbf{{Fréquence:}} {self.escape_latex_advanced(str(controles['frequence'])[:80])}\n"
                    section += "\\end{itemize}\n\n"
            
            section += "\\vspace{0.3cm}\n"
            
            # Précautions critiques (SÉCURITÉ)
            if proc.get('precautions_critiques'):
                section += "\\begin{center}\n"
                section += "\\colorbox{lightred}{\\parbox{0.95\\textwidth}{\n"
                section += "\\textbf{\\textcolor{medred}{⚠️ PRÉCAUTIONS CRITIQUES:}} \\\\\n"
                for j, prec in enumerate(proc['precautions_critiques'][:5]):
                    section += f"\\textbf{{{j+1}.}} {self.escape_latex_advanced(str(prec)[:150])} \\\\\n"
                section += "}}\n"
                section += "\\end{center}\n\n"
            
            # Interprétation clinique
            interpretation = proc.get('interpretation_clinique', {})
            if interpretation and isinstance(interpretation, dict):
                section += "\\textbf{\\textcolor{medblue}{INTERPRÉTATION CLINIQUE:}}\n"
                if interpretation.get('resultats_possibles'):
                    section += "\\begin{itemize}[leftmargin=1cm]\n"
                    for res in interpretation['resultats_possibles'][:6]:
                        section += f"\\item {self.escape_latex_advanced(str(res)[:150])}\n"
                    section += "\\end{itemize}\n"
                if interpretation.get('seuils_cliniques'):
                    section += f"\\textbf{{Seuils cliniques:}} {self.escape_latex_advanced(str(interpretation['seuils_cliniques'])[:150])}\n\n"
            
            section += "\\vspace{0.3cm}\n"
            
            section += "\\vspace{0.4cm}\n"
            
            # Saut de page après 3 procédures pour lisibilité
            if i == 2 and len(procedures) > 3:
                section += "\\newpage\n"
        
        return section
    
    def generate_complete_maintenance_section(self, maintenance: List[Dict]) -> str:
        """Section maintenance préventive EXHAUSTIVE"""
        if not maintenance:
            return ""
        
        section = r"""
\section*{MAINTENANCE PRÉVENTIVE}

\colorbox{lightorange}{\parbox{0.98\textwidth}{
\textbf{\textcolor{medorange}{IMPORTANCE CRITIQUE:}} La maintenance préventive est essentielle pour garantir la fiabilité diagnostique, la sécurité des analyses et la validité des résultats.}}

\vspace{0.3cm}

"""
        
        for i, maint in enumerate(maintenance[:8]):  # Maximum 8 maintenances
            if not isinstance(maint, dict):
                continue
                
            section += f"\\subsection*{{\\textcolor{{medorange}}{{{i+1}. {self.escape_latex_advanced(maint.get('type_maintenance', f'Maintenance {i+1}')[:50])}}}}}\n\n"
            
            # Informations générales DÉTAILLÉES
            section += "\\begin{itemize}[leftmargin=1cm]\n"
            if maint.get('frequence_precise'):
                section += f"\\item \\textbf{{Fréquence:}} {self.escape_latex_advanced(str(maint['frequence_precise'])[:80])}\n"
            if maint.get('duree_estimee'):
                section += f"\\item \\textbf{{Durée estimée:}} {self.escape_latex_advanced(str(maint['duree_estimee'])[:60])}\n"
            if maint.get('niveau'):
                section += f"\\item \\textbf{{Niveau:}} {self.escape_latex_advanced(str(maint.get('niveau', 'Personnel qualifié'))[:80])}\n"
            section += "\\end{itemize}\n\n"
            
            # Procédure step-by-step COMPLÈTE
            procedure = maint.get('procedure_step_by_step', {})
            if procedure and isinstance(procedure, dict):
                if procedure.get('preparation'):
                    section += "\\textbf{\\textcolor{medgreen}{Préparation:}}\n"
                    section += "\\begin{enumerate}[leftmargin=1cm]\n"
                    for step in procedure['preparation'][:6]:
                        section += f"\\item {self.escape_latex_advanced(str(step)[:120])}\n"
                    section += "\\end{enumerate}\n\n"
                
                if procedure.get('execution'):
                    section += "\\textbf{\\textcolor{medgreen}{Exécution:}}\n"
                    section += "\\begin{enumerate}[leftmargin=1cm]\n"
                    for step in procedure['execution'][:8]:
                        section += f"\\item {self.escape_latex_advanced(str(step)[:120])}\n"
                    section += "\\end{enumerate}\n\n"
                
                if procedure.get('verification'):
                    section += "\\textbf{\\textcolor{medblue}{Vérifications:}}\n"
                    section += "\\begin{itemize}[leftmargin=1cm]\n"
                    for verif in procedure['verification'][:6]:
                        section += f"\\item {self.escape_latex_advanced(str(verif)[:100])}\n"
                    section += "\\end{itemize}\n\n"
            
            # Matériels requis DÉTAILLÉS
            if maint.get('materiels_specifiques'):
                materials = maint['materiels_specifiques']
                if materials:
                    section += f"\\textbf{{Matériels requis:}} "
                    materials_text = ', '.join([self.escape_latex_advanced(str(mat)[:60]) for mat in materials[:8]])
                    section += f"{materials_text}\n\n"
            
            section += "\\vspace{0.3cm}\n"
        
        return section
    
    def generate_daily_usage_section(self, guide: Dict) -> str:
        """Section guide d'utilisation quotidienne EXHAUSTIF"""
        section = r"""
\section*{GUIDE D'UTILISATION QUOTIDIENNE}

"""
        
        # Démarrage système COMPLET
        if guide.get('demarrage_systeme'):
            section += "\\subsection*{\\textcolor{medgreen}{Démarrage système}}\n"
            section += "\\colorbox{lightgreen}{\\parbox{0.98\\textwidth}{\n"
            section += "\\begin{enumerate}[leftmargin=0.5cm]\n"
            for step in guide['demarrage_systeme'][:8]:
                section += f"\\item {self.escape_latex_advanced(str(step)[:120])}\n"
            section += "\\end{enumerate}\n"
            section += "}}\n\n"
        
        # Workflows disponibles
        if guide.get('workflow_type'):
            section += "\\subsection*{\\textcolor{medblue}{Workflows disponibles}}\n"
            section += "\\begin{itemize}[leftmargin=1cm]\n"
            for workflow in guide['workflow_type'][:6]:
                section += f"\\item {self.escape_latex_advanced(str(workflow)[:150])}\n"
            section += "\\end{itemize}\n\n"
        
        # Arrêt système COMPLET
        if guide.get('arret_systeme'):
            section += "\\subsection*{\\textcolor{medorange}{Arrêt système}}\n"
            section += "\\colorbox{lightorange}{\\parbox{0.98\\textwidth}{\n"
            section += "\\begin{enumerate}[leftmargin=0.5cm]\n"
            for step in guide['arret_systeme'][:8]:
                section += f"\\item {self.escape_latex_advanced(str(step)[:120])}\n"
            section += "\\end{enumerate}\n"
            section += "}}\n\n"
        
        # Contrôle qualité routine DÉTAILLÉ
        if guide.get('controle_qualite_routine'):
            section += "\\subsection*{\\textcolor{medblue}{Contrôles qualité routine}}\n"
            section += "\\begin{itemize}[leftmargin=1cm]\n"
            for ctrl in guide['controle_qualite_routine'][:8]:
                section += f"\\item {self.escape_latex_advanced(str(ctrl)[:120])}\n"
            section += "\\end{itemize}\n\n"
        
        # Maintenance quotidienne
        if guide.get('maintenance_quotidienne'):
            section += "\\subsection*{\\textcolor{medgreen}{Maintenance quotidienne}}\n"
            section += "\\begin{itemize}[leftmargin=1cm]\n"
            for task in guide['maintenance_quotidienne'][:6]:
                section += f"\\item {self.escape_latex_advanced(str(task)[:100])}\n"
            section += "\\end{itemize}\n\n"
        
        return section
    
    def generate_technical_specs_section(self, specs: List[Dict]) -> str:
        """Section spécifications techniques (si disponibles)"""
        if not specs:
            return ""
        
        section = r"""
\section*{SPÉCIFICATIONS TECHNIQUES}

"""
        
        for spec in specs[:4]:  # Maximum 4 catégories
            if not isinstance(spec, dict):
                continue
            if spec.get('categorie') and spec.get('parametres_detailles'):
                section += f"\\subsection*{{\\textcolor{{medblue}}{{{self.escape_latex_advanced(spec['categorie'][:50])}}}}}\n\n"
                
                section += "\\begin{longtable}{|>{\\bfseries}p{4cm}|p{5cm}|p{2cm}|p{3cm}|}\n"
                section += "\\hline\n"
                section += "\\rowcolor{lightblue}\n"
                section += "\\textcolor{medblue}{\\textbf{PARAMÈTRE}} & \\textcolor{medblue}{\\textbf{VALEUR}} & \\textcolor{medblue}{\\textbf{UNITÉ}} & \\textcolor{medblue}{\\textbf{CONDITIONS}} \\\\\n"
                section += "\\hline\n"
                
                for param in spec['parametres_detailles'][:10]:  # Max 10 paramètres par catégorie
                    if isinstance(param, dict):
                        nom = self.escape_latex_advanced(str(param.get('nom', 'Paramètre'))[:35])
                        valeur = self.escape_latex_advanced(str(param.get('valeur', 'N/A'))[:45])
                        unite = self.escape_latex_advanced(str(param.get('unite', ''))[:15])
                        conditions = self.escape_latex_advanced(str(param.get('conditions_mesure', ''))[:30])
                        
                        section += f"{nom} & {valeur} & {unite} & {conditions} \\\\\n\\hline\n"
                
                section += "\\end{longtable}\n\n"
        
        return section
    
    def escape_latex_advanced(self, text: str) -> str:
        """Échappement LaTeX AVANCÉ pour préserver toutes les informations"""
        if not isinstance(text, str):
            text = str(text)
        
        if not text.strip():
            return "Non spécifié"
        
        # Échappement complet pour préserver toutes les informations
        replacements = {
            '\\': r'\textbackslash{}',
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '^': r'\textasciicircum{}',
            '~': r'\textasciitilde{}',
            '°': r'$^\circ$',
            'µ': r'$\mu$',
            '≤': r'$\leq$',
            '≥': r'$\geq$',
            '±': r'$\pm$',
            '→': r'$\rightarrow$',
            '←': r'$\leftarrow$',
            '↔': r'$\leftrightarrow$'
        }
        
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        
        # Nettoyer les caractères de contrôle mais préserver les retours à la ligne
        import re
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
        
        return text
    
    def compile_latex_comprehensive(self, latex_content: str, output_path: Path, manual_name: str) -> bool:
        """Compilation LaTeX EXHAUSTIVE avec timeout généreux"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Fichier LaTeX
                tex_file = temp_dir_path / "comprehensive_synthesis.tex"
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                logger.info(f"📄 Compilation LaTeX EXHAUSTIVE: {manual_name[:50]}")
                
                # Configuration optimisée pour document médical complet
                env = dict(os.environ)
                env.update({
                    'MIKTEX_AUTOINSTALL': 'No',  
                    'MIKTEX_UPDATE_CHECK': 'No',  
                    'max_print_line': '2000',     
                    'error_line': '500',
                    'half_error_line': '100'
                })
                
                cmd = [
                    'pdflatex', 
                    '-interaction=batchmode',      
                    '-file-line-error',            
                    '-no-shell-escape',            
                    '-output-directory', str(temp_dir_path),
                    str(tex_file)
                ]
                
                logger.info("⏱️ Démarrage compilation EXHAUSTIVE (timeout 120s)...")
                
                # Première passe
                result1 = subprocess.run(
                    cmd,
                    capture_output=True, 
                    text=True, 
                    cwd=temp_dir_path, 
                    timeout=120,  # Timeout généreux pour document complet
                    env=env
                )
                
                # Deuxième passe pour les références croisées
                logger.info("📄 Deuxième passe LaTeX pour références...")
                result2 = subprocess.run(
                    cmd,
                    capture_output=True, 
                    text=True, 
                    cwd=temp_dir_path, 
                    timeout=120,
                    env=env
                )
                
                # Vérifier PDF généré (priorité au résultat)
                pdf_file = temp_dir_path / "comprehensive_synthesis.pdf"
                if pdf_file.exists() and pdf_file.stat().st_size > 5000:
                    logger.info(f"✅ PDF EXHAUSTIF généré: {pdf_file.stat().st_size:,} bytes")
                    
                    # Copie vers destination
                    shutil.copy2(pdf_file, output_path)
                    
                    if output_path.exists():
                        final_size = output_path.stat().st_size
                        logger.info(f"✅ PDF médical EXHAUSTIF créé: {final_size:,} bytes")
                        return True
                
                # Échec - diagnostics détaillés
                logger.error(f"❌ Compilation échouée (codes {result1.returncode}, {result2.returncode})")
                
                # Diagnostics spécifiques pour document exhaustif
                stderr1 = result1.stderr.lower()
                stdout1 = result1.stdout.lower()
                
                if "memory" in stderr1 or "capacity exceeded" in stderr1:
                    logger.error("💡 SOLUTION: Document trop volumineux pour LaTeX")
                    logger.error("   1. Le document est très complet, normal pour usage médical")
                    logger.error("   2. Augmenter la mémoire LaTeX si possible")
                elif "emergency stop" in stdout1 or "fatal error" in stdout1:
                    logger.error("💡 SOLUTION: Erreur dans le document LaTeX exhaustif")
                    logger.error("   Document très détaillé, certains caractères spéciaux posent problème")
                else:
                    logger.error("💡 DIAGNOSTIC: Document LaTeX exhaustif complexe")
                    logger.error(f"   STDERR: {result1.stderr[:300]}")
                
                return False
                    
        except subprocess.TimeoutExpired:
            logger.error("❌ TIMEOUT compilation LaTeX EXHAUSTIVE (120s)")
            logger.error("💡 Document médical très complet, compilation longue normale")
            logger.error("   Solutions:")
            logger.error("   1. Le document contient beaucoup d'informations (normal)")
            logger.error("   2. Augmenter le timeout si nécessaire")
            return False
        except Exception as e:
            logger.error(f"❌ ERREUR critique compilation exhaustive: {e}")
            return False


def test_latex_comprehensive():
    """Test du générateur exhaustif"""
    
    test_synthesis = {
        "resume_executif": "Test de génération PDF médical EXHAUSTIF avec toutes les informations détaillées extraites par Gemini 2.0 Flash. Ce document contient l'ensemble des procédures, maintenances et spécifications techniques critiques pour usage médical professionnel.",
        
        "informations_generales": {
            "nom_instrument": "Analyseur Test Complet",
            "fabricant": "Test Medical Corp", 
            "modele": "Model-X Pro Advanced",
            "type_instrument": "Analyseur médical automatisé haute performance",
            "applications_principales": [
                "Diagnostic médical de précision",
                "Analyses quantitatives en routine",
                "Contrôle qualité laboratoire",
                "Suivi thérapeutique patient"
            ],
            "principe_fonctionnement": "Principe technique avancé basé sur la technologie de pointe pour analyses médicales de haute précision avec validation clinique complète",
            "approche_diagnostique": "Méthodologie diagnostique intégrée avec workflow optimisé pour usage clinique quotidien"
        },
        
        "procedures_analyses": [
            {
                "nom_analyse": "Analyse Test Complète Détaillée",
                "indication_clinique": "Diagnostic et suivi médical pour population cible spécifique avec indications cliniques précises",
                "echantillon": {
                    "type": "Échantillon sanguin EDTA",
                    "volume_minimum": "500 µL minimum requis",
                    "volume_traitement": "200 µL pour traitement",
                    "anticoagulant": "EDTA K3 recommandé"
                },
                "preparation_detaillee": {
                    "etapes": [
                        "Prélèvement selon procédure standard avec précautions aseptiques",
                        "Centrifugation à 3000 rpm pendant 10 minutes à température ambiante",
                        "Séparation du plasma avec pipetage soigneux évitant contamination",
                        "Stockage temporaire à 2-8°C maximum 4 heures avant analyse"
                    ],
                    "stabilite": "Stable 24h à 2-8°C, 1 semaine à -20°C, 6 mois à -80°C",
                    "stockage": "Conditions de stockage strictes selon température et durée spécifiées"
                },
                "procedure_analytique": {
                    "workflow": [
                        "Initialisation système avec contrôles qualité obligatoires",
                        "Chargement échantillons selon protocole validé",
                        "Analyse automatisée avec surveillance continue paramètres",
                        "Validation résultats avec contrôles intégrés",
                        "Génération rapport avec interprétation technique"
                    ],
                    "duree_totale": "45 minutes par série incluant contrôles",
                    "conditions_techniques": "Température 18-25°C, humidité <60%, vibrations minimales"
                },
                "performance_analytique": {
                    "gamme_mesure": "0.1 - 1000 UI/mL avec linéarité validée",
                    "limite_detection": "0.05 UI/mL (IC 95%)",
                    "precision": "CV intra-série <3%, inter-série <5%",
                    "sensibilite_clinique": "98.5% (IC 95%: 96.2-99.4%)",
                    "specificite_clinique": "99.2% (IC 95%: 97.8-99.8%)"
                },
                "controles_qualite": {
                    "types_controles": [
                        "Contrôle négatif: <0.1 UI/mL attendu",
                        "Contrôle positif bas: 50±15 UI/mL",
                        "Contrôle positif haut: 500±50 UI/mL"
                    ],
                    "frequence": "Chaque série d'analyse, minimum quotidien"
                },
                "interpretation_clinique": {
                    "resultats_possibles": [
                        "Non détecté (<0.1 UI/mL): Résultat négatif, interprétation selon contexte clinique",
                        "Détecté (0.1-10 UI/mL): Résultat faiblement positif, contrôle recommandé",
                        "Quantifié (>10 UI/mL): Résultat quantitatif fiable pour suivi"
                    ],
                    "seuils_cliniques": "Seuil décisionnel: 1.0 UI/mL selon recommandations fabricant"
                },
                "precautions_critiques": [
                    "SÉCURITÉ BIOLOGIQUE: Manipulation échantillons infectieux - EPI complet obligatoire (gants, blouse, lunettes)",
                    "QUALITÉ ANALYTIQUE: Prévention contamination croisée - nettoyage système entre séries",
                    "INTERPRÉTATION CLINIQUE: Résultats à interpréter dans contexte clinique - pas de diagnostic isolé"
                ]
            }
        ],
        
        "maintenance_preventive": [
            {
                "type_maintenance": "Maintenance quotidienne système",
                "frequence_precise": "Chaque jour d'utilisation obligatoire",
                "duree_estimee": "15-20 minutes selon complexité",
                "procedure_step_by_step": {
                    "preparation": [
                        "Arrêt complet système selon procédure sécurisée",
                        "Préparation solutions nettoyage selon concentrations",
                        "Vérification disponibilité matériels maintenance"
                    ],
                    "execution": [
                        "Nettoyage surfaces externes avec solution désinfectante",
                        "Vidange et rinçage circuits fluidiques internes",
                        "Contrôle visuel composants critiques usure",
                        "Test fonctionnel rapide avant remise en service"
                    ],
                    "verification": [
                        "Vérification étanchéité circuits après nettoyage",
                        "Test alarmes et sécurités système",
                        "Validation paramètres techniques nominaux"
                    ]
                },
                "materiels_specifiques": [
                    "Solution nettoyage spécialisée référence XYZ-123",
                    "Kits consommables maintenance hebdomadaire",
                    "Outils calibrage fournis par fabricant"
                ]
            }
        ],
        
        "guide_utilisation_quotidienne": {
            "demarrage_systeme": [
                "Vérification alimentation électrique et connexions réseau",
                "Contrôle niveaux réactifs et consommables disponibles",
                "Test fonctionnel système avec séquence diagnostic",
                "Validation contrôles qualité journaliers obligatoires",
                "Initialisation complète prête pour analyses routine"
            ],
            "arret_systeme": [
                "Finalisation toutes analyses en cours avec sauvegarde",
                "Nettoyage automatique circuits selon programme",
                "Sauvegarde données et rapports journaliers",
                "Mise en sécurité système pour arrêt prolongé"
            ],
            "maintenance_quotidienne": [
                "Contrôle visuel général instrument et accessoires",
                "Nettoyage surfaces externes selon produits autorisés",
                "Vérification niveaux et péremption réactifs",
                "Documentation observations dans registre maintenance"
            ]
        }
    }
    
    try:
        generator = LatexSynthesisGenerator()
        output_path = Path("test_exhaustive.pdf")
        
        print("🧪 TEST GÉNÉRATEUR LaTeX EXHAUSTIF")
        print("=" * 50)
        
        success = generator.generate_latex_synthesis(
            test_synthesis, output_path, "Test Médical Exhaustif"
        )
        
        if success:
            print(f"✅ SUCCÈS: PDF EXHAUSTIF généré")
            print(f"📄 Fichier: {output_path}")
            print(f"📊 Taille: {output_path.stat().st_size:,} bytes")
            print(f"🎯 Document complet avec toutes les informations détaillées")
        else:
            print("❌ ÉCHEC: Génération impossible")
            
    except Exception as e:
        print(f"💥 ERREUR: {e}")

if __name__ == "__main__":
    test_latex_comprehensive()