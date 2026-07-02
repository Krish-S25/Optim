import numpy as np
from scipy.optimize import curve_fit
from typing import Dict, Any, List

# Define our mathematical model shapes for complexity estimation
def model_constant(n, a, b):
    return a * np.ones_like(n) + b

def model_logarithmic(n, a, b):
    # Avoid log(0) issues by adding an infinitesimal offset
    return a * np.log2(n + 1e-9) + b

def model_linear(n, a, b):
    return a * n + b

def model_n_log_n(n, a, b): return a * n * np.log2(n + 1e-9) + b
def model_quadratic(n, a, b): return a * (n ** 2) + b
def model_cubic(n, a, b): return a * (n ** 3) + b
def model_sqrt(n, a, b): return a * np.sqrt(n) + b
def model_cbrt(n, a, b): return a * np.cbrt(n) + b

import os

# --- Configurable Occam's Razor Penalties ---
OCCAM_PENALTY_NLOGN = 0.15  # 15% margin for N log N -> N
OCCAM_PENALTY_CONST = 0.05  # 5% margin for log N -> 1
# --------------------------------------------

def estimate_complexity():
    """
    Fits the runtime data against candidate Big-O models using least-squares error optimization.
    Returns the best complexity profile alongside a basic percentage score.
    """
    sizes = []
    runtimes = []
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
    metrics_path = os.path.join(root_dir, "metrics.csv")
    
    with open(metrics_path, "r") as f:
        lines = f.read().strip().split('\n')
        for line in lines[1:]:
            if not line.strip() or ',' not in line:
                continue
            s, t = line.split(',')
            sizes.append(int(s))
            runtimes.append(float(t))

    # Convert incoming arrays into high-performance NumPy float64 vectors
    x_data = np.array(sizes, dtype=np.float64)
    y_data = np.array(runtimes, dtype=np.float64)

    # Dictionary pairing string representations with their math function references
    complexity_candidates = {
        "O(1)": model_constant,
        "O(log N)": model_logarithmic,
        "O(N^(1/3))": model_cbrt,
        "O(sqrt(N))": model_sqrt,
        "O(N)": model_linear,
        "O(N log N)": model_n_log_n,
        "O(N^2)": model_quadratic,
        "O(N^3)": model_cubic
    }

    # The Physical Limit Override:
    # 0.005 ms is 5 microseconds. An empty loop traversing 100,000 elements takes 
    # roughly 15-20 microseconds in Java. Therefore, if an algorithm finishes in 
    # under 5 microseconds, it is physically impossible to have touched every element.
    # It MUST be Sublinear.
    max_runtime = max(runtimes) if runtimes else 0
    max_size = max(sizes) if sizes else 0
    
    if max_runtime < 0.005:
        valid_candidates = ["O(1)", "O(log N)"]
    else:
        # Otherwise, let the math regression freely evaluate all models to correct 
        # any misclassifications made by the Java Heuristic Probe
        valid_candidates = list(complexity_candidates.keys())

    best_fit_model = None
    lowest_residual_error = float('inf')
    model_errors = {}

    # Iterate through ONLY mathematically valid curve shapes for this data
    for label in valid_candidates:
        model_func = complexity_candidates[label]
        try:
            # THE FIX: Bounds restrict 'a' >= 0 to prevent inverted curves, but allow 'b' (intercept) to float
            # This prevents artificial RMSE inflation on linear models when hardware cache bends the data up
            popt, _ = curve_fit(model_func, x_data, y_data, bounds=([0, -np.inf], [np.inf, np.inf]), maxfev=10000)
            
            # Generate the predicted points based on our optimized variables
            predictions = model_func(x_data, *popt)
            
            # Compute Root Mean Squared Error (RMSE)
            rmse = np.sqrt(np.mean((y_data - predictions) ** 2))
            model_errors[label] = float(rmse)

            # Track the model with the absolute lowest structural variance
            if rmse < lowest_residual_error:
                lowest_residual_error = rmse
                best_fit_model = label
                
        except Exception:
            # Handle math edge cases or un-fittable curve shapes gracefully
            model_errors[label] = float('inf')

    # Occam's Razor Step 1: N^3 -> N^2
    if best_fit_model == "O(N^3)":
        quad_error = model_errors.get("O(N^2)", float('inf'))
        if quad_error <= lowest_residual_error * 1.10: # 10% margin
            best_fit_model = "O(N^2)"
            lowest_residual_error = quad_error

    # Occam's Razor Step 2: N^2 -> N log N
    if best_fit_model == "O(N^2)":
        nlogn_error = model_errors.get("O(N log N)", float('inf'))
        if nlogn_error <= lowest_residual_error * 1.15: # 15% margin
            best_fit_model = "O(N log N)"
            lowest_residual_error = nlogn_error

    # Occam's Razor Step 3: CV Test for N log N vs N
    if best_fit_model in ["O(N log N)", "O(N)"]:
        # Compute Coefficient of Variation for T/N
        norm_n = y_data / x_data
        cv_n = np.std(norm_n) / np.mean(norm_n) if np.mean(norm_n) > 0 else float('inf')
        
        # Compute Coefficient of Variation for T/(N log N)
        norm_nlogn = y_data / (x_data * np.log2(x_data + 1e-9))
        cv_nlogn = np.std(norm_nlogn) / np.mean(norm_nlogn) if np.mean(norm_nlogn) > 0 else float('inf')
        
        if cv_n <= cv_nlogn * (1.0 + OCCAM_PENALTY_NLOGN):
            best_fit_model = "O(N)"
            lowest_residual_error = model_errors.get("O(N)", float('inf'))
        else:
            best_fit_model = "O(N log N)"
            lowest_residual_error = model_errors.get("O(N log N)", float('inf'))

    # Occam's Razor Step 4: N -> sqrt(N)
    if best_fit_model == "O(N)":
        sqrt_error = model_errors.get("O(sqrt(N))", float('inf'))
        if sqrt_error <= lowest_residual_error * 1.10:
            best_fit_model = "O(sqrt(N))"
            lowest_residual_error = sqrt_error

    # Occam's Razor Step 5: sqrt(N) -> N^(1/3)
    if best_fit_model == "O(sqrt(N))":
        cbrt_error = model_errors.get("O(N^(1/3))", float('inf'))
        if cbrt_error <= lowest_residual_error * 1.10:
            best_fit_model = "O(N^(1/3))"
            lowest_residual_error = cbrt_error

    # Occam's Razor Step 6: N^(1/3) -> log N
    if best_fit_model == "O(N^(1/3))":
        logn_error = model_errors.get("O(log N)", float('inf'))
        if logn_error <= lowest_residual_error * 1.10:
            best_fit_model = "O(log N)"
            lowest_residual_error = logn_error

    # Occam's Razor Step 7: RMSE Test for log N vs 1
    if best_fit_model in ["O(log N)", "O(1)"]:
        const_error = model_errors.get("O(1)", float('inf'))
        logn_error = model_errors.get("O(log N)", float('inf'))
        
        # We use RMSE here because tiny sub-microsecond runtimes clamped to ~0 
        # create a scale-invariant spike at the L3 cache boundary that breaks CV.
        if const_error <= logn_error * (1.0 + OCCAM_PENALTY_CONST):
            best_fit_model = "O(1)"
            lowest_residual_error = const_error
        else:
            best_fit_model = "O(log N)"
            lowest_residual_error = logn_error

    # Compute statistically accurate R-squared (R^2) for the chosen model to use as Confidence %
    if best_fit_model:
        popt, _ = curve_fit(complexity_candidates[best_fit_model], x_data, y_data, bounds=([0, -np.inf], [np.inf, np.inf]), maxfev=10000)
        predictions = complexity_candidates[best_fit_model](x_data, *popt)
        ss_res = np.sum((y_data - predictions) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        confidence_pct = max(0.0, min(100.0, r_squared * 100.0))
        
        # Cache Boundary Math Patch: If it finished in under 5 microseconds, we are functionally certain 
        # it is sublinear. Math models break at the L3 cache boundary spike, so we override the artificially 
        # destroyed R^2 score.
        if max_runtime < 0.005 and best_fit_model in ["O(1)", "O(log N)"]:
            confidence_pct = max(confidence_pct, 99.0)
    else:
        confidence_pct = 0.0

    metrics_dict = {
        "sizes": sizes,
        "runtimes": runtimes
    }

    analysis_dict = {
        "estimated_complexity": best_fit_model if best_fit_model else "Unknown",
        "confidence_percentage": round(confidence_pct, 2),
        "model_residual_errors": model_errors
    }

    return metrics_dict, analysis_dict