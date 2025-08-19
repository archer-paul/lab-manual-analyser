import { useState } from 'react'
import { FileText, Clock, Shield, Mail, Github, Linkedin } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { FileUploader } from '@/components/FileUploader'
import { LogConsole } from '@/components/LogConsole'
import { PDFPreview } from '@/components/PDFPreview'
import LanguageToggle from '@/components/LanguageToggle'
import { useTranslation } from 'react-i18next'

interface LogEntry {
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
}

const Index = () => {
  const { t, i18n } = useTranslation()
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [synthesisId, setSynthesisId] = useState<string | null>(null)
  // URL de votre API Cloud Run
  const backendUrl = 'https://manual-miner-857985308573.europe-west1.run.app'

  const addLog = (level: LogEntry['level'], message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, { timestamp, level, message }])
  }

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file)
    setIsProcessing(true)
    setLogs([])

    try {
      // Préparer le FormData pour l'upload
      const formData = new FormData()
      formData.append('file', file)
      formData.append('language', i18n.language || 'en')

      // Démarrer l'analyse avec streaming vers le backend Python sur Cloud Run
      fetch(`${backendUrl}/analyze`, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
        },
        cache: 'no-store',
        body: formData,
      }).then(response => {
        if (!response.ok) {
          throw new Error(`Erreur ${response.status}: ${response.statusText}`)
        }

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let doneStream = false

        const processEvent = (eventBlock: string) => {
          const lines = eventBlock.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (!data) continue
              try {
                const logEntry = JSON.parse(data)
                if (logEntry.type === 'complete') {
                  setIsProcessing(false)
                  if (logEntry.analysisId) setSynthesisId(logEntry.analysisId)
                  doneStream = true
                } else if (logEntry.type === 'error') {
                  setIsProcessing(false)
                  doneStream = true
                } else if (logEntry.timestamp && logEntry.level && logEntry.message) {
                  addLog(logEntry.level, logEntry.message)
                }
              } catch (e) {
                console.warn('Erreur parsing log:', e)
              }
            }
          }
        }

        const readStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              buffer += decoder.decode(value, { stream: true })

              let idx
              while ((idx = buffer.indexOf('\n\n')) !== -1) {
                const eventBlock = buffer.slice(0, idx)
                buffer = buffer.slice(idx + 2)
                if (eventBlock.startsWith(':')) continue
                processEvent(eventBlock)
              }

              if (doneStream) {
                try { await reader.cancel() } catch {}
                break
              }
            }
          } catch (error: any) {
            console.error('Erreur lecture stream:', error)
            addLog('error', `Erreur de communication: ${error.message}`)
          } finally {
            setIsProcessing(false)
          }
        }

        readStream()
      }).catch(error => {
        console.error('Erreur lors de l\'analyse:', error)
        addLog('error', `Erreur: ${error.message}`)
        setIsProcessing(false)
      })

    } catch (error) {
      console.error('Erreur lors de l\'analyse:', error)
      addLog('error', `Erreur: ${error.message}`)
      setIsProcessing(false)
    }
  }

  const handleDownload = async () => {
    if (!synthesisId) {
      addLog('error', 'Aucune synthèse disponible pour le téléchargement')
      return
    }

    try {
      // Utiliser l'endpoint de téléchargement du backend Python
      const downloadUrl = `${backendUrl}/download/${synthesisId}`
      
      // Ouvrir le téléchargement
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = selectedFile?.name.replace('.pdf', '_SYNTHESE_MANUALMINER.pdf') || 'synthese_manualminer.pdf'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      addLog('success', 'Téléchargement lancé!')
    } catch (error) {
      addLog('error', `Erreur de téléchargement: ${error.message}`)
    }
  }

  const handlePreview = () => {
    setShowPreview(true)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-white/20 rounded-lg">
                <img src="/icon_landing_page.png" alt="ManualMiner" className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-bold">{t('header.title')}</h1>
                <p className="text-blue-100">{t('header.subtitle')}</p>
              </div>
            </div>
            <LanguageToggle />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            <div className="flex items-center space-x-3 text-blue-100">
              <FileText className="w-5 h-5" />
              <span className="text-sm">{t('header.features.pages')}</span>
            </div>
            <div className="flex items-center space-x-3 text-blue-100">
              <Clock className="w-5 h-5" />
              <span className="text-sm">{t('header.features.analysis')}</span>
            </div>
            <div className="flex items-center space-x-3 text-blue-100">
              <Shield className="w-5 h-5" />
              <span className="text-sm">{t('header.features.compliance')}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - File Upload */}
          <div className="space-y-6">
            <Card className="p-6 bg-white shadow-md">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                {t('upload.title')}
              </h2>
              <p className="text-gray-600 mb-6">
                {t('upload.description')}
              </p>
              <FileUploader 
                onFileSelect={handleFileSelect}
                isProcessing={isProcessing}
              />
            </Card>

            {logs.length > 0 && !isProcessing && (
              <Card className="p-6 bg-white shadow-md">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  {t('results.title')}
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-5 h-5 text-green-600" />
                      <span className="text-green-700 font-medium">{t('results.synthesisReady')}</span>
                    </div>
                    <div className="text-sm text-green-600">
                      {selectedFile && `${selectedFile.name.replace('.pdf', '_SYNTHESE_MANUALMINER.pdf')}`}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">
                    {t('results.description')}
                  </p>
                </div>
              </Card>
            )}
          </div>

          {/* Right Column - Log Console */}
          <div className="h-full min-h-[600px]">
            <LogConsole 
              logs={logs}
              isProcessing={isProcessing}
              onDownload={handleDownload}
              onPreview={handlePreview}
              showActions={logs.length > 0 && !isProcessing}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="container mx-auto px-6 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="text-gray-500 text-sm">
              {t('footer.copyright')}
            </div>
            <div className="flex items-center gap-4">
              <a 
                href="mailto:paul.erwan.archer@gmail.com" 
                className="text-gray-500 hover:text-blue-600 transition-colors"
                title="Email"
              >
                <Mail className="h-5 w-5" />
              </a>
              <a 
                href="https://github.com/archer-paul" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-500 hover:text-blue-600 transition-colors"
                title="GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
              <a 
                href="https://www.linkedin.com/in/p-archer/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-500 hover:text-blue-600 transition-colors"
                title="LinkedIn"
              >
                <Linkedin className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* PDF Preview Modal */}
      <PDFPreview 
        isOpen={showPreview}
        onClose={() => setShowPreview(false)}
        onDownload={handleDownload}
        fileName={selectedFile ? selectedFile.name.replace('.pdf', '_SYNTHESE_MANUALMINER.pdf') : undefined}
      />
    </div>
  )
}

export default Index