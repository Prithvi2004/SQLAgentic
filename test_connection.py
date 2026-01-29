"""
Quick test script to verify database connection and Ollama availability.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 80)
print("SQL Agent - System Test")
print("=" * 80)

# Test 1: Database Connection
print("\n1️⃣ Testing Database Connection...")
try:
    from db_manager import DatabaseManager
    
    db = DatabaseManager(
        'Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=BackupDB;Trusted_Connection=yes;'
    )
    
    if db.test_connection():
        print("   ✅ Database connection successful!")
        
        # Try to get schema
        print("\n2️⃣ Testing Schema Extraction...")
        schema = db.get_schema_summary()
        print(f"   ✅ Schema extracted successfully!")
        print(f"   Preview (first 500 chars):\n")
        print(schema[:500])
        
    db.close()
    
except Exception as e:
    print(f"   ❌ Database test failed: {e}")
    print("\n   Troubleshooting:")
    print("   - Ensure SQL Server is running")
    print("   - Verify BackupDB database exists")
    print("   - Check ODBC Driver 17 is installed")

# Test 2: Ollama Connection
print("\n" + "=" * 80)
print("3️⃣ Testing Ollama Connection...")
try:
    import ollama
    
    client = ollama.Client(host='http://localhost:11434')
    
    # Try a simple test
    response = client.chat(
        model='deepseek-v3.1:671b-cloud',
        messages=[
            {'role': 'user', 'content': 'Say "test successful" and nothing else.'}
        ]
    )
    
    print(f"   ✅ Ollama connection successful!")
    print(f"   Model response: {response['message']['content']}")
    
except Exception as e:
    print(f"   ❌ Ollama test failed: {e}")
    print("\n   Troubleshooting:")
    print("   - Ensure Ollama is running: ollama serve")
    print("   - Verify model is pulled: ollama pull deepseek-v3.1:671b-cloud")
    print("   - Check Ollama is accessible at http://localhost:11434")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
