#!/usr/bin/env python3
"""
效能基準測試腳本
對 Kubernetes 考試模擬器進行全面的效能測試和基準測試
"""

import asyncio
import json
import time
import statistics
import sys
import psutil
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich import print as rprint

console = Console()

@dataclass
class BenchmarkResult:
    """基準測試結果"""
    test_name: str
    metric_name: str
    value: float
    unit: str
    target: Optional[float] = None
    passed: Optional[bool] = None

@dataclass
class SystemInfo:
    """系統資訊"""
    cpu_count: int
    cpu_freq: float
    memory_total: int
    memory_available: int
    disk_total: int
    disk_free: int
    platform: str
    python_version: str

class PerformanceBenchmark:
    """效能基準測試器"""

    def __init__(self):
        self.base_url = "http://localhost"
        self.api_url = f"{self.base_url}/api/v1"
        self.results: List[BenchmarkResult] = []
        self.system_info = self._get_system_info()

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    def _get_system_info(self) -> SystemInfo:
        """收集系統資訊"""
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')

        return SystemInfo(
            cpu_count=psutil.cpu_count(),
            cpu_freq=cpu_freq.current if cpu_freq else 0,
            memory_total=memory.total,
            memory_available=memory.available,
            disk_total=disk.total,
            disk_free=disk.free,
            platform=platform.platform(),
            python_version=platform.python_version()
        )

    def add_result(self, test_name: str, metric_name: str, value: float, unit: str, target: float = None):
        """添加測試結果"""
        passed = None
        if target is not None:
            if "時間" in metric_name or "延遲" in metric_name:
                passed = value <= target  # 越小越好
            else:
                passed = value >= target  # 越大越好

        result = BenchmarkResult(
            test_name=test_name,
            metric_name=metric_name,
            value=value,
            unit=unit,
            target=target,
            passed=passed
        )
        self.results.append(result)

        # 顯示結果
        status = ""
        if passed is not None:
            status = "[green]✓[/green]" if passed else "[red]✗[/red]"

        target_text = f" (目標: {target}{unit})" if target else ""
        console.print(f"  {status} {metric_name}: {value:.2f}{unit}{target_text}")

    async def test_api_response_times(self) -> None:
        """測試 API 響應時間"""
        console.print("\n[bold]1. API 響應時間測試[/bold]")

        endpoints = [
            ("/health", "健康檢查"),
            ("/vm-configs", "VM 配置列表"),
            ("/question-sets", "題組列表"),
            ("/question-sets/reload", "題組重載")
        ]

        for endpoint, description in endpoints:
            times = []

            # 預熱請求
            for _ in range(3):
                try:
                    if "reload" in endpoint:
                        await self.http_client.post(f"{self.api_url}{endpoint}")
                    else:
                        await self.http_client.get(f"{self.api_url}{endpoint}")
                except:
                    pass

            # 實際測試
            for _ in range(10):
                start_time = time.time()
                try:
                    if "reload" in endpoint:
                        response = await self.http_client.post(f"{self.api_url}{endpoint}")
                    else:
                        response = await self.http_client.get(f"{self.api_url}{endpoint}")

                    if response.status_code in [200, 201]:
                        end_time = time.time()
                        times.append((end_time - start_time) * 1000)  # 轉換為毫秒
                except Exception as e:
                    console.print(f"    [yellow]請求失敗: {e}[/yellow]")
                    continue

            if times:
                avg_time = statistics.mean(times)
                median_time = statistics.median(times)
                p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0]

                self.add_result(f"API-{description}", "平均響應時間", avg_time, "ms", 200)
                self.add_result(f"API-{description}", "中位數響應時間", median_time, "ms", 150)
                self.add_result(f"API-{description}", "95百分位響應時間", p95_time, "ms", 500)

    async def test_concurrent_requests(self) -> None:
        """測試並發請求處理"""
        console.print("\n[bold]2. 並發請求測試[/bold]")

        concurrent_levels = [1, 5, 10, 20, 50]

        for concurrent_count in concurrent_levels:
            console.print(f"  測試 {concurrent_count} 個並發請求...")

            tasks = []
            start_time = time.time()

            for _ in range(concurrent_count):
                task = asyncio.create_task(self.http_client.get(f"{self.api_url}/health"))
                tasks.append(task)

            try:
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                successful_requests = sum(
                    1 for r in responses
                    if hasattr(r, 'status_code') and r.status_code == 200
                )

                total_time = (end_time - start_time) * 1000  # 毫秒
                success_rate = (successful_requests / concurrent_count) * 100
                requests_per_second = concurrent_count / ((end_time - start_time) if end_time > start_time else 0.001)

                self.add_result(
                    f"並發-{concurrent_count}",
                    "成功率",
                    success_rate,
                    "%",
                    95 if concurrent_count <= 20 else 80
                )

                self.add_result(
                    f"並發-{concurrent_count}",
                    "每秒請求數",
                    requests_per_second,
                    "req/s",
                    concurrent_count * 0.5
                )

                self.add_result(
                    f"並發-{concurrent_count}",
                    "總處理時間",
                    total_time,
                    "ms",
                    concurrent_count * 100
                )

            except Exception as e:
                console.print(f"    [red]並發測試失敗: {e}[/red]")

    async def test_data_processing_performance(self) -> None:
        """測試資料處理效能"""
        console.print("\n[bold]3. 資料處理效能測試[/bold]")

        # 測試 VM 配置 CRUD 效能
        await self._test_vm_config_performance()

        # 測試大量資料載入效能
        await self._test_bulk_data_performance()

    async def _test_vm_config_performance(self) -> None:
        """測試 VM 配置操作效能"""
        console.print("  VM 配置操作效能測試...")

        test_config = {
            "name": "效能測試配置",
            "description": "用於效能測試的配置",
            "nodes": [
                {"name": f"node-{i}", "ip": f"192.168.1.{10+i}", "roles": ["worker"]}
                for i in range(10)  # 建立 10 個節點
            ],
            "ssh_user": "ubuntu"
        }

        # CREATE 效能測試
        create_times = []
        created_ids = []

        for i in range(5):
            config = test_config.copy()
            config["name"] = f"效能測試配置-{i}"

            start_time = time.time()
            try:
                response = await self.http_client.post(f"{self.api_url}/vm-configs", json=config)
                if response.status_code == 201:
                    end_time = time.time()
                    create_times.append((end_time - start_time) * 1000)
                    created_ids.append(response.json().get("id"))
            except Exception as e:
                console.print(f"    [yellow]建立配置失敗: {e}[/yellow]")

        if create_times:
            avg_create_time = statistics.mean(create_times)
            self.add_result("VM配置", "建立平均時間", avg_create_time, "ms", 100)

        # READ 效能測試
        if created_ids:
            read_times = []
            for config_id in created_ids:
                start_time = time.time()
                try:
                    response = await self.http_client.get(f"{self.api_url}/vm-configs/{config_id}")
                    if response.status_code == 200:
                        end_time = time.time()
                        read_times.append((end_time - start_time) * 1000)
                except Exception:
                    continue

            if read_times:
                avg_read_time = statistics.mean(read_times)
                self.add_result("VM配置", "讀取平均時間", avg_read_time, "ms", 50)

        # 清理測試資料
        for config_id in created_ids:
            try:
                await self.http_client.delete(f"{self.api_url}/vm-configs/{config_id}")
            except Exception:
                pass

    async def _test_bulk_data_performance(self) -> None:
        """測試大量資料處理效能"""
        console.print("  大量資料處理效能測試...")

        # 建立大型題組用於測試
        large_question_set = {
            "metadata": {
                "title": "效能測試大型題組",
                "description": "包含大量題目的效能測試題組",
                "time_limit_minutes": 180,
                "passing_score": 70
            },
            "questions": [
                {
                    "id": i,
                    "title": f"題目 {i}",
                    "description": f"這是第 {i} 個測試題目，包含詳細的描述和要求。" * 10,  # 長描述
                    "scenario": f"測試情境 {i}，需要執行多個步驟來完成任務。" * 5,
                    "scoring": {
                        "max_points": 10,
                        "validation_commands": [
                            f"kubectl get pod test-pod-{i}",
                            f"kubectl describe pod test-pod-{i}",
                            f"kubectl logs test-pod-{i}"
                        ],
                        "expected_conditions": [
                            {"field": "status.phase", "value": "Running"}
                        ]
                    }
                }
                for i in range(1, 51)  # 50 個題目
            ]
        }

        # 建立測試題組檔案
        test_dir = Path("data/question_sets/cka/performance-test")
        test_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        try:
            with open(test_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(large_question_set["metadata"], f, ensure_ascii=False, indent=2)

            with open(test_dir / "questions.json", "w", encoding="utf-8") as f:
                json.dump(large_question_set["questions"], f, ensure_ascii=False, indent=2)

            # 測試重載時間
            reload_start = time.time()
            response = await self.http_client.post(f"{self.api_url}/question-sets/reload")
            reload_end = time.time()

            if response.status_code == 200:
                reload_time = (reload_end - reload_start) * 1000
                self.add_result("題組載入", "大型題組重載時間", reload_time, "ms", 2000)

                # 測試大型題組檢索時間
                retrieve_start = time.time()
                response = await self.http_client.get(f"{self.api_url}/question-sets/cka/performance-test")
                retrieve_end = time.time()

                if response.status_code == 200:
                    retrieve_time = (retrieve_end - retrieve_start) * 1000
                    self.add_result("題組檢索", "大型題組檢索時間", retrieve_time, "ms", 500)

                    # 檢查回應大小
                    response_size = len(response.content)
                    self.add_result("題組檢索", "回應資料大小", response_size / 1024, "KB", None)

        except Exception as e:
            console.print(f"    [red]大量資料測試失敗: {e}[/red]")

        finally:
            # 清理測試檔案
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)

    async def test_system_resource_usage(self) -> None:
        """測試系統資源使用情況"""
        console.print("\n[bold]4. 系統資源使用測試[/bold]")

        # 收集基準資源使用情況
        initial_memory = psutil.virtual_memory()
        initial_cpu_percent = psutil.cpu_percent(interval=1)

        # 執行一系列 API 請求來模擬負載
        console.print("  執行負載測試...")
        tasks = []
        for _ in range(100):
            task = asyncio.create_task(self.http_client.get(f"{self.api_url}/health"))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        # 測量負載後的資源使用
        final_memory = psutil.virtual_memory()
        final_cpu_percent = psutil.cpu_percent(interval=1)

        # 計算資源使用指標
        memory_usage_mb = (final_memory.used - initial_memory.used) / (1024 * 1024)
        memory_usage_percent = final_memory.percent
        cpu_usage_increase = max(0, final_cpu_percent - initial_cpu_percent)

        self.add_result("系統資源", "記憶體使用百分比", memory_usage_percent, "%", 80)
        self.add_result("系統資源", "CPU 使用增量", cpu_usage_increase, "%", 50)

        # 檢查系統是否有足夠的可用資源
        available_memory_gb = final_memory.available / (1024**3)
        self.add_result("系統資源", "可用記憶體", available_memory_gb, "GB", 1.0)

    async def test_database_performance(self) -> None:
        """測試資料庫效能（SQLite）"""
        console.print("\n[bold]5. 資料庫效能測試[/bold]")

        # 透過 API 測試資料庫操作效能
        # 建立多個 VM 配置來測試資料庫寫入效能
        write_times = []
        created_configs = []

        for i in range(20):
            config = {
                "name": f"DB測試配置-{i}",
                "description": f"資料庫效能測試配置 {i}",
                "nodes": [{"name": "test-node", "ip": f"192.168.1.{100+i}", "roles": ["master"]}],
                "ssh_user": "ubuntu"
            }

            start_time = time.time()
            try:
                response = await self.http_client.post(f"{self.api_url}/vm-configs", json=config)
                if response.status_code == 201:
                    end_time = time.time()
                    write_times.append((end_time - start_time) * 1000)
                    created_configs.append(response.json().get("id"))
            except Exception:
                continue

        if write_times:
            avg_write_time = statistics.mean(write_times)
            max_write_time = max(write_times)
            self.add_result("資料庫", "平均寫入時間", avg_write_time, "ms", 100)
            self.add_result("資料庫", "最大寫入時間", max_write_time, "ms", 500)

        # 測試資料庫讀取效能
        read_times = []
        for _ in range(10):
            start_time = time.time()
            try:
                response = await self.http_client.get(f"{self.api_url}/vm-configs")
                if response.status_code == 200:
                    end_time = time.time()
                    read_times.append((end_time - start_time) * 1000)
            except Exception:
                continue

        if read_times:
            avg_read_time = statistics.mean(read_times)
            self.add_result("資料庫", "平均查詢時間", avg_read_time, "ms", 50)

        # 清理測試資料
        for config_id in created_configs:
            try:
                await self.http_client.delete(f"{self.api_url}/vm-configs/{config_id}")
            except Exception:
                pass

    def generate_performance_report(self) -> None:
        """生成效能報告"""
        console.print("\n" + "="*80)
        console.print(Panel.fit(
            "[bold]效能基準測試報告[/bold]",
            style="blue"
        ))

        # 系統資訊
        console.print("\n[bold]系統資訊[/bold]")
        system_table = Table()
        system_table.add_column("項目", style="cyan")
        system_table.add_column("數值", style="white")

        system_table.add_row("CPU 核心數", str(self.system_info.cpu_count))
        system_table.add_row("CPU 頻率", f"{self.system_info.cpu_freq:.1f} MHz")
        system_table.add_row("記憶體總量", f"{self.system_info.memory_total / (1024**3):.2f} GB")
        system_table.add_row("可用記憶體", f"{self.system_info.memory_available / (1024**3):.2f} GB")
        system_table.add_row("磁碟空間", f"{self.system_info.disk_free / (1024**3):.2f} GB 可用")
        system_table.add_row("平台", self.system_info.platform)
        system_table.add_row("Python 版本", self.system_info.python_version)

        console.print(system_table)

        # 效能結果摘要
        console.print("\n[bold]效能結果摘要[/bold]")

        # 按測試類別分組
        categories = {}
        for result in self.results:
            category = result.test_name.split('-')[0] if '-' in result.test_name else result.test_name
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        for category, results in categories.items():
            console.print(f"\n[cyan]{category}[/cyan]")

            category_table = Table()
            category_table.add_column("指標", style="white")
            category_table.add_column("數值", justify="right")
            category_table.add_column("單位", style="dim")
            category_table.add_column("目標", justify="right", style="dim")
            category_table.add_column("狀態", justify="center")

            for result in results:
                status = ""
                if result.passed is not None:
                    status = "[green]✓[/green]" if result.passed else "[red]✗[/red]"

                target_text = f"{result.target}" if result.target else "-"

                category_table.add_row(
                    result.metric_name,
                    f"{result.value:.2f}",
                    result.unit,
                    target_text,
                    status
                )

            console.print(category_table)

        # 整體評估
        total_tests = len([r for r in self.results if r.passed is not None])
        passed_tests = len([r for r in self.results if r.passed is True])

        if total_tests > 0:
            pass_rate = (passed_tests / total_tests) * 100

            console.print(f"\n[bold]整體效能評估[/bold]")
            console.print(f"通過率: {pass_rate:.1f}% ({passed_tests}/{total_tests})")

            if pass_rate >= 90:
                grade = "[green]A - 優秀[/green]"
                recommendation = "系統效能表現優秀，可以投入生產使用"
            elif pass_rate >= 80:
                grade = "[yellow]B - 良好[/yellow]"
                recommendation = "系統效能良好，建議對部分項目進行最佳化"
            elif pass_rate >= 70:
                grade = "[yellow]C - 一般[/yellow]"
                recommendation = "系統效能一般，需要進行最佳化"
            else:
                grade = "[red]D - 需改善[/red]"
                recommendation = "系統效能不符要求，需要重大最佳化"

            console.print(f"效能等級: {grade}")
            console.print(f"建議: {recommendation}")

        # 失敗的測試項目
        failed_tests = [r for r in self.results if r.passed is False]
        if failed_tests:
            console.print(f"\n[bold red]需要改善的項目:[/bold red]")
            for result in failed_tests:
                console.print(f"  [red]●[/red] {result.test_name} - {result.metric_name}: {result.value:.2f}{result.unit} (目標: {result.target}{result.unit})")

        # 效能最佳化建議
        console.print(f"\n[bold]效能最佳化建議:[/bold]")
        recommendations = [
            "考慮增加系統記憶體以提升資料庫查詢效能",
            "使用連接池來減少資料庫連接開銷",
            "實施 API 回應快取機制",
            "最佳化大型題組的載入和序列化",
            "考慮使用非同步處理提升並發能力",
            "實施適當的速率限制防止濫用",
            "定期監控和分析效能指標",
            "在生產環境中使用效能監控工具"
        ]

        for rec in recommendations:
            console.print(f"  • {rec}")

        # 儲存報告到檔案
        self._save_report_to_file()

    def _save_report_to_file(self) -> None:
        """儲存報告到檔案"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "cpu_count": self.system_info.cpu_count,
                "cpu_freq": self.system_info.cpu_freq,
                "memory_total": self.system_info.memory_total,
                "memory_available": self.system_info.memory_available,
                "disk_total": self.system_info.disk_total,
                "disk_free": self.system_info.disk_free,
                "platform": self.system_info.platform,
                "python_version": self.system_info.python_version
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "metric_name": r.metric_name,
                    "value": r.value,
                    "unit": r.unit,
                    "target": r.target,
                    "passed": r.passed
                }
                for r in self.results
            ]
        }

        report_dir = Path("tests/performance/reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"benchmark-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        console.print(f"\n[dim]報告已儲存至: {report_file}[/dim]")

async def main():
    """主要執行函數"""
    console.print(Panel.fit(
        "[bold]Kubernetes 考試模擬器\n效能基準測試工具[/bold]",
        style="blue"
    ))

    async with PerformanceBenchmark() as benchmark:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            performance_tests = [
                ("API 響應時間測試", benchmark.test_api_response_times),
                ("並發請求測試", benchmark.test_concurrent_requests),
                ("資料處理效能測試", benchmark.test_data_processing_performance),
                ("系統資源使用測試", benchmark.test_system_resource_usage),
                ("資料庫效能測試", benchmark.test_database_performance),
            ]

            for description, test_func in performance_tests:
                task = progress.add_task(description, total=100)
                try:
                    await test_func()
                    progress.update(task, completed=100)
                except Exception as e:
                    console.print(f"[red]效能測試錯誤: {e}[/red]")
                    progress.update(task, completed=100)

        # 生成報告
        benchmark.generate_performance_report()

if __name__ == "__main__":
    # 檢查依賴
    try:
        import httpx
        import psutil
        import rich
    except ImportError as e:
        print(f"缺少必要的依賴套件: {e}")
        print("請執行: pip install httpx psutil rich")
        sys.exit(1)

    # 執行基準測試
    asyncio.run(main())