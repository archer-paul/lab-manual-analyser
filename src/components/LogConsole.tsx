import { useEffect, useRef } from 'react'
import { Terminal, Download, Eye } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useTranslation } from 'react-i18next'

interface LogEntry {
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
}

interface LogConsoleProps {
  logs: LogEntry[]
  isProcessing: boolean
  onDownload?: () => void
  onPreview?: () => void
  showActions?: boolean
}

export function LogConsole({ logs, isProcessing, onDownload, onPreview, showActions }: LogConsoleProps) {
  const { t } = useTranslation()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return 'text-destructive'
      case 'warning':
        return 'text-warning'
      case 'success':
        return 'text-success'
      default:
        return 'text-muted-foreground'
    }
  }

  const getLevelPrefix = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return '[ERROR]'
      case 'warning':
        return '[WARNING]'
      case 'success':
        return '[SUCCESS]'
      default:
        return '[INFO]'
    }
  }

  return (
    <Card className="h-full flex flex-col bg-card border shadow-md">
      <div className="p-4 border-b bg-gradient-accent">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Terminal className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-foreground">{t('console.title')}</h3>
          </div>
          {showActions && (
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onPreview}
                disabled={isProcessing}
              >
                <Eye className="w-4 h-4 mr-2" />
                {t('results.preview')}
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={onDownload}
                disabled={isProcessing}
                className="bg-gradient-primary hover:opacity-90"
              >
                <Download className="w-4 h-4 mr-2" />
                {t('results.download')}
              </Button>
            </div>
          )}
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div ref={scrollRef} className="space-y-2 font-mono text-sm">
          {logs.length === 0 ? (
            <div className="text-muted-foreground italic">
              {t('console.noLogs')}
            </div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="flex space-x-2">
                <span className="text-muted-foreground text-xs min-w-[60px]">
                  {log.timestamp}
                </span>
                <span className={`text-xs min-w-[80px] ${getLevelColor(log.level)}`}>
                  {getLevelPrefix(log.level)}
                </span>
                <span className={getLevelColor(log.level)}>
                  {log.message}
                </span>
              </div>
            ))
          )}
          
          {isProcessing && (
            <div className="flex items-center space-x-2 animate-pulse">
              <span className="text-muted-foreground text-xs min-w-[60px]">
                {new Date().toLocaleTimeString()}
              </span>
              <span className="text-primary text-xs">
                [ANALYSE]
              </span>
              <span className="text-primary">
                {t('console.processing')}
              </span>
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  )
}