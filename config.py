# Flask configurations
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit
JSONIFY_PRETTYPRINT_REGULAR = False
PREVENT_UNSAFE_SERIALIZATION = True

# Gunicorn configurations (used in gunicorn.conf.py)
workers = 4
worker_class = 'gevent'
worker_connections = 100
timeout = 300
bind = '0.0.0.0:5000'
preload = True