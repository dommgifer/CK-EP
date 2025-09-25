import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { X } from "lucide-react";

interface AddVMDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddVM: (vmConfig: any) => void;
}

export const AddVMDialog: React.FC<AddVMDialogProps> = ({
  open,
  onOpenChange,
  onAddVM
}) => {
  const [configName, setConfigName] = useState("");
  const [masterIP, setMasterIP] = useState("");
  const [workerIPs, setWorkerIPs] = useState("");
  const [sshUser, setSshUser] = useState("ubuntu");
  const [sshPort, setSshPort] = useState("22");
  const [authMethod, setAuthMethod] = useState("ssh-key");
  const [sshKeyPath, setSshKeyPath] = useState("/app/ssh-keys/exam-key");
  const [description, setDescription] = useState("");

  const handleSubmit = () => {
    const vmConfig = {
      name: configName,
      masterIP,
      workerIPs: workerIPs.split('\n').filter(ip => ip.trim()),
      sshUser,
      sshPort,
      authMethod,
      sshKeyPath,
      description
    };
    onAddVM(vmConfig);
    onOpenChange(false);
    // Reset form
    setConfigName("");
    setMasterIP("");
    setWorkerIPs("");
    setSshUser("ubuntu");
    setSshPort("22");
    setAuthMethod("ssh-key");
    setSshKeyPath("/app/ssh-keys/exam-key");
    setDescription("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl bg-background border border-border">
        <DialogHeader className="space-y-4">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-bold text-foreground">
              新增 VM 配置
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

        <div className="space-y-4 py-4">
          {/* 配置名稱 */}
          <div className="space-y-2">
            <Label htmlFor="configName" className="text-sm font-medium text-foreground">
              配置名稱
            </Label>
            <Input
              id="configName"
              value={configName}
              onChange={(e) => setConfigName(e.target.value)}
              placeholder="例：生產環境 VM"
              className="w-full"
            />
          </div>

          {/* Master 節點 IP */}
          <div className="space-y-2">
            <Label htmlFor="masterIP" className="text-sm font-medium text-foreground">
              Master 節點 IP
            </Label>
            <Input
              id="masterIP"
              value={masterIP}
              onChange={(e) => setMasterIP(e.target.value)}
              placeholder="例：192.168.1.100"
              className="w-full"
            />
          </div>

          {/* Worker 節點 IP */}
          <div className="space-y-2">
            <Label htmlFor="workerIPs" className="text-sm font-medium text-foreground">
              Worker 節點 IP (每行一個)
            </Label>
            <Textarea
              id="workerIPs"
              value={workerIPs}
              onChange={(e) => setWorkerIPs(e.target.value)}
              placeholder="192.168.1.101&#10;192.168.1.102"
              className="w-full min-h-[80px]"
            />
            <p className="text-xs text-muted-foreground">至少需要一個 Worker 節點</p>
          </div>

          {/* SSH 使用者 */}
          <div className="space-y-2">
            <Label htmlFor="sshUser" className="text-sm font-medium text-foreground">
              SSH 使用者
            </Label>
            <Input
              id="sshUser"
              value={sshUser}
              onChange={(e) => setSshUser(e.target.value)}
              className="w-full"
            />
          </div>

          {/* SSH 埠號 */}
          <div className="space-y-2">
            <Label htmlFor="sshPort" className="text-sm font-medium text-foreground">
              SSH 埠號
            </Label>
            <Input
              id="sshPort"
              value={sshPort}
              onChange={(e) => setSshPort(e.target.value)}
              className="w-full"
            />
          </div>

          {/* 認證方式 */}
          <div className="space-y-3">
            <Label className="text-sm font-medium text-foreground">認證方式</Label>
            <RadioGroup
              value={authMethod}
              onValueChange={setAuthMethod}
              className="flex gap-6"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="ssh-key" id="ssh-key" />
                <Label htmlFor="ssh-key" className="text-sm text-foreground">SSH 密鑰</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="password" id="password" />
                <Label htmlFor="password" className="text-sm text-foreground">帳號密碼</Label>
              </div>
            </RadioGroup>
          </div>

          {/* SSH 私鑰路徑 */}
          <div className="space-y-2">
            <Label htmlFor="sshKeyPath" className="text-sm font-medium text-foreground">
              SSH 私鑰路徑
            </Label>
            <Input
              id="sshKeyPath"
              value={sshKeyPath}
              onChange={(e) => setSshKeyPath(e.target.value)}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">請提供 SSH 私鑰的完整路徑</p>
          </div>

          {/* 描述 */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-sm font-medium text-foreground">
              描述 (選填)
            </Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="此配置的說明..."
              className="w-full min-h-[60px]"
            />
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
            onClick={handleSubmit}
            className="px-8 bg-primary hover:bg-primary/90 text-primary-foreground"
            disabled={!configName || !masterIP || !workerIPs.trim()}
          >
            新增
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};