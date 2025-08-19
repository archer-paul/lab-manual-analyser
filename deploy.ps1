# deploy.ps1 - Script de déploiement ManualMiner pour Windows PowerShell

param(
    [string]$ServiceName = "manual-miner",
    [string]$Region = "europe-west1"
)

$PROJECT_ID = "research-funding-analyser"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$ServiceName"
$BUCKET_NAME = "$PROJECT_ID-manualminer"

Write-Host ""
Write-Host "DÉPLOIEMENT MANUALMINER SUR GOOGLE CLOUD RUN" -ForegroundColor Cyan
Write-Host "=" * 50
Write-Host ""

# Vérifications préalables
Write-Host "Vérification de l'environnement..." -ForegroundColor Yellow

# Vérifier gcloud
try {
    $gcloudVersion = gcloud version --format="value(Google Cloud SDK)"
    Write-Host "Google Cloud SDK détecté: $gcloudVersion" -ForegroundColor Green
} catch {
    Write-Host "Google Cloud SDK non trouvé. Installez-le depuis:" -ForegroundColor Red
    Write-Host "   https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Vérifier le projet
$currentProject = gcloud config get-value project
if ($currentProject -ne $PROJECT_ID) {
    Write-Host "Configuration du projet: $PROJECT_ID" -ForegroundColor Yellow
    gcloud config set project $PROJECT_ID
}

# Vérifier les fichiers requis
$requiredFiles = @(
    "app.py",
    "Dockerfile", 
    "requirements.txt",
    "config.json",
    "credentials/service-account.json",
    "lab_manual_analyzer_organized.py",
    "latex_generator.py",
    "pdf_decryptor.py"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "Fichier manquant: $file" -ForegroundColor Red
        exit 1
    }
}
Write-Host "Tous les fichiers requis sont présents" -ForegroundColor Green

# Activer les APIs nécessaires
Write-Host ""
Write-Host "Activation des APIs Google Cloud..." -ForegroundColor Yellow
$apis = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Activation de $api..." -ForegroundColor Gray
    gcloud services enable $api --quiet
}
Write-Host "✅ APIs activées" -ForegroundColor Green

# Créer le bucket s'il n'existe pas
Write-Host ""
Write-Host "Vérification du bucket de stockage..." -ForegroundColor Yellow
try {
    gsutil ls -b "gs://$BUCKET_NAME" | Out-Null
    Write-Host "Bucket existant: gs://$BUCKET_NAME" -ForegroundColor Green
} catch {
    Write-Host "Création du bucket: gs://$BUCKET_NAME" -ForegroundColor Yellow
    gsutil mb -l $Region.Split('-')[0] "gs://$BUCKET_NAME"
    Write-Host "Bucket créé" -ForegroundColor Green
}

# Build de l'image Docker
Write-Host ""
Write-Host "Construction de l'image Docker ManualMiner..." -ForegroundColor Yellow
Write-Host "Cela peut prendre plusieurs minutes..." -ForegroundColor Gray

try {
    gcloud builds submit --tag $IMAGE_NAME --quiet
    Write-Host "Image Docker construite avec succès" -ForegroundColor Green
} catch {
    Write-Host "Erreur lors de la construction de l'image" -ForegroundColor Red
    Write-Host "Vérifiez les logs de Cloud Build dans la console GCP" -ForegroundColor Yellow
    exit 1
}

# Déploiement sur Cloud Run
Write-Host ""
Write-Host "Déploiement du service ManualMiner sur Cloud Run..." -ForegroundColor Yellow

try {
    gcloud run deploy $ServiceName `
        --image $IMAGE_NAME `
        --platform managed `
        --region $Region `
        --allow-unauthenticated `
        --memory 2Gi `
        --cpu 2 `
        --timeout 900s `
        --concurrency 10 `
        --max-instances 10 `
        --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,STORAGE_BUCKET=$BUCKET_NAME" `
        --service-account "lab-analyzer@$PROJECT_ID.iam.gserviceaccount.com" `
        --quiet

    Write-Host "Service déployé avec succès" -ForegroundColor Green
} catch {
    Write-Host "Erreur lors du déploiement" -ForegroundColor Red
    exit 1
}

# Récupérer l'URL du service
Write-Host ""
Write-Host "Récupération de l'URL du service..." -ForegroundColor Yellow
$SERVICE_URL = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"

# Test de santé
Write-Host "Test du service..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-RestMethod -Uri "$SERVICE_URL/health" -Method Get -TimeoutSec 30
    Write-Host "Service opérationnel" -ForegroundColor Green
} catch {
    Write-Host "Service déployé mais health check échoué" -ForegroundColor Yellow
    Write-Host "   Le service peut prendre quelques secondes à démarrer" -ForegroundColor Gray
}

# Affichage des résultats
Write-Host ""
Write-Host "DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host ""
Write-Host "INFORMATIONS DU SERVICE:" -ForegroundColor Cyan
Write-Host "   Nom du service: $ServiceName" -ForegroundColor White
Write-Host "   Région: $Region" -ForegroundColor White
Write-Host "   URL: $SERVICE_URL" -ForegroundColor Yellow -BackgroundColor Black
Write-Host "   Bucket: gs://$BUCKET_NAME" -ForegroundColor White
Write-Host ""
Write-Host "ENDPOINTS DISPONIBLES:" -ForegroundColor Cyan
Write-Host "   Health Check: $SERVICE_URL/health" -ForegroundColor White
Write-Host "   Analyse PDF:  $SERVICE_URL/analyze" -ForegroundColor White
Write-Host "   Téléchargement: $SERVICE_URL/download/<id>" -ForegroundColor White
Write-Host ""
Write-Host "COMMANDES DE TEST:" -ForegroundColor Cyan
Write-Host "   curl $SERVICE_URL/health" -ForegroundColor Gray
Write-Host ""
Write-Host "ÉTAPES SUIVANTES:" -ForegroundColor Yellow
Write-Host "   1. Copiez l'URL du service: $SERVICE_URL" -ForegroundColor White
Write-Host "   2. Mettez à jour votre frontend React avec cette URL" -ForegroundColor White
Write-Host "   3. Testez l'upload d'un PDF via l'interface" -ForegroundColor White
Write-Host ""

# Sauvegarder l'URL dans un fichier pour référence
$SERVICE_URL | Out-File -FilePath "service-url.txt" -Encoding UTF8
Write-Host "URL sauvegardée dans: service-url.txt" -ForegroundColor Gray
Write-Host ""