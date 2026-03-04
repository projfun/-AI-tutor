"""
Test script for Portal Client with BrowserConnector.
"""

from portal import SchoolPortalClient
from datetime import date
import json
import sys


def test_portal():
    """Testing main functions of SchoolPortalClient."""
    print("=" * 50)
    print("TESTING AI-TUTOR PORTAL CLIENT")
    print("=" * 50)
    
    # Create client
    print("\n1. Creating client...")
    client = SchoolPortalClient()
    print("   [OK] Client created")
    
    # Test getting profile
    print("\n2. Getting profile via BrowserConnector...")
    try:
        profile = client.get_profile()
        if profile and profile.get('name') != 'Student':
            print(f"   [OK] Profile received: {profile.get('name')}")
            print(f"   [INFO] Class: {profile.get('class')}")
        else:
            print("   [WARN] Profile not loaded (authorization may be needed in browser)")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test getting schedule
    print("\n3. Getting schedule via BrowserConnector...")
    try:
        schedule = client.get_schedule(date.today())
        if schedule and schedule.get('lessons'):
            print(f"   [OK] Schedule received: {schedule['total_lessons']} lessons")
            for lesson in schedule['lessons'][:3]:  # Show first 3 lessons
                print(f"      {lesson['number']}. {lesson['subject']} ({lesson['start_time']})")
        else:
            print("   [WARN] Schedule not loaded (authorization may be needed in browser)")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test JSON export
    print("\n4. Testing JSON export...")
    try:
        json_str = client.get_schedule_as_json()
        # Verify it's valid JSON
        data = json.loads(json_str)
        print(f"   [OK] JSON is valid, keys: {list(data.keys())}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test full export
    print("\n5. Testing full export to file...")
    try:
        filepath = client.export_to_json(data_type='all')
        print(f"   [OK] Data exported to: {filepath}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Close connection
    print("\n6. Closing connection...")
    client.close()
    print("   [OK] Connection closed")
    
    print("\n" + "=" * 50)
    print("TESTING COMPLETED")
    print("=" * 50)
    print("\nNote: To get real data you need to:")
    print("   1. Login to https://authedu.mosreg.ru/ in Chrome")
    print("   2. Run the client - it will connect to the browser via CDP")


def test_json_export_only():
    """Quick test of JSON export only, without browser."""
    print("\nTest JSON export...")
    client = SchoolPortalClient()
    
    # Try to get data
    schedule = client.get_schedule()
    
    if schedule:
        # Export
        filepath = client.export_to_json(data_type='schedule')
        print(f"[OK] Schedule saved to: {filepath}")
        
        # Show content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\nJSON Content:")
            print(content[:500] + "..." if len(content) > 500 else content)
    else:
        print("[WARN] Schedule not received")
    
    client.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_json_export_only()
    else:
        test_portal()
