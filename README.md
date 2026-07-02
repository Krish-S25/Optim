# Optim: Empirical Performance Judgment Engine

Optim is a full-stack algorithm performance and complexity analysis engine.

## Features

*   **Dynamic JIT Benchmarking:** Runs inside a fully integrated Java environment that handles JVM warm-up, Garbage Collection pauses, and Dead Code Elimination (DCE) mitigation.
*   **High-Fidelity Profiling:** Uses multi-pass median clusters and progressive scaling probes to bypass OS thread noise and memory allocation overhead.
*   **Mathematical Curve Fitting:** Leverages Python's `SciPy` to map physical hardware execution metrics to algorithmic time complexities.
*   **Supported Complexities:** Can classify $O(1)$, $O(\log N)$, $O(N^{1/3})$, $O(\sqrt{N})$, $O(N)$, $O(N \log N)$, $O(N^2)$, and $O(N^3)$.
*   **Advanced Configurations:** Supports `int` and `double` arrays, as well as specific array distributions (`random`, `sorted`, `nearly_sorted`).
*   **Occam's Razor Scaling:** Employs a Coefficient of Variation (CV) test and cascading error margins to naturally prefer simpler complexities when hardware noise bends the curves.

## Architecture

*   **Backend:** Python, FastAPI, NumPy, SciPy (for regression and math engines).
*   **Runner:** Native Java JDK execution via dynamic source-code template generation.
*   **Frontend:** React, Vite, Tailwind CSS.

## Getting Started

### Prerequisites
*   Node.js & npm
*   Python 3.x
*   Java Development Kit (JDK 11+)

### Running the Project

**1. Start the Backend API (FastAPI)**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

**2. Start the Frontend Dashboard (React)**
```powershell
cd frontend
npm run dev
```

## How It Works

1.  **Submission:** The frontend sends a raw Java sorting algorithm to the backend.
2.  **Dry Run:** The engine generates a `DryRunDriver.java` to verify code correctness and quickly catch exponential $O(2^N)$ blowups before they crash the server.
3.  **Heuristic Probe:** The engine generates a dynamic `BenchmarkDriver.java` using a template. It runs small-scale and massive-scale cluster probes to identify the algorithm's bracket (Sublinear, Linear, Quadratic, Superlinear) and calculates maximum safe array sizes.
4.  **High-Precision Tracking:** The Java driver executes the algorithm across scaled sizes, subtracting base memory allocation overhead, and writes the pure execution metrics to `metrics.csv`.
5.  **Regression Analysis:** The Python `analyzer.py` engine reads the metrics and runs bounded `curve_fit` optimizations, using physical limits and Coefficient of Variation checks to output a highly confident Big-O complexity.
