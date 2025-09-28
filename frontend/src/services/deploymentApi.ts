/**
 * 部署API服務
 * 處理考試環境部署相關的API呼叫
 */

import { vmConfigApi } from './vmConfigApi';

// 部署相關的類型定義
export interface ExamSessionCreate {
  question_set_id: string;
  vm_config_id: string;
  exam_type: string;
}

export interface ExamSessionResponse {
  id: string;
  question_set_id: string;
  vm_config_id: string;
  exam_type: string;
  status: 'created' | 'deploying' | 'ready' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  current_question_index?: number;
  time_elapsed?: number;
}

export interface DeployRequest {
  playbook?: string;
}

export interface DeploymentResponse {
  session_id: string;
  status: string;
  playbook: string;
  log_stream_url: string;
  started_at: string;
}

export interface DeploymentStatus {
  session_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  playbook: string;
  started_at: string;
  completed_at?: string;
  exit_code?: number;
}

export interface GenerateInventoryRequest {
  session_id: string;
  vm_config: any;
  question_set_id?: string;
}

export interface DeploymentLogEntry {
  id: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  raw?: string;
}

class DeploymentApiService {
  private baseUrl = '/api/v1';

  /**
   * 建立考試會話
   */
  async createExamSession(data: ExamSessionCreate): Promise<ExamSessionResponse> {
    const response = await fetch(`${this.baseUrl}/exam-sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '建立考試會話失敗');
    }

    return response.json();
  }

  /**
   * 取得考試會話詳細資訊
   */
  async getExamSession(sessionId: string): Promise<ExamSessionResponse> {
    const response = await fetch(`${this.baseUrl}/exam-sessions/${sessionId}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '取得考試會話失敗');
    }

    return response.json();
  }

  /**
   * 生成 Kubespray inventory 配置
   */
  async generateInventory(sessionId: string, vmConfigId: string, questionSetId?: string): Promise<any> {
    // 先取得VM配置詳細資料
    const vmConfig = await vmConfigApi.getById(vmConfigId);

    // 移除可能造成序列化問題的 datetime 欄位
    const cleanVmConfig = {
      ...vmConfig,
      created_at: undefined,
      updated_at: undefined,
      last_tested_at: undefined,
    };

    const requestData: GenerateInventoryRequest = {
      session_id: sessionId,
      vm_config: cleanVmConfig,
      question_set_id: questionSetId,
    };

    const response = await fetch(`${this.baseUrl}/exam-sessions/${sessionId}/kubespray/inventory`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '生成 Kubespray 配置失敗');
    }

    return response.json();
  }

  /**
   * 啟動 Kubespray 部署
   */
  async startDeployment(sessionId: string, request: DeployRequest = {}): Promise<DeploymentResponse> {
    const response = await fetch(`${this.baseUrl}/exam-sessions/${sessionId}/kubespray/deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '啟動部署失敗');
    }

    return response.json();
  }

  /**
   * 查詢部署狀態
   */
  async getDeploymentStatus(sessionId: string): Promise<DeploymentStatus> {
    const response = await fetch(`${this.baseUrl}/exam-sessions/${sessionId}/kubespray/deploy/status`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '查詢部署狀態失敗');
    }

    return response.json();
  }

  /**
   * 建立 SSE 連線來接收即時部署日誌
   */
  createLogStream(sessionId: string): EventSource {
    const url = `${this.baseUrl}/exam-sessions/${sessionId}/kubespray/deploy/logs/stream`;
    return new EventSource(url);
  }

  /**
   * 解析 SSE 資料為日誌條目
   */
  parseLogEntry(data: string, timestamp?: string): DeploymentLogEntry {
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
   * 完整的部署流程：建立會話 -> 生成配置 -> 啟動部署
   */
  async startFullDeployment(params: {
    examType: string;
    examSet: string;
    vmConfigId: string;
  }): Promise<{ session: ExamSessionResponse; deployment: DeploymentResponse }> {
    try {
      // 1. 建立考試會話
      const session = await this.createExamSession({
        question_set_id: params.examSet,
        vm_config_id: params.vmConfigId,
        exam_type: params.examType,
      });

      // 2. 生成 Kubespray inventory
      await this.generateInventory(session.id, params.vmConfigId, params.examSet);

      // 3. 啟動部署
      const deployment = await this.startDeployment(session.id);

      return { session, deployment };
    } catch (error) {
      console.error('完整部署流程失敗:', error);
      throw error;
    }
  }
}

export const deploymentApi = new DeploymentApiService();