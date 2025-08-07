import React, { useState } from "react";
import { CheckCircle, XCircle, AlertCircle, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface HumanReviewDialogProps {
  /** 是否显示对话框 */
  open: boolean;
  /** interrupt payload数据 */
  payload: any;
  /** 批准回调 */
  onApprove: () => Promise<void>;
  /** 拒绝回调 */
  onReject: () => Promise<void>;
  /** 取消回调 */
  onCancel: () => void;
  /** 是否正在处理中 */
  isLoading: boolean;
}

export const HumanReviewDialog: React.FC<HumanReviewDialogProps> = ({
  open,
  payload,
  onApprove,
  onReject,
  onCancel,
  isLoading,
}) => {
  const [error, setError] = useState<string | null>(null);

  const handleApprove = async () => {
    try {
      setError(null);
      await onApprove();
    } catch (err) {
      const message = err instanceof Error ? err.message : "批准失败";
      setError(message);
    }
  };

  const handleReject = async () => {
    try {
      setError(null);
      await onReject();
    } catch (err) {
      const message = err instanceof Error ? err.message : "拒绝失败";
      setError(message);
    }
  };

  const handleCancel = () => {
    setError(null);
    onCancel();
  };

  return (
    <Dialog open={open} onOpenChange={() => !isLoading && handleCancel()}>
      <DialogContent 
        className="max-w-2xl max-h-[85vh] overflow-y-auto"
        showCloseButton={!isLoading}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            {payload?.title || "人工审核"}
          </DialogTitle>
          <DialogDescription>
            请仔细审核以下信息，确认是否继续执行
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* 审核内容 */}
          {payload?.content && (
            <div className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
              {payload.content}
            </div>
          )}

          {/* 活动信息展示 */}
          {payload?.campaign_info && (
            <Card>
              <CardContent className="pt-4">
                <h4 className="font-medium mb-3 text-foreground">📋 活动基本信息</h4>
                <div className="space-y-2 text-sm">
                  {Object.entries(payload.campaign_info).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-muted-foreground capitalize">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      <span className="text-foreground font-medium">
                        {value !== null && value !== undefined 
                          ? Array.isArray(value) 
                            ? value.join(', ') 
                            : String(value)
                          : '未设置'
                        }
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 错误信息显示 */}
          {error && (
            <Card className="border-destructive/50 bg-destructive/10">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-destructive text-sm">
                  <XCircle className="h-4 w-4" />
                  {error}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
          >
            取消
          </Button>
          
          <Button
            variant="destructive"
            onClick={handleReject}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <XCircle className="h-4 w-4 mr-2" />
            )}
            拒绝 (No)
          </Button>
          
          <Button
            onClick={handleApprove}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-2" />
            )}
            批准 (Yes)
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};