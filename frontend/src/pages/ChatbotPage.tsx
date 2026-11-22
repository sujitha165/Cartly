import React, { useState, useRef, useEffect } from 'react';
import { ChatMessageItem } from '../components/chatbot/ChatMessageItem';
import { ChatInputArea } from '../components/chatbot/ChatInputArea';
import { useLanguage } from '../context/LanguageContext';
import { chatService } from '../services/chatService';
import { ChatMessage } from '../types';
import { BotMessageSquare, RotateCcw, Sparkles } from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const ChatbotPage: React.FC = () => {
  const { t, language } = useLanguage();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'assistant',
      text: `Hello Farmer! 🌱 I am your **AgriSense AI Assistant**.\n\nAsk me anything about:\n* **Crop Pathologies:** Early/Late blight, leaf curls, powdery mildew, blast.\n* **Safe Treatments:** Biological controls (*Trichoderma*, *Bacillus*), certified copper sprays, and cultural practices.\n* **Government Financials:** Subsidies for sprayers, PM-KISAN, or PMFBY crop insurance.\n\nHow may I help your fields today?`,
      timestamp: new Date().toISOString()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatScrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (text: string, image?: string) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      image,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const replyText = await chatService.sendMessage(text, language);
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e) {
      console.error('Chat error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Clear current assistant conversation?')) {
      setMessages([
        {
          id: 'welcome-reset',
          sender: 'assistant',
          text: 'Conversation cleared. How can I assist you with your crops today?',
          timestamp: new Date().toISOString()
        }
      ]);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8.5rem)] flex flex-col space-y-4">
      {/* Top Title & Reset Bar */}
      <div className="flex items-center justify-between bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-2xl p-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
            <BotMessageSquare className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold text-stone-900 dark:text-stone-100">
                {t('chat.title')}
              </h1>
              <Badge variant="emerald" size="sm" icon={<Sparkles className="w-3 h-3" />}>
                Live AI
              </Badge>
            </div>
            <p className="text-xs text-stone-500 dark:text-stone-400">
              {t('chat.subtitle')}
            </p>
          </div>
        </div>

        <button
          onClick={handleClearChat}
          className="flex items-center gap-1 text-xs text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 p-2 rounded-xl hover:bg-stone-100 dark:hover:bg-darkbg-input transition-colors"
          title={t('chat.clearChat')}
        >
          <RotateCcw className="w-4 h-4" />
          <span className="hidden sm:inline">{t('chat.clearChat')}</span>
        </button>
      </div>

      {/* Chat Messages Scrolling History */}
      <div className="flex-1 overflow-y-auto bg-stone-50/50 dark:bg-darkbg-surface/50 border border-stone-200/80 dark:border-darkbg-border rounded-3xl p-4 sm:p-6 space-y-4 shadow-inner">
        {messages.map(msg => (
          <ChatMessageItem key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-stone-400 pl-11 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-agri-600 animate-bounce" />
            <span className="w-2 h-2 rounded-full bg-agri-600 animate-bounce [animation-delay:0.2s]" />
            <span className="w-2 h-2 rounded-full bg-agri-600 animate-bounce [animation-delay:0.4s]" />
            <span>AgriSense Assistant is formulating guidance...</span>
          </div>
        )}

        <div ref={chatScrollRef} />
      </div>

      {/* Input Control Bar */}
      <ChatInputArea onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};
