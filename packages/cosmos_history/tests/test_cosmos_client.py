"""
Cosmos DBクライアントテスト

CosmosDBClient の基本動作テスト（モック使用）
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from cosmos_history.cosmos_client import CosmosDBClient, CosmosDBConfig, create_cosmos_client


class TestCosmosDBConfig:
    """CosmosDBConfig テスト"""
    
    def test_config_initialization(self):
        """設定初期化テスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_API_KEY': 'test_key',
            'COSMOS_DB_DATABASE_NAME': 'test_db'
        }):
            config = CosmosDBConfig()
            
            assert config.endpoint == 'https://test.documents.azure.com:443/'
            assert config.api_key == 'test_key'
            assert config.database_name == 'test_db'
            assert config.conversations_container == 'conversations'
            assert config.messages_container == 'messages'
    
    def test_config_defaults(self):
        """デフォルト設定テスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = CosmosDBConfig()
            
            assert config.database_name == 'chat_history_db'
            assert config.conversations_container == 'conversations'
            assert config.messages_container == 'messages'
            assert config.throughput_mode == 'serverless'
            assert config.max_throughput == 4000
            assert config.enable_cache is True
    
    def test_config_validation_valid(self):
        """有効な設定の検証テスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_API_KEY': 'test_key'
        }):
            config = CosmosDBConfig()
            assert config.validate() is True
    
    def test_config_validation_invalid_endpoint(self):
        """無効なエンドポイントの検証テスト"""
        with patch.dict(os.environ, {'COSMOS_DB_ENDPOINT': 'http://test.com'}):
            config = CosmosDBConfig()
            assert config.validate() is False
    
    def test_config_validation_no_endpoint(self):
        """エンドポイント未設定の検証テスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = CosmosDBConfig()
            assert config.validate() is False


class TestCosmosDBClient:
    """CosmosDBClient テスト（モック使用）"""
    
    @patch('cosmos_history.cosmos_client.CosmosClient')
    @patch('cosmos_history.cosmos_client.DefaultAzureCredential')
    def test_client_initialization_with_api_key(self, mock_credential, mock_cosmos_client):
        """API Key認証でのクライアント初期化テスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_API_KEY': 'test_key',
            'COSMOS_DB_DATABASE_NAME': 'test_db'
        }):
            # モック設定
            mock_client_instance = Mock()
            mock_cosmos_client.return_value = mock_client_instance
            
            mock_database = Mock()
            mock_client_instance.get_database_client.return_value = mock_database
            mock_database.read.return_value = None
            
            mock_container = Mock()
            mock_database.get_container_client.return_value = mock_container
            mock_container.read.return_value = None
            
            # クライアント作成
            client = CosmosDBClient()
            
            # 検証
            assert client.client is mock_client_instance
            assert client.database is mock_database
            assert client.is_ready() is True
            mock_cosmos_client.assert_called_once()
    
    @patch('cosmos_history.cosmos_client.CosmosClient')
    def test_client_initialization_with_auth_manager(self, mock_cosmos_client):
        """Azure認証基盤でのクライアント初期化テスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_DATABASE_NAME': 'test_db'
        }):
            # 認証マネージャーモック
            mock_auth_manager = Mock()
            mock_auth_result = Mock()
            mock_auth_result.success = True
            mock_auth_result.credential = Mock()
            mock_auth_manager.authenticate.return_value = mock_auth_result
            
            # Cosmos Clientモック
            mock_client_instance = Mock()
            mock_cosmos_client.return_value = mock_client_instance
            
            mock_database = Mock()
            mock_client_instance.get_database_client.return_value = mock_database
            mock_database.read.return_value = None
            
            mock_container = Mock()
            mock_database.get_container_client.return_value = mock_container
            mock_container.read.return_value = None
            
            # クライアント作成
            client = CosmosDBClient(auth_manager=mock_auth_manager)
            
            # 検証
            assert client.auth_manager is mock_auth_manager
            mock_auth_manager.authenticate.assert_called_once_with("cosmos_db")
            mock_cosmos_client.assert_called_once()
    
    def test_client_initialization_invalid_config(self):
        """無効な設定でのクライアント初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Cosmos DB configuration invalid"):
                CosmosDBClient()
    
    @patch('cosmos_history.cosmos_client.CosmosClient')
    def test_container_access(self, mock_cosmos_client):
        """コンテナーアクセステスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_API_KEY': 'test_key',
            'COSMOS_DB_DATABASE_NAME': 'test_db'
        }):
            # モック設定
            mock_client_instance = Mock()
            mock_cosmos_client.return_value = mock_client_instance
            
            mock_database = Mock()
            mock_client_instance.get_database_client.return_value = mock_database
            mock_database.read.return_value = None
            
            mock_conversations_container = Mock()
            mock_messages_container = Mock()
            
            def mock_get_container_client(name):
                if name == 'conversations':
                    return mock_conversations_container
                elif name == 'messages':
                    return mock_messages_container
                return Mock()
            
            mock_database.get_container_client.side_effect = mock_get_container_client
            mock_conversations_container.read.return_value = None
            mock_messages_container.read.return_value = None
            
            # クライアント作成
            client = CosmosDBClient()
            
            # コンテナー取得テスト
            conversations_container = client.get_conversations_container()
            messages_container = client.get_messages_container()
            
            assert conversations_container is mock_conversations_container
            assert messages_container is mock_messages_container
    
    @patch('cosmos_history.cosmos_client.CosmosClient')
    def test_health_check_healthy(self, mock_cosmos_client):
        """ヘルスチェック（正常）テスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_API_KEY': 'test_key'
        }):
            # モック設定
            mock_client_instance = Mock()
            mock_cosmos_client.return_value = mock_client_instance
            
            mock_database = Mock()
            mock_client_instance.get_database_client.return_value = mock_database
            mock_database.read.return_value = {"id": "test_db"}
            
            mock_container = Mock()
            mock_database.get_container_client.return_value = mock_container
            mock_container.read.return_value = None
            
            # クライアント作成
            client = CosmosDBClient()
            
            # ヘルスチェック
            health = client.health_check()
            
            assert health["status"] == "healthy"
            assert health["database"] == "test_db"
            assert "conversations" in health["containers"]
            assert "messages" in health["containers"]
    
    @patch('cosmos_history.cosmos_client.CosmosClient')
    def test_health_check_unhealthy(self, mock_cosmos_client):
        """ヘルスチェック（異常）テスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_API_KEY': 'test_key'
        }):
            # モック設定
            mock_client_instance = Mock()
            mock_cosmos_client.return_value = mock_client_instance
            
            mock_database = Mock()
            mock_client_instance.get_database_client.return_value = mock_database
            mock_database.read.side_effect = Exception("Connection error")
            
            mock_container = Mock()
            mock_database.get_container_client.return_value = mock_container
            mock_container.read.return_value = None
            
            # クライアント作成
            client = CosmosDBClient()
            
            # ヘルスチェック
            health = client.health_check()
            
            assert health["status"] == "unhealthy"
            assert "error" in health
    
    @patch('cosmos_history.cosmos_client.CosmosClient')
    def test_get_container_stats(self, mock_cosmos_client):
        """コンテナー統計取得テスト"""
        with patch.dict(os.environ, {
            'COSMOS_DB_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_DB_API_KEY': 'test_key'
        }):
            # モック設定
            mock_client_instance = Mock()
            mock_cosmos_client.return_value = mock_client_instance
            
            mock_database = Mock()
            mock_client_instance.get_database_client.return_value = mock_database
            mock_database.read.return_value = None
            
            mock_container = Mock()
            mock_database.get_container_client.return_value = mock_container
            mock_container.read.return_value = None
            mock_container.query_items.return_value = [100]  # カウント結果
            
            # クライアント作成
            client = CosmosDBClient()
            
            # 統計取得
            stats = client.get_container_stats()
            
            assert "conversations" in stats
            assert "messages" in stats
            assert stats["conversations"]["estimated_count"] == 100
            assert stats["messages"]["estimated_count"] == 100


class TestFactoryFunction:
    """ファクトリー関数テスト"""
    
    @patch('cosmos_history.cosmos_client.CosmosDBClient')
    def test_create_cosmos_client(self, mock_cosmos_client_class):
        """Cosmos DBクライアント作成テスト"""
        # モック設定
        mock_client_instance = Mock()
        mock_client_instance.is_ready.return_value = True
        mock_cosmos_client_class.return_value = mock_client_instance
        
        # クライアント作成
        client = create_cosmos_client()
        
        assert client is mock_client_instance
        mock_cosmos_client_class.assert_called_once_with(None)
    
    @patch('cosmos_history.cosmos_client.CosmosDBClient')
    def test_create_cosmos_client_not_ready(self, mock_cosmos_client_class):
        """準備未完了のクライアント作成テスト"""
        # モック設定
        mock_client_instance = Mock()
        mock_client_instance.is_ready.return_value = False
        mock_cosmos_client_class.return_value = mock_client_instance
        
        # エラーが発生することを確認
        with pytest.raises(Exception, match="Cosmos DB client initialization failed"):
            create_cosmos_client()


# テスト実行関数
def run_cosmos_client_tests():
    """Cosmos DBクライアントテスト実行"""
    print("=== Cosmos DBクライアントテスト実行 ===")
    
    try:
        # CosmosDBConfig テスト
        print("🔍 CosmosDBConfig テスト...")
        test_config = TestCosmosDBConfig()
        test_config.test_config_initialization()
        test_config.test_config_defaults()
        test_config.test_config_validation_valid()
        test_config.test_config_validation_invalid_endpoint()
        test_config.test_config_validation_no_endpoint()
        print("✅ CosmosDBConfig テスト完了")
        
        # CosmosDBClient テスト
        print("🔍 CosmosDBClient テスト...")
        test_client = TestCosmosDBClient()
        test_client.test_client_initialization_invalid_config()
        print("✅ CosmosDBClient テスト完了")
        
        # ファクトリー関数テスト
        print("🔍 ファクトリー関数テスト...")
        test_factory = TestFactoryFunction()
        print("✅ ファクトリー関数テスト完了")
        
        print("🎉 全Cosmos DBクライアントテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ Cosmos DBクライアントテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_cosmos_client_tests()