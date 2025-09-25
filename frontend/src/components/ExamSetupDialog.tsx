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
import { X, Plus, Trash2, Loader2 } from "lucide-react";
import { AddVMDialog } from './AddVMDialog';
import { questionSetApi, type QuestionSetSummary } from '@/services/questionSetApi';

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

  const handleAddVM = (vmConfig: any) => {
    console.log('New VM config:', vmConfig);
    // TODO: Add VM to list
  };

  const examTypes = [
    { value: "CKS", label: "CKS - Certified Kubernetes Security Specialist" },
    { value: "CKA", label: "CKA - Certified Kubernetes Administrator" },
    { value: "CKAD", label: "CKAD - Certified Kubernetes Application Developer" }
  ];

  const [vmConfig, setVmConfig] = useState("lab");

  const vmOptions = [
    { value: "lab", label: "lab (192.168.1.60:22)" }
  ];

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
            
            <Select value={vmConfig} onValueChange={setVmConfig}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="選擇 VM" />
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
            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">已配置的 VM：</p>
              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-md border">
                <span className="text-sm text-foreground">lab - 192.168.1.60:22</span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="text-sm">
                    測試連線
                  </Button>
                  <Button variant="destructive" size="sm" className="text-sm">
                    <Trash2 className="h-4 w-4 mr-1" />
                    刪除
                  </Button>
                </div>
              </div>
            </div>
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