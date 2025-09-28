import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";
// import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Rocket, Settings, X, CheckCircle2, Clock } from "lucide-react";

interface DeploymentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeploymentComplete: () => void;
}

interface DeploymentStep {
  id: number;
  title: string;
  status: 'pending' | 'in-progress' | 'completed';
}

interface DeploymentLog {
  id: number;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  raw?: string; // 原始 Ansible 輸出
}

export const DeploymentDialog: React.FC<DeploymentDialogProps> = ({
  open,
  onOpenChange,
  onDeploymentComplete
}) => {
  const [progress, setProgress] = useState(0);
  const [currentStatus, setCurrentStatus] = useState("準備中...");
  const [steps, setSteps] = useState<DeploymentStep[]>([
    { id: 1, title: "準備SSH連接", status: 'pending' },
    { id: 2, title: "驗證VM環境", status: 'pending' },
    { id: 3, title: "安裝Docker和依賴", status: 'pending' },
    { id: 4, title: "配置防火牆規則", status: 'pending' },
    { id: 5, title: "下載Kubernetes映像", status: 'pending' },
    { id: 6, title: "初始化Master節點", status: 'pending' },
    { id: 7, title: "配置網路插件", status: 'pending' },
    { id: 8, title: "加入Worker節點", status: 'pending' },
    { id: 9, title: "驗證集群狀態", status: 'pending' }
  ]);
  const [logs, setLogs] = useState<DeploymentLog[]>([
    { id: 1, timestamp: "下午7:32:35", type: 'info', message: "TASK [kubernetes/preinstall : Stat systemctl file configuration] **********************" },
    { id: 2, timestamp: "下午7:32:35", type: 'info', message: "task path: /kubespray/roles/kubernetes/preinstall/tasks/0080-system-configurations.yml:47" },
    { id: 3, timestamp: "10:22:40", type: 'info', message: "準備SSH連接 - 執行中..." },
    { id: 4, timestamp: "10:22:42", type: 'success', message: "驗證VM環境 - 執行中..." },
    { id: 5, timestamp: "10:22:44", type: 'info', message: "安裝Docker和依賴 - 執行中..." },
    { id: 6, timestamp: "10:22:46", type: 'info', message: "配置防火牆規則 - 執行中..." },
    { id: 7, timestamp: "10:22:48", type: 'info', message: "下載Kubernetes映像 - 執行中..." },
    { id: 8, timestamp: "10:22:50", type: 'info', message: "初始化Master節點 - 執行中..." },
    { id: 9, timestamp: "10:22:52", type: 'info', message: "配置網路插件 - 執行中..." },
    { id: 10, timestamp: "10:22:54", type: 'info', message: "加入Worker節點 - 執行中..." }
  ]);

  const [isDeploying, setIsDeploying] = useState(false);
  const [isDeploymentComplete, setIsDeploymentComplete] = useState(false);

  // TODO: 替換為真實的 WebSocket 或 Server-Sent Events 連接
  useEffect(() => {
    if (open && !isDeploying && !isDeploymentComplete) {
      const timer = setTimeout(() => {
        setIsDeploying(true);
        // TODO: 這裡將改為調用真實的部署 API
        simulateDeployment();
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [open, isDeploying, isDeploymentComplete]);

  // TODO: 實際的部署函數，將連接到真實的 API
  const startRealDeployment = async () => {
    setIsDeploying(true);
    setCurrentStatus("正在啟動部署...");

    try {
      // TODO: 實際的 API 調用
      // const response = await fetch('/api/v1/exam-sessions/{id}/deploy', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' }
      // });

      // TODO: 建立 WebSocket 或 Server-Sent Events 連接來接收即時日誌
      // const eventSource = new EventSource('/api/v1/exam-sessions/{id}/deployment-logs');
      // eventSource.onmessage = (event) => {
      //   const logData = JSON.parse(event.data);
      //   addLogEntry(logData);
      // };

    } catch (error) {
      console.error('部署啟動失敗:', error);
      setCurrentStatus("部署啟動失敗");
    }
  };

  // 添加新的日誌條目
  const addLogEntry = (logEntry: Omit<DeploymentLog, 'id'>) => {
    setLogs(prev => [...prev, { ...logEntry, id: Date.now() + Math.random() }]);
  };

  const startDeployment = () => {
    setIsDeploying(true);
    simulateDeployment();
  };

  const simulateDeployment = () => {
    let currentStep = 0;
    const totalSteps = steps.length;
    
    const interval = setInterval(() => {
      if (currentStep < totalSteps) {
        // Update current step to in-progress
        setSteps(prev => prev.map(step => 
          step.id === currentStep + 1 
            ? { ...step, status: 'in-progress' }
            : step.id < currentStep + 1
            ? { ...step, status: 'completed' }
            : step
        ));
        
        setCurrentStatus(`正在執行: ${steps[currentStep].title}`);
        setProgress(((currentStep + 1) / totalSteps) * 100);
        
        // Add random logs
        const newLog: DeploymentLog = {
          id: logs.length + Math.random(),
          timestamp: new Date().toLocaleTimeString('zh-TW', { hour12: false }),
          type: Math.random() > 0.8 ? 'success' : 'info',
          message: `${steps[currentStep].title} - 執行中...`
        };
        
        setLogs(prev => [...prev, newLog]);
        
        currentStep++;
      } else {
        // Complete all steps
        setSteps(prev => prev.map(step => ({ ...step, status: 'completed' })));
        setCurrentStatus("部署完成！");
        setProgress(100);
        clearInterval(interval);
        
        setTimeout(() => {
          setIsDeploymentComplete(true);
          setCurrentStatus("Kubernetes 集群部署完成！準備開始考試");
          const finalLog: DeploymentLog = {
            id: logs.length + Math.random(),
            timestamp: new Date().toLocaleTimeString('zh-TW', { hour12: false }),
            type: 'success',
            message: "✅ Kubernetes 集群部署成功！所有節點運行正常，準備開始考試..."
          };
          setLogs(prev => [...prev, finalLog]);
          
          // Auto-transition to exam after 2 seconds
          setTimeout(() => {
            onDeploymentComplete();
            onOpenChange(false);
          }, 2000);
        }, 1000);
      }
    }, 2000);
  };

  const getStepIcon = (status: DeploymentStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'in-progress':
        return <Clock className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-muted-foreground" />;
    }
  };

  const getLogTypeColor = (type: DeploymentLog['type']) => {
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] bg-background border border-border">
        <DialogHeader className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Rocket className="h-6 w-6 text-blue-500" />
              <DialogTitle className="text-2xl font-bold text-foreground">
                正在部屬 Kubernetes 集群
              </DialogTitle>
            </div>
            <Button
              variant="ghost" 
              size="icon"
              onClick={() => onOpenChange(false)}
              className="h-8 w-8 rounded-full hover:bg-muted"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="space-y-2">
            <p className="text-muted-foreground">
              請稍候，正在為您的考試環境部署 Kubernetes 集群...
            </p>
          </div>
        </DialogHeader>

        <div className="py-4">
          {/* Deployment Logs */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">部署紀錄：</h3>
            </div>
            
            <Card className="h-[400px] bg-slate-900 border-slate-700">
              <div className="h-full p-4 overflow-y-auto">
                <div className="space-y-1 font-mono text-sm">
                  {logs.map((log) => (
                    <div key={log.id} className="flex gap-2 text-slate-300">
                      <span className="text-slate-500 whitespace-nowrap">
                        {log.timestamp}
                      </span>
                      <span className={getLogTypeColor(log.type)}>
                        {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        </div>

        <div className="flex items-center justify-end py-2 border-t border-border">
          <div className="flex items-center gap-4">
            <div className="text-xs text-muted-foreground">
              已用時間：0:28
            </div>
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