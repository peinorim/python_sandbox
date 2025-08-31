from os import getenv

from redis import StrictRedis


class RedisCache:

    def __init__(self):
        self.conn = StrictRedis()

    def get(self, name=None):
        if not getenv('REDIS_HOST'):
            return {}
        return self.conn.get(name)

    def set(self, name=None, data=None, ex=None):
        if not getenv('REDIS_HOST'):
            return {}
        return self.conn.set(name, data, ex=ex)