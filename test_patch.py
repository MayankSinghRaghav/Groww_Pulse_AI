import sys
import six
import urllib3

# Monkey patch for app-store-scraper
if not hasattr(urllib3, 'packages'):
    urllib3.packages = type('packages', (), {'six': six})()
    sys.modules['urllib3.packages'] = urllib3.packages
    sys.modules['urllib3.packages.six'] = six
    sys.modules['urllib3.packages.six.moves'] = six.moves

try:
    from app_store_scraper import AppStore
    print("Success! AppStore imported.")
except Exception as e:
    print("Failed:", e)
