from psexec import PsExecManager
from pathlib import Path

current_ip = '55.184.87.205'
current_hostname = 'P118301-071-003'


SCRIPT_DIR = Path(__file__).parent
LOG_PATH = SCRIPT_DIR / "tmp"
BIN_PATH = SCRIPT_DIR / "bin"
psexec_path = SCRIPT_DIR / "bin" / 'PsExec64.exe'

psexec = PsExecManager(current_ip,netbios=current_hostname ,psexec_path=str(psexec_path),tmp_dir=LOG_PATH)

result = psexec.get_distinguished_name()
print(result)
result = psexec.get_product_name()
print(result)
result = psexec.get_display_version()
print(result)
result = psexec.get_active_user()
print(result)