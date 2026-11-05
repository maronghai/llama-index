"""Install the exact versions used for integration verification."""
import subprocess
import sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                       'llama-index-core==0.14.25', 'fastapi==0.162.0',
                       'uvicorn==0.54.0', 'httpx==0.28.1', 'pytest==9.2.0'])
