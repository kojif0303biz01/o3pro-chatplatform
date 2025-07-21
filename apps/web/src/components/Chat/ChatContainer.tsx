import React, { useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ModeSelector from './ModeSelector';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  mode?: string;
  effort?: string;
}

export interface ChatMode {
  mode: 'reasoning' | 'streaming' | 'background';
  effort: 'low' | 'medium' | 'high';
}

const ChatContainer: React.FC = () => {
  // Zustand store
  const {
    messages,
    isLoading,
    currentMode,
    currentSessionId,
    error,
    connectionStatus,
    setMode,
    createSession,
    clearError,
  } = useChatStore();

  // WebSocket client
  const {
    isConnected,
    sendMessage: sendMessageWS,
    changeMode: changeModeWS,
  } = useWebSocket();

  // 初期セッション作成
  useEffect(() => {
    if (!currentSessionId) {
      createSession().catch(console.error);
    }
  }, [currentSessionId, createSession]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;
    
    // まずは常にZustorのsendMessage関数を使用（REST API経由）
    try {
      // ZustorのsendMessage関数を呼び出し
      const chatStore = useChatStore.getState();
      await chatStore.sendMessage(content);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleModeChange = (newMode: ChatMode) => {
    setMode(newMode);
    
    // WebSocket経由でモード変更を送信
    if (isConnected) {
      changeModeWS(newMode);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* エラー表示（WebSocket接続エラーは除外） */}
      {error && !error.includes('接続に失敗しました') && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-2 mx-4 mt-2 rounded">
          <div className="flex justify-between items-center">
            <p className="text-xs">{error}</p>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 ml-2"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* モード選択 */}
      <div className="bg-white border-b px-4 py-3">
        <ModeSelector 
          currentMode={currentMode}
          onModeChange={handleModeChange}
          disabled={isLoading}
        />
      </div>

      {/* メッセージリスト */}
      <div className="flex-1 overflow-hidden">
        <MessageList 
          messages={messages}
          isLoading={isLoading}
        />
      </div>

      {/* メッセージ入力 */}
      <div className="bg-white border-t px-4 py-4">
        <MessageInput 
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          currentMode={currentMode}
        />
      </div>
    </div>
  );
};

export default ChatContainer;