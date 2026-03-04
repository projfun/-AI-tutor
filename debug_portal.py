import requests
from datetime import date
import json
import urllib3
import ssl

# Отключаем предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Пытаемся решить проблему с SSL (Legacy renegotiation)
class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

COOKIES = "aupd_token=eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxNTczODIyIiwic2NwIjoib3BlbmlkIHByb2ZpbGUiLCJtc2giOiI2OWE4YzJmOC1lMmJmLTRkZWMtOGZiZC04ZDEwNjg5MDA0MmUiLCJpc3MiOiJodHRwczpcL1wvYXV0aGVkdS5tb3NyZWcucnUiLCJyb2wiOiIiLCJzc28iOiIxMjEwNjQ2OTYwIiwiYXVkIjoiMjoxIiwibmJmIjoxNzcyNjIwODk5LCJhdGgiOiJlc2lhIiwicmxzIjoiezE6WzIwOjI6W10sMzA6NDpbXSw0MDoxOltdLDE4MzoxNjpbXSwyMTE6MTk6W10sNTMzOjQ4OltdXX0iLCJyZ24iOiI1MCIsImV4cCI6MTc3MzQ4NDg5NiwiaWF0IjoxNzcyNjIwODk5LCJqdGkiOiJmZmY1NmMyNC0xNDNmLTQwMWQtYjU2Yy0yNDE0M2Y1MDFkOWQifQ.bKcFOugJK0RJwITvweNkeTMwiQ2sbGMP_zP51oX3hs6o8pk_ETAi9zlD_DP_7OC9Il3DX5Hor8Q4VQRWFUY9rcUX_Nk90DoTNtHlpzLQ8YnsKCJu37aLGEU_RkoF5ws-ybeT6mQKQHHb2pCQEt06NkAL4jgq6R86cXGEIRiD4Vw0sdAHpA4ZKOvSc7xx7sGERx9ukI8T1KTOiFJitOFsvfCqqDLlZ2nnAIAvxH3RLVFmdJmaJ0gx-AzHMIAWfIfhZcNKvGuoDDJ9qHQyRqjdLbrumAzKSa2fS5Zf4R_Ox7GpKbrUVmbCZ_HU8Vh7U7kwBaYpGvWhKQePXoRf8A_REg; active_student=1226456; aupd_current_role=2:1"

DIARY_API = "https://diary.mosreg.ru"

def test_portal():
    session = requests.Session()
    session.mount("https://", TLSAdapter())
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    
    for pair in COOKIES.split(';'):
        if '=' in pair:
            key, value = pair.strip().split('=', 1)
            session.cookies.set(key, value, domain='.mosreg.ru')
    
    print(f"--- Проверка профиля ---")
    try:
        r = session.get(f"{DIARY_API}/api/v2/user/profile", timeout=15)
        print(f"Profile API v2 Status: {r.status_code}")
        if r.status_code == 200:
            print("Profile OK")
        else:
            print(f"Error: {r.text[:200]}")
    except Exception as e:
        print(f"Profile error: {e}")

if __name__ == "__main__":
    test_portal()
