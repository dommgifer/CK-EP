import React, { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Rocket, CheckCircle2, Clock, AlertCircle, Wifi, WifiOff } from "lucide-react";
import { deploymentApi, type DeploymentLogEntry, type ExamSessionResponse, type DeploymentStatus } from '@/services/deploymentApi';
import { createWebSocketDeploymentClient, WebSocketDeploymentClient, WebSocketState } from '@/services/websocketApi';

interface DeploymentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeploymentComplete: () => void;
  deploymentParams?: {
    examType: string;
    examSet: string;
    vmConfigId: string;
  };
}

export const DeploymentDialog: React.FC<DeploymentDialogProps> = ({
  open,
  onOpenChange,
  onDeploymentComplete,
  deploymentParams
}) => {
  // 處理關閉對話框的確認
  const handleCloseDialog = (shouldClose: boolean) => {
    if (shouldClose && isDeploying && !isDeploymentComplete) {
      const confirmed = confirm('部署正在進行中，確定要關閉嗎？這將中斷部署過程。');
      if (!confirmed) {
        return;
      }

      // 清理資源
      if (wsClientRef.current) {
        wsClientRef.current.disconnect();
        wsClientRef.current = null;
      }
      if (statusPollingRef.current) {
        clearInterval(statusPollingRef.current);
        statusPollingRef.current = null;
      }
    }

    onOpenChange(shouldClose);
  };

  const [currentStatus, setCurrentStatus] = useState("準備中...");
  const [logs, setLogs] = useState<DeploymentLogEntry[]>([]);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isDeploymentComplete, setIsDeploymentComplete] = useState(false);
  const [deploymentError, setDeploymentError] = useState<string | null>(null);
  const [currentSession, setCurrentSession] = useState<ExamSessionResponse | null>(null);
  const [deploymentStatus, setDeploymentStatus] = useState<DeploymentStatus | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [elapsedTime, setElapsedTime] = useState('0:00');

  // WebSocket 相關狀態
  const [wsState, setWsState] = useState<WebSocketState>('disconnected');

  const wsClientRef = useRef<WebSocketDeploymentClient | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const statusPollingRef = useRef<NodeJS.Timeout | null>(null);
  const timeUpdateRef = useRef<NodeJS.Timeout | null>(null);

  // 自動開始部署
  useEffect(() => {
    if (open && !isDeploying && !isDeploymentComplete && deploymentParams) {
      const timer = setTimeout(() => {
        startRealDeployment();
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [open, deploymentParams]);

  // 清理資源
  useEffect(() => {
    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.disconnect();
        wsClientRef.current = null;
      }
      if (statusPollingRef.current) {
        clearInterval(statusPollingRef.current);
        statusPollingRef.current = null;
      }
      if (timeUpdateRef.current) {
        clearInterval(timeUpdateRef.current);
        timeUpdateRef.current = null;
      }
    };
  }, []);

  // 更新經過時間
  useEffect(() => {
    if (startTime && !isDeploymentComplete) {
      timeUpdateRef.current = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now.getTime() - startTime.getTime()) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        setElapsedTime(`${minutes}:${seconds.toString().padStart(2, '0')}`);
      }, 1000);

      return () => {
        if (timeUpdateRef.current) {
          clearInterval(timeUpdateRef.current);
          timeUpdateRef.current = null;
        }
      };
    }
  }, [startTime, isDeploymentComplete]);

  // 自動滾動到最新日誌
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // 實際的部署函數
  const startRealDeployment = async () => {
    if (!deploymentParams) {
      setDeploymentError('缺少部署參數');
      return;
    }

    setIsDeploying(true);
    setCurrentStatus("正在啟動部署...");
    setStartTime(new Date());
    setDeploymentError(null);
    setLogs([]);

    try {
      // 1. 啟動完整部署流程
      const { session, deployment } = await deploymentApi.startFullDeployment(deploymentParams);
      setCurrentSession(session);
      setCurrentStatus("部署已啟動，正在建立 WebSocket 連線...");

      // 2. 建立 WebSocket 連線接收即時日誌
      setupWebSocketConnection(session.id);

      // 3. 開始輪詢部署狀態
      startStatusPolling(session.id);

    } catch (error) {
      console.error('部署啟動失敗:', error);
      setDeploymentError(error instanceof Error ? error.message : '未知錯誤');
      setCurrentStatus("部署啟動失敗");
      setIsDeploying(false);
    }
  };

  // 設定 WebSocket 連線
  const setupWebSocketConnection = (sessionId: string) => {
    const wsClient = createWebSocketDeploymentClient(sessionId, {
      onConnected: () => {
        setWsState('connected');
        setCurrentStatus("WebSocket 連線已建立，正在接收部署日誌...");
        addLogEntry({
          id: `ws-connected-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString('zh-TW', { hour12: false }),
          type: 'success',
          message: "✅ WebSocket 連線已建立",
        });
      },
      onDisconnected: () => {
        setWsState('disconnected');
        setCurrentStatus("WebSocket 連線已斷開");
      },
      onError: (error) => {
        setWsState('error');
        setCurrentStatus(`WebSocket 錯誤: ${error}`);
        addLogEntry({
          id: `ws-error-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString('zh-TW', { hour12: false }),
          type: 'error',
          message: `❌ WebSocket 錯誤: ${error}`,
        });
      },
      onLog: (logEntry) => {
        addLogEntry(logEntry);
      },
      onStatus: (status) => {
        if (status.status === 'completed') {
          setIsDeploymentComplete(true);
          setCurrentStatus("Kubernetes 集群部署完成！準備開始考試");
        } else if (status.status === 'failed') {
          setDeploymentError(`部署失敗 (退出代碼: ${status.exit_code})`);
          setCurrentStatus("部署失敗");
          setIsDeploying(false);
        }
      }
    });

    wsClientRef.current = wsClient;
    setWsState('connecting');
    wsClient.connect();
  };

  // 開始狀態輪詢
  const startStatusPolling = (sessionId: string) => {
    const checkStatus = async () => {
      try {
        const status = await deploymentApi.getDeploymentStatus(sessionId);
        setDeploymentStatus(status);

        if (status.status === 'completed') {
          setIsDeploymentComplete(true);
          setCurrentStatus("Kubernetes 集群部署完成！準備開始考試");

          // 關閉連線
          cleanupConnections();

          // 添加完成日誌
          addLogEntry({
            id: `completion-${Date.now()}`,
            timestamp: new Date().toLocaleTimeString('zh-TW', { hour12: false }),
            type: 'success',
            message: "✅ Kubernetes 集群部署成功！所有節點運行正常，準備開始考試...",
          });

          // 自動跳轉到考試（延遲3秒讓使用者看到完成訊息）
          setTimeout(() => {
            onDeploymentComplete();
            onOpenChange(false);
          }, 3000);

        } else if (status.status === 'failed') {
          setDeploymentError(`部署失敗 (退出代碼: ${status.exit_code})`);
          setCurrentStatus("部署失敗");
          setIsDeploying(false);
          cleanupConnections();
        } else if (status.status === 'running') {
          setCurrentStatus("正在部署 Kubernetes 集群...");
        }
      } catch (error) {
        console.error('查詢部署狀態失敗:', error);
      }
    };

    // 立即檢查一次，然後每10秒檢查一次
    checkStatus();
    statusPollingRef.current = setInterval(checkStatus, 10000);
  };

  // 清理連線
  const cleanupConnections = () => {
    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
      wsClientRef.current = null;
    }
    if (statusPollingRef.current) {
      clearInterval(statusPollingRef.current);
      statusPollingRef.current = null;
    }
  };

  // 添加新的日誌條目
  const addLogEntry = (logEntry: DeploymentLogEntry) => {
    setLogs(prev => [...prev, logEntry]);
  };

  // 重新開始部署
  const retryDeployment = () => {
    setDeploymentError(null);
    setIsDeploying(false);
    setIsDeploymentComplete(false);
    setLogs([]);
    setCurrentStatus("準備中...");
    setElapsedTime('0:00');

    setTimeout(() => {
      startRealDeployment();
    }, 1000);
  };

  // 發送 WebSocket 指令
  const sendWebSocketCommand = (command: string) => {
    if (wsClientRef.current && wsClientRef.current.isConnected()) {
      wsClientRef.current.sendCommand(command);
      addLogEntry({
        id: `command-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString('zh-TW', { hour12: false }),
        type: 'info',
        message: `📤 發送指令: ${command}`,
      });
    }
  };

  const getLogTypeColor = (type: DeploymentLogEntry['type']) => {
    switch (type) {
      case 'success':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-muted-foreground';
    }
  };

  const getConnectionIcon = () => {
    return wsState === 'connected' ? <Wifi className="h-4 w-4 text-green-500" /> : <WifiOff className="h-4 w-4 text-red-500" />;
  };

  return (
    <Dialog open={open} onOpenChange={handleCloseDialog}>
      <DialogContent className="max-w-6xl max-h-[90vh] bg-background border border-border">
        <DialogHeader className="space-y-4">
          <div className="flex items-center gap-3">
            <Rocket className="h-6 w-6 text-blue-500" />
            <DialogTitle className="text-2xl font-bold text-foreground">
              正在部屬 Kubernetes 集群
            </DialogTitle>
          </div>

          <div className="space-y-2">
            <p className="text-muted-foreground">
              請稍候，正在為您的考試環境部署 Kubernetes 集群...
            </p>
          </div>
        </DialogHeader>

        <div className="py-4">
          {/* 錯誤顯示 */}
          {deploymentError && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <div>
                  <h4 className="text-red-800 font-medium">部署失敗</h4>
                  <p className="text-red-600 text-sm mt-1">{deploymentError}</p>
                  <Button
                    onClick={retryDeployment}
                    className="mt-3 bg-red-600 hover:bg-red-700 text-white"
                    size="sm"
                  >
                    重新部署
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* 部署狀態 */}
          <div className="mb-4 p-3 bg-muted/30 rounded-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isDeploying && !isDeploymentComplete && (
                  <Clock className="h-4 w-4 animate-spin text-blue-500" />
                )}
                {isDeploymentComplete && (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
                <span className="text-sm font-medium">{currentStatus}</span>
              </div>
              <div className="flex items-center gap-2">
                {getConnectionIcon()}
                <Badge variant="outline">
                  WebSocket ({wsState})
                </Badge>
                {deploymentStatus && (
                  <Badge variant="outline">
                    狀態: {deploymentStatus.status}
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* WebSocket 控制按鈕 */}
          {isDeploying && (
            <div className="mb-4 flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => sendWebSocketCommand('status')}
                disabled={!wsClientRef.current?.isConnected()}
              >
                查詢狀態
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => wsClientRef.current?.ping()}
                disabled={!wsClientRef.current?.isConnected()}
              >
                發送心跳
              </Button>
            </div>
          )}

          {/* Deployment Logs */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">即時部署日誌：</h3>
              <div className="text-sm text-muted-foreground">
                {logs.length} 條記錄
              </div>
            </div>

            <Card className="h-[400px] bg-slate-900 border-slate-700">
              <div ref={logContainerRef} className="h-full p-4 overflow-y-auto">
                {logs.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-slate-500">
                    <div className="text-center">
                      <Clock className="h-8 w-8 mx-auto mb-2 animate-pulse" />
                      <p>等待部署日誌...</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1 font-mono text-sm">
                    {logs.map((log) => (
                      <div key={log.id} className="flex gap-2 text-slate-300">
                        <span className="text-slate-500 whitespace-nowrap flex-shrink-0">
                          {log.timestamp}
                        </span>
                        <span className={getLogTypeColor(log.type)}>
                          {log.message}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>

        <div className="flex items-center justify-between py-2 border-t border-border">
          <div className="flex items-center gap-4">
            <div className="text-xs text-muted-foreground">
              已用時間：{elapsedTime}
            </div>
            <div className="text-xs text-muted-foreground">
              連線模式：WebSocket
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isDeploymentComplete && (
              <Button
                onClick={() => {
                  onDeploymentComplete();
                  onOpenChange(false);
                }}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                開始考試
              </Button>
            )}
          </div>
        </div>

      </DialogContent>
    </Dialog>
  );
};