#!/usr/bin/env python3
"""
開発環境用の起動スクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages"))

# 環境変数読み込み
from dotenv import load_dotenv
load_dotenv(project_root / ".env")
load_dotenv(project_root / ".env.cosmos")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting O3-Pro Chat API on port {port}")
    print(f"📁 Project root: {project_root}")
    print(f"🔗 API: http://localhost:{port}")
    print(f"📚 Docs: http://localhost:{port}/docs")
    
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
        reload_dirs=[str(project_root)]
    )