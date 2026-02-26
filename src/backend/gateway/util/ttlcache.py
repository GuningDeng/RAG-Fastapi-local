"""
Docstring for backend.gateway.util.ttlcache
@description: Automatically clear the cache of key-value pairs based on their expiration dates.
"""
import time
from threading import Lock, Thread

from enum import Enum

class Error(Enum):
    OK = 1
    FULL = -1
    EXPIRED = -2
    NOT_FOUND = -3

class Cache:
    def __init__(self, max_size, ttl):
        """
        initialize the cache class
        :param max_size: maximum size of cache
        :param ttl: each chache element's time-to-live (seconds)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}  # store cache data
        self.lock = Lock()  # for thread safety
        self._start_cleanup_thread()  # start cleanup thread

    def _start_cleanup_thread(self):
        """
        Start a background thread to periodically clean up expired cache.
        """
        def cleanup():
            while True:
                time.sleep(1)
                self._remove_expired_keys()

        thread = Thread(target=cleanup, daemon=True)
        thread.start()

    def _remove_expired_keys(self):
        """remove expired cache keys"""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expire_at) in self.cache.items()
                if expire_at <= current_time
            ]
            for key in expired_keys:
                del self.cache[key]
                print(f"clean up expired cache key: {key}")

    def add(self, key, value):
        """
        add cache element
        :param key: cache key
        :param value: cache value
        :raises CacheFullError: throws CacheFullError when cache is full
        """
        with self.lock:
            if key in self.cache:
                # if key is already exist, update the value and expire time
                self.cache[key] = (value, time.time() + self.ttl)
                return
            if len(self.cache) >= self.max_size:
                print("The cache is full, and no new element can be added.")  
                return Error.FULL
            self.cache[key] = (value, time.time() + self.ttl)
            return Error.OK

    def get(self, key):
        """
        get cache value
        :param key: cache key
        :return: cache value
        :raises KeyError: throws error when cache is full
        """
        with self.lock:
            if key in self.cache:
                value, expire_at = self.cache[key]
                if time.time() < expire_at:
                    return Error.OK, value
                else:
                    del self.cache[key]  # automatically clear expired keys
                    return Error.EXPIRED,None
            return Error.NOT_FOUND,None

    def is_full(self):
        """check if cache is full"""  
        with self.lock:
            return len(self.cache) >= self.max_size
        
    def __contains__(self, key):
        """
        check if key is exist in cache
        :param key: cache key
        :return: True or False. False if key exists and not expired, otherwise True
        """
        with self.lock:
            if key in self.cache:
                _, expire_at = self.cache[key]
                if time.time() < expire_at:
                    return True
                else:
                    del self.cache[key]
            return False

    def __len__(self):
        """get current number of elements in cache"""
        with self.lock:
            return len(self.cache)

    def clear(self):
        """clear all cache"""
        with self.lock:
            self.cache.clear()


# example usage
if __name__ == "__main__":
    cache = Cache(max_size=3, ttl=5)

    # add cache
    cache.add("key1", "value1")
    print("key1" in cache)  # True

    time.sleep(6)
    print("key1" in cache)  # False，expired

    # add multiple elements
    cache.add("key2", "value2")
    cache.add("key3", "value3")
    cache.add("key4", "value4")
    result = cache.add("key5", "value5")  # Exceeding the limit 
    print(f'add key5:{result}')  


    # get cache value
    result = cache.get("key2")  # normally get
    print(f'key2 is:{result}')
    time.sleep(6)
    result = cache.get("key2")  # expired
    print(result)