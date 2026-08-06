import os
os.environ.setdefault('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
os.environ.setdefault('SECRET_KEY', 'TEST-SECRET-KEY-ONLY-CHANGE-IN-PRODUCTION-123456789')
