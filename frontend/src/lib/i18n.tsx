'use client';
import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import en from '@/messages/en.json';
import ru from '@/messages/ru.json';
import de from '@/messages/de.json';
import fr from '@/messages/fr.json';
import es from '@/messages/es.json';
import it from '@/messages/it.json';
import pt from '@/messages/pt.json';
import pl from '@/messages/pl.json';

export type Locale = 'en' | 'ru' | 'de' | 'fr' | 'es' | 'it' | 'pt' | 'pl';
type Messages = typeof en;

const MESSAGES: Record<Locale, Messages> = { en, ru: ru as Messages, de: de as Messages, fr: fr as Messages, es: es as Messages, it: it as Messages, pt: pt as Messages, pl: pl as Messages };
export const SUPPORTED_LOCALES: Locale[] = ['en', 'ru', 'de', 'fr', 'es', 'it', 'pt', 'pl'];
const STORAGE_KEY = 'prism_locale';

interface I18nContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function lookup(messages: Messages, key: string): string {
  const parts = key.split('.');
  let cur: unknown = messages;
  for (const p of parts) {
    if (cur && typeof cur === 'object' && p in (cur as Record<string, unknown>)) {
      cur = (cur as Record<string, unknown>)[p];
    } else {
      return key;
    }
  }
  return typeof cur === 'string' ? cur : key;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en');

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Locale | null;
      if (stored && SUPPORTED_LOCALES.includes(stored)) {
        setLocaleState(stored);
        return;
      }
      const lang = (typeof navigator !== 'undefined' ? navigator.language?.toLowerCase() : '') || '';
      if (lang.startsWith('ru')) setLocaleState('ru');
      else if (lang.startsWith('de')) setLocaleState('de');
      else if (lang.startsWith('fr')) setLocaleState('fr');
      else if (lang.startsWith('es')) setLocaleState('es');
      else if (lang.startsWith('it')) setLocaleState('it');
      else if (lang.startsWith('pt')) setLocaleState('pt');
      else if (lang.startsWith('pl')) setLocaleState('pl');
    } catch {}
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    try { localStorage.setItem(STORAGE_KEY, l); } catch {}
  }, []);

  const t = useCallback((key: string) => lookup(MESSAGES[locale], key), [locale]);

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslations() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    return { locale: 'en' as Locale, setLocale: () => {}, t: (key: string) => key };
  }
  return ctx;
}
