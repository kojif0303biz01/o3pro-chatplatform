import React, { useEffect, useRef } from 'react';
import type { Message } from './ChatContainer';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`message-bubble px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white ml-12'
            : 'bg-white text-gray-900 mr-12 shadow-sm border'
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
        <div
          className={`text-xs mt-1 ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          }`}
        >
          {message.timestamp.toLocaleTimeString()}
          {message.mode && ` • ${message.mode}/${message.effort}`}
        </div>
      </div>
    </div>
  );
};

const LoadingIndicator: React.FC = () => (
  <div className="flex justify-start mb-4">
    <div className="message-bubble bg-white text-gray-900 shadow-sm border px-4 py-2 rounded-lg mr-12">
      <div className="flex items-center space-x-2">
        <div className="typing-indicator flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
        </div>
        <span className="text-sm text-gray-500">o3-proが回答を生成中...</span>
      </div>
    </div>
  </div>
);

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="h-full overflow-y-auto p-4 bg-gray-50">
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <div className="text-6xl mb-4">🤖</div>
            <h3 className="text-xl font-medium mb-2">o3-proチャットボット</h3>
            <p>メッセージを送信して対話を開始してください</p>
            <p className="text-sm mt-2">現在のモードで応答します</p>
          </div>
        </div>
      )}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isLoading && <LoadingIndicator />}

      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;