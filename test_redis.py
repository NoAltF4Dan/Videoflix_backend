import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.cache import cache

try:
    cache.set('test_key', 'Hello from Django!', timeout=60)
    value = cache.get('test_key')
    
    if value:
        print("✅ Django-Redis connection successful!")
        print(f"✅ Retrieved value: {value}")
        cache.delete('test_key')
        print("✅ Cache operations working correctly")
    else:
        print("❌ Could not retrieve cached value")
        
except Exception as error:
    print(f"❌ Django-Redis connection failed: {error}")