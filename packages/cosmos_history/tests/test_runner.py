"""
統合テストランナー

全てのテストを実行し、結果をまとめて表示
"""

import sys
import time
from typing import Dict, List, Tuple

def run_all_tests() -> Dict[str, bool]:
    """全テスト実行"""
    print("=" * 60)
    print("🧪 Cosmos History モジュール 統合テスト開始")
    print("=" * 60)
    
    test_results = {}
    total_start_time = time.time()
    
    # テストモジュールリスト
    test_modules = [
        ("データモデル", "test_models", "run_model_tests"),
        ("Cosmos DBクライアント", "test_cosmos_client", "run_cosmos_client_tests"),
        ("履歴管理", "test_history_manager", "run_history_manager_tests"),
        ("検索サービス", "test_search_service", "run_search_service_tests"),
        ("移行サービス", "test_migration_service", "run_migration_service_tests")
    ]
    
    # 各テストモジュール実行
    for module_name, module_file, test_function in test_modules:
        print(f"\n📋 {module_name}テスト開始...")
        start_time = time.time()
        
        try:
            # PYTHONPATHにカレントディレクトリを追加
            import sys
            if '.' not in sys.path:
                sys.path.append('.')
            
            # モジュール動的インポート
            module = __import__(f"cosmos_history.tests.{module_file}", fromlist=[test_function])
            test_func = getattr(module, test_function)
            
            # テスト実行
            result = test_func()
            test_results[module_name] = result
            
            duration = time.time() - start_time
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"   {status} ({duration:.2f}秒)")
            
        except Exception as e:
            test_results[module_name] = False
            duration = time.time() - start_time
            print(f"   ❌ エラー: {e} ({duration:.2f}秒)")
    
    # 結果サマリー
    total_duration = time.time() - total_start_time
    print_test_summary(test_results, total_duration)
    
    return test_results


def print_test_summary(results: Dict[str, bool], total_duration: float):
    """テスト結果サマリー表示"""
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"実行時間: {total_duration:.2f}秒")
    print(f"成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    print()
    
    # 詳細結果
    for module_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {status} {module_name}")
    
    print("\n" + "=" * 60)
    
    if success_count == total_count:
        print("🎉 全テストが成功しました！")
    else:
        print(f"⚠️  {total_count - success_count}個のテストが失敗しました")
        print("詳細なエラー情報は上記のログを確認してください")
    
    print("=" * 60)


def run_specific_test(test_name: str) -> bool:
    """特定のテストのみ実行"""
    test_mapping = {
        "models": ("test_models", "run_model_tests"),
        "client": ("test_cosmos_client", "run_cosmos_client_tests"),
        "history": ("test_history_manager", "run_history_manager_tests"),
        "search": ("test_search_service", "run_search_service_tests"),
        "migration": ("test_migration_service", "run_migration_service_tests")
    }
    
    if test_name not in test_mapping:
        print(f"❌ 不明なテスト名: {test_name}")
        print(f"利用可能なテスト: {', '.join(test_mapping.keys())}")
        return False
    
    module_file, test_function = test_mapping[test_name]
    
    print(f"🧪 {test_name}テスト実行中...")
    start_time = time.time()
    
    try:
        # PYTHONPATHにカレントディレクトリを追加
        import sys
        if '.' not in sys.path:
            sys.path.append('.')
            
        module = __import__(f"cosmos_history.tests.{module_file}", fromlist=[test_function])
        test_func = getattr(module, test_function)
        result = test_func()
        
        duration = time.time() - start_time
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{status} ({duration:.2f}秒)")
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ エラー: {e} ({duration:.2f}秒)")
        return False


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        # 特定のテスト実行
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # 全テスト実行
        results = run_all_tests()
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        sys.exit(0 if success_count == total_count else 1)


if __name__ == "__main__":
    main()