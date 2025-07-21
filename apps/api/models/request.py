"""
リクエストモデル定義
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """セッション作成リクエスト"""
    title: Optional[str] = Field(None, description="セッションタイトル")
    user_id: Optional[str] = Field("default", description="ユーザーID")
    mode: Optional[Literal["reasoning", "streaming", "background"]] = Field("reasoning", description="チャットモード")
    effort: Optional[Literal["low", "medium", "high"]] = Field("low", description="処理レベル")


class UpdateSessionModeRequest(BaseModel):
    """セッションモード更新リクエスト"""
    mode: Literal["reasoning", "streaming", "background"] = Field(..., description="チャットモード")
    effort: Literal["low", "medium", "high"] = Field("low", description="処理レベル")


class SendMessageRequest(BaseModel):
    """メッセージ送信リクエスト"""
    message: str = Field(..., description="メッセージ内容", min_length=1, max_length=4000)
    session_id: str = Field(..., description="セッションID")


class GetHistoryRequest(BaseModel):
    """履歴取得リクエスト"""
    limit: int = Field(50, description="取得件数", ge=1, le=200)