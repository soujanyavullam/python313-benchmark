#!/usr/bin/env python3

"""

Enhanced benchmark for CPU-bound and IO-bound multithreading with and without the GIL.

Measures:
- True multithreading gains (CPU-bound: 2×–5× speedup expected)
- IO-bound workload performance (should be similar across versions)
- Single-thread overhead (3.13 free-threaded: 5–15% slower expected)
- Best-case scenarios (near-linear scaling with cores)

Run this script under different interpreters:

1) Classic CPython 3.x (GIL only):
   python gil_benchmark.py

2) Python 3.13 free-threaded build, GIL enabled:
   PYTHON_GIL=1 python3.13 gil_benchmark.py
   # or: python3.13 -X gil=1 gil_benchmark.py

3) Python 3.13 free-threaded build, GIL disabled:
   PYTHON_GIL=0 python3.13 gil_benchmark.py
   # or: python3.13 -X gil=0 gil_benchmark.py
"""

import argparse
import concurrent.futures
import hashlib
import math
import os
import random
import sys
import sysconfig
import time
from typing import Dict, Tuple





def detect_gil_status() -> Tuple[bool, bool]:
    """Best-effort detection of GIL status and free-threaded build."""
    free_threaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED") or 0)

    try:
        gil_enabled = sys._is_gil_enabled()  # Only in 3.13+
    except AttributeError:
        gil_enabled = True  # Older Pythons always have the GIL

    return free_threaded, gil_enabled


def get_python_version_info() -> Tuple[int, int, int]:
    """Extract Python version as (major, minor, micro)."""
    version = sys.version_info
    return (version.major, version.minor, version.micro)





def cpu_bound_task(n: int) -> int:
    """
    A simple CPU-bound task:
    Sum of square roots of integers up to n (rough but heavy enough).
    Uses pure Python math operations - no C extensions.
    """
    total = 0.0
    for i in range(1, n + 1):
        total += math.sqrt(i)
    return int(total)


def cpu_bound_pure_python_task(n: int) -> int:
    """
    Pure Python CPU-bound task using hashlib (thread-safe, no C extension issues).
    Best-case scenario for GIL-disabled performance.
    """
    data = bytearray(range(n % 256))
    result = 0
    for i in range(1000):  # Multiple iterations for measurable work
        h = hashlib.sha256(data)
        result += int.from_bytes(h.digest()[:4], 'big')
        data[0] = (data[0] + 1) % 256
    return result


def io_bound_task(duration_ms: int) -> int:
    """
    Simulated IO-bound task using sleep.
    IO waits dominate, so GIL on/off shouldn't matter much.
    """
    time.sleep(duration_ms / 1000.0)
    return duration_ms





def run_single_thread_cpu(num_tasks: int, task_size: int) -> float:
    """Run CPU-bound tasks in single thread."""
    start = time.perf_counter()
    for _ in range(num_tasks):
        cpu_bound_task(task_size)
    end = time.perf_counter()
    return end - start


def run_multi_thread_cpu(num_tasks: int, task_size: int, num_threads: int) -> float:
    """Run CPU-bound tasks in multiple threads."""
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as ex:
        futures = [
            ex.submit(cpu_bound_task, task_size)
            for _ in range(num_tasks)
        ]
        for f in futures:
            _ = f.result()
    end = time.perf_counter()
    return end - start


def run_single_thread_pure_python(num_tasks: int, task_size: int) -> float:
    """Run pure Python CPU-bound tasks in single thread (best-case scenario)."""
    start = time.perf_counter()
    for _ in range(num_tasks):
        cpu_bound_pure_python_task(task_size)
    end = time.perf_counter()
    return end - start


def run_multi_thread_pure_python(num_tasks: int, task_size: int, num_threads: int) -> float:
    """Run pure Python CPU-bound tasks in multiple threads (best-case scenario)."""
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as ex:
        futures = [
            ex.submit(cpu_bound_pure_python_task, task_size)
            for _ in range(num_tasks)
        ]
        for f in futures:
            _ = f.result()
    end = time.perf_counter()
    return end - start


def run_single_thread_io(num_tasks: int, duration_ms: int) -> float:
    """Run IO-bound tasks in single thread."""
    start = time.perf_counter()
    for _ in range(num_tasks):
        io_bound_task(duration_ms)
    end = time.perf_counter()
    return end - start


def run_multi_thread_io(num_tasks: int, duration_ms: int, num_threads: int) -> float:
    """Run IO-bound tasks in multiple threads."""
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as ex:
        futures = [
            ex.submit(io_bound_task, duration_ms)
            for _ in range(num_tasks)
        ]
        for f in futures:
            _ = f.result()
    end = time.perf_counter()
    return end - start





def analyze_results(
    results: Dict[str, float],
    free_threaded: bool,
    gil_enabled: bool,
    num_threads: int,
    cpu_cores: int
) -> None:
    """Analyze and report benchmark results with expected ranges."""
    print("\n" + "=" * 70)
    print("ANALYSIS & EXPECTED RANGES")
    print("=" * 70)

    # CPU-bound multithreading gains
    cpu_speedup = results.get('cpu_speedup', 0)
    print(f"\n1. CPU-BOUND MULTITHREADING GAINS")
    print(f"   Speedup: {cpu_speedup:.2f}x")
    if free_threaded and not gil_enabled:
        if cpu_speedup >= 2.0:
            print(f"   ✓ EXCELLENT: 2×–5× expected for GIL-disabled (you got {cpu_speedup:.2f}×)")
        elif cpu_speedup >= 1.5:
            print(f"   ✓ GOOD: Approaching expected range (2×–5×)")
        else:
            print(f"   ⚠ BELOW EXPECTED: Should see 2×–5× with GIL disabled")
    elif free_threaded and gil_enabled:
        if cpu_speedup <= 1.2:
            print(f"   ✓ EXPECTED: Limited speedup (~1.1×) with GIL enabled")
        else:
            print(f"   ⚠ UNEXPECTED: Higher speedup than expected with GIL on")
    else:
        if cpu_speedup <= 1.2:
            print(f"   ✓ EXPECTED: Classic CPython shows minimal speedup (~1.1×)")
        else:
            print(f"   ⚠ UNEXPECTED: Higher speedup than expected for classic CPython")

    # Best-case scenario (pure Python)
    pure_python_speedup = results.get('pure_python_speedup', 0)
    if pure_python_speedup > 0:
        print(f"\n2. BEST-CASE SCENARIO (Pure Python, Thread-Safe)")
        print(f"   Speedup: {pure_python_speedup:.2f}x")
        expected_best = num_threads * 0.85  # ~85% efficiency
        if free_threaded and not gil_enabled:
            if pure_python_speedup >= expected_best:
                print(f"   ✓ EXCELLENT: Near-linear scaling ({pure_python_speedup:.2f}× ≈ {num_threads} threads)")
            elif pure_python_speedup >= expected_best * 0.7:
                print(f"   ✓ GOOD: Strong scaling ({pure_python_speedup:.2f}×)")
            else:
                print(f"   ⚠ BELOW EXPECTED: Should approach {expected_best:.1f}× for {num_threads} threads")
        else:
            print(f"   ⚠ LIMITED: GIL prevents true parallelism")

    # IO-bound performance
    io_speedup = results.get('io_speedup', 0)
    if io_speedup > 0:
        print(f"\n3. IO-BOUND WORKLOAD PERFORMANCE")
        print(f"   Speedup: {io_speedup:.2f}x")
        if io_speedup >= num_threads * 0.8:
            print(f"   ✓ EXPECTED: IO-bound tasks scale well regardless of GIL")
        else:
            print(f"   ⚠ UNEXPECTED: IO-bound should scale well (GIL doesn't matter)")

    # Single-thread overhead
    single_thread_time = results.get('cpu_single', 0)
    if free_threaded:
        print(f"\n4. SINGLE-THREAD OVERHEAD (Python 3.13 free-threaded)")
        print(f"   Single-thread time: {single_thread_time:.3f} s")
        print(f"   Expected: 5–15% slower than classic CPython 3.11/3.12")
        print(f"   Note: Compare this value with classic CPython baseline")

    # Extension compatibility
    if free_threaded and not gil_enabled:
        cpu_vs_pure = results.get('cpu_speedup', 0) / max(results.get('pure_python_speedup', 1), 1)
        print(f"\n5. EXTENSION COMPATIBILITY IMPACT")
        if cpu_vs_pure >= 0.9:
            print(f"   ✓ GOOD: CPU task performance ({results.get('cpu_speedup', 0):.2f}×) close to")
            print(f"           pure Python ({results.get('pure_python_speedup', 0):.2f}×)")
        else:
            print(f"   ⚠ WARNING: CPU task ({results.get('cpu_speedup', 0):.2f}×) significantly slower")
            print(f"              than pure Python ({results.get('pure_python_speedup', 0):.2f}×)")
            print(f"              C-extensions may be forcing GIL fallback")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced benchmark for CPU-bound and IO-bound multithreading with/without the GIL."
    )
    parser.add_argument(
        "--tasks",
        type=int,
        default=32,
        help="Number of tasks to run (default: 32)",
    )
    parser.add_argument(
        "--task-size",
        type=int,
        default=200_000,
        help="Work per CPU task (loop upper bound, default: 200000)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Number of threads for multithreaded runs (default: CPU count)",
    )
    parser.add_argument(
        "--io-duration",
        type=int,
        default=50,
        help="IO task duration in milliseconds (default: 50)",
    )
    parser.add_argument(
        "--skip-io",
        action="store_true",
        help="Skip IO-bound workload tests",
    )
    parser.add_argument(
        "--skip-pure-python",
        action="store_true",
        help="Skip pure Python best-case scenario test",
    )

    args = parser.parse_args()

    free_threaded, gil_enabled = detect_gil_status()
    version_info = get_python_version_info()
    cpu_cores = os.cpu_count() or 1
    num_threads = args.threads or cpu_cores

    print("=" * 70)
    print("ENHANCED Python GIL / Threading Benchmark")
    print("=" * 70)
    print(f"Python version      : {sys.version.splitlines()[0]}")
    print(f"Free-threaded build : {free_threaded}")
    print(f"GIL enabled at run  : {gil_enabled}")
    print(f"CPU cores detected  : {cpu_cores}")
    print(f"Tasks               : {args.tasks}")
    print(f"Task size           : {args.task_size}")
    print(f"Threads             : {num_threads}")
    print("-" * 70)

    results: Dict[str, float] = {}

    # 1. CPU-bound workload (standard)
    print("\n[1/3] CPU-BOUND WORKLOAD (Standard)")
    print("-" * 70)
    t_single_cpu = run_single_thread_cpu(args.tasks, args.task_size)
    print(f"Single-thread time      : {t_single_cpu:.3f} s")
    results['cpu_single'] = t_single_cpu

    t_multi_cpu = run_multi_thread_cpu(args.tasks, args.task_size, num_threads)
    print(f"Multi-thread time       : {t_multi_cpu:.3f} s")
    results['cpu_multi'] = t_multi_cpu

    cpu_speedup = t_single_cpu / t_multi_cpu if t_multi_cpu > 0 else 0
    print(f"Speedup (single / multi): {cpu_speedup:.2f}x")
    results['cpu_speedup'] = cpu_speedup

    # 2. Pure Python best-case scenario
    if not args.skip_pure_python:
        print("\n[2/3] CPU-BOUND WORKLOAD (Pure Python - Best Case)")
        print("-" * 70)
        t_single_pure = run_single_thread_pure_python(args.tasks, args.task_size // 10)
        print(f"Single-thread time      : {t_single_pure:.3f} s")
        results['pure_python_single'] = t_single_pure

        t_multi_pure = run_multi_thread_pure_python(args.tasks, args.task_size // 10, num_threads)
        print(f"Multi-thread time       : {t_multi_pure:.3f} s")
        results['pure_python_multi'] = t_multi_pure

        pure_python_speedup = t_single_pure / t_multi_pure if t_multi_pure > 0 else 0
        print(f"Speedup (single / multi): {pure_python_speedup:.2f}x")
        results['pure_python_speedup'] = pure_python_speedup

    # 3. IO-bound workload
    if not args.skip_io:
        print("\n[3/3] IO-BOUND WORKLOAD")
        print("-" * 70)
        t_single_io = run_single_thread_io(args.tasks, args.io_duration)
        print(f"Single-thread time      : {t_single_io:.3f} s")
        results['io_single'] = t_single_io

        t_multi_io = run_multi_thread_io(args.tasks, args.io_duration, num_threads)
        print(f"Multi-thread time       : {t_multi_io:.3f} s")
        results['io_multi'] = t_multi_io

        io_speedup = t_single_io / t_multi_io if t_multi_io > 0 else 0
        print(f"Speedup (single / multi): {io_speedup:.2f}x")
        results['io_speedup'] = io_speedup

    # Analysis
    analyze_results(results, free_threaded, gil_enabled, num_threads, cpu_cores)

    print(
        "\nCOMPARISON TIPS:\n"
        "  • Run this script on CPython 3.11/3.12 for baseline\n"
        "  • Run on Python 3.13 free-threaded with GIL ON (PYTHON_GIL=1)\n"
        "  • Run on Python 3.13 free-threaded with GIL OFF (PYTHON_GIL=0)\n"
        "  • Compare single-thread times to measure overhead\n"
        "  • Compare multi-thread speedups to measure true parallelism gains"
    )





if __name__ == "__main__":

    main()

