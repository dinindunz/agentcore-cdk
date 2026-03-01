"""Query caching with 15-minute TTL."""

import time
from functools import lru_cache


@lru_cache(maxsize=100)
def cached_query_results(query_hash: str, cache_key: int, query_func, *args, **kwargs):
    """Cache CloudWatch query results with time-based expiration.

    Args:
        query_hash: Hash of the query string
        cache_key: Time bucket for cache expiration (timestamp // 900 for 15min buckets)
        query_func: Function to execute if cache miss
        *args: Arguments for query_func
        **kwargs: Keyword arguments for query_func

    Returns:
        Query results from cache or fresh execution
    """
    return query_func(*args, **kwargs)


def get_cache_key():
    """Get current cache key (15-minute time bucket).

    Returns:
        Integer cache key for current 15-minute window
    """
    return int(time.time() // 900)  # 900 seconds = 15 minutes


def run_cached_query(query_func, *args, **kwargs):
    """Execute query with caching.

    Args:
        query_func: CloudWatch query function to execute
        *args: Arguments for query function
        **kwargs: Keyword arguments for query function

    Returns:
        Cached or fresh query results
    """
    # Create query signature for caching
    query_hash = hash((query_func.__name__, str(args), str(kwargs)))
    cache_key = get_cache_key()

    return cached_query_results(str(query_hash), cache_key, query_func, *args, **kwargs)
