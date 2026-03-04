from portal import SchoolPortalClient
from datetime import date
import json

COOKIES = "aupd_token=eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxNTczODIyIiwic2NwIjoib3BlbmlkIHByb2ZpbGUiLCJtc2giOiI2OWE4YzJmOC1lMmJmLTRkZWMtOGZiZC04ZDEwNjg5MDA0MmUiLCJpc3MiOiJodHRwczpcL1wvYXV0aGVkdS5tb3NyZWcucnUiLCJyb2wiOiIiLCJzc28iOiIxMjEwNjQ2OTYwIiwiYXVkIjoiMjoxIiwibmJmIjoxNzcyNjIwODk5LCJhdGgiOiJlc2lhIiwicmxzIjoiezE6WzIwOjI6W10sMzA6NDpbXSw0MDoxOltdLDE4MzoxNjpbXSwyMTE6MTk6W10sNTMzOjQ4OltdXX0iLCJyZ24iOiI1MCIsImV4cCI6MTc3MzQ4NDg5NiwiaWF0IjoxNzcyNjIwODk5LCJqdGkiOiJmZmY1NmMyNC0xNDNmLTQwMWQtYjU2Yy0yNDE0M2Y1MDFkOWQifQ.bKcFOugJK0RJwITvweNkeTMwiQ2sbGMP_zP51oX3hs6o8pk_ETAi9zlD_DP_7OC9Il3DX5Hor8Q4VQRWFUY9rcUX_Nk90DoTNtHlpzLQ8YnsKCJu37aLGEU_RkoF5ws-ybeT6mQKQHHb2pCQEt06NkAL4jgq6R86cXGEIRiD4Vw0sdAHpA4ZKOvSc7xx7sGERx9ukI8T1KTOiFJitOFsvfCqqDLlZ2nnAIAvxH3RLVFmdJmaJ0gx-AzHMIAWfIfhZcNKvGuoDDJ9qHQyRqjdLbrumAzKSa2fS5Zf4R_Ox7GpKbrUVmbCZ_HU8Vh7U7kwBaYpGvWhKQePXoRf8A_REg; active_student=1226456; aupd_current_role=2:1"

def test_portal_final():
    client = SchoolPortalClient(COOKIES)
    
    print("--- Проверка авторизации ---")
    if client.verify_cookies():
        print("Авторизация успешна!")
        
        print("\n--- Проверка профиля ---")
        profile = client.get_profile()
        print(f"Профиль: {profile}")
        
        print("\n--- Проверка расписания ---")
        schedule = client.get_schedule(date.today())
        if schedule:
            print(f"Найдено уроков: {len(schedule.get('lessons', []))}")
            for lesson in schedule.get('lessons', []):
                print(f"{lesson['number']}. {lesson['subject']} ({lesson['start_time']} - {lesson['end_time']})")
                if lesson.get('homework'):
                    print(f"   ДЗ: {lesson['homework']}")
        else:
            print("Расписание не получено")
    else:
        print("Куки недействительны!")

if __name__ == "__main__":
    test_portal_final()
