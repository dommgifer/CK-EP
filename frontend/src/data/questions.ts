export interface Question {
  id: number;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  status: 'not-started' | 'in-progress' | 'completed';
  points: number;
  description: string;
  requirements: string[];
  hints: string[];
  marked?: boolean;
}

export const mockQuestions: Question[] = [
  {
    id: 1,
    title: "ETCD Cluster Information",
    difficulty: 'easy',
    status: 'not-started',
    points: 10,
    description: "The cluster admin asked you to find out the following information about etcd running on cluster2-master1:",
    requirements: [
      "Server private key location",
      "Server certificate expiration date",
      "Is client certificate authentication enabled"
    ],
    hints: [
      "使用 kubectl describe 查看 etcd pod 配置",
      "檢查 /etc/kubernetes/manifests/etcd.yaml",
      "使用 openssl 命令查看證書信息"
    ]
  },
  {
    id: 2,
    title: "部署 Apache Deployment 和 Service",
    difficulty: 'medium',
    status: 'not-started',
    points: 15,
    description: "創建 Apache Deployment 並配置對應的 Service 進行負載均衡。",
    requirements: [
      "Deployment 名稱為 apache-deploy",
      "使用 httpd:latest 鏡像",
      "副本數為 3",
      "創建 ClusterIP Service"
    ],
    hints: [
      "使用 kubectl create deployment 命令",
      "Service 需要正確的 selector",
      "檢查 endpoints 是否正確設置"
    ]
  },
  {
    id: 3,
    title: "配置 ConfigMap 和 Secret",
    difficulty: 'medium',
    status: 'not-started',
    points: 20,
    description: "創建 ConfigMap 和 Secret，並在 Pod 中使用它們作為環境變數。",
    requirements: [
      "創建名為 app-config 的 ConfigMap",
      "創建名為 app-secret 的 Secret",
      "在 Pod 中掛載 ConfigMap 和 Secret",
      "驗證環境變數正確設置"
    ],
    hints: [
      "使用 kubectl create configmap 命令",
      "Secret 需要 base64 編碼",
      "使用 envFrom 引用 ConfigMap"
    ]
  },
  {
    id: 4,
    title: "設置 Ingress 路由",
    difficulty: 'hard',
    status: 'not-started',
    points: 25,
    description: "配置 Ingress 控制器並建立路由規則，實現外部訪問。",
    requirements: [
      "部署 nginx-ingress-controller",
      "創建 Ingress 資源",
      "配置 TLS 終止",
      "設置路徑路由規則"
    ],
    hints: [
      "檢查 Ingress Controller 是否運行",
      "使用 TLS secret 配置 HTTPS",
      "注意 annotations 的使用"
    ]
  },
  {
    id: 5,
    title: "實現持久化存儲",
    difficulty: 'hard',
    status: 'not-started',
    points: 20,
    description: "配置 PersistentVolume 和 PersistentVolumeClaim，實現資料持久化。",
    requirements: [
      "創建 2Gi 的 PersistentVolume",
      "創建對應的 PersistentVolumeClaim",
      "在 Pod 中掛載 PVC",
      "驗證資料持久化"
    ],
    hints: [
      "PV 需要指定 storageClassName",
      "PVC 必須匹配 PV 的規格",
      "使用 volumeMounts 掛載到 Pod"
    ]
  },
  {
    id: 6,
    title: "配置 RBAC 權限",
    difficulty: 'hard',
    status: 'not-started',
    points: 30,
    description: "配置基於角色的訪問控制 (RBAC)，限制 ServiceAccount 權限。",
    requirements: [
      "創建 ServiceAccount",
      "定義 Role 和 ClusterRole",
      "建立 RoleBinding",
      "測試權限限制"
    ],
    hints: [
      "最小權限原則",
      "使用 kubectl auth can-i 測試權限",
      "區分 Role 和 ClusterRole 的使用場景"
    ]
  },
  {
    id: 7,
    title: "故障排除與監控",
    difficulty: 'medium',
    status: 'not-started',
    points: 15,
    description: "診斷和修復有問題的 Pod，實施監控和日誌收集。",
    requirements: [
      "識別失敗的 Pod",
      "檢查事件和日誌",
      "修復配置問題",
      "驗證 Pod 正常運行"
    ],
    hints: [
      "使用 kubectl describe 查看詳細信息",
      "kubectl logs 查看容器日誌",
      "檢查資源限制和請求"
    ]
  },
  {
    id: 8,
    title: "網路策略配置",
    difficulty: 'hard',
    status: 'not-started',
    points: 25,
    description: "實施網路策略以控制 Pod 間的通信，提高安全性。",
    requirements: [
      "創建限制性網路策略",
      "允許特定標籤的 Pod 通信",
      "阻止不必要的流量",
      "測試網路隔離效果"
    ],
    hints: [
      "使用 podSelector 選擇目標 Pod",
      "ingress 和 egress 規則的區別",
      "確保 CNI 支持網路策略"
    ]
  }
];

export const examConfig = {
  timeLimit: 120, // 2 hours in minutes
  totalQuestions: mockQuestions.length,
  maxPoints: mockQuestions.reduce((sum, q) => sum + q.points, 0),
  passingScore: 100 // 100 points to pass
};