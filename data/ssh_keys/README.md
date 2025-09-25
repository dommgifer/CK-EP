# SSH 金鑰管理說明

## 使用方式

1. 將您的 SSH 私鑰放置在此目錄下，命名為 `id_rsa`
2. 確保私鑰權限設定為 600：
   ```bash
   chmod 600 data/ssh_keys/id_rsa
   ```

## 範例

```bash
# 生成新的 SSH 金鑰對
ssh-keygen -t rsa -b 2048 -f data/ssh_keys/id_rsa

# 將公鑰安裝到目標 VM
ssh-copy-id -i data/ssh_keys/id_rsa.pub ubuntu@192.168.1.100

# 測試連線
ssh -i data/ssh_keys/id_rsa ubuntu@192.168.1.100
```

## 注意事項

- 私鑰將被掛載到容器內的 `/root/.ssh/id_rsa` 路徑
- 請確保目標 VM 已安裝對應的公鑰
- 系統不會自動管理 SSH 金鑰的分發和輪換