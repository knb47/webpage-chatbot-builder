#!/usr/bin/env python
#!/usr/bin/env python
import os
import sys
from dotenv import load_dotenv

def main():
    # Determine which environment file to load
    print(f"DJANGO_ENV: {os.environ.get('DJANGO_ENV')}")
    env_file = '.env.prod' if os.environ.get('DJANGO_ENV') == 'production' else '.env.dev'
    load_dotenv(env_file)
    
    # Set the appropriate settings module
    if os.environ.get('DJANGO_ENV') == 'production':
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.production')
        print(f"Using production settings: live views, no debug, etc.")
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
        print(f"Using development settings: mock views, debug, etc.")
    
    try:
        from django.core.management import execute_from_command_line
        from django.conf import settings
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
