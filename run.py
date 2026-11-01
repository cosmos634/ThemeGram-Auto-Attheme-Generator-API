import os

import uvicorn

from app.config import validate_startup_config


if __name__ == "__main__":
    validate_startup_config()
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
