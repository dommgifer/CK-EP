#!/usr/bin/env python3
"""
手動測試驗證腳本
協助進行系統的手動測試驗證，確保所有關鍵功能正常運作
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import httpx
import docker
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

console = Console()

class ManualTestValidator:
    """手動測試驗證器"""

    def __init__(self):
        self.base_url = "http://localhost"
        self.api_url = f"{self.base_url}/api/v1"
        self.docker_client = None
        self.test_results = []

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            console.print(f"[yellow]警告: 無法連接 Docker: {e}[/yellow]")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
        if self.docker_client:
            self.docker_client.close()

    def log_test_result(self, category: str, test_name: str, passed: bool, details: str = ""):
        """記錄測試結果"""
        self.test_results.append({
            "category": category,
            "test": test_name,
            "passed": passed,
            "details": details
        })

        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {status} {test_name}: {details}")

    async def check_system_startup(self) -> None:
        """檢查系統啟動狀態"""
        console.print("\n[bold]1. 系統啟動測試[/bold]")

        # 檢查容器狀態
        if self.docker_client:
            try:
                containers = self.docker_client.containers.list()
                required_containers = ["backend", "frontend", "nginx", "redis"]
                running_containers = [c.name for c in containers]

                for req_container in required_containers:
                    found = any(req_container in name.lower() for name in running_containers)
                    self.log_test_result(
                        "系統啟動",
                        f"{req_container.title()} 容器運行",
                        found,
                        f"容器狀態: {'運行中' if found else '未找到'}"
                    )
            except Exception as e:
                self.log_test_result("系統啟動", "Docker 容器檢查", False, str(e))

        # 檢查健康端點
        try:
            response = await self.http_client.get(f"{self.api_url}/health")
            passed = response.status_code == 200
            self.log_test_result(
                "系統啟動",
                "API 健康檢查",
                passed,
                f"狀態碼: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("系統啟動", "API 健康檢查", False, str(e))

        # 檢查前端頁面
        try:
            response = await self.http_client.get(self.base_url)
            passed = response.status_code == 200 and "html" in response.headers.get("content-type", "").lower()
            self.log_test_result(
                "系統啟動",
                "前端頁面載入",
                passed,
                f"狀態碼: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("系統啟動", "前端頁面載入", False, str(e))

    async def check_api_functionality(self) -> None:
        """檢查 API 基本功能"""
        console.print("\n[bold]2. API 功能測試[/bold]")

        # 檢查 API 文件
        try:
            response = await self.http_client.get(f"{self.api_url}/docs")
            passed = response.status_code == 200
            self.log_test_result(
                "API 功能",
                "API 文件頁面",
                passed,
                f"狀態碼: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("API 功能", "API 文件頁面", False, str(e))

        # 測試 VM 配置 CRUD
        await self._test_vm_config_crud()

        # 測試題組端點
        await self._test_question_sets()

    async def _test_vm_config_crud(self) -> None:
        """測試 VM 配置 CRUD 操作"""
        # 建立 VM 配置
        test_config = {
            "name": "測試配置",
            "description": "自動測試建立的配置",
            "nodes": [
                {
                    "name": "test-master",
                    "ip": "192.168.1.10",
                    "roles": ["master", "etcd"]
                }
            ],
            "ssh_user": "ubuntu"
        }

        try:
            # CREATE
            response = await self.http_client.post(f"{self.api_url}/vm-configs", json=test_config)
            create_passed = response.status_code == 201
            config_id = response.json().get("id") if create_passed else None
            self.log_test_result(
                "API 功能",
                "VM 配置建立",
                create_passed,
                f"狀態碼: {response.status_code}"
            )

            if config_id:
                # READ
                response = await self.http_client.get(f"{self.api_url}/vm-configs/{config_id}")
                read_passed = response.status_code == 200
                self.log_test_result(
                    "API 功能",
                    "VM 配置讀取",
                    read_passed,
                    f"狀態碼: {response.status_code}"
                )

                # LIST
                response = await self.http_client.get(f"{self.api_url}/vm-configs")
                list_passed = response.status_code == 200 and len(response.json()) > 0
                self.log_test_result(
                    "API 功能",
                    "VM 配置列表",
                    list_passed,
                    f"狀態碼: {response.status_code}, 配置數: {len(response.json()) if list_passed else 0}"
                )

                # DELETE
                response = await self.http_client.delete(f"{self.api_url}/vm-configs/{config_id}")
                delete_passed = response.status_code in [200, 204]
                self.log_test_result(
                    "API 功能",
                    "VM 配置刪除",
                    delete_passed,
                    f"狀態碼: {response.status_code}"
                )

        except Exception as e:
            self.log_test_result("API 功能", "VM 配置 CRUD", False, str(e))

    async def _test_question_sets(self) -> None:
        """測試題組相關端點"""
        try:
            # 檢查題組列表
            response = await self.http_client.get(f"{self.api_url}/question-sets")
            passed = response.status_code == 200
            question_sets = response.json() if passed else []
            self.log_test_result(
                "API 功能",
                "題組列表",
                passed,
                f"狀態碼: {response.status_code}, 題組數: {len(question_sets)}"
            )

            # 測試重載端點
            response = await self.http_client.post(f"{self.api_url}/question-sets/reload")
            passed = response.status_code == 200
            self.log_test_result(
                "API 功能",
                "題組重載",
                passed,
                f"狀態碼: {response.status_code}"
            )

        except Exception as e:
            self.log_test_result("API 功能", "題組測試", False, str(e))

    async def check_file_system_setup(self) -> None:
        """檢查檔案系統設定"""
        console.print("\n[bold]3. 檔案系統設定檢查[/bold]")

        # 檢查必要目錄
        required_dirs = [
            ("data/question_sets", "題組目錄"),
            ("data/vm_configs", "VM 配置目錄"),
            ("data/ssh_keys", "SSH 金鑰目錄"),
            ("data/exam_results", "考試結果目錄"),
            ("data/kubespray_configs", "Kubespray 配置目錄")
        ]

        for dir_path, description in required_dirs:
            full_path = Path(dir_path)
            exists = full_path.exists() and full_path.is_dir()
            self.log_test_result(
                "檔案系統",
                description,
                exists,
                f"路徑: {full_path.absolute()}"
            )

        # 檢查 SSH 金鑰
        ssh_key_path = Path("data/ssh_keys/id_rsa")
        has_ssh_key = ssh_key_path.exists()
        self.log_test_result(
            "檔案系統",
            "SSH 私鑰檔案",
            has_ssh_key,
            f"檔案存在: {has_ssh_key}"
        )

        # 檢查題組目錄結構
        for exam_type in ["cka", "ckad", "cks"]:
            exam_dir = Path(f"data/question_sets/{exam_type}")
            exists = exam_dir.exists()
            self.log_test_result(
                "檔案系統",
                f"{exam_type.upper()} 題組目錄",
                exists,
                f"目錄存在: {exists}"
            )

    async def check_performance_basics(self) -> None:
        """基本效能檢查"""
        console.print("\n[bold]4. 基本效能測試[/bold]")

        # API 回應時間測試
        endpoints_to_test = [
            ("/health", "健康檢查"),
            ("/vm-configs", "VM 配置列表"),
            ("/question-sets", "題組列表")
        ]

        for endpoint, description in endpoints_to_test:
            try:
                start_time = time.time()
                response = await self.http_client.get(f"{self.api_url}{endpoint}")
                end_time = time.time()

                response_time = (end_time - start_time) * 1000  # 轉換為毫秒
                passed = response.status_code == 200 and response_time < 200

                self.log_test_result(
                    "效能",
                    f"{description}回應時間",
                    passed,
                    f"{response_time:.1f}ms (目標: <200ms)"
                )

            except Exception as e:
                self.log_test_result("效能", f"{description}回應時間", False, str(e))

        # 並發請求測試
        try:
            tasks = []
            for _ in range(10):
                task = self.http_client.get(f"{self.api_url}/health")
                tasks.append(task)

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            total_time = (end_time - start_time) * 1000

            passed = successful >= 8  # 至少 80% 成功
            self.log_test_result(
                "效能",
                "並發請求處理",
                passed,
                f"{successful}/10 成功, 總時間: {total_time:.1f}ms"
            )

        except Exception as e:
            self.log_test_result("效能", "並發請求測試", False, str(e))

    async def validate_sample_data(self) -> None:
        """驗證範例資料"""
        console.print("\n[bold]5. 範例資料驗證[/bold]")

        # 建立範例題組
        sample_question_set = {
            "metadata": {
                "title": "驗證測試題組",
                "description": "用於自動驗證的測試題組",
                "time_limit_minutes": 30,
                "passing_score": 70
            },
            "questions": [
                {
                    "id": 1,
                    "title": "測試題目",
                    "description": "這是一個測試題目",
                    "scoring": {"max_points": 10}
                }
            ]
        }

        # 建立範例題組檔案
        test_dir = Path("data/question_sets/cka/validation-test")
        try:
            test_dir.mkdir(parents=True, exist_ok=True)

            with open(test_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(sample_question_set["metadata"], f, ensure_ascii=False, indent=2)

            with open(test_dir / "questions.json", "w", encoding="utf-8") as f:
                json.dump(sample_question_set["questions"], f, ensure_ascii=False, indent=2)

            self.log_test_result("範例資料", "題組檔案建立", True, "檔案建立成功")

            # 測試重載和檢索
            await self.http_client.post(f"{self.api_url}/question-sets/reload")
            response = await self.http_client.get(f"{self.api_url}/question-sets/cka/validation-test")

            passed = response.status_code == 200
            self.log_test_result(
                "範例資料",
                "題組載入驗證",
                passed,
                f"狀態碼: {response.status_code}"
            )

            # 清理測試檔案
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)

        except Exception as e:
            self.log_test_result("範例資料", "範例資料測試", False, str(e))

    def generate_report(self) -> None:
        """生成測試報告"""
        console.print("\n[bold]測試報告摘要[/bold]")

        # 統計結果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests

        # 建立摘要表格
        table = Table(title="測試結果統計")
        table.add_column("類別", style="cyan")
        table.add_column("通過", style="green")
        table.add_column("失敗", style="red")
        table.add_column("總計", style="blue")

        categories = {}
        for result in self.test_results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0}

            if result["passed"]:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1

        for category, stats in categories.items():
            table.add_row(
                category,
                str(stats["passed"]),
                str(stats["failed"]),
                str(stats["passed"] + stats["failed"])
            )

        table.add_row(
            "[bold]總計[/bold]",
            f"[bold]{passed_tests}[/bold]",
            f"[bold]{failed_tests}[/bold]",
            f"[bold]{total_tests}[/bold]"
        )

        console.print(table)

        # 成功率
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        if success_rate >= 90:
            status_color = "green"
            status_text = "優秀"
        elif success_rate >= 75:
            status_color = "yellow"
            status_text = "良好"
        else:
            status_color = "red"
            status_text = "需要改善"

        console.print(f"\n[bold]整體成功率: [{status_color}]{success_rate:.1f}%[/{status_color}] ({status_text})[/bold]")

        # 顯示失敗的測試
        if failed_tests > 0:
            console.print(f"\n[bold red]失敗的測試項目:[/bold red]")
            for result in self.test_results:
                if not result["passed"]:
                    console.print(f"  [red]✗[/red] {result['category']} - {result['test']}: {result['details']}")

        # 建議
        console.print(f"\n[bold]建議:[/bold]")
        if success_rate >= 95:
            console.print("[green]✓ 系統準備好投入生產使用[/green]")
        elif success_rate >= 80:
            console.print("[yellow]⚠ 建議修復失敗的測試項目後再投入生產[/yellow]")
        else:
            console.print("[red]✗ 系統需要重大修復才能投入生產使用[/red]")

async def main():
    """主要執行函數"""
    console.print(Panel.fit(
        "[bold]Kubernetes 考試模擬器\n手動測試驗證工具[/bold]",
        style="blue"
    ))

    async with ManualTestValidator() as validator:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # 執行各項測試
            tests = [
                ("檢查系統啟動狀態...", validator.check_system_startup),
                ("測試 API 功能...", validator.check_api_functionality),
                ("檢查檔案系統設定...", validator.check_file_system_setup),
                ("執行基本效能測試...", validator.check_performance_basics),
                ("驗證範例資料...", validator.validate_sample_data),
            ]

            for description, test_func in tests:
                task = progress.add_task(description, total=None)
                try:
                    await test_func()
                except Exception as e:
                    console.print(f"[red]測試執行錯誤: {e}[/red]")
                progress.remove_task(task)

        # 生成報告
        validator.generate_report()

if __name__ == "__main__":
    # 檢查依賴
    try:
        import httpx
        import docker
        import rich
    except ImportError as e:
        print(f"缺少必要的依賴套件: {e}")
        print("請執行: pip install httpx docker rich")
        sys.exit(1)

    # 執行驗證
    asyncio.run(main())