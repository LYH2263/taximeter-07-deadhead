import os
import tempfile

# 必须在 app.config / app.db 被导入前指向临时目录，避免污染开发库
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="taximeter-test-")
