import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'

const LanguageToggle = () => {
  const { i18n } = useTranslation()

  const toggleLanguage = () => {
    const newLanguage = i18n.language === 'fr' ? 'en' : 'fr'
    i18n.changeLanguage(newLanguage)
  }

  const currentLanguage = i18n.language || 'en'
  const isEnglish = currentLanguage === 'en'

  return (
    <Button
      onClick={toggleLanguage}
      variant="ghost"
      size="sm"
      className="relative h-10 w-20 p-1 hover:bg-white/20 transition-all duration-200 rounded-lg"
      aria-label={`Switch to ${isEnglish ? 'French' : 'English'}`}
    >
      <div className="flex items-center justify-center space-x-1">
        {/* French flag */}
        <div 
          className={`transition-all duration-200 ${
            !isEnglish ? 'opacity-100 scale-110 ring-2 ring-white/50 rounded-sm' : 'opacity-60 scale-90'
          }`}
        >
          <img 
            src="/flags/fr.svg" 
            alt="Français" 
            className="w-6 h-4 object-cover rounded-sm"
          />
        </div>
        
        {/* Separator */}
        <div className="w-px h-4 bg-white/30"></div>
        
        {/* English flag */}
        <div 
          className={`transition-all duration-200 ${
            isEnglish ? 'opacity-100 scale-110 ring-2 ring-white/50 rounded-sm' : 'opacity-60 scale-90'
          }`}
        >
          <img 
            src="/flags/gb.svg" 
            alt="English" 
            className="w-6 h-4 object-cover rounded-sm"
          />
        </div>
      </div>
    </Button>
  )
}

export default LanguageToggle