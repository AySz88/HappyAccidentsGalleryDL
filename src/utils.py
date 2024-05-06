import os
import requests
import json
from urllib.parse import urlparse
from typing import Dict

class Cache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir

    def get(self, key: str):
        cache_file = os.path.join(self.cache_dir, f'{key}.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as file:
                return json.load(file)
        else:
            return None

    def set(self, key: str, value: Dict):
        cache_file = os.path.join(self.cache_dir, f'{key}.json')
        with open(cache_file, 'w') as file:
            json.dump(value, file)

class Backoff:
    def __init__(self, initial: float = 1.0, maxTime: float = 32, minTime: float = 0.5):
        self.max = maxTime
        self.min = minTime
        self._current = min(max(initial, self.min), self.max)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = min(max(value, self.min), self.max)

    def increment(self):
        self.current *= 1.41421356  # 2.0^0.5

    def decrement(self):
        self.current *= 0.933032992  # 2.0^-0.1

    def be_nice(self, download_time):
        if download_time > 1.0 and download_time > self.current:
            self.current = (download_time + self.current) / 2.0
        else:
            self.decrement()

def is_successful_status(r: requests.Response) -> bool:
    return 200 <= r.status_code < 300

def create_directory(directory):
    """
    Creates a directory if it doesn't exist.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
