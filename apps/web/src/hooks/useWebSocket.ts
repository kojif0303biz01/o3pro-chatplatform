import { useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useChatStore } from '../stores/chatStore';
import type { Message, ChatMode } from '../components/Chat';

interface WebSocketEvents {
  // Client -> Server
  send_message: {
    message: string;
    session_id: string;
  };
  change_mode: {
    mode: ChatMode['mode'];
    effort: ChatMode['effort'];
  };
  get_job_status: {
    job_id: string;
  };
  ping: undefined;

  // Server -> Client
  connected: {
    session_id: string;
    mode: ChatMode['mode'];
    effort: ChatMode['effort'];
  };
  message_chunk: {
    chunk: string;
  };
  message_complete: {
    response?: string;
    duration: number;
  };
  job_started: {
    job_id: string;
    message: string;
  };
  job_completed: {
    job_id: string;
    response: string;
    total_time: number;
  };
  job_status: {
    job_id: string;
    status: string;
    elapsed_time: number;
  };
  stream_start: undefined;
  mode_changed: {
    mode: ChatMode['mode'];
    effort: ChatMode['effort'];
  };
  error: {
    message: string;
  };
  pong: undefined;
}

export const useWebSocket = () => {
  const socketRef = useRef<Socket | null>(null);
  const streamingMessageRef = useRef<string>('');
  
  const {
    currentSessionId,
    currentMode,
    addMessage,
    setConnectionStatus,
    setError,
    setLoading,
  } = useChatStore();

  // WebSocket接続
  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const API_KEY = import.meta.env.VITE_API_KEY || 'test-api-key-123';

    setConnectionStatus('connecting');

    socketRef.current = io(`${WS_URL}/chat`, {
      query: {
        api_key: API_KEY,
        session_id: currentSessionId || 'temp',
      },
      transports: ['websocket', 'polling'],
      timeout: 10000,
    });

    const socket = socketRef.current;

    // 接続イベント
    socket.on('connect', () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
      setError(null);
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setConnectionStatus('disconnected');
      
      if (reason === 'io server disconnect') {
        // サーバーが切断した場合は再接続しない
        setError('サーバーとの接続が切断されました');
      }
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setConnectionStatus('error');
      setError('接続に失敗しました');
    });

    // チャットイベント
    socket.on('connected', (data) => {
      console.log('Chat connected:', data);
      setError(null);
    });

    socket.on('stream_start', () => {
      console.log('Stream started');
      streamingMessageRef.current = '';
      setLoading(true);
    });

    socket.on('message_chunk', (data) => {
      streamingMessageRef.current += data.chunk;
      
      // ストリーミング表示用の一時メッセージを更新
      // 実装は簡略化のため、完了時に一括表示
    });

    socket.on('message_complete', (data) => {
      console.log('Message complete:', data);
      setLoading(false);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response || streamingMessageRef.current,
        timestamp: new Date(),
        mode: currentMode.mode,
        effort: currentMode.effort,
      };

      addMessage(assistantMessage);
      streamingMessageRef.current = '';
    });

    socket.on('job_started', (data) => {
      console.log('Job started:', data);
      setLoading(false);

      const statusMessage: Message = {
        id: `status-${Date.now()}`,
        role: 'assistant',
        content: `🔄 ${data.message} (ID: ${data.job_id.substring(0, 8)}...)`,
        timestamp: new Date(),
      };

      addMessage(statusMessage);
    });

    socket.on('job_completed', (data) => {
      console.log('Job completed:', data);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        mode: 'background',
      };

      addMessage(assistantMessage);
    });

    socket.on('job_status', (data) => {
      console.log('Job status:', data);
      // ステータス表示は簡略化
    });

    socket.on('mode_changed', (data) => {
      console.log('Mode changed:', data);
      // モード変更確認（必要に応じてUI更新）
    });

    socket.on('error', (data) => {
      console.error('WebSocket error:', data);
      setLoading(false);
      setError(data.message);
    });

    socket.on('pong', () => {
      console.log('Pong received');
    });

  }, [currentSessionId, currentMode, addMessage, setConnectionStatus, setError, setLoading]);

  // WebSocket切断
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setConnectionStatus('disconnected');
    }
  }, [setConnectionStatus]);

  // メッセージ送信（WebSocket経由）
  const sendMessageWS = useCallback((message: string) => {
    if (!socketRef.current?.connected || !currentSessionId) {
      setError('WebSocketが接続されていません');
      return false;
    }

    // ユーザーメッセージを即座に表示
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    addMessage(userMessage);

    // WebSocketでメッセージ送信
    socketRef.current.emit('send_message', {
      message,
      session_id: currentSessionId,
    });

    setLoading(true);
    return true;
  }, [currentSessionId, addMessage, setError, setLoading]);

  // モード変更（WebSocket経由）
  const changeModeWS = useCallback((mode: ChatMode) => {
    if (!socketRef.current?.connected) {
      return false;
    }

    socketRef.current.emit('change_mode', {
      mode: mode.mode,
      effort: mode.effort,
    });

    return true;
  }, []);

  // ジョブステータス確認
  const getJobStatusWS = useCallback((jobId: string) => {
    if (!socketRef.current?.connected) {
      return false;
    }

    socketRef.current.emit('get_job_status', {
      job_id: jobId,
    });

    return true;
  }, []);

  // Ping送信
  const ping = useCallback(() => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('ping');
    }
  }, []);

  // 初期接続とクリーンアップ（現在は無効化）
  useEffect(() => {
    // WebSocketサーバーが稼働していないため接続を無効化
    // ストリーミングチャット実装時に有効化
    // if (currentSessionId) {
    //   connect();
    // }

    return () => {
      disconnect();
    };
  }, [currentSessionId, connect, disconnect]);

  // 定期的なPing（接続維持）
  useEffect(() => {
    const pingInterval = setInterval(ping, 30000); // 30秒間隔

    return () => {
      clearInterval(pingInterval);
    };
  }, [ping]);

  return {
    isConnected: socketRef.current?.connected ?? false,
    sendMessage: sendMessageWS,
    changeMode: changeModeWS,
    getJobStatus: getJobStatusWS,
    connect,
    disconnect,
    ping,
  };
};