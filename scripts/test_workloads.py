#!/usr/bin/env python3
"""
Test script for profiling with py-spy.

This script runs a variety of workloads across multiple threads and async tasks:
- CPU-bound tasks (fibonacci, prime calculations, sorting)
- I/O-bound tasks (simulated network requests, file operations)
- Lock contention (shared resource access with synchronization)
- Async tasks (mixed CPU and I/O in async context)

Usage:
    python3 test_workloads.py

Press Ctrl+C to stop.
"""

import asyncio
import threading
import time
import os
import sys
from collections import defaultdict
from threading import Lock, Event
import random
import signal

# Global state tracking
class WorkloadTracker:
    def __init__(self):
        self.lock = Lock()
        self.counters = defaultdict(int)
        self.errors = defaultdict(int)
        self.start_time = time.time()

    def increment(self, workload_name):
        with self.lock:
            self.counters[workload_name] += 1

    def error(self, workload_name):
        with self.lock:
            self.errors[workload_name] += 1

    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            return dict(self.counters), dict(self.errors), elapsed

    def print_status(self):
        counters, errors, elapsed = self.get_stats()
        print(f"\n=== Status (elapsed: {elapsed:.1f}s) ===")
        total = sum(counters.values())
        print(f"Total tasks completed: {total}")
        for name in sorted(counters.keys()):
            count = counters[name]
            err = errors.get(name, 0)
            rate = count / elapsed if elapsed > 0 else 0
            err_str = f" ({err} errors)" if err > 0 else ""
            print(f"  {name}: {count} ({rate:.2f}/s){err_str}")

tracker = WorkloadTracker()
shutdown_event = Event()

# ============================================================================
# CPU-BOUND WORKLOADS
# ============================================================================

def fibonacci(n):
    """Compute fibonacci number recursively (CPU-bound)."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def cpu_fibonacci():
    """CPU-bound: Fibonacci calculation."""
    try:
        result = fibonacci(20)
        tracker.increment("cpu_fibonacci")
    except Exception as e:
        tracker.error("cpu_fibonacci")

def cpu_prime_check():
    """CPU-bound: Check if large number is prime."""
    try:
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0:
                    return False
            return True

        is_prime(982451653)
        tracker.increment("cpu_prime_check")
    except Exception as e:
        tracker.error("cpu_prime_check")

def cpu_sorting():
    """CPU-bound: Sort large list."""
    try:
        data = [random.random() for _ in range(10000)]
        sorted(data)
        tracker.increment("cpu_sorting")
    except Exception as e:
        tracker.error("cpu_sorting")

def cpu_matrix_multiply():
    """CPU-bound: Matrix multiplication."""
    try:
        size = 50
        matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
        matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]

        result = [[sum(matrix_a[i][k] * matrix_b[k][j] for k in range(size))
                   for j in range(size)] for i in range(size)]
        tracker.increment("cpu_matrix_multiply")
    except Exception as e:
        tracker.error("cpu_matrix_multiply")

def cpu_sha256():
    """CPU-bound: SHA256 hashing."""
    try:
        import hashlib
        data = b"x" * 100000
        for _ in range(100):
            hashlib.sha256(data).hexdigest()
        tracker.increment("cpu_sha256")
    except Exception as e:
        tracker.error("cpu_sha256")

# ============================================================================
# I/O-BOUND WORKLOADS (SIMULATED)
# ============================================================================

def io_sleep():
    """I/O-bound: Simulated I/O with sleep."""
    try:
        time.sleep(random.uniform(0.001, 0.01))
        tracker.increment("io_sleep")
    except Exception as e:
        tracker.error("io_sleep")

def io_file_write_read():
    """I/O-bound: Write and read temporary file."""
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', delete=True) as f:
            f.write("x" * 10000)
            f.seek(0)
            f.read()
        tracker.increment("io_file_write_read")
    except Exception as e:
        tracker.error("io_file_write_read")

def io_json_parse():
    """I/O-bound: Parse JSON data."""
    try:
        import json
        data = json.dumps([{"id": i, "value": random.random()} for i in range(1000)])
        json.loads(data)
        tracker.increment("io_json_parse")
    except Exception as e:
        tracker.error("io_json_parse")

# ============================================================================
# LOCK CONTENTION WORKLOADS
# ============================================================================

class SharedResource:
    """Shared resource protected by lock."""
    def __init__(self):
        self.lock = Lock()
        self.value = 0

    def increment(self):
        with self.lock:
            time.sleep(0.001)  # Simulate work while holding lock
            self.value += 1

shared_resource = SharedResource()

def lock_contention_increment():
    """Lock contention: Multiple threads accessing shared resource."""
    try:
        shared_resource.increment()
        tracker.increment("lock_contention_increment")
    except Exception as e:
        tracker.error("lock_contention_increment")

def lock_contention_heavy():
    """Lock contention: Heavy lock contention with more work."""
    try:
        for _ in range(10):
            shared_resource.increment()
        tracker.increment("lock_contention_heavy")
    except Exception as e:
        tracker.error("lock_contention_heavy")

class RWLock:
    """Simple read-write lock."""
    def __init__(self):
        self._read_lock = Lock()
        self._write_lock = Lock()
        self._readers = 0

    def acquire_read(self):
        with self._read_lock:
            self._readers += 1
        return self

    def release_read(self):
        with self._read_lock:
            self._readers -= 1

    def acquire_write(self):
        self._write_lock.acquire()
        # Wait for readers
        while True:
            with self._read_lock:
                if self._readers == 0:
                    break
            time.sleep(0.0001)

    def release_write(self):
        self._write_lock.release()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

rw_lock = RWLock()

def lock_rwlock_read():
    """Lock contention: Read-write lock read operations."""
    try:
        rw_lock.acquire_read()
        time.sleep(0.001)
        rw_lock.release_read()
        tracker.increment("lock_rwlock_read")
    except Exception as e:
        tracker.error("lock_rwlock_read")

def lock_rwlock_write():
    """Lock contention: Read-write lock write operations."""
    try:
        rw_lock.acquire_write()
        time.sleep(0.001)
        rw_lock.release_write()
        tracker.increment("lock_rwlock_write")
    except Exception as e:
        tracker.error("lock_rwlock_write")

# ============================================================================
# ASYNC WORKLOADS
# ============================================================================

async def async_sleep():
    """Async I/O: Sleep in async context."""
    try:
        await asyncio.sleep(random.uniform(0.001, 0.01))
        tracker.increment("async_sleep")
    except Exception as e:
        tracker.error("async_sleep")

async def async_cpu_work():
    """Async CPU: CPU work in async context."""
    try:
        result = fibonacci(15)
        tracker.increment("async_cpu_work")
    except Exception as e:
        tracker.error("async_cpu_work")

async def async_gather_tasks():
    """Async: Gather multiple async tasks."""
    try:
        await asyncio.gather(
            asyncio.sleep(0.001),
            asyncio.sleep(0.002),
            asyncio.sleep(0.003)
        )
        tracker.increment("async_gather_tasks")
    except Exception as e:
        tracker.error("async_gather_tasks")

async def async_queue_producer():
    """Async: Queue producer."""
    try:
        queue = asyncio.Queue()
        for i in range(10):
            await queue.put(i)
        tracker.increment("async_queue_producer")
    except Exception as e:
        tracker.error("async_queue_producer")

async def async_lock_contention():
    """Async: Lock contention with async lock."""
    try:
        lock = asyncio.Lock()
        async with lock:
            await asyncio.sleep(0.001)
        tracker.increment("async_lock_contention")
    except Exception as e:
        tracker.error("async_lock_contention")

async def async_create_tasks():
    """Async: Create and manage tasks."""
    try:
        tasks = [asyncio.create_task(asyncio.sleep(0.001)) for _ in range(5)]
        await asyncio.gather(*tasks)
        tracker.increment("async_create_tasks")
    except Exception as e:
        tracker.error("async_create_tasks")

# ============================================================================
# MIXED WORKLOADS
# ============================================================================

async def async_mixed_cpu_io():
    """Async: Mixed CPU and I/O work."""
    try:
        result = fibonacci(12)
        await asyncio.sleep(0.005)
        tracker.increment("async_mixed_cpu_io")
    except Exception as e:
        tracker.error("async_mixed_cpu_io")

def mixed_thread_lock():
    """Mixed: Thread work with locks."""
    try:
        with shared_resource.lock:
            data = sorted([random.random() for _ in range(1000)])
        tracker.increment("mixed_thread_lock")
    except Exception as e:
        tracker.error("mixed_thread_lock")

async def async_many_awaits():
    """Async: Many small async operations."""
    try:
        for _ in range(50):
            await asyncio.sleep(0)
        tracker.increment("async_many_awaits")
    except Exception as e:
        tracker.error("async_many_awaits")

# ============================================================================
# WORKER THREADS
# ============================================================================

def cpu_worker():
    """Worker thread: Continuous CPU-bound tasks."""
    while not shutdown_event.is_set():
        cpu_fibonacci()

def io_worker():
    """Worker thread: Continuous I/O-bound tasks."""
    while not shutdown_event.is_set():
        io_sleep()
        io_file_write_read()

def lock_worker():
    """Worker thread: Continuous lock contention tasks."""
    while not shutdown_event.is_set():
        lock_contention_increment()
        lock_contention_heavy()

def mixed_worker():
    """Worker thread: Mixed workloads."""
    while not shutdown_event.is_set():
        if random.choice([True, False]):
            cpu_sorting()
        else:
            io_json_parse()
            mixed_thread_lock()

# ============================================================================
# ASYNC EVENT LOOP RUNNER
# ============================================================================

async def async_worker():
    """Async worker: Continuous async tasks."""
    while not shutdown_event.is_set():
        # Randomly select async workload
        choice = random.choice([
            async_sleep(),
            async_cpu_work(),
            async_gather_tasks(),
            async_queue_producer(),
            async_lock_contention(),
            async_create_tasks(),
            async_mixed_cpu_io(),
            async_many_awaits(),
        ])
        await choice
        await asyncio.sleep(0)  # Allow other tasks to run

async def async_main():
    """Main async event loop runner."""
    tasks = [
        asyncio.create_task(async_worker()),
        asyncio.create_task(async_worker()),
        asyncio.create_task(async_worker()),
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass

def run_async_event_loop():
    """Run async event loop in thread."""
    asyncio.run(async_main())

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    print(f"Starting workload test script")
    print(f"PID: {os.getpid()}")
    print(f"Ctrl+C to stop\n")

    # Start worker threads
    threads = []

    # CPU workers
    for i in range(2):
        t = threading.Thread(target=cpu_worker, name=f"cpu_worker_{i}", daemon=True)
        t.start()
        threads.append(t)

    # I/O workers
    for i in range(2):
        t = threading.Thread(target=io_worker, name=f"io_worker_{i}", daemon=True)
        t.start()
        threads.append(t)

    # Lock contention workers
    for i in range(3):
        t = threading.Thread(target=lock_worker, name=f"lock_worker_{i}", daemon=True)
        t.start()
        threads.append(t)

    # Mixed workers
    for i in range(2):
        t = threading.Thread(target=mixed_worker, name=f"mixed_worker_{i}", daemon=True)
        t.start()
        threads.append(t)

    # Async event loop worker
    t = threading.Thread(target=run_async_event_loop, name="async_worker", daemon=True)
    t.start()
    threads.append(t)

    # Status printer thread
    def status_printer():
        while not shutdown_event.is_set():
            time.sleep(10)
            if not shutdown_event.is_set():
                tracker.print_status()

    status_thread = threading.Thread(target=status_printer, name="status_printer", daemon=True)
    status_thread.start()

    # Handle Ctrl+C
    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    # Wait for all threads to complete
    try:
        while not shutdown_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        shutdown_event.set()

    # Print final stats
    time.sleep(1)
    tracker.print_status()

if __name__ == "__main__":
    main()
