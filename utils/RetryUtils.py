import time
from typing import Callable, Any

class RetryUtils:
    @staticmethod
    def run_with_retry(func: Callable, *args: Any, try_limit: int, delay: int):
        tries = 0
        while tries < try_limit:
            try:
                return func(*args)
            except Exception as e:
                tries += 1
                if tries >= try_limit:
                    raise RecursionError(f"Function {func.__name__} failed after {try_limit} attempts: {str(e)}")
                time.sleep(delay)
