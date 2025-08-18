import { FileText, Download, X } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

interface PDFPreviewProps {
  isOpen: boolean
  onClose: () => void
  onDownload: () => void
  fileName?: string
}

export function PDFPreview({ isOpen, onClose, onDownload, fileName = "synthese_medicale.pdf" }: PDFPreviewProps) {
  // Simulation du contenu PDF
  const previewContent = [
    "SYNTHÈSE DU MANUEL D'UTILISATION",
    "",
    "Appareil: [Nom de l'appareil médical]",
    "Modèle: [Référence du modèle]",
    "Fabricant: [Nom du fabricant]",
    "",
    "RÉSUMÉ EXÉCUTIF",
    "Cette synthèse présente les informations essentielles pour l'utilisation sécurisée et efficace de l'appareil médical.",
    "",
    "INSTRUCTIONS PRINCIPALES",
    "1. Préparation avant utilisation",
    "   - Vérification de l'intégrité de l'appareil",
    "   - Contrôle des connexions électriques",
    "   - Test des fonctions de sécurité",
    "",
    "2. Procédures d'utilisation",
    "   - Mise en marche selon la séquence recommandée",
    "   - Réglages des paramètres selon le patient",
    "   - Surveillance continue pendant l'utilisation",
    "",
    "3. Maintenance et nettoyage",
    "   - Protocoles de désinfection",
    "   - Vérifications périodiques",
    "   - Calendrier de maintenance préventive",
    "",
    "ALERTES ET PRÉCAUTIONS",
    "⚠️ Points critiques de sécurité identifiés dans le manuel original",
    "⚠️ Contre-indications importantes",
    "⚠️ Procédures d'urgence en cas de dysfonctionnement",
    "",
    "Cette synthèse a été générée automatiquement à partir du manuel d'origine.",
    "Consultez toujours le manuel complet pour les détails techniques."
  ]

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] bg-background">
        <DialogHeader className="border-b pb-4">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-primary" />
              <span>Aperçu - {fileName}</span>
            </DialogTitle>
            <div className="flex space-x-2">
              <Button
                onClick={onDownload}
                className="bg-gradient-primary hover:opacity-90"
              >
                <Download className="w-4 h-4 mr-2" />
                Télécharger
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <Card className="h-full bg-card border">
            <div className="p-6 h-full overflow-y-auto">
              <div className="max-w-none">
                {previewContent.map((line, index) => (
                  <div key={index} className="mb-2">
                    {line === "" ? (
                      <div className="h-4" />
                    ) : line.startsWith("SYNTHÈSE") || line.startsWith("RÉSUMÉ") || line.startsWith("INSTRUCTIONS") || line.startsWith("ALERTES") ? (
                      <h2 className="text-lg font-bold text-primary border-b border-primary/20 pb-1 mb-2">
                        {line}
                      </h2>
                    ) : line.match(/^\d+\./) ? (
                      <h3 className="text-base font-semibold text-foreground mt-4 mb-2">
                        {line}
                      </h3>
                    ) : line.startsWith("   -") ? (
                      <p className="text-sm text-muted-foreground ml-6 mb-1">
                        {line.substring(5)}
                      </p>
                    ) : line.startsWith("⚠️") ? (
                      <p className="text-sm text-warning bg-warning/10 p-2 rounded mb-1">
                        {line}
                      </p>
                    ) : line.startsWith("Appareil:") || line.startsWith("Modèle:") || line.startsWith("Fabricant:") ? (
                      <p className="text-sm font-medium text-foreground mb-1">
                        {line}
                      </p>
                    ) : (
                      <p className="text-sm text-foreground mb-1">
                        {line}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  )
}