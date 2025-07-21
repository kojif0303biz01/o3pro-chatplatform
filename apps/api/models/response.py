"""
レスポンスモデル定義
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    """セッションレスポンス"""
    id: str = Field(..., description="セッションID")
    title: str = Field(..., description="セッションタイトル")
    user_id: str = Field(..., description="ユーザーID")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")
    mode: str = Field(..., description="現在のモード")
    effort: str = Field(..., description="現在のeffort")
    message_count: int = Field(..., description="メッセージ数")


class MessageResponse(BaseModel):
    """メッセージレスポンス"""
    success: bool = Field(..., description="処理成功フラグ")
    response: Optional[str] = Field(None, description="レスポンステキスト")
    job_id: Optional[str] = Field(None, description="ジョブID（backgroundモード）")
    duration: Optional[float] = Field(None, description="処理時間（秒）")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class JobStatusResponse(BaseModel):
    """ジョブステータスレスポンス"""
    success: bool = Field(..., description="取得成功フラグ")
    job_id: str = Field(..., description="ジョブID")
    status: Literal["pending", "processing", "completed", "failed", "cancelled"] = Field(..., description="ジョブステータス")
    elapsed_time: float = Field(..., description="経過時間（秒）")
    effort: str = Field(..., description="処理レベル")
    question: Optional[str] = Field(None, description="元の質問")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class JobResultResponse(BaseModel):
    """ジョブ結果レスポンス"""
    success: bool = Field(..., description="取得成功フラグ")
    job_id: str = Field(..., description="ジョブID")
    response: Optional[str] = Field(None, description="レスポンステキスト")
    question: str = Field(..., description="元の質問")
    effort: str = Field(..., description="処理レベル")
    total_time: float = Field(..., description="総処理時間（秒）")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class HistoryMessage(BaseModel):
    """履歴メッセージ"""
    id: str = Field(..., description="メッセージID")
    role: Literal["user", "assistant"] = Field(..., description="送信者ロール")
    content: str = Field(..., description="メッセージ内容")
    timestamp: str = Field(..., description="タイムスタンプ")
    sender: str = Field(..., description="送信者表示名")


class HistoryResponse(BaseModel):
    """履歴レスポンス"""
    session_id: str = Field(..., description="セッションID")
    messages: List[HistoryMessage] = Field(..., description="メッセージリスト")
    total_count: int = Field(..., description="総メッセージ数")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: Dict[str, Any] = Field(..., description="エラー詳細")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = Field(..., description="ステータス")
    service: str = Field(..., description="サービス名")
    timestamp: str = Field(..., description="タイムスタンプ")


class ApiInfoResponse(BaseModel):
    """API情報レスポンス"""
    title: str = Field(..., description="APIタイトル")
    description: str = Field(..., description="API説明")
    version: str = Field(..., description="バージョン")
    features: Dict[str, bool] = Field(..., description="機能フラグ")