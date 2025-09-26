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
import { X, Loader2, Info } from "lucide-react";

interface VMConfigData {
  name: string;
  description?: string;
  nodes: {
    name: string;
    ip: string;
    role: 'master' | 'worker';
  }[];
  ssh_config: {
    user: string;
    port: number;
    private_key_path: string;
  };
}

interface AddVMDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddVM: (vmConfig: VMConfigData) => void;
}

export const AddVMDialog: React.FC<AddVMDialogProps> = ({
  open,
  onOpenChange,
  onAddVM
}) => {
  const [configName, setConfigName] = useState("");
  const [masterName, setMasterName] = useState("k8s-master");
  const [masterIP, setMasterIP] = useState("");
  const [workerName, setWorkerName] = useState("k8s-worker");
  const [workerIP, setWorkerIP] = useState("");
  const [sshUser, setSshUser] = useState("ubuntu");
  const [sshPort, setSshPort] = useState("22");
  const [sshKeyPath, setSshKeyPath] = useState("/root/.ssh/id_rsa");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!configName || !masterIP || !workerIP) {
      alert('請填寫所有必填欄位');
      return;
    }

    if (masterIP === workerIP) {
      alert('Master 和 Worker 節點的 IP 位址不能相同');
      return;
    }

    setIsSubmitting(true);

    try {
      const vmConfig: VMConfigData = {
        name: configName,
        description: description || undefined,
        nodes: [
          {
            name: masterName,
            ip: masterIP,
            role: 'master'
          },
          {
            name: workerName,
            ip: workerIP,
            role: 'worker'
          }
        ],
        ssh_config: {
          user: sshUser,
          port: parseInt(sshPort),
          private_key_path: sshKeyPath
        }
      };

      await onAddVM(vmConfig);
      onOpenChange(false);
      resetForm();
    } catch (error) {
      alert(`建立 VM 配置失敗：${error instanceof Error ? error.message : '未知錯誤'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setConfigName("");
    setMasterName("k8s-master");
    setMasterIP("");
    setWorkerName("k8s-worker");
    setWorkerIP("");
    setSshUser("ubuntu");
    setSshPort("22");
    setSshKeyPath("/root/.ssh/id_rsa");
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

          {/* Master 節點配置 */}
          <div className="space-y-4 p-4 bg-muted/20 rounded-lg border">
            <h3 className="text-sm font-medium text-foreground">🖥️ Master 節點</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="masterName" className="text-xs font-medium text-foreground">
                  節點名稱
                </Label>
                <Input
                  id="masterName"
                  value={masterName}
                  onChange={(e) => setMasterName(e.target.value)}
                  placeholder="k8s-master"
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="masterIP" className="text-xs font-medium text-foreground">
                  IP 位址 *
                </Label>
                <Input
                  id="masterIP"
                  value={masterIP}
                  onChange={(e) => setMasterIP(e.target.value)}
                  placeholder="192.168.1.60"
                  className="w-full"
                  required
                />
              </div>
            </div>
          </div>

          {/* Worker 節點配置 */}
          <div className="space-y-4 p-4 bg-muted/20 rounded-lg border">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-foreground">💼 Worker 節點</h3>
              <Info
                className="h-4 w-4 text-muted-foreground cursor-help"
                title="系統限定為 1 個 Master + 1 個 Worker 節點架構"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="workerName" className="text-xs font-medium text-foreground">
                  節點名稱
                </Label>
                <Input
                  id="workerName"
                  value={workerName}
                  onChange={(e) => setWorkerName(e.target.value)}
                  placeholder="k8s-worker"
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="workerIP" className="text-xs font-medium text-foreground">
                  IP 位址 *
                </Label>
                <Input
                  id="workerIP"
                  value={workerIP}
                  onChange={(e) => setWorkerIP(e.target.value)}
                  placeholder="192.168.1.61"
                  className="w-full"
                  required
                />
              </div>
            </div>
          </div>

          {/* SSH 配置 */}
          <div className="space-y-4 p-4 bg-muted/20 rounded-lg border">
            <h3 className="text-sm font-medium text-foreground">🔐 SSH 配置</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="sshUser" className="text-xs font-medium text-foreground">
                  SSH 使用者
                </Label>
                <Input
                  id="sshUser"
                  value={sshUser}
                  onChange={(e) => setSshUser(e.target.value)}
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sshPort" className="text-xs font-medium text-foreground">
                  SSH 埠號
                </Label>
                <Input
                  id="sshPort"
                  type="number"
                  value={sshPort}
                  onChange={(e) => setSshPort(e.target.value)}
                  className="w-full"
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="sshKeyPath" className="text-xs font-medium text-foreground">
                  SSH 私鑰路徑
                </Label>
                <Info
                  className="h-3 w-3 text-muted-foreground cursor-help"
                  title="私鑰路徑固定為 container 內部路徑，請將私鑰放置於 host 的 data/ssh_keys/id_rsa"
                />
              </div>
              <Input
                id="sshKeyPath"
                value={sshKeyPath}
                onChange={(e) => setSshKeyPath(e.target.value)}
                className="w-full"
                readOnly
              />
            </div>
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
            disabled={!configName || !masterIP || !workerIP || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                建立中...
              </>
            ) : (
              '新增'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};