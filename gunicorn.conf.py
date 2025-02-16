import multiprocessing

# Number of workers = (2 * CPU cores) + 1
workers = 3
worker_class = 'gevent'
worker_connections = 100
timeout = 300
bind = '0.0.0.0:8080'
preload = True