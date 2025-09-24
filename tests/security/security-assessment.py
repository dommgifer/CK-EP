#!/usr/bin/env python3
"""
安全性評估和滲透測試腳本
對 Kubernetes 考試模擬器進行基本的安全檢查
"""

import asyncio
import json
import sys
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class SecurityAssessment:
    """安全評估工具"""

    def __init__(self):
        self.base_url = "http://localhost"
        self.api_url = f"{self.base_url}/api/v1"
        self.vulnerabilities = []
        self.recommendations = []

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    def log_vulnerability(self, severity: str, category: str, description: str, details: str = ""):
        """記錄安全漏洞"""
        self.vulnerabilities.append({
            "severity": severity,
            "category": category,
            "description": description,
            "details": details
        })

        color = {
            "critical": "red",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
            "info": "white"
        }.get(severity.lower(), "white")

        console.print(f"  [{color}]{severity.upper()}[/{color}] {category}: {description}")
        if details:
            console.print(f"    詳情: {details}")

    def add_recommendation(self, category: str, recommendation: str):
        """添加安全建議"""
        self.recommendations.append({
            "category": category,
            "recommendation": recommendation
        })

    async def check_http_headers(self) -> None:
        """檢查 HTTP 安全標頭"""
        console.print("\n[bold]1. HTTP 安全標頭檢查[/bold]")

        try:
            response = await self.http_client.get(self.base_url)
            headers = response.headers

            # 檢查安全標頭
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,  # HTTPS only
                "Content-Security-Policy": None,
                "Referrer-Policy": None
            }

            for header, expected in security_headers.items():
                header_value = headers.get(header)

                if not header_value:
                    severity = "medium" if header in ["X-Content-Type-Options", "X-Frame-Options"] else "low"
                    self.log_vulnerability(
                        severity,
                        "缺少安全標頭",
                        f"缺少 {header} 標頭",
                        "建議添加適當的安全標頭以防止 XSS、點擊劫持等攻擊"
                    )
                elif expected and isinstance(expected, list):
                    if header_value not in expected:
                        self.log_vulnerability(
                            "low",
                            "安全標頭配置",
                            f"{header} 值可能不安全",
                            f"當前值: {header_value}, 建議值: {' 或 '.join(expected)}"
                        )
                elif expected and header_value != expected:
                    self.log_vulnerability(
                        "low",
                        "安全標頭配置",
                        f"{header} 值可能不安全",
                        f"當前值: {header_value}, 建議值: {expected}"
                    )

            # 檢查是否暴露了伺服器資訊
            server_header = headers.get("Server")
            if server_header:
                self.log_vulnerability(
                    "info",
                    "資訊洩露",
                    "暴露伺服器資訊",
                    f"Server 標頭: {server_header}"
                )

        except Exception as e:
            self.log_vulnerability("high", "網路安全", "無法連接到應用程式", str(e))

    async def check_api_security(self) -> None:
        """檢查 API 安全性"""
        console.print("\n[bold]2. API 安全性檢查[/bold]")

        # 檢查是否需要身份驗證
        try:
            response = await self.http_client.get(f"{self.api_url}/vm-configs")
            if response.status_code == 200:
                self.log_vulnerability(
                    "high",
                    "身份驗證",
                    "API 端點無需身份驗證",
                    "所有 API 端點都可以無需認證即可存取"
                )
                self.add_recommendation("身份驗證", "實施 API 金鑰、JWT 或其他身份驗證機制")

        except Exception as e:
            console.print(f"  [yellow]API 連接錯誤: {e}[/yellow]")

        # 測試 SQL 注入（如果適用）
        await self._test_sql_injection()

        # 測試 XSS 漏洞
        await self._test_xss_vulnerabilities()

        # 測試檔案路徑遍歷
        await self._test_path_traversal()

    async def _test_sql_injection(self) -> None:
        """測試 SQL 注入攻擊"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE vm_configs; --",
            "' UNION SELECT * FROM sqlite_master --"
        ]

        for payload in sql_payloads:
            try:
                # 測試在查詢參數中
                response = await self.http_client.get(
                    f"{self.api_url}/vm-configs",
                    params={"search": payload}
                )

                # 檢查是否有 SQL 錯誤訊息
                response_text = response.text.lower()
                sql_errors = ["sql", "sqlite", "database", "syntax error"]

                if any(error in response_text for error in sql_errors):
                    self.log_vulnerability(
                        "high",
                        "SQL 注入",
                        "可能的 SQL 注入漏洞",
                        f"載荷: {payload}, 響應包含 SQL 錯誤訊息"
                    )

            except Exception:
                continue

    async def _test_xss_vulnerabilities(self) -> None:
        """測試 XSS 漏洞"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]

        # 測試 VM 配置建立中的 XSS
        for payload in xss_payloads:
            try:
                test_config = {
                    "name": payload,
                    "description": payload,
                    "nodes": [{"name": "test", "ip": "192.168.1.1", "roles": ["master"]}],
                    "ssh_user": "ubuntu"
                }

                response = await self.http_client.post(
                    f"{self.api_url}/vm-configs",
                    json=test_config
                )

                if response.status_code == 201:
                    # 檢查回應是否包含未轉義的腳本
                    response_text = response.text
                    if payload in response_text and "<script>" in payload:
                        self.log_vulnerability(
                            "medium",
                            "XSS 漏洞",
                            "可能的跨站腳本攻擊漏洞",
                            f"載荷: {payload} 未被正確轉義"
                        )

                    # 清理測試資料
                    config_id = response.json().get("id")
                    if config_id:
                        await self.http_client.delete(f"{self.api_url}/vm-configs/{config_id}")

            except Exception:
                continue

    async def _test_path_traversal(self) -> None:
        """測試路徑遍歷攻擊"""
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]

        for payload in path_payloads:
            try:
                # 測試檔案存取端點（如果有的話）
                response = await self.http_client.get(
                    f"{self.api_url}/question-sets/{payload}"
                )

                # 檢查是否返回了系統檔案內容
                if response.status_code == 200:
                    response_text = response.text.lower()
                    system_indicators = ["root:", "bin/bash", "windows", "system32"]

                    if any(indicator in response_text for indicator in system_indicators):
                        self.log_vulnerability(
                            "critical",
                            "路徑遍歷",
                            "嚴重的路徑遍歷漏洞",
                            f"載荷: {payload} 可讀取系統檔案"
                        )

            except Exception:
                continue

    async def check_file_permissions(self) -> None:
        """檢查檔案權限"""
        console.print("\n[bold]3. 檔案權限檢查[/bold]")

        # 檢查敏感檔案權限
        sensitive_files = [
            ("data/ssh_keys/id_rsa", "SSH 私鑰", 0o600),
            (".env", "環境變數檔案", 0o600),
            ("docker-compose.yml", "Docker Compose 配置", 0o644)
        ]

        for file_path, description, expected_mode in sensitive_files:
            path = Path(file_path)
            if path.exists():
                current_mode = path.stat().st_mode & 0o777

                if current_mode != expected_mode:
                    severity = "high" if "ssh" in file_path.lower() or ".env" in file_path else "medium"
                    self.log_vulnerability(
                        severity,
                        "檔案權限",
                        f"{description} 權限不安全",
                        f"當前權限: {oct(current_mode)}, 建議權限: {oct(expected_mode)}"
                    )
            else:
                if "ssh" in file_path:
                    self.log_vulnerability(
                        "info",
                        "檔案缺失",
                        f"{description} 不存在",
                        f"檔案路徑: {file_path}"
                    )

        # 檢查配置目錄權限
        config_dirs = ["data/", "nginx/", "backend/", "frontend/"]
        for dir_path in config_dirs:
            path = Path(dir_path)
            if path.exists():
                # 檢查是否所有人都可寫
                current_mode = path.stat().st_mode & 0o777
                if current_mode & 0o002:  # 其他人可寫
                    self.log_vulnerability(
                        "medium",
                        "目錄權限",
                        f"{dir_path} 目錄所有人可寫",
                        f"當前權限: {oct(current_mode)}"
                    )

    async def check_container_security(self) -> None:
        """檢查容器安全性"""
        console.print("\n[bold]4. 容器安全性檢查[/bold]")

        try:
            # 檢查 Docker Compose 配置
            compose_file = Path("docker-compose.yml")
            if compose_file.exists():
                with open(compose_file, 'r', encoding='utf-8') as f:
                    compose_content = f.read()

                # 檢查特權模式
                if "privileged: true" in compose_content:
                    self.log_vulnerability(
                        "high",
                        "容器特權",
                        "容器以特權模式運行",
                        "特權容器可能會對主機系統造成安全風險"
                    )

                # 檢查主機網路模式
                if "network_mode: host" in compose_content:
                    self.log_vulnerability(
                        "medium",
                        "網路安全",
                        "容器使用主機網路模式",
                        "主機網路模式可能暴露不必要的端口"
                    )

                # 檢查是否有資源限制
                if "mem_limit" not in compose_content and "memory" not in compose_content:
                    self.log_vulnerability(
                        "low",
                        "資源限制",
                        "容器沒有記憶體限制",
                        "建議設定記憶體限制防止 DoS 攻擊"
                    )

                # 檢查卷掛載
                sensitive_mounts = ["/", "/etc", "/usr", "/var", "/proc", "/sys"]
                for mount in sensitive_mounts:
                    if f":{mount}" in compose_content or f" {mount}:" in compose_content:
                        self.log_vulnerability(
                            "high",
                            "卷掛載",
                            f"敏感目錄掛載: {mount}",
                            "掛載敏感目錄可能導致容器逃逸"
                        )

        except Exception as e:
            console.print(f"  [yellow]無法讀取 Docker Compose 配置: {e}[/yellow]")

    async def check_secrets_exposure(self) -> None:
        """檢查機密資訊暴露"""
        console.print("\n[bold]5. 機密資訊暴露檢查[/bold]")

        # 檢查原始碼中的機密資訊
        secret_patterns = {
            r'password\s*=\s*["\'][^"\']+["\']': "硬編碼密碼",
            r'api_key\s*=\s*["\'][^"\']+["\']': "API 金鑰",
            r'secret\s*=\s*["\'][^"\']+["\']': "機密值",
            r'token\s*=\s*["\'][^"\']+["\']': "認證令牌",
            r'-----BEGIN PRIVATE KEY-----': "私鑰",
            r'-----BEGIN RSA PRIVATE KEY-----': "RSA 私鑰"
        }

        # 搜尋源碼檔案
        source_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".yml", ".yaml", ".json"]

        for file_path in Path(".").rglob("*"):
            if (file_path.is_file() and
                file_path.suffix in source_extensions and
                not any(ignore in str(file_path) for ignore in [".git", "node_modules", "__pycache__", ".venv", "venv"])):

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern, description in secret_patterns.items():
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # 排除明顯的範例或註解
                            line = match.group(0)
                            if not any(ignore in line.lower() for ignore in ["example", "dummy", "test", "placeholder", "#", "//"]):
                                self.log_vulnerability(
                                    "high",
                                    "機密暴露",
                                    f"檔案中可能包含{description}",
                                    f"檔案: {file_path}, 內容: {line[:50]}..."
                                )

                except Exception:
                    continue

        # 檢查環境變數檔案
        env_files = [".env", ".env.local", ".env.production"]
        for env_file in env_files:
            path = Path(env_file)
            if path.exists():
                # 檢查 .env 檔案是否在版本控制中
                gitignore_path = Path(".gitignore")
                if gitignore_path.exists():
                    with open(gitignore_path, 'r') as f:
                        gitignore_content = f.read()

                    if env_file not in gitignore_content:
                        self.log_vulnerability(
                            "medium",
                            "版本控制",
                            f"{env_file} 可能被版本控制追蹤",
                            "環境變數檔案應該添加到 .gitignore"
                        )

    async def check_network_security(self) -> None:
        """檢查網路安全配置"""
        console.print("\n[bold]6. 網路安全檢查[/bold]")

        # 檢查開放的端口
        try:
            result = subprocess.run(
                ["netstat", "-tuln"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                listening_ports = []

                for line in lines:
                    if "LISTEN" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            address_port = parts[3]
                            if ":" in address_port:
                                port = address_port.split(":")[-1]
                                listening_ports.append(port)

                # 檢查危險的開放端口
                dangerous_ports = {
                    "22": "SSH",
                    "23": "Telnet",
                    "3306": "MySQL",
                    "5432": "PostgreSQL",
                    "27017": "MongoDB",
                    "6379": "Redis"
                }

                for port in listening_ports:
                    if port in dangerous_ports:
                        service = dangerous_ports[port]
                        self.log_vulnerability(
                            "medium",
                            "網路暴露",
                            f"{service} 服務對外開放",
                            f"端口 {port} 正在監聽，確保有適當的存取控制"
                        )

        except Exception as e:
            console.print(f"  [yellow]無法檢查網路端口: {e}[/yellow]")

        # 檢查 HTTPS 配置
        try:
            response = await self.http_client.get("https://localhost", verify=False)
            # 如果 HTTPS 回應成功但沒有適當的憑證
            console.print("  [yellow]檢測到 HTTPS 但可能使用自簽憑證[/yellow]")
        except Exception:
            self.log_vulnerability(
                "low",
                "HTTPS",
                "未配置 HTTPS",
                "建議在生產環境中使用 HTTPS"
            )

    def generate_security_report(self) -> None:
        """生成安全報告"""
        console.print("\n[bold]安全評估報告[/bold]")

        # 統計漏洞
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in self.vulnerabilities:
            severity_counts[vuln["severity"].lower()] += 1

        # 建立漏洞統計表
        table = Table(title="安全漏洞統計")
        table.add_column("嚴重程度", style="cyan")
        table.add_column("數量", justify="right")
        table.add_column("描述", style="dim")

        severity_info = {
            "critical": ("紅色", "需要立即修復"),
            "high": ("紅色", "高優先級修復"),
            "medium": ("黃色", "中優先級修復"),
            "low": ("藍色", "低優先級修復"),
            "info": ("白色", "資訊性項目")
        }

        total_vulnerabilities = 0
        for severity, count in severity_counts.items():
            if count > 0:
                color, desc = severity_info[severity]
                table.add_row(
                    f"[{color.lower()}]{severity.upper()}[/{color.lower()}]",
                    str(count),
                    desc
                )
                total_vulnerabilities += count

        console.print(table)

        # 風險評級
        if severity_counts["critical"] > 0:
            risk_level = "critical"
            risk_color = "red"
            risk_desc = "極高風險 - 立即採取行動"
        elif severity_counts["high"] > 0:
            risk_level = "high"
            risk_color = "red"
            risk_desc = "高風險 - 需要儘快修復"
        elif severity_counts["medium"] > 3:
            risk_level = "medium-high"
            risk_color = "yellow"
            risk_desc = "中高風險 - 建議優先修復"
        elif severity_counts["medium"] > 0:
            risk_level = "medium"
            risk_color = "yellow"
            risk_desc = "中等風險 - 計劃修復"
        else:
            risk_level = "low"
            risk_color = "green"
            risk_desc = "低風險 - 可接受"

        console.print(f"\n[bold]總體風險評級: [{risk_color}]{risk_level.upper()}[/{risk_color}][/bold]")
        console.print(f"評估: {risk_desc}")

        # 顯示關鍵漏洞
        critical_vulns = [v for v in self.vulnerabilities if v["severity"].lower() in ["critical", "high"]]
        if critical_vulns:
            console.print(f"\n[bold red]關鍵安全問題 ({len(critical_vulns)} 個):[/bold red]")
            for vuln in critical_vulns:
                console.print(f"  [red]●[/red] {vuln['category']}: {vuln['description']}")
                if vuln['details']:
                    console.print(f"    {vuln['details']}")

        # 安全建議
        if self.recommendations:
            console.print(f"\n[bold]安全建議:[/bold]")
            grouped_recommendations = {}
            for rec in self.recommendations:
                category = rec['category']
                if category not in grouped_recommendations:
                    grouped_recommendations[category] = []
                grouped_recommendations[category].append(rec['recommendation'])

            for category, recommendations in grouped_recommendations.items():
                console.print(f"\n[cyan]{category}:[/cyan]")
                for rec in recommendations:
                    console.print(f"  • {rec}")

        # 通用安全建議
        console.print(f"\n[bold]通用安全建議:[/bold]")
        general_recommendations = [
            "實施身份驗證和授權機制",
            "啟用 HTTPS 並使用有效的 SSL 憑證",
            "設定適當的 HTTP 安全標頭",
            "實施輸入驗證和輸出編碼",
            "定期更新依賴套件和基礎映像",
            "設定適當的檔案和目錄權限",
            "實施日誌記錄和監控",
            "建立事件回應計畫"
        ]

        for recommendation in general_recommendations:
            console.print(f"  • {recommendation}")

async def main():
    """主要執行函數"""
    console.print(Panel.fit(
        "[bold]Kubernetes 考試模擬器\n安全性評估工具[/bold]",
        style="red"
    ))

    console.print("[yellow]警告: 此工具僅執行基本安全檢查，不能取代專業的安全審計[/yellow]\n")

    async with SecurityAssessment() as assessment:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            security_tests = [
                ("檢查 HTTP 安全標頭...", assessment.check_http_headers),
                ("評估 API 安全性...", assessment.check_api_security),
                ("檢查檔案權限...", assessment.check_file_permissions),
                ("檢查容器安全性...", assessment.check_container_security),
                ("掃描機密資訊暴露...", assessment.check_secrets_exposure),
                ("檢查網路安全配置...", assessment.check_network_security),
            ]

            for description, test_func in security_tests:
                task = progress.add_task(description, total=None)
                try:
                    await test_func()
                except Exception as e:
                    console.print(f"[red]安全測試錯誤: {e}[/red]")
                progress.remove_task(task)

        # 生成報告
        assessment.generate_security_report()

if __name__ == "__main__":
    # 檢查依賴
    try:
        import httpx
        import rich
    except ImportError as e:
        print(f"缺少必要的依賴套件: {e}")
        print("請執行: pip install httpx rich")
        sys.exit(1)

    # 執行安全評估
    asyncio.run(main())