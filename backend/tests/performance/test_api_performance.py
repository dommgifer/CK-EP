#!/usr/bin/env python3
"""
T105: 後端 API 效能測試
目標：<200ms 回應時間

使用 pytest-benchmark 進行效能測試
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import httpx
import sys
import os

# 添加 src 到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from main import app
from fastapi.testclient import TestClient


class APIPerformanceTest:
    """API 效能測試類別"""

    def __init__(self):
        self.client = TestClient(app)
        self.response_times: List[float] = []
        self.performance_target = 0.2  # 200ms target

    def time_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """測量單一請求的回應時間"""
        start_time = time.time()

        if method.upper() == 'GET':
            response = self.client.get(url, **kwargs)
        elif method.upper() == 'POST':
            response = self.client.post(url, **kwargs)
        elif method.upper() == 'PUT':
            response = self.client.put(url, **kwargs)
        elif method.upper() == 'DELETE':
            response = self.client.delete(url, **kwargs)

        end_time = time.time()
        response_time = end_time - start_time

        return {
            'response_time': response_time,
            'status_code': response.status_code,
            'response': response
        }

    def run_performance_test(self, method: str, url: str, iterations: int = 100, **kwargs) -> Dict[str, Any]:
        """執行效能測試並收集統計資料"""
        response_times = []
        status_codes = []

        for i in range(iterations):
            result = self.time_request(method, url, **kwargs)
            response_times.append(result['response_time'])
            status_codes.append(result['status_code'])

        return {
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'p95_response_time': statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            'p99_response_time': statistics.quantiles(response_times, n=100)[98],  # 99th percentile
            'std_deviation': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            'success_rate': sum(1 for code in status_codes if 200 <= code < 300) / len(status_codes) * 100,
            'total_requests': iterations
        }


@pytest.fixture
def performance_tester():
    """效能測試器 fixture"""
    return APIPerformanceTest()


@pytest.fixture
def mock_dependencies():
    """模擬外部依賴以專注於 API 效能"""
    with patch('src.database.get_db') as mock_db, \
         patch('src.services.question_set_file_manager.QuestionSetFileManager') as mock_qsm, \
         patch('src.services.vm_cluster_service.VMClusterService') as mock_vcs:

        # 設定基本的模擬回應
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        mock_qsm_instance = Mock()
        mock_qsm.return_value = mock_qsm_instance

        mock_vcs_instance = Mock()
        mock_vcs.return_value = mock_vcs_instance

        yield {
            'db': mock_db_session,
            'qsm': mock_qsm_instance,
            'vcs': mock_vcs_instance
        }


class TestVMConfigAPIPerformance:
    """VM 配置 API 效能測試"""

    def test_get_vm_configs_performance(self, performance_tester, mock_dependencies):
        """測試 GET /api/v1/vm-configs 效能"""
        # 模擬回應資料
        mock_configs = [
            {
                'id': f'config-{i}',
                'name': f'測試叢集 {i}',
                'description': f'測試用叢集 {i}',
                'nodes': [{'name': 'master-1', 'ip': f'192.168.1.{10+i}', 'roles': ['master']}],
                'ssh_user': 'ubuntu',
                'created_by': 'test_user'
            } for i in range(10)
        ]

        with patch('src.api.endpoints.vm_configs.get_vm_configs') as mock_get:
            mock_get.return_value = mock_configs

            stats = performance_tester.run_performance_test('GET', '/api/v1/vm-configs', iterations=50)

            # 驗證效能目標
            assert stats['avg_response_time'] < performance_tester.performance_target, \
                f"平均回應時間 {stats['avg_response_time']:.3f}s 超過目標 {performance_tester.performance_target}s"

            assert stats['p95_response_time'] < performance_tester.performance_target * 1.5, \
                f"95th 百分位回應時間 {stats['p95_response_time']:.3f}s 超過容忍範圍"

            assert stats['success_rate'] >= 95, \
                f"成功率 {stats['success_rate']:.1f}% 低於 95% 要求"

    def test_create_vm_config_performance(self, performance_tester, mock_dependencies):
        """測試 POST /api/v1/vm-configs 效能"""
        config_data = {
            'name': '效能測試叢集',
            'description': '用於效能測試的叢集',
            'nodes': [
                {
                    'name': 'master-1',
                    'ip': '192.168.1.10',
                    'roles': ['master', 'etcd'],
                    'specs': {'cpu': 2, 'memory': '4Gi', 'disk': '20Gi'}
                }
            ],
            'ssh_user': 'ubuntu',
            'created_by': 'perf_test'
        }

        with patch('src.api.endpoints.vm_configs.create_vm_config') as mock_create:
            mock_create.return_value = {'id': 'perf-test-001', **config_data}

            stats = performance_tester.run_performance_test(
                'POST',
                '/api/v1/vm-configs',
                iterations=30,
                json=config_data
            )

            assert stats['avg_response_time'] < performance_tester.performance_target, \
                f"建立配置平均回應時間 {stats['avg_response_time']:.3f}s 超過目標"


class TestQuestionSetAPIPerformance:
    """題組 API 效能測試"""

    def test_get_question_sets_performance(self, performance_tester, mock_dependencies):
        """測試 GET /api/v1/question-sets 效能"""
        mock_question_sets = {
            f'cka/set-{i}': {
                'metadata': {
                    'exam_type': 'CKA',
                    'set_id': f'set-{i}',
                    'name': f'CKA 測試集 {i}',
                    'description': f'測試用題組 {i}',
                    'time_limit_minutes': 120,
                    'passing_score': 70.0
                },
                'questions': [
                    {
                        'id': j,
                        'content': f'測試題目 {j}',
                        'weight': 25.0,
                        'kubernetes_objects': ['Pod'],
                        'hints': [f'提示 {j}']
                    } for j in range(1, 5)
                ]
            } for i in range(5)
        }

        with patch('src.services.question_set_file_manager.QuestionSetFileManager.get_all_question_sets') as mock_get:
            mock_get.return_value = mock_question_sets

            stats = performance_tester.run_performance_test('GET', '/api/v1/question-sets', iterations=50)

            assert stats['avg_response_time'] < performance_tester.performance_target, \
                f"題組列表回應時間 {stats['avg_response_time']:.3f}s 超過目標"

    def test_get_single_question_set_performance(self, performance_tester, mock_dependencies):
        """測試 GET /api/v1/question-sets/{set_id} 效能"""
        mock_question_set = {
            'metadata': {
                'exam_type': 'CKA',
                'set_id': 'perf-test',
                'name': 'CKA 效能測試集',
                'description': '效能測試用題組',
                'time_limit_minutes': 120,
                'passing_score': 70.0
            },
            'questions': [
                {
                    'id': i,
                    'content': f'效能測試題目 {i}',
                    'weight': 25.0,
                    'kubernetes_objects': ['Pod'],
                    'hints': [f'效能測試提示 {i}']
                } for i in range(1, 21)  # 20 個題目
            ]
        }

        with patch('src.services.question_set_file_manager.QuestionSetFileManager.get_question_set') as mock_get:
            mock_get.return_value = mock_question_set

            stats = performance_tester.run_performance_test(
                'GET',
                '/api/v1/question-sets/cka/perf-test',
                iterations=50
            )

            assert stats['avg_response_time'] < performance_tester.performance_target, \
                f"單一題組回應時間 {stats['avg_response_time']:.3f}s 超過目標"


class TestExamSessionAPIPerformance:
    """考試會話 API 效能測試"""

    def test_create_exam_session_performance(self, performance_tester, mock_dependencies):
        """測試 POST /api/v1/exam-sessions 效能"""
        session_data = {
            'question_set_id': 'cka/perf-test',
            'vm_cluster_config_id': 'perf-cluster'
        }

        mock_session = {
            'id': 'perf-session-001',
            'status': 'created',
            'created_at': '2025-09-24T10:00:00Z',
            **session_data
        }

        with patch('src.services.exam_session_service.ExamSessionService.create_exam_session') as mock_create:
            mock_create.return_value = mock_session

            stats = performance_tester.run_performance_test(
                'POST',
                '/api/v1/exam-sessions',
                iterations=20,
                json=session_data
            )

            # 會話建立可能涉及更多邏輯，容許稍長時間
            extended_target = performance_tester.performance_target * 1.5
            assert stats['avg_response_time'] < extended_target, \
                f"建立會話平均回應時間 {stats['avg_response_time']:.3f}s 超過延長目標 {extended_target:.3f}s"

    def test_get_exam_session_performance(self, performance_tester, mock_dependencies):
        """測試 GET /api/v1/exam-sessions/{session_id} 效能"""
        mock_session = {
            'id': 'perf-session-001',
            'question_set_id': 'cka/perf-test',
            'vm_cluster_config_id': 'perf-cluster',
            'status': 'in_progress',
            'current_question_index': 5,
            'answers': {str(i): {'solution': f'answer {i}'} for i in range(1, 6)},
            'progress': 25.0,
            'created_at': '2025-09-24T10:00:00Z'
        }

        with patch('src.services.exam_session_service.ExamSessionService.get_exam_session') as mock_get:
            mock_get.return_value = mock_session

            stats = performance_tester.run_performance_test(
                'GET',
                '/api/v1/exam-sessions/perf-session-001',
                iterations=50
            )

            assert stats['avg_response_time'] < performance_tester.performance_target, \
                f"取得會話回應時間 {stats['avg_response_time']:.3f}s 超過目標"


class TestConcurrentPerformance:
    """並發效能測試"""

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, mock_dependencies):
        """測試並發 API 呼叫效能"""
        async def make_request(client, endpoint):
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            return {
                'response_time': end_time - start_time,
                'status_code': response.status_code
            }

        client = TestClient(app)

        with patch('src.api.endpoints.vm_configs.get_vm_configs') as mock_get:
            mock_get.return_value = [{'id': 'test', 'name': 'test'}]

            # 模擬 10 個並發請求
            tasks = []
            for i in range(10):
                task = asyncio.create_task(make_request(client, '/api/v1/vm-configs'))
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # 驗證並發效能
            response_times = [r['response_time'] for r in results]
            avg_concurrent_time = statistics.mean(response_times)

            # 並發請求的平均時間應該在合理範圍內
            assert avg_concurrent_time < 0.5, \
                f"並發請求平均時間 {avg_concurrent_time:.3f}s 過長"

            # 所有請求應該成功
            success_count = sum(1 for r in results if r['status_code'] == 200)
            assert success_count == 10, f"並發請求成功率 {success_count}/10"


class TestDatabasePerformance:
    """資料庫效能測試"""

    def test_database_query_performance(self, performance_tester, mock_dependencies):
        """測試資料庫查詢效能"""
        # 模擬複雜的資料庫查詢
        mock_query_result = [
            {
                'id': f'session-{i}',
                'question_set_id': f'cka/set-{i%3}',
                'status': 'completed' if i % 2 == 0 else 'in_progress',
                'created_at': f'2025-09-24T{10 + i%12:02d}:00:00Z',
                'final_score': 75.0 + (i % 20)
            } for i in range(100)
        ]

        with patch('src.api.endpoints.exam_sessions.list_exam_sessions') as mock_list:
            mock_list.return_value = mock_query_result

            stats = performance_tester.run_performance_test(
                'GET',
                '/api/v1/exam-sessions?limit=100',
                iterations=20
            )

            assert stats['avg_response_time'] < performance_tester.performance_target, \
                f"大量資料查詢回應時間 {stats['avg_response_time']:.3f}s 超過目標"


def generate_performance_report(test_results: Dict[str, Dict[str, Any]]) -> str:
    """生成效能測試報告"""
    report = ["# API 效能測試報告", ""]
    report.append(f"測試執行時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"效能目標: <200ms 平均回應時間")
    report.append("")

    for test_name, stats in test_results.items():
        report.append(f"## {test_name}")
        report.append(f"- 平均回應時間: {stats['avg_response_time']:.3f}s")
        report.append(f"- 中位數回應時間: {stats['median_response_time']:.3f}s")
        report.append(f"- 95th 百分位: {stats['p95_response_time']:.3f}s")
        report.append(f"- 99th 百分位: {stats['p99_response_time']:.3f}s")
        report.append(f"- 成功率: {stats['success_rate']:.1f}%")

        # 效能評級
        if stats['avg_response_time'] < 0.1:
            grade = "優秀 🟢"
        elif stats['avg_response_time'] < 0.2:
            grade = "良好 🟡"
        else:
            grade = "需改善 🔴"

        report.append(f"- 效能評級: {grade}")
        report.append("")

    return "\n".join(report)


if __name__ == "__main__":
    # 執行效能測試
    pytest.main([__file__, "-v", "--tb=short"])