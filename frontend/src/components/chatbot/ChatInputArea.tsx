import React, { useState, useRef } from 'react';
import { Send, Mic, Image as ImageIcon, X, Sparkles } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';

interface ChatInputAreaProps {
  onSendMessage: (text: string, image?: string) => void;
  isLoading: boolean;
}

export const ChatInputArea: React.FC<ChatInputAreaProps> = ({ onSendMessage, isLoading }) => {
  const { t } = useLanguage();
  const { showToast } = useToast();
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [attachedImage, setAttachedImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const suggestedQuestions = [
    'What is wrong with my tomato plant?',
    'How can I prevent leaf diseases organically?',
    'What should I do after detecting early blight?',
    'What government schemes are available for subsidies?',
    'How do I calculate expected crop profit?'
  ];

  const handleSend = () => {
    if ((!text.trim() && !attachedImage) || isLoading) return;
    onSendMessage(text, attachedImage || undefined);
    setText('');
    setAttachedImage(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleVoice = () => {
    if (!isRecording) {
      setIsRecording(true);
      showToast('Voice input simulation started. Speak clearly...', 'info');

      // Simulate voice speech-to-text after 3 seconds
      setTimeout(() => {
        setText('How can I protect my tomato crops from early blight fungal disease?');
        setIsRecording(false);
        showToast('Voice transcription complete!', 'success');
      }, 3000);
    } else {
      setIsRecording(false);
    }
  };

  const handleImageAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setAttachedImage(url);
      showToast('Leaf photo attached to message', 'info');
    }
  };

  return (
    <div className="space-y-3">
      {/* Suggested Quick Prompt Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs no-scrollbar">
        <span className="flex items-center gap-1 font-semibold text-stone-400 shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-agri-600" />
          Suggestions:
        </span>
        {suggestedQuestions.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSendMessage(q)}
            className="px-3 py-1.5 rounded-full bg-white dark:bg-darkbg-card hover:bg-agri-50 dark:hover:bg-darkbg-input border border-stone-200 dark:border-darkbg-border text-stone-700 dark:text-stone-300 shrink-0 text-xs transition-colors shadow-2xs"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Image Preview attachment badge */}
      {attachedImage && (
        <div className="flex items-center gap-2 p-2 bg-stone-100 dark:bg-darkbg-input rounded-xl max-w-xs border border-stone-200 dark:border-darkbg-border">
          <img src={attachedImage} alt="Attachment" className="w-10 h-10 rounded-lg object-cover" />
          <span className="text-xs text-stone-600 dark:text-stone-300 truncate flex-1">
            Crop photo attached
          </span>
          <button
            onClick={() => setAttachedImage(null)}
            className="text-stone-400 hover:text-stone-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Input Control Bar */}
      <div className="flex items-center gap-2 bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-2xl p-2 shadow-sm focus-within:border-agri-500 transition-all">
        {/* Hidden File Input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleImageAttach}
          accept="image/*"
          className="hidden"
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="p-2 text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-darkbg-border rounded-xl transition-colors shrink-0"
          title={t('chat.attachImage')}
        >
          <ImageIcon className="w-5 h-5" />
        </button>

        <button
          type="button"
          onClick={toggleVoice}
          className={`p-2 rounded-xl transition-all shrink-0 ${
            isRecording
              ? 'bg-rose-500 text-white animate-pulse'
              : 'text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-darkbg-border'
          }`}
          title={isRecording ? 'Listening...' : 'Voice Input'}
        >
          <Mic className="w-5 h-5" />
        </button>

        <textarea
          rows={1}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isRecording ? t('chat.listening') : t('chat.placeholder')}
          className="flex-1 bg-transparent border-none focus:outline-none text-xs sm:text-sm text-stone-900 dark:text-stone-100 placeholder-stone-400 resize-none py-1.5"
        />

        <button
          type="button"
          onClick={handleSend}
          disabled={isLoading || (!text.trim() && !attachedImage)}
          className="p-2.5 rounded-xl bg-agri-600 hover:bg-agri-700 disabled:opacity-40 disabled:cursor-not-allowed text-white shadow-xs transition-colors shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
