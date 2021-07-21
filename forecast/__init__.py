import os

import redis
from flask_caching import Cache


class RedisCache:

    def __init__(self, app=None):
        self.app = app

    def get_cache(self):
        try:
            rs = redis.StrictRedis(
                host=os.environ.get('REDIS_HOST', '127.0.0.1'),
                port=os.environ.get('REDIS_PORT', '6379'),
                db=os.environ.get('REDIS_DB', '0'),
                password=os.environ.get('REDIS_PASSWORD', '')
            )
            rs.ping()
            return Cache(self.app.server, config={
                'CACHE_TYPE': 'redis',
                'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', '127.0.0.1'),
                'CACHE_REDIS_PORT': os.environ.get('REDIS_PORT', '6379'),
                'CACHE_REDIS_DB': os.environ.get('REDIS_DB', '0'),
                'CACHE_REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD', '')
            })
        except ConnectionError:
            return Cache(self.app.server, config={
                'CACHE_TYPE': 'filesystem',
                'CACHE_DIR': 'cache-directory'
            })
