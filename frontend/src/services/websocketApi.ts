/**
 * WebSocket 部署 API 服務
 * 替代 SSE 實作，提供雙向通信
 */

import { DeploymentLogEntry } from './deploymentApi';

// WebSocket 訊息類型定義
export interface WebSocketMessage {
  type: 'connected' | 'log' | 'status' | 'error' | 'ping' | 'pong' | 'command' | 'command_received' | 'get_status';
  session_id: string;
  data?: any;
  message?: string;
  timestamp: string;
}

// WebSocket 連線狀態
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error';

// WebSocket 事件回調
export interface WebSocketCallbacks {
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: string) => void;
  onLog?: (log: DeploymentLogEntry) => void;
  onStatus?: (status: any) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export class WebSocketDeploymentClient {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private callbacks: WebSocketCallbacks;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1 秒
  private pingInterval: NodeJS.Timeout | null = null;
  private state: WebSocketState = 'disconnected';

  constructor(sessionId: string, callbacks: WebSocketCallbacks = {}) {
    this.sessionId = sessionId;
    this.callbacks = callbacks;
  }

  /**
   * 建立 WebSocket 連線
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('WebSocket 已經連線');
      return;
    }

    this.state = 'connecting';
    
    // 建構 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/exam-sessions/${this.sessionId}/kubespray/deploy/logs/ws`;

    console.log('正在連接 WebSocket:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('WebSocket 連線失敗:', error);
      this.handleError(`連線失敗: ${error}`);
    }
  }

  /**
   * 設定事件處理器
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket 連線已建立');
      this.state = 'connected';
      this.reconnectAttempts = 0;
      this.callbacks.onConnected?.();
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('解析 WebSocket 訊息失敗:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket 連線關閉:', event.code, event.reason);
      this.state = 'disconnected';
      this.stopPingInterval();
      this.callbacks.onDisconnected?.();

      // 嘗試重連（如果不是正常關閉）
      if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket 錯誤:', error);
      this.handleError('WebSocket 連線錯誤');
    };
  }

  /**
   * 處理接收到的訊息
   */
  private handleMessage(message: WebSocketMessage): void {
    console.log('收到 WebSocket 訊息:', message);

    // 呼叫通用訊息回調
    this.callbacks.onMessage?.(message);

    // 根據訊息類型處理
    switch (message.type) {
      case 'connected':
        console.log('WebSocket 連線確認');
        break;

      case 'log':
        if (message.data) {
          const logEntry = this.parseLogEntry(message.data.message, message.data.timestamp);
          this.callbacks.onLog?.(logEntry);
        }
        break;

      case 'status':
        if (message.data) {
          this.callbacks.onStatus?.(message.data);
        }
        break;

      case 'error':
        this.handleError(message.message || '未知錯誤');
        break;

      case 'pong':
        // 心跳回應，保持連線
        break;

      case 'command_received':
        console.log('指令已接收:', message.data);
        break;

      default:
        console.warn('未知的訊息類型:', message.type);
    }
  }

  /**
   * 解析日誌條目
   */
  private parseLogEntry(data: string, timestamp?: string): DeploymentLogEntry {
    const now = timestamp || new Date().toLocaleTimeString('zh-TW', { hour12: false });

    // 簡單的日誌類型判斷
    let type: DeploymentLogEntry['type'] = 'info';
    const lowerData = data.toLowerCase();

    if (lowerData.includes('error') || lowerData.includes('failed') || lowerData.includes('fatal')) {
      type = 'error';
    } else if (lowerData.includes('warning') || lowerData.includes('warn')) {
      type = 'warning';
    } else if (lowerData.includes('ok') || lowerData.includes('success') || lowerData.includes('completed')) {
      type = 'success';
    }

    return {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: now,
      type,
      message: data,
      raw: data,
    };
  }

  /**
   * 發送訊息到伺服器
   */
  send(message: Partial<WebSocketMessage>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket 未連線，無法發送訊息');
      return;
    }

    const fullMessage: WebSocketMessage = {
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      ...message,
    } as WebSocketMessage;

    try {
      this.ws.send(JSON.stringify(fullMessage));
    } catch (error) {
      console.error('發送 WebSocket 訊息失敗:', error);
    }
  }

  /**
   * 發送心跳
   */
  ping(): void {
    this.send({ type: 'ping' });
  }

  /**
   * 查詢部署狀態
   */
  getStatus(): void {
    this.send({ type: 'get_status' });
  }

  /**
   * 發送指令
   */
  sendCommand(command: string, data?: any): void {
    this.send({
      type: 'command',
      data: { command, ...data }
    });
  }

  /**
   * 斷開連線
   */
  disconnect(): void {
    this.stopPingInterval();
    
    if (this.ws) {
      this.ws.close(1000, '正常關閉');
      this.ws = null;
    }
    
    this.state = 'disconnected';
  }

  /**
   * 開始心跳檢測
   */
  private startPingInterval(): void {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      this.ping();
    }, 30000); // 每 30 秒發送一次心跳
  }

  /**
   * 停止心跳檢測
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * 處理錯誤
   */
  private handleError(error: string): void {
    console.error('WebSocket 錯誤:', error);
    this.state = 'error';
    this.callbacks.onError?.(error);
  }

  /**
   * 安排重連
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // 指數退避

    console.log(`將在 ${delay}ms 後嘗試第 ${this.reconnectAttempts} 次重連`);

    setTimeout(() => {
      if (this.state !== 'connected') {
        this.connect();
      }
    }, delay);
  }

  /**
   * 取得當前連線狀態
   */
  getState(): WebSocketState {
    return this.state;
  }

  /**
   * 是否已連線
   */
  isConnected(): boolean {
    return this.state === 'connected' && this.ws?.readyState === WebSocket.OPEN;
  }
}

/**
 * 建立 WebSocket 部署客戶端
 */
export function createWebSocketDeploymentClient(
  sessionId: string,
  callbacks: WebSocketCallbacks = {}
): WebSocketDeploymentClient {
  return new WebSocketDeploymentClient(sessionId, callbacks);
}