#!/usr/bin/env python3
"""
基本驗證腳本 - 不依賴外部套件
檢查檔案結構和基本 Python 語法
"""
import os
import sys
import ast
from pathlib import Path


def check_file_syntax(file_path):
    """檢查 Python 檔案語法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用 AST 解析檢查語法
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"語法錯誤: {e}"
    except Exception as e:
        return False, f"檔案錯誤: {e}"


def verify_directory_structure():
    """驗證目錄結構"""
    print("=== 驗證目錄結構 ===")

    required_dirs = [
        "src",
        "src/api",
        "src/api/v1",
        "src/models",
        "src/services",
        "src/database",
        "src/cache",
        "src/middleware"
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✓ {dir_path}")

    if missing_dirs:
        print(f"✗ 缺少目錄: {', '.join(missing_dirs)}")
        return False

    print("✓ 目錄結構完整")
    return True


def verify_python_files():
    """驗證 Python 檔案語法"""
    print("\n=== 驗證 Python 檔案語法 ===")

    python_files = list(Path("src").rglob("*.py"))

    syntax_errors = []
    valid_files = 0

    for py_file in python_files:
        is_valid, error = check_file_syntax(py_file)
        if is_valid:
            print(f"✓ {py_file}")
            valid_files += 1
        else:
            print(f"✗ {py_file}: {error}")
            syntax_errors.append((py_file, error))

    print(f"\n檔案檢查結果: {valid_files}/{len(python_files)} 個檔案語法正確")

    if syntax_errors:
        print("\n語法錯誤檔案:")
        for file_path, error in syntax_errors:
            print(f"  {file_path}: {error}")
        return False

    return True


def verify_key_files():
    """驗證關鍵檔案存在"""
    print("\n=== 驗證關鍵檔案 ===")

    key_files = [
        "src/main.py",
        "src/api/v1/router.py",
        "src/database/connection.py",
        "src/cache/redis_client.py",
        "requirements.txt"
    ]

    missing_files = []
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ 缺少關鍵檔案: {', '.join(missing_files)}")
        return False

    print("✓ 所有關鍵檔案存在")
    return True


def verify_api_endpoints():
    """驗證 API 端點檔案"""
    print("\n=== 驗證 API 端點檔案 ===")

    api_files = [
        "src/api/v1/vm_configs.py",
        "src/api/v1/question_sets.py",
        "src/api/v1/exam_sessions.py",
        "src/api/v1/environment.py",
        "src/api/v1/vnc_access.py",
        "src/api/v1/question_scoring.py"
    ]

    missing_files = []
    for file_path in api_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ 缺少 API 端點檔案: {', '.join(missing_files)}")
        return False

    print("✓ 所有 API 端點檔案存在")
    return True


def verify_service_files():
    """驗證服務檔案"""
    print("\n=== 驗證服務檔案 ===")

    service_files = [
        "src/services/exam_session_service.py",
        "src/services/environment_service.py",
        "src/services/container_service.py",
        "src/services/question_set_file_manager.py",
        "src/services/vm_config_file_service.py",
        "src/services/kubespray_config_service.py",
        "src/services/exam_result_file_service.py"
    ]

    missing_files = []
    for file_path in service_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ 缺少服務檔案: {', '.join(missing_files)}")
        return False

    print("✓ 所有服務檔案存在")
    return True


def verify_model_files():
    """驗證資料模型檔案"""
    print("\n=== 驗證資料模型檔案 ===")

    model_files = [
        "src/models/vm_cluster_config.py",
        "src/models/exam_session.py",
        "src/models/exam_result.py",
        "src/models/question_set_data.py"
    ]

    missing_files = []
    for file_path in model_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ 缺少模型檔案: {', '.join(missing_files)}")
        return False

    print("✓ 所有模型檔案存在")
    return True


def verify_data_directories():
    """驗證並建立資料目錄"""
    print("\n=== 驗證資料目錄 ===")

    data_dirs = [
        "../data",
        "../data/question_sets",
        "../data/vm_configs",
        "../data/ssh_keys",
        "../data/kubespray_configs",
        "../data/kubespray_configs/templates",
        "../data/kubespray_configs/generated",
        "../data/exam_results"
    ]

    created_dirs = []
    for dir_path in data_dirs:
        path_obj = Path(dir_path)
        if not path_obj.exists():
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                print(f"✓ 建立目錄: {dir_path}")
                created_dirs.append(dir_path)
            except Exception as e:
                print(f"✗ 無法建立目錄 {dir_path}: {e}")
                return False
        else:
            print(f"✓ 目錄已存在: {dir_path}")

    if created_dirs:
        print(f"建立了 {len(created_dirs)} 個新目錄")

    print("✓ 所有資料目錄準備就緒")
    return True


def main():
    """主驗證函數"""
    print("🚀 開始基本功能驗證")
    print("=" * 60)

    verifications = [
        ("目錄結構", verify_directory_structure),
        ("關鍵檔案", verify_key_files),
        ("API 端點檔案", verify_api_endpoints),
        ("服務檔案", verify_service_files),
        ("資料模型檔案", verify_model_files),
        ("Python 檔案語法", verify_python_files),
        ("資料目錄", verify_data_directories)
    ]

    results = []
    for name, func in verifications:
        try:
            result = func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} 驗證過程中發生錯誤: {e}")
            results.append((name, False))

    # 總結
    print("\n" + "=" * 60)
    print("📊 驗證結果總結:")

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"  {name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 總體結果: {passed}/{total} 項驗證通過")

    if passed == total:
        print("🎉 基本驗證全部通過！檔案結構和語法正確。")
        print("\n📝 下一步:")
        print("  1. 安裝依賴套件: pip install -r requirements.txt")
        print("  2. 啟動應用程式: uvicorn src.main:app --reload")
        return 0
    else:
        print(f"⚠️  有 {total - passed} 項驗證失敗，請先修正問題。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n驗證過程被使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n驗證過程發生未預期的錯誤: {e}")
        sys.exit(1)