import React, { useState, useRef } from 'react';
import type { ChatMode } from './ChatContainer';

interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled: boolean;
  currentMode: ChatMode;
}

const MessageInput: React.FC<MessageInputProps> = ({ 
  onSendMessage, 
  disabled, 
  currentMode 
}) => {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end space-x-3">
      <div className="flex-1">
        <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`${currentMode.mode}モード (${currentMode.effort}) でメッセージを送信...`}
          disabled={disabled}
          rows={1}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
          style={{ minHeight: '42px', maxHeight: '120px' }}
        />
      </div>
      
      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {disabled ? (
          <div className="w-5 h-5 animate-spin border-2 border-white border-t-transparent rounded-full"></div>
        ) : (
          '送信'
        )}
      </button>
    </form>
  );
};

export default MessageInput;