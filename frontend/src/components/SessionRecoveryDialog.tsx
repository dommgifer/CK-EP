/**
 * Session 恢復對話框
 * 當偵測到活動中的考試會話時，提示使用者恢復或結束
 */
import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface SessionData {
  id: string;
  question_set_id: string;
  status: string;
  created_at: string;
  start_time: string | null;
}

interface SessionRecoveryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionData: SessionData | null;
  onResumeExam: () => void;
  onStopAndStartNew: () => void;
}

export const SessionRecoveryDialog: React.FC<SessionRecoveryDialogProps> = ({
  open,
  onOpenChange,
  sessionData,
  onResumeExam,
  onStopAndStartNew,
}) => {
  if (!sessionData) return null;

  // 解析題組資訊
  const questionSetParts = sessionData.question_set_id.split('-');
  const examType = questionSetParts[0]?.toUpperCase() || 'CKS';
  const examSet = questionSetParts[1] || '001';

  // 格式化時間
  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '未開始';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  // 狀態顯示
  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      'in_progress': '考試中',
      'created': '已建立',
      'paused': '已暫停',
      'completed': '已完成',
      'timeout': '已逾時',
      'cancelled': '已取消'
    };
    return statusMap[status] || status;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-lg font-bold mb-4">
            發現現有考試會話
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <Card className="p-4 bg-primary/10 border-primary/20">
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="bg-primary text-primary-foreground">
                  考試類型: {examType}
                </Badge>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-primary/30">
                  題組: {examSet}
                </Badge>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-primary/30">
                  狀態: {getStatusText(sessionData.status)}
                </Badge>
              </div>

              <div className="space-y-1 text-xs text-muted-foreground mt-3">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">創建時間:</span>
                  <span className="font-mono">{formatDateTime(sessionData.created_at)}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">開始時間:</span>
                  <span className="font-mono">{formatDateTime(sessionData.start_time)}</span>
                </div>

                <div className="break-all mt-2">
                  <span className="text-muted-foreground">會話 ID:</span>
                  <div className="font-mono text-xs mt-1 p-2 bg-muted rounded">
                    {sessionData.id}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* 按鈕區域：左側停止（紅色邊框），右側恢復（綠色填滿） */}
          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              onClick={onStopAndStartNew}
              className="flex-1 border-red-500 text-red-500 hover:bg-red-50 hover:text-red-600"
            >
              停止並開始新考試
            </Button>

            <Button
              onClick={onResumeExam}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
            >
              恢復並繼續考試
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
