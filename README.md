<<<<<<< HEAD
# python313-benchmark
=======
# Python 3.13 GIL Benchmarking Project

This project provides an enhanced benchmark for measuring CPU-bound and IO-bound multithreading performance with and without the Global Interpreter Lock (GIL) in Python 3.13.

## Overview

The benchmark comprehensively measures:
- **True multithreading gains**: CPU-bound tasks (2×–5× speedup expected with GIL disabled)
- **IO-bound workloads**: Performance comparison (should be similar across versions)
- **Single-thread overhead**: Python 3.13 free-threaded mode overhead (5–15% slower expected)
- **Best-case scenarios**: Pure Python workloads showing near-linear scaling with cores
- **Extension compatibility**: Impact of C-extensions on GIL-disabled performance

## Requirements

- Python 3.10+ (for baseline comparison)
- Python 3.13 free-threaded build (for GIL-disabled testing)

**Note:** The script uses only standard library modules, so no additional dependencies are required.

## Usage

### 1. Classic CPython 3.x (GIL always enabled)

```bash
python gil_benchmark.py
# or
python3.10 gil_benchmark.py
python3.11 gil_benchmark.py
python3.12 gil_benchmark.py
```

### 2. Python 3.13 free-threaded build, GIL enabled

```bash
PYTHON_GIL=1 python3.13 gil_benchmark.py
# or
python3.13 -X gil=1 gil_benchmark.py
```

### 3. Python 3.13 free-threaded build, GIL disabled

```bash
PYTHON_GIL=0 python3.13 gil_benchmark.py
# or
python3.13 -X gil=0 gil_benchmark.py
```

## Command-line Options

- `--tasks N`: Number of tasks to run (default: 32)
- `--task-size N`: Work per CPU task - loop upper bound (default: 200000)
- `--threads N`: Number of threads for multithreaded runs (default: CPU count)
- `--io-duration N`: IO task duration in milliseconds (default: 50)
- `--skip-io`: Skip IO-bound workload tests
- `--skip-pure-python`: Skip pure Python best-case scenario test

### Examples

```bash
# Run with custom parameters
python3.13 gil_benchmark.py --tasks 64 --task-size 500000 --threads 16

# Compare different configurations
PYTHON_GIL=0 python3.13 gil_benchmark.py --threads 4
PYTHON_GIL=1 python3.13 gil_benchmark.py --threads 4

# Skip IO tests for faster CPU-only benchmarking
python3.13 gil_benchmark.py --skip-io

# Quick test with fewer tasks
python3.13 gil_benchmark.py --tasks 16 --threads 4
```

## What the Benchmark Measures

### 1. CPU-Bound Workload (Standard)
Performs CPU-intensive work by computing the sum of square roots of integers. This test uses standard Python math operations and may be affected by C-extension compatibility.

### 2. CPU-Bound Workload (Pure Python - Best Case)
Uses pure Python hashlib operations (thread-safe, no C extension issues). This represents the best-case scenario for GIL-disabled performance, showing near-linear scaling with cores.

### 3. IO-Bound Workload
Simulates IO-bound tasks using sleep operations. IO waits dominate, so GIL on/off shouldn't matter much - this validates that IO-bound performance is similar across versions.

## Expected Results

### CPU-Bound Multithreading Gains
- **Classic CPython (3.10/3.11/3.12)**: Minimal speedup (~1.1×) due to GIL
- **Python 3.13 free-threaded with GIL ON**: Limited speedup (~1.1×), similar to classic CPython
- **Python 3.13 free-threaded with GIL OFF**: **2×–5× speedup** for CPU-bound tasks
- **Pure Python best-case**: **Near-linear scaling** (e.g., 4 threads ≈ 3.5× speedup)

### IO-Bound Workloads
- Performance should be **similar across all versions** (3.11 → 3.13, GIL on/off)
- IO waits dominate, so GIL doesn't significantly impact performance
- Multi-threaded IO should scale well regardless of GIL status

### Single-Thread Overhead
- **Python 3.13 free-threaded mode**: Currently **5–15% slower** for single-threaded code than classic 3.11/3.12
- This is due to extra locking and checks required for thread safety
- Compare single-thread times across versions to measure this overhead

### Extension Compatibility Impact
- C-extensions not yet thread-safe may force fallback to GIL
- This reduces gains or causes inconsistent performance
- The benchmark compares standard CPU tasks vs pure Python tasks to detect this

## Analysis Output

The benchmark includes automatic analysis that:
- Compares your results against expected ranges
- Identifies if performance matches expectations
- Warns about potential C-extension compatibility issues
- Provides guidance on interpreting results

## Notes

- Results will vary based on your CPU core count and system load
- Run multiple iterations for more reliable results
- For accurate comparison, run the same test on different Python versions/configurations
- The benchmark automatically detects GIL status and provides context-aware analysis

>>>>>>> 102e1d5 (benchmarking)
