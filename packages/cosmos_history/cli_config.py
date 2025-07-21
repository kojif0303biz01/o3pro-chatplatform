"""
設定管理 CLI ツール

コマンドライン用の設定管理ユーティリティ
"""

import argparse
import sys
from pathlib import Path

# モジュールパス設定
if '.' not in sys.path:
    sys.path.append('.')

from cosmos_history.config_manager import run_config_diagnostics, create_config_manager
from cosmos_history.config import load_config_from_env


def cmd_show_config(args):
    """設定表示コマンド"""
    try:
        config = load_config_from_env()
        manager = create_config_manager(config)
        manager.display_config(mask_secrets=not args.show_secrets)
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def cmd_validate_config(args):
    """設定検証コマンド"""
    try:
        config = load_config_from_env()
        manager = create_config_manager(config)
        return manager.print_validation_result()
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def cmd_check_required(args):
    """必須設定チェックコマンド"""
    try:
        config = load_config_from_env()
        manager = create_config_manager(config)
        return manager.print_required_settings_check()
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def cmd_diagnostics(args):
    """設定診断コマンド"""
    return run_config_diagnostics()


def cmd_export_config(args):
    """設定出力コマンド"""
    try:
        config = load_config_from_env()
        manager = create_config_manager(config)
        manager.export_config(args.output, include_secrets=args.include_secrets)
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def cmd_suggest_env(args):
    """環境ファイル提案コマンド"""
    try:
        config = load_config_from_env()
        manager = create_config_manager(config)
        suggestions = manager.suggest_env_file_content()
        
        if suggestions:
            print("📝 推奨 .env 設定:")
            print(suggestions)
        else:
            print("✅ 現在の設定に問題はありません")
        
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def create_parser():
    """CLI パーサー作成"""
    parser = argparse.ArgumentParser(
        description="Cosmos History 設定管理ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定診断実行
  python cosmos_history/cli_config.py diagnostics

  # 設定表示（秘密情報マスク）
  python cosmos_history/cli_config.py show

  # 設定表示（秘密情報含む）
  python cosmos_history/cli_config.py show --show-secrets

  # 設定検証のみ
  python cosmos_history/cli_config.py validate

  # 必須設定チェックのみ
  python cosmos_history/cli_config.py check-required

  # 設定をJSONファイルに出力
  python cosmos_history/cli_config.py export config.json

  # 推奨 .env 設定を表示
  python cosmos_history/cli_config.py suggest-env
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # diagnostics コマンド
    diagnostics_parser = subparsers.add_parser(
        'diagnostics', 
        help='全体的な設定診断を実行'
    )
    diagnostics_parser.set_defaults(func=cmd_diagnostics)
    
    # show コマンド
    show_parser = subparsers.add_parser(
        'show', 
        help='現在の設定を表示'
    )
    show_parser.add_argument(
        '--show-secrets', 
        action='store_true',
        help='秘密情報もマスクせずに表示'
    )
    show_parser.set_defaults(func=cmd_show_config)
    
    # validate コマンド
    validate_parser = subparsers.add_parser(
        'validate', 
        help='設定検証のみ実行'
    )
    validate_parser.set_defaults(func=cmd_validate_config)
    
    # check-required コマンド
    check_parser = subparsers.add_parser(
        'check-required', 
        help='必須設定チェックのみ実行'
    )
    check_parser.set_defaults(func=cmd_check_required)
    
    # export コマンド
    export_parser = subparsers.add_parser(
        'export', 
        help='設定をJSONファイルに出力'
    )
    export_parser.add_argument(
        'output',
        help='出力ファイルパス'
    )
    export_parser.add_argument(
        '--include-secrets',
        action='store_true',
        help='秘密情報も含めて出力'
    )
    export_parser.set_defaults(func=cmd_export_config)
    
    # suggest-env コマンド
    suggest_parser = subparsers.add_parser(
        'suggest-env',
        help='推奨 .env 設定を表示'
    )
    suggest_parser.set_defaults(func=cmd_suggest_env)
    
    return parser


def main():
    """メイン関数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        success = args.func(args)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによって中断されました")
        return 1
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())