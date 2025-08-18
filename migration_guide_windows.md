# Guide de Migration ManualMiner - Windows PowerShell

## Configuration existante détectée ✅

Votre configuration est déjà bien préparée ! Voici ce que nous allons utiliser :

- **Projet GCP** : `research-funding-analyser`
- **Service Account** : `lab-analyzer@research-funding-analyser.iam.gserviceaccount.com`
- **Document AI** : Processeur `6710bec997a6b306` en région EU
- **Gemini** : Configuré avec votre clé API

## Étapes de migration (Windows PowerShell)

### 1. Vérification de l'environnement

```powershell
# Vérifier Google Cloud CLI
gcloud version

# Si non installé, télécharger depuis : https://cloud.google.com/sdk/docs/install
# Puis redémarrer PowerShell

# Se connecter et configurer le projet
gcloud auth login
gcloud config set project research-funding-analyser
```

### 2. Vérification des permissions existantes

```powershell
# Vérifier les rôles de votre service account
gcloud projects get-iam-policy research-funding-analyser --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:lab-analyzer@research-funding-analyser.iam.gserviceaccount.com"
```

Si des permissions manquent, ajoutez-les :

```powershell
# Storage Admin (pour Cloud Storage)
gcloud projects add-iam-policy-binding research-funding-analyser --member="serviceAccount:lab-analyzer@research-funding-analyser.iam.gserviceaccount.com" --role="roles/storage.admin"

# Logs Writer
gcloud projects add-iam-policy-binding research-funding-analyser --member="serviceAccount:lab-analyzer@research-funding-analyser.iam.gserviceaccount.com" --role="roles/logging.logWriter"
```

### 3. Activation des APIs nécessaires

```powershell
# Activer Cloud Run et Cloud Build
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 4. Préparation du projet ManualMiner

```powershell
# Créer le dossier du projet
mkdir manualminer-backend
cd manualminer-backend

# Créer la structure
mkdir credentials
mkdir temp
mkdir manuels\syntheses
```

### 5. Configuration adaptée à votre setup

Créez le fichier `config.json` adapté :

```json
{
  "application": {
    "name": "ManualMiner",
    "version": "1.0",
    "author": "Paul Archer"
  },
  "google_cloud": {
    "project_id": "research-funding-analyser",
    "location": "eu",
    "processor_id": "6710bec997a6b306",
    "credentials_path": "credentials/service-account.json"
  },
  "gemini": {
    "api_key": "VOTRE_CLE_GEMINI_ICI",
    "model": "gemini-1.5-pro",
    "advanced_model": "gemini-2.0-flash-exp"
  },
  "analysis": {
    "max_pages_per_chunk": 15,
    "delay_between_requests": 3,
    "max_tokens_per_request": 700000,
    "max_retries": 2
  },
  "storage": {
    "bucket_name": "research-funding-analyser-manualminer",
    "syntheses_folder": "syntheses"
  },
  "branding": {
    "application_name": "ManualMiner",
    "copyright": "© Paul Archer - ManualMiner"
  }
}
```

### 6. Copier vos fichiers existants

```powershell
# Copier votre service account (remplacez le chemin par le vôtre)
Copy-Item "C:\chemin\vers\votre\credentials\service-account.json" -Destination "credentials\service-account.json"

# Copier vos fichiers Python existants
Copy-Item "lab_manual_analyzer_organized.py" -Destination "."
Copy-Item "latex_generator.py" -Destination "."
Copy-Item "pdf_decryptor.py" -Destination "."
```

### 7. Créer le bucket de stockage

```powershell
# Créer le bucket
gsutil mb -l eu gs://research-funding-analyser-manualminer

# Vérifier la création
gsutil ls -b gs://research-funding-analyser-manualminer
```

### 8. Script de déploiement Windows

Créez `deploy.ps1` :

```powershell
# deploy.ps1 - Script de déploiement ManualMiner Windows

$PROJECT_ID = "research-funding-analyser"
$SERVICE_NAME = "manualminer-api"
$REGION = "europe-west1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$BUCKET_NAME = "$PROJECT_ID-manualminer"

Write-Host "Déploiement ManualMiner sur Cloud Run" -ForegroundColor Green
Write-Host "======================================"

# Configuration du projet
gcloud config set project $PROJECT_ID

# Build de l'image
Write-Host "Construction de l'image Docker..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME

# Déploiement
Write-Host "Déploiement sur Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 900s `
    --concurrency 10 `
    --max-instances 10 `
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
    --set-env-vars "STORAGE_BUCKET=$BUCKET_NAME"

# Récupérer l'URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

Write-Host ""
Write-Host "DÉPLOIEMENT TERMINÉ!" -ForegroundColor Green
Write-Host "URL du service: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Endpoints disponibles:"
Write-Host "- $SERVICE_URL/health"
Write-Host "- $SERVICE_URL/analyze"
Write-Host "- $SERVICE_URL/download/<id>"
```

### 9. Test local (optionnel)

```powershell
# Installer les dépendances Python
pip install -r requirements.txt

# Variables d'environnement
$env:GOOGLE_CLOUD_PROJECT = "research-funding-analyser"
$env:STORAGE_BUCKET = "research-funding-analyser-manualminer"

# Lancer l'app
python app.py

# Dans un autre terminal, tester
curl http://localhost:8080/health
```

### 10. Déploiement

```powershell
# Rendre le script exécutable et l'exécuter
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy.ps1
```

## URL courte sans nom de domaine

Vous avez plusieurs options pour obtenir une URL plus courte :

### Option 1 : URL personnalisée Cloud Run (RECOMMANDÉE)

Cloud Run vous donne déjà une URL assez courte :
```
https://manualminer-api-[hash]-ew.a.run.app
```

Vous pouvez la raccourcir en modifiant le nom du service :

```powershell
# Déployer avec un nom plus court
gcloud run deploy manual-miner `
    --image $IMAGE_NAME `
    --region europe-west1 `
    # ... autres options
```

Résultat : `https://manual-miner-[hash]-ew.a.run.app`

### Option 2 : Firebase Hosting (GRATUIT)

Firebase Hosting offre des URLs gratuites :

```powershell
# Installer Firebase CLI
npm install -g firebase-tools

# Initialiser Firebase
firebase login
firebase init hosting

# Configurer le proxy vers Cloud Run dans firebase.json
```

Résultat : `https://manual-miner-[project].web.app`

### Option 3 : Vercel (GRATUIT pour projets personnels)

```powershell
# Créer un simple proxy Next.js
npx create-next-app@latest manual-miner-proxy

# Configurer le proxy dans next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://your-cloud-run-url/:path*'
      }
    ]
  }
}

# Déployer sur Vercel
vercel --prod
```

Résultat : `https://manual-miner.vercel.app`

### Option 4 : Sous-domaine gratuit Netlify

Similar à Vercel mais avec Netlify.

### **Recommandation** 

Je recommande l'**Option 1** (URL Cloud Run raccourcie) car :
- ✅ Pas de configuration supplémentaire
- ✅ Latence minimale (pas de proxy)
- ✅ SSL automatique
- ✅ Totalement gratuit dans les limites GCP

Puis si vous voulez vraiment plus court, l'**Option 2** (Firebase Hosting) est parfaite.

## URLs finales possibles

1. **Cloud Run direct** : `https://manual-miner-abc123-ew.a.run.app`
2. **Firebase** : `https://manual-miner-research.web.app`
3. **Vercel** : `https://manual-miner.vercel.app`

Quelle option préférez-vous ? Je peux vous donner les détails de configuration pour celle qui vous intéresse.

## Checklist rapide

- [ ] Cloud CLI installé et configuré
- [ ] Permissions service account vérifiées  
- [ ] Bucket de stockage créé
- [ ] Fichiers copiés dans le projet
- [ ] `config.json` mis à jour avec votre clé Gemini
- [ ] Déployé avec `deploy.ps1`
- [ ] URL testée
- [ ] Frontend mis à jour avec la nouvelle URL

Votre configuration existante simplifie beaucoup les choses ! 🚀
