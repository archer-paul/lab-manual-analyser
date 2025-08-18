# Dockerfile pour ManualMiner sur Cloud Run
FROM python:3.11-slim

# Installer les dépendances système pour LaTeX et PDF
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-lang-french \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/manuels/syntheses /app/temp

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PORT=8080
ENV FLASK_APP=app.py

# Exposer le port
EXPOSE 8080

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "300", "app:app"]
