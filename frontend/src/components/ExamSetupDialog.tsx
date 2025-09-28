import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { X, Plus, Trash2, Loader2, Check, AlertCircle } from "lucide-react";
import { AddVMDialog } from './AddVMDialog';
import { questionSetApi, type QuestionSetSummary } from '@/services/questionSetApi';
import { vmConfigApi, type VMConfig } from '@/services/vmConfigApi';

interface ExamSetupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStartDeployment: () => void;
}

export const ExamSetupDialog: React.FC<ExamSetupDialogProps> = ({
  open,
  onOpenChange,
  onStartDeployment
}) => {
  const [examType, setExamType] = useState("CKS");
  const [examSet, setExamSet] = useState("");
  const [showAddVMDialog, setShowAddVMDialog] = useState(false);
  const [questionSets, setQuestionSets] = useState<QuestionSetSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vmConfigs, setVmConfigs] = useState<VMConfig[]>([]);
  const [vmLoading, setVmLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{
    status: 'idle' | 'success' | 'error';
    message?: string;
    successNodes?: number;
    totalNodes?: number;
  }>({ status: 'idle' });

  // 載入題組數據
  const loadQuestionSets = async (examType: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await questionSetApi.getAll({ exam_type: examType });
      setQuestionSets(response.question_sets);

      // 如果有題組，預設選中第一個
      if (response.question_sets.length > 0) {
        const setId = `${response.question_sets[0].exam_type.toLowerCase()}-${response.question_sets[0].set_id}`;
        setExamSet(setId);
      } else {
        // 如果沒有題組，確保清空選擇
        setExamSet("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '載入題組失敗');
      setQuestionSets([]);
    } finally {
      setLoading(false);
    }
  };

  // 監聽考試類型變化，重新載入題組
  useEffect(() => {
    if (open && examType) {
      loadQuestionSets(examType);
    }
  }, [examType, open]);

  // 監聽對話框開啟，載入 VM 配置
  useEffect(() => {
    if (open) {
      loadVMConfigs();
    }
  }, [open]);

  // 監聽 examType 變化，重設 examSet
  const handleExamTypeChange = (newExamType: string) => {
    setExamType(newExamType);
    setExamSet(""); // 重設題組選擇
    setQuestionSets([]); // 立即清空題組列表
  };

  const handleStartDeployment = () => {
    onStartDeployment();
    onOpenChange(false);
  };

  const handleAddVM = async (vmConfigData: any) => {
    try {
      await vmConfigApi.create(vmConfigData);
      await loadVMConfigs(); // 重新載入 VM 配置列表
      console.log('VM config created successfully');
    } catch (error) {
      console.error('Failed to create VM config:', error);
    }
  };

  // 載入 VM 配置列表
  const loadVMConfigs = async () => {
    setVmLoading(true);
    try {
      const configs = await vmConfigApi.getAll();
      setVmConfigs(configs);
      // 如果有配置，選中第一個
      if (configs.length > 0) {
        setVmConfig(configs[0].id);
      } else {
        setVmConfig('');
      }
    } catch (error) {
      console.error('Failed to load VM configs:', error);
      setVmConfigs([]);
    } finally {
      setVmLoading(false);
    }
  };

  // 測試 VM 連線
  const handleTestConnection = async () => {
    if (!vmConfig) return;

    setTestingConnection(true);
    setConnectionStatus({ status: 'idle' });

    try {
      const result = await vmConfigApi.testConnection(vmConfig);
      if (result.success) {
        setConnectionStatus({
          status: 'success',
          message: '連線成功',
          successNodes: result.successful_nodes,
          totalNodes: result.total_nodes
        });
      } else {
        setConnectionStatus({
          status: 'error',
          message: result.message || '連線失敗'
        });
      }
    } catch (error) {
      setConnectionStatus({
        status: 'error',
        message: error instanceof Error ? error.message : '未知錯誤'
      });
    } finally {
      setTestingConnection(false);
    }
  };

  // 刪除 VM 配置
  const handleDeleteVM = async () => {
    if (!vmConfig) return;

    if (confirm('確定要刪除此 VM 配置嗎？此操作無法復原。')) {
      try {
        await vmConfigApi.delete(vmConfig);
        await loadVMConfigs(); // 重新載入列表
        alert('VM 配置已刪除');
      } catch (error) {
        alert(`刪除失敗：${error instanceof Error ? error.message : '未知錯誤'}`);
      }
    }
  };

  const examTypes = [
    { value: "CKS", label: "CKS - Certified Kubernetes Security Specialist" },
    { value: "CKA", label: "CKA - Certified Kubernetes Administrator" },
    { value: "CKAD", label: "CKAD - Certified Kubernetes Application Developer" }
  ];

  const [vmConfig, setVmConfig] = useState("");

  // 動態生成 VM 選項
  const vmOptions = vmConfigs.map(config => {
    const masterNode = config.nodes.find(node => node.role === 'master');
    const workerNode = config.nodes.find(node => node.role === 'worker');
    const ips = [masterNode?.ip, workerNode?.ip].filter(Boolean).join(', ');
    return {
      value: config.id,
      label: `${config.name} (${ips})`
    };
  });

  // 獲取當前選中的 VM 配置
  const currentVMConfig = vmConfigs.find(config => config.id === vmConfig);

  // 根據選中的題組 ID 找到對應的題組資料
  const currentExamSet = questionSets.find(set => {
    const setId = `${set.exam_type.toLowerCase()}-${set.set_id}`;
    return setId === examSet;
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-background border border-border">
        <DialogHeader className="space-y-4">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-2xl font-bold text-foreground">
              Kubernetes 考試設定
            </DialogTitle>
            <Button
              variant="ghost" 
              size="icon"
              onClick={() => onOpenChange(false)}
              className="h-8 w-8 rounded-full hover:bg-muted"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* 考試類型選擇 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              考試類型
            </label>
            <Select value={examType} onValueChange={handleExamTypeChange}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="選擇考試類型" />
              </SelectTrigger>
              <SelectContent>
                {examTypes.map(type => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 題組選擇 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              題組選擇
            </label>
            <Select value={examSet} onValueChange={setExamSet} disabled={loading}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder={loading ? "載入中..." : "選擇題組"} />
                {loading && <Loader2 className="h-4 w-4 animate-spin ml-2" />}
              </SelectTrigger>
              <SelectContent>
                {questionSets.map(set => {
                  const setId = `${set.exam_type.toLowerCase()}-${set.set_id}`;
                  return (
                    <SelectItem key={setId} value={setId}>
                      {set.name}
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
            {error && (
              <p className="text-sm text-red-500">
                {error}
              </p>
            )}
          </div>

          {/* 考試描述 */}
          {currentExamSet && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                描述：{currentExamSet.description}
              </p>
              <p className="text-sm text-muted-foreground">
                題目數量：{currentExamSet.total_questions}
              </p>
              <p className="text-sm text-muted-foreground">
                考試時間：{currentExamSet.time_limit} 分鐘
              </p>
              <p className="text-sm text-muted-foreground">
                及格分數：{currentExamSet.passing_score}%
              </p>
            </div>
          )}

          {!currentExamSet && examSet && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                請選擇題組以查看詳細資訊
              </p>
            </div>
          )}

          {/* VM 配置 */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-foreground">
                VM 配置
              </label>
              <Button 
                variant="outline" 
                size="sm" 
                className="text-sm"
                onClick={() => setShowAddVMDialog(true)}
              >
                <Plus className="h-4 w-4 mr-1" />
                新增 VM
              </Button>
            </div>
            
            <Select
              value={vmConfig}
              onValueChange={(value) => {
                setVmConfig(value);
                setConnectionStatus({ status: 'idle' });
              }}
              disabled={vmLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={vmLoading ? "載入中..." : "選擇 VM"} />
                {vmLoading && <Loader2 className="h-4 w-4 animate-spin ml-2" />}
              </SelectTrigger>
              <SelectContent>
                {vmOptions.map(vm => (
                  <SelectItem key={vm.value} value={vm.value}>
                    {vm.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* 已配置的 VM */}
            {currentVMConfig && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground">已配置的 VM：</p>
                <div className="flex items-center justify-between p-3 bg-muted/30 rounded-md border">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-foreground">
                      {currentVMConfig.name}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 space-y-0.5">
                      <div>Master: {currentVMConfig.nodes.find(n => n.role === 'master')?.ip}</div>
                      <div>Worker: {currentVMConfig.nodes.find(n => n.role === 'worker')?.ip}</div>
                    </div>
                    {currentVMConfig.description && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {currentVMConfig.description}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {/* 測試連線按鈕和狀態 */}
                    <div className="flex items-center gap-2">
                      {/* 連線狀態指示器 - 顯示在測試連線按鈕左邊 */}
                      {connectionStatus.status === 'success' && (
                        <div className="flex items-center gap-1 text-green-600">
                          <Check className="h-4 w-4" />
                          <span className="text-sm">連線成功</span>
                        </div>
                      )}

                      {connectionStatus.status === 'error' && (
                        <div className="flex items-center gap-1 text-red-600">
                          <AlertCircle className="h-4 w-4" />
                          <span className="text-sm">連線失敗</span>
                        </div>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        className="text-sm"
                        onClick={handleTestConnection}
                        disabled={testingConnection}
                      >
                        {testingConnection ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin mr-1" />
                            測試中
                          </>
                        ) : (
                          '測試連線'
                        )}
                      </Button>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="text-sm"
                      onClick={handleDeleteVM}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      刪除
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {vmConfigs.length === 0 && !vmLoading && (
              <div className="text-center py-4 text-muted-foreground">
                <p className="text-sm">尚未配置任何 VM</p>
                <p className="text-xs mt-1">點擊 "新增 VM" 開始配置</p>
              </div>
            )}
          </div>
        </div>

        {/* 底部按鈕 */}
        <div className="flex justify-end gap-3 pt-4 border-t border-border">
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            className="px-6"
          >
            取消
          </Button>
          <Button 
            onClick={handleStartDeployment}
            className="px-8 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            建立考試環境
          </Button>
        </div>
      </DialogContent>
      
      <AddVMDialog 
        open={showAddVMDialog}
        onOpenChange={setShowAddVMDialog}
        onAddVM={handleAddVM}
      />
    </Dialog>
  );
};