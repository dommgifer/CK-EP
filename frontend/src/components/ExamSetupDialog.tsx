import React, { useState } from 'react';
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
import { X, Plus, Trash2 } from "lucide-react";
import { AddVMDialog } from './AddVMDialog';

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
  const [examSet, setExamSet] = useState("CKS-001");
  const [showAddVMDialog, setShowAddVMDialog] = useState(false);

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

  const examSets = [
    { 
      value: "CKS-001", 
      label: "CKS 模擬測驗 001 - 基礎安全強化",
      description: "涵蓋完整的 CKS 考試主題，包含 Pod Security、Network Policies、RBAC、系統強化、運行時安全等",
      questions: 15,
      time: 120
    },
    { 
      value: "CKS-002", 
      label: "CKS 模擬測驗 002 - 進階安全管理",
      description: "進階安全場景，包含複雜的網絡策略配置、映像安全掃描、運行時威脅檢測等實務操作",
      questions: 24,
      time: 120
    }
  ];

  const vmOptions = [
    { value: "lab", label: "lab (192.168.1.60:22)" }
  ];

  const currentExamSet = examSets.find(set => set.value === examSet) || examSets[0];

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
            <Select value={examType} onValueChange={setExamType}>
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
            <Select value={examSet} onValueChange={setExamSet}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="選擇題組" />
              </SelectTrigger>
              <SelectContent>
                {examSets.map(set => (
                  <SelectItem key={set.value} value={set.value}>
                    {set.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 考試描述 */}
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              描述：{currentExamSet.description}
            </p>
            <p className="text-sm text-muted-foreground">
              題目數量：{currentExamSet.questions}
            </p>
            <p className="text-sm text-muted-foreground">
              考試時間：{currentExamSet.time} 分鐘
            </p>
          </div>

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