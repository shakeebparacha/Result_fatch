import os

from redis import Redis
from rq import Connection, Worker


def main():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL is not set. Configure Redis before running the worker.")

    redis_conn = Redis.from_url(redis_url)
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
