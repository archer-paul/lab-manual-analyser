import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useTranslation } from 'react-i18next'

interface FileUploaderProps {
  onFileSelect: (file: File) => void
  isProcessing: boolean
}

export function FileUploader({ onFileSelect, isProcessing }: FileUploaderProps) {
  const { t } = useTranslation()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setSelectedFile(file)
      setUploadProgress(0)
      
      // Simuler le upload
      const interval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval)
            return 100
          }
          return prev + 10
        })
      }, 100)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: isProcessing
  })

  const handleProcess = () => {
    if (selectedFile) {
      onFileSelect(selectedFile)
    }
  }

  const handleRemove = () => {
    setSelectedFile(null)
    setUploadProgress(0)
  }

  return (
    <div className="space-y-6">
      <Card className="border-2 border-dashed border-primary/20 bg-gradient-secondary">
        <div
          {...getRootProps()}
          className={`p-8 text-center cursor-pointer transition-all duration-300 ${
            isDragActive ? 'border-primary bg-primary/5' : 'hover:border-primary/40 hover:bg-primary/5'
          } ${isProcessing ? 'cursor-not-allowed opacity-50' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-primary/10 rounded-full">
              <Upload className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                {isDragActive ? t('upload.dragDrop').split(',')[0] : t('upload.selectFile')}
              </h3>
              <p className="text-muted-foreground">
                {t('upload.dragDrop')} <span className="text-primary font-medium">{t('upload.browse')}</span>
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {t('upload.acceptedFormat')}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {selectedFile && (
        <Card className="p-6 bg-card border shadow-md">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary/10 rounded">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-foreground">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemove}
              disabled={isProcessing}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {uploadProgress < 100 && (
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">{t('upload.processing')}</span>
                <span className="text-primary font-medium">{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          )}

          {uploadProgress === 100 && !isProcessing && (
            <Button 
              onClick={handleProcess}
              className="w-full bg-gradient-primary hover:opacity-90 transition-opacity"
            >
              {t('logs.analysisStarted')}
            </Button>
          )}

          {isProcessing && (
            <div className="text-center text-muted-foreground">
              <div className="animate-pulse">{t('console.processing')}</div>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}