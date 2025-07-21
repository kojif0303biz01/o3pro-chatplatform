import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Message, ChatMode } from '../components/Chat';

interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
}

interface ChatState {
  // セッション管理
  currentSessionId: string | null;
  sessions: Session[];
  
  // メッセージ管理
  messages: Message[];
  isLoading: boolean;
  
  // モード管理
  currentMode: ChatMode;
  
  // 接続状態
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  
  // エラー管理
  error: string | null;
}

interface ChatActions {
  // セッション操作
  createSession: (title?: string) => Promise<string>;
  switchSession: (sessionId: string) => void;
  loadSessions: () => Promise<void>;
  
  // メッセージ操作
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  loadMessages: (sessionId: string) => Promise<void>;
  
  // モード操作
  setMode: (mode: ChatMode) => void;
  
  // 接続管理
  setConnectionStatus: (status: ChatState['connectionStatus']) => void;
  
  // エラー管理
  setError: (error: string | null) => void;
  clearError: () => void;
  
  // ローディング状態
  setLoading: (loading: boolean) => void;
}

type ChatStore = ChatState & ChatActions;

// API設定
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || 'test-api-key-123';

// APIヘルパー
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
};

export const useChatStore = create<ChatStore>()(
  devtools(
    (set, get) => ({
      // 初期状態
      currentSessionId: null,
      sessions: [],
      messages: [],
      isLoading: false,
      currentMode: { mode: 'reasoning', effort: 'low' },
      isConnected: false,
      connectionStatus: 'disconnected',
      error: null,

      // セッション操作
      createSession: async (title) => {
        try {
          set({ isLoading: true, error: null });
          
          const sessionData = await apiRequest('/api/v1/sessions/', {
            method: 'POST',
            body: JSON.stringify({
              title: title || `チャットセッション ${new Date().toLocaleString()}`,
              user_id: 'default'
            }),
          });

          const newSession: Session = {
            id: sessionData.id,
            title: sessionData.title,
            createdAt: new Date(sessionData.created_at),
            updatedAt: new Date(sessionData.updated_at),
            messageCount: sessionData.message_count,
          };

          set(state => ({
            sessions: [newSession, ...state.sessions],
            currentSessionId: newSession.id,
            messages: [],
            isLoading: false,
          }));

          return newSession.id;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'セッション作成に失敗しました';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      switchSession: (sessionId: string) => {
        set({ currentSessionId: sessionId, messages: [] });
        get().loadMessages(sessionId);
      },

      loadSessions: async () => {
        try {
          set({ error: null });
          
          const sessionsData = await apiRequest('/api/v1/sessions/', {
            method: 'GET',
          });

          const sessions: Session[] = sessionsData.map((session: any) => ({
            id: session.id,
            title: session.title,
            createdAt: new Date(session.created_at),
            updatedAt: new Date(session.updated_at),
            messageCount: session.message_count,
          }));

          set({ sessions });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'セッション取得に失敗しました';
          set({ error: errorMessage });
        }
      },

      // メッセージ操作
      sendMessage: async (content: string) => {
        const { currentSessionId, currentMode } = get();
        
        if (!currentSessionId) {
          // セッションがない場合は新規作成
          const newSessionId = await get().createSession();
          set({ currentSessionId: newSessionId });
        }

        try {
          set({ isLoading: true, error: null });

          // ユーザーメッセージを即座に追加
          const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content,
            timestamp: new Date(),
          };
          
          get().addMessage(userMessage);

          // API呼び出し
          const response = await apiRequest('/api/v1/chat/message', {
            method: 'POST',
            body: JSON.stringify({
              message: content,
              session_id: get().currentSessionId,
            }),
          });

          if (response.success) {
            // アシスタント応答を追加
            const assistantMessage: Message = {
              id: `assistant-${Date.now()}`,
              role: 'assistant',
              content: response.response,
              timestamp: new Date(),
              mode: currentMode.mode,
              effort: currentMode.effort,
            };
            
            get().addMessage(assistantMessage);
          } else {
            throw new Error(response.error || 'メッセージ送信に失敗しました');
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'メッセージ送信に失敗しました';
          set({ error: errorMessage });
          
          // エラーメッセージを追加
          const errorMessageObj: Message = {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: `❌ エラー: ${errorMessage}`,
            timestamp: new Date(),
          };
          
          get().addMessage(errorMessageObj);
        } finally {
          set({ isLoading: false });
        }
      },

      addMessage: (message: Message) => {
        set(state => ({
          messages: [...state.messages, message],
        }));
      },

      clearMessages: () => {
        set({ messages: [] });
      },

      loadMessages: async (sessionId: string) => {
        try {
          set({ isLoading: true, error: null });
          
          const historyData = await apiRequest(`/api/v1/chat/history/${sessionId}`);
          
          const messages: Message[] = historyData.messages.map((msg: any) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            mode: msg.mode,
            effort: msg.effort,
          }));

          set({ messages, isLoading: false });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '履歴取得に失敗しました';
          set({ error: errorMessage, isLoading: false });
        }
      },

      // モード操作
      setMode: (mode: ChatMode) => {
        set({ currentMode: mode });
      },

      // 接続管理
      setConnectionStatus: (status: ChatState['connectionStatus']) => {
        set({ 
          connectionStatus: status,
          isConnected: status === 'connected'
        });
      },

      // エラー管理
      setError: (error: string | null) => {
        set({ error });
      },

      clearError: () => {
        set({ error: null });
      },

      // ローディング状態
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'chat-store', // devtools用の名前
    }
  )
);

export type { ChatStore, Session };