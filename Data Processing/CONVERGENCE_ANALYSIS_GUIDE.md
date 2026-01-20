# Robust Convergence Analysis - Implementation Guide

## Overview

Improvement 3 adds robust convergence analysis to detect data quality issues and provide confidence-scored trim recommendations. The algorithm automatically identifies the optimal amount of initial data to discard (transient effects) to achieve the best convergence statistics.

## Key Concepts

### What is Data Trimming?

CFD simulations have **transient effects at the beginning** where the solver is reaching steady state. By trimming (removing) initial iterations, you keep only the converged, stable portion of the data.

**Example:**
```
Original 1200 iterations:  [noisy transient] | [stable converged data]
                            ← 120 removed ←      ← 1080 used →

Result: Lower COV (better statistics) by removing the junk at the start
```

### How Many Test Points?

`Tests: 20` means the algorithm evaluates **20 evenly-spaced trim amounts** between 0% and 80%:

```python
trim_fractions = [0%, 4.2%, 8.4%, 12.6%, 16.8%, 21%, ..., 76.8%, 80%]
```

For each trim point, it calculates statistics and scores confidence. The algorithm then **selects the trim point with the lowest COV** (highest convergence quality).

**Why 20?**
- Fast: ~1-2 seconds per configuration
- Thorough: Catches the optimal trim within ~4% resolution
- Configurable: Change `CONVERGENCE_NUM_TESTS` in `main.py` (line ~45)

### Data Selection

The algorithm **keeps the tail end** (remaining data after removing from the beginning):

```python
trimmed_data = data_array[iterations_to_remove:]
iterations_used = len(trimmed_data)
```

This discards transient effects while preserving the converged portion.

---

## Confidence Scoring System

### What is Confidence?

A **0-1 score** indicating how trustworthy a trim recommendation is. Combines three factors:

| Factor | Weight | Logic |
|--------|--------|-------|
| **COV Quality** | 60% | Lower COV (more stable) = higher confidence |
| **Data Retention** | 30% | More remaining data = higher confidence |
| **Oscillation** | -10% | Sign changes (oscillating) = penalty |

### Calculation

```python
confidence = 0.6 * (1 - cov_normalized) + 0.3 * data_retention_ratio - oscillation_penalty
```

**Examples:**

| Scenario | COV | Data Kept | Oscillation | Confidence |
|----------|-----|-----------|-------------|------------|
| Good convergence | 2.3% | 90% | No | 92% |
| Moderate convergence | 5.1% | 75% | No | 76% |
| Poor convergence | 12% | 50% | Yes | 45% |
| Over-trimmed | 1.8% | 15% | No | 42% (risky) |

### Interpreting Confidence

- **>85%**: Excellent - use this trim with confidence
- **70-85%**: Good - acceptable, but watch for warnings
- **50-70%**: Marginal - data quality concerns exist
- **<50%**: Poor - consider investigating the simulation

---

## Oscillation Penalty Explained

### What is Oscillation?

When the **mean value changes sign** as you trim more data:

```
Trim 0%:   Lift mean = +12.45 N  (positive)
Trim 5%:   Lift mean = +12.51 N  (positive)
Trim 15%:  Lift mean = -2.30 N   (negative!) ← Sign changed = Oscillation detected
Trim 20%:  Lift mean = +8.75 N   (positive again)
```

This indicates the data is **still transitioning** - not fully converged.

### Why It Matters

- Oscillating data = unstable solution
- Even if COV looks low, the solution is questionable
- Algorithm deprioritizes trim points with oscillation

### The Penalty

```python
oscillation_penalty = 0.5 if sign_changed else 0.0
confidence = ... - oscillation_penalty
```

**Effect:**
- Without oscillation: Confidence might be 0.92 (92%)
- With oscillation: Confidence becomes 0.92 - 0.50 = 0.42 (42%)

This large penalty (0.5) signals: *"Be cautious here - data quality is questionable."*

---

## Safety Mechanisms

### Minimum Retention Floor

**Problem**: Algorithm might recommend trimming 90% of data to get slightly lower COV, but then statistics are unreliable (only 120 points left).

**Solution**: `min_retention=0.2` (keep at least 20% of data)

```python
def analyze_convergence(..., min_retention=0.2):
    if trim_at_min_cov >= min_retention:
        # Use this recommendation
        results['trim_recommendation'] = ...
    else:
        # Find conservative trim instead (keep >20% data)
        conservative_indices = [i for i in ... if iterations_used[i] / total >= min_retention]
        results['trim_recommendation'] = best_conservative_trim
        results['trim_reason'] = "Conservative trim keeping 65% data..."
```

### What You'll See in Output

**Case 1: Good recommendation**
```
✓ Lift - Minimum COV (2.34%) at 10% trim. Confidence: 92%
```

**Case 2: Conservative fallback** (over-trimming prevented)
```
⚠️  Drag - Conservative trim keeping 65% data. COV: 4.11%, Confidence: 76%
   Best COV (1.8%) requires trimming 85% (keeping only 15%). Below safety threshold (20%).
```

**Case 3: No recommendation** (too many issues)
```
⚠️  Lift - No clear recommendation
   Mean changed sign (oscillating). Data not fully settled.
```

---

## Return Dictionary Structure

Each configuration stores complete analysis results:

```python
convergence_results[(config, aoa)] = {
    'lift': {
        # Arrays (one value per test point)
        'iterations_removed': [0, 50, 100, 150, ...],      # Trim amount
        'iterations_used': [1200, 1150, 1100, 1050, ...],  # Remaining data
        'mean': [12.45, 12.48, 12.51, 12.53, ...],         # Mean force
        'std_dev': [0.298, 0.189, 0.160, 0.195, ...],      # Std deviation
        'median': [12.40, 12.50, 12.55, 12.58, ...],       # Median (robust)
        'mad': [0.15, 0.10, 0.08, 0.12, ...],              # Median Absolute Dev
        'cov': [2.39, 1.51, 1.28, 1.55, ...],              # COV (%)
        'sign_changes': [False, False, False, True, ...],  # Oscillation flags
        'confidence_score': [0.87, 0.91, 0.94, 0.72, ...], # Confidence 0-1
        
        # Recommendation
        'trim_recommendation': 100,                         # Iterations to remove
        'trim_reason': "Minimum COV (1.28%) at 8.4% trim. Confidence: 94%",
        
        # Issues
        'warnings': []                                      # Edge cases found
    },
    'drag': { ... same structure ... },
    'plot': '/path/to/convergence_config_aoa.png'
}
```

### Key Output Fields

| Field | Type | Meaning | Example |
|-------|------|---------|---------|
| `trim_recommendation` | int | Iterations to remove from start | 100 |
| `trim_reason` | str | Why this trim was chosen | "Minimum COV (1.28%) at 8.4% trim. Confidence: 94%" |
| `confidence_score` | list[float] | Confidence per test point (0-1) | [0.87, 0.91, 0.94, ...] |
| `cov` | list[float] | Coefficient of Variation per test (%) | [2.39, 1.51, 1.28, ...] |
| `sign_changes` | list[bool] | Oscillation detected at each trim | [False, False, False, True, ...] |
| `warnings` | list[str] | Issues encountered | ["Mean is zero (stall condition)"] |

---

## Console Output Examples

### Successful Analysis

```
[1/16] Analyzing: 3.1.1.NG.10 - AoA_10
  ✓ Plot saved: .../convergence_analysis/convergence_3.1.1.NG.10.png
  ✓ Lift - Minimum COV (2.34%) at 10% trim. Confidence: 92%
  ✓ Drag - Minimum COV (1.87%) at 5% trim. Confidence: 88%
```

**Interpretation:**
- Best lift: Remove first 10% of iterations → COV drops to 2.34% with 92% confidence
- Best drag: Remove first 5% of iterations → COV drops to 1.87% with 88% confidence

### Conservative Fallback

```
[2/16] Analyzing: 3.1.1.NG.14 - AoA_14
  ✓ Plot saved: .../convergence_analysis/convergence_3.1.1.NG.14.png
  ✓ Lift - Conservative trim keeping 65.0% data. COV: 4.11%, Confidence: 76%
  ⚠️  Drag - No clear recommendation
     Best COV (7.45%) requires trimming 75% (keeping only 25%). Below safety threshold (20%).
```

**Interpretation:**
- Lift: Best COV requires over-trimming, so fallback to conservative recommendation
- Drag: Even conservative trim doesn't meet safety threshold - data quality is poor

### Edge Case Detection

```
⚠️  Lift - No clear recommendation
   Trim 40%: Mean is zero (stall condition). Using median/MAD instead.
   Trim 60%: Mean changed sign (oscillating). Data not fully settled.
```

**Interpretation:**
- Stall angle: Mean force = 0 (ambiguous), use robust median instead
- Oscillation: Solution is still transitioning between states

---

## Output Files

When convergence analysis runs, you get:

```
OUTPUT_DIR/
├── convergence_results.pkl              # Python pickle with all analysis data
├── convergence_analysis/
│   ├── convergence_3.1.1.NG.10.png      # Plots for each config
│   ├── convergence_3.1.1.NG.14.png
│   ├── ... (one per configuration)
│   └── Convergence_Analysis_Results.txt # Text summary
└── SUMMARY_*.xlsx                        # Excel workbook (updated with convergence data)
```

### Loading Results in Python

```python
import pickle

with open('convergence_results.pkl', 'rb') as f:
    data = pickle.load(f)
    
convergence_results = data['convergence_results']

# Access a specific config's lift analysis
config_key = ('3.1.1.NG.10', 'AoA_10')
lift_analysis = convergence_results[config_key]['lift']

print(f"Recommendation: Remove {lift_analysis['trim_recommendation']} iterations")
print(f"Reason: {lift_analysis['trim_reason']}")
print(f"COV values: {lift_analysis['cov']}")
```

---

## Configuration Options

### In `main.py` (lines 40-50)

```python
# Convergence analysis settings
RUN_CONVERGENCE_ANALYSIS = True         # Enable/disable convergence analysis
CONVERGENCE_MAX_TRIM = 0.8              # Max % of data to trim (0 = 0%, 0.8 = 80%)
CONVERGENCE_NUM_TESTS = 20              # Number of trim points to test (default 20)
```

### In `cfd_functions.py` (line 224)

```python
def analyze_convergence(data_array, min_trim=0, max_trim=0.5, num_tests=10, min_retention=0.2):
    # min_retention: Safety floor (0.2 = keep at least 20% of data)
```

**Change retention floor if needed:**
```python
# In main.py, around line 220:
lift_results, drag_results, plot_path = plot_convergence_analysis(
    config, aoa,
    data['lift'],
    data['drag'],
    OUTPUT_DIR,
    CONVERGENCE_MAX_TRIM,
    CONVERGENCE_NUM_TESTS,
    min_retention=0.25  # Keep at least 25% (instead of default 20%)
)
```

---

## How to Use

### 1. Enable Convergence Analysis

```python
# main.py, line ~45
RUN_CONVERGENCE_ANALYSIS = True
```

### 2. Run the Pipeline

```bash
cd "Data Processing"
python main.py
```

### 3. Review Output

**During execution**, watch for:
- ✓ High confidence (>85%) → Trust the recommendation
- ⚠️ Low confidence (<70%) or warnings → Investigate the data
- Conservative trim messages → Data quality concerns

**After execution**, check:
- `convergence_analysis/*.png` → Visual plots
- `convergence_analysis/Convergence_Analysis_Results.txt` → Summary
- `convergence_results.pkl` → Full data for further analysis

### 4. Use Results

Apply the trim recommendations to your statistics:

```python
# Example: Use recommended trim for lift
trim_iterations = lift_analysis['trim_recommendation']
converged_lift = all_lift_data[trim_iterations:]
final_mean = np.mean(converged_lift)
final_cov = lift_analysis['cov']  # Already calculated
```

---

## Troubleshooting

### "No clear recommendation" message

**Causes:**
- All trim points have oscillation (unstable solution)
- Data quality issues throughout the simulation
- Insufficient data points

**Solutions:**
1. Check CFD simulation parameters (convergence criteria, time stepping)
2. Run simulation longer (more iterations)
3. Verify mesh quality and boundary conditions
4. Check if stall angle (where lift = 0)

### Low confidence (<50%)

**Causes:**
- High COV (poor convergence)
- Over-trimming required to achieve low COV
- Oscillating data

**Solutions:**
1. Increase simulation iteration count
2. Refine mesh
3. Adjust numerical scheme in solver
4. Check for unphysical boundary conditions

### Confidence: 0% or very low

**Likely Issue:**
- `min_retention` safety floor was triggered
- Even conservative trim doesn't meet criteria
- Simulation may not have converged at all

**Action:**
- Review raw convergence plots in `convergence_analysis/*.png`
- Consider re-running simulation with better settings

---

## Technical Details

### COV Normalization

```python
cov_normalized = min(max(cov_val / 50, 0), 1)
```

Maps COV to 0-1 scale:
- COV = 0% → cov_normalized = 0.0 → confidence boost ✓
- COV = 50% → cov_normalized = 1.0 → confidence penalty ✗
- COV > 50% → cov_normalized = 1.0 → maximum penalty

### Robust Statistics

When mean ≈ 0 (stall condition), standard stats fail:
- **COV = σ/μ** → undefined when μ ≈ 0
- **Median Absolute Deviation (MAD)** → used as fallback
  - `MAD = median(|x - median(x)|)`
  - Robust to outliers and zero-mean data

### Backward Compatibility

- Existing code that uses `analyze_convergence()` without `min_retention` works unchanged
- Default value `min_retention=0.2` applies automatically
- Old notebooks/scripts continue to function

---

## References

**Key Equations:**

Coefficient of Variation:
$$COV = \frac{\sigma}{\mu} \times 100\%$$

Median Absolute Deviation:
$$MAD = \text{median}(|x_i - \text{median}(x)|)$$

Confidence Score:
$$C = 0.6(1 - COV_{norm}) + 0.3 \cdot r - p$$

Where:
- $COV_{norm}$ = normalized COV (0-1)
- $r$ = data retention ratio (0-1)
- $p$ = oscillation penalty (0 or 0.5)

---

**Created**: December 15, 2025  
**Implementation**: Improvement 3 - Robust Convergence Analysis  
**Status**: Complete and tested
