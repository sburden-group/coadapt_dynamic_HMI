# Dynamic Human-Machine Interface (Dynamic HMI) — Co-Adaptation Experiment

This repository contains code and data for a human-in-the-loop experiment studying **online co-adaptation between a human operator and a dynamic interface**.  A participant controls a tracking task through an interface (transfer function *I*) that automatically updates each trial to minimise a combined cost over task error and control effort.  The experiment is described in:

> [paper citation placeholder]

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Hardware Requirements](#2-hardware-requirements)
3. [Environment Setup](#3-environment-setup)
4. [Running the Experiment](#4-running-the-experiment)
5. [Raw Data Structure](#5-raw-data-structure)
6. [Analysis Pipeline](#6-analysis-pipeline)
7. [Pre-processed Data (Pickles)](#7-pre-processed-data-pickles)
8. [Analysis Notebooks and Figures](#8-analysis-notebooks-and-figures)
9. [Key Variables Reference](#9-key-variables-reference)

---

## 1. System Overview

```
        d (disturbance)
        │
        ▼
 u_H ──►[  Interface I  ]──► u_G ──►[  Plant M  ]──► y (output)
  │      (co-adaptive)                (fixed)          │
  └──────────────────────────────────────────────────┘
                    Human closes the loop
```

| Symbol | Meaning |
|--------|---------|
| `y`    | System output (cursor position on screen) |
| `d`    | Sum-of-sines disturbance injected at the output |
| `u_H`  | Human input (slider or keyboard) |
| `u_G`  | Interface output fed to the plant |
| `H`    | Human transfer function (estimated each trial) |
| `I`    | Interface transfer function (co-adapted each trial) |
| `M`    | Plant transfer function (fixed, non-minimum phase) |

**Plant** `M`: discrete-time version of `−2(s−2.2)/(s²+3.6s+4)`, sampled at 60 Hz.

**Interface orders tested:**
- 0th-order: `I = b` (scalar gain)
- 1st-order: `I = (b₀z + b₁)/(z + a)`
- 2nd-order: `I = (b₀z² + b₁z + b₂)/(z² + a₀z + a₁)`

**Co-adaptation algorithm (per trial):**
1. Estimate `H` from closed-loop I/O: `H̃ = −U_H / Y` at stimulated frequencies.
2. Smooth `H` estimate: `H_est = 0.75·H_prev + 0.25·H_current`.
3. Global search over pre-computed interface candidates to minimise the interface cost `c_I = (‖y‖ + 1.5·‖u_H‖ + 0.5·‖u_G‖) / ‖d‖`.
4. Smooth interface update: `I_new = 0.75·I_old + 0.25·I_optimal`.

---

## 2. Hardware Requirements

- **Slider device** (Arduino-based): provides continuous analogue input via USB serial.  A keyboard can be substituted for testing (see [Running the Experiment](#4-running-the-experiment)).
- Computer running Windows or macOS with a display capable of 60 Hz refresh.

To list available serial ports:
```bash
python lib/print_serial.py
```

---

## 3. Environment Setup

The experiment script requires **Python 3.5.4** (pygame 1.9.x is not compatible with Python 3.6+).

### Using conda (recommended)

```bash
conda create --name hmi-exp python=3.5.4 pip
conda activate hmi-exp
```

### Install dependencies

```bash
pip install -U matplotlib
pip install numpy==1.14.3
pip install ipython==6.1.0
pip install pygame==1.9.2
pip install pyserial==3.2.1
pip install control==0.8.0
pip install scipy
```

### Analysis environment

The analysis notebooks can use a more recent Python (3.8+).  Install additionally:

```bash
pip install pandas seaborn jupyter
```

---

## 4. Running the Experiment

Navigate to the repository root and launch the experiment from IPython:

```bash
cd /path/to/dynamic_HMI
ipython
```

```python
run HIL_<order>_nonminphase_AC <subject_id> co-adaptation [COMX]
```

| Argument | Description | Example |
|----------|-------------|---------|
| `<order>` | Interface order: `0th`, `1st`, or `2nd` | `1st` |
| `<subject_id>` | Subject folder name under `data/` | `HCPS097_1st` |
| `co-adaptation` | Protocol file (`protocols/co-adaptation.py`) | `co-adaptation` |
| `[COMX]` | Serial port for slider (omit to use keyboard) | `COM4` or `/dev/cu.usbmodem...` |

**Example:**
```python
run HIL_1st_nonminphase_AC HCPS097_1st co-adaptation COM4
```

**Keyboard controls** (when no slider is connected):
- `←` / `→` — apply left/right input
- `↓` — zero input
- `Space` / `P` — pause/unpause
- `Q` / `Esc` — quit

**Trial structure per condition (21 trials total):**

| Trials | Interface | Description |
|--------|-----------|-------------|
| 0 – 2  | Fixed `I*` | Baseline (fixed initial interface) |
| 3 – 17 | Co-adapting | Interface updates after each trial |
| 18 – 20| Fixed `I*` | Return-to-baseline (fixed interface) |

Each trial lasts **40 seconds** at **60 Hz** (2400 time steps).  A brief reset phase is shown between trials.

**Baseline (passthrough) condition:** Use `HIL_<order>_nonminphase_AC` with a protocol that sets `passthrough = True`.  This keeps `I = 1` for all 12 trials.

---

## 5. Raw Data Structure

Trials are saved automatically at the end of each run into `data/<subject_id>/`.

### File naming

```
data/<subject_id>/<timestamp>_co-adaptation_<trial_id>[_sfx].{npz,csv}
```

Suffixes:
- *(none)* — main trial data
- `_rst0`, `_rst1`, `_rst2` — inter-trial reset phases (exclude from analysis)
- `_react` — reaction-time probe (exclude from analysis)
- `_rej` — manually rejected trial (exclude from analysis)

### NPZ contents

Each `.npz` file contains the following arrays:

| Key | Shape | Description |
|-----|-------|-------------|
| `time_` | `(N,)` | Simulation timestamps (s) |
| `realtime_` | `(N,)` | Wall-clock timestamps (s) |
| `ref_` | `(N,)` | Reference signal (zero in co-adapt protocol) |
| `inp_` | `(N,)` | Human input `u_H(t)` |
| `dis_` | `(N,)` | Disturbance `d(t)` |
| `state_` | `(N, n)` | Plant state |
| `out_` | `(N,)` | System output `y(t)` |
| `mach_` | `(N,)` | Interface output `u_G(t)` |
| `H_` | `(8,)` | Estimated human TF at stimulated frequencies (complex) |
| `G_` | `(p,)` | Interface parameters used in this trial |

`N = 2400` (last 40 s at 60 Hz).  `H_` and `G_` are only present in adaptive-condition trials.

### CSV contents

The `.csv` mirrors the `.npz` with columns: `time, realtime, ref, inp, dis, state1, state2, machine_out, human, machine`.

---

## 6. Analysis Pipeline

```
data/<subject>/*.npz          ← raw per-trial files
        │
        ▼ analysis/collect_data.py
        │  (findFilename, getrawdata, get_data, analyze)
        ▼
analysis/generate_data_pickles.ipynb
        │
        ▼
analysis/HCPS097_107_data.pkl  ← pre-processed group data (11 subjects)
        │
        ├──► H_I_coadaptation_figures.ipynb    (Figure 4)
        ├──► experiment_results_figures.ipynb  (Figure 5)
        └──► computational_results_figures.ipynb (Figure 6)
                    ▲               ▲
      human_model_fit_data.pkl   simulation_results.pkl
```

**To reproduce the analysis from raw data**, open and run `analysis/generate_data_pickles.ipynb`.  This reads all `.npz` files, computes frequency-domain transfer functions via FFT, and saves `HCPS097_107_data.pkl`.

If you only want to reproduce the figures, the pre-computed `.pkl` files are already included — just run the figure notebooks directly.

---

## 7. Pre-processed Data (Pickles)

All pickles live in `analysis/` and are loaded by `analysis/load_data_pickles.py`.

### `HCPS097_107_data.pkl`

Group data for 11 subjects (HCPS097–HCPS107).  Unpacks to:

```python
G_parameters, Gs, Hs, Ds, UHs, UGs, Ys,
ds, uhs, ugs, ys, errors,
Gs_base, Hs_base, Ds_base, UHs_base, UGs_base, Ys_base,
ds_base, uhs_base, ugs_base, ys_base, errors_base
```

**Shape conventions:**

| Variable | Shape | Description |
|----------|-------|-------------|
| `Gs` | `(11, 3, 21, 8)` | Interface TF at 8 stimulated freqs |
| `Hs` | `(11, 3, 21, 2400)` | Human TF (full FFT length) |
| `Ds` | `(11, 3, 21, 2400)` | Disturbance (frequency domain, full FFT) |
| `UHs` | `(11, 3, 21, 2400)` | Human input (frequency domain, full FFT) |
| `UGs` | `(11, 3, 21, 8)` | Interface input at 8 stimulated freqs |
| `Ys` | `(11, 3, 21, 2400)` | Output (frequency domain, full FFT) |
| `ds/uhs/ugs/ys` | `(11, 3, 21, 2400)` | Time-domain counterparts |
| `errors` | `(11, 3, 21)` | MSE per trial |
| `G_parameters` | list of 3 arrays | Interface TF params per order; shapes `(11,21,1)`, `(11,21,3)`, `(11,21,5)` |
| `*_base` variants | — | Same quantities for baseline (passthrough) condition; trial axis has size 12 |

**Axes:** `[subject, condition, trial, frequency/time]`

- `subject`: 0–10 (11 subjects)
- `condition`: 0=0th-order, 1=1st-order, 2=2nd-order interface
- `trial`: 0–20 (21 trials); trials 0–2 and 18–20 are fixed; 3–17 are adaptive

**Indexing fixed vs adaptive trials:**
```python
fixed_trials   = [0, 1, 2, 18, 19, 20]   # fixed interface I*
initial_trials = [3, 4, 5]               # first adaptive trials
final_trials   = [15, 16, 17]            # last adaptive trials
```

### `human_model_fit_data.pkl`

Second- and first-order parametric fits of the human transfer function.  Unpacks to:

```python
H_2nd_params, H_2nd_fits, H_2nd_params_base, H_2nd_fits_base,
H_1st_params, H_1st_fits, H_1st_params_base, H_1st_fits_base
```

`H_2nd_fits` has shape `(11, 3, 21, 8)` — fitted human TF values at the 8 stimulated frequencies.

### `simulation_results.pkl`

Output of `analysis/simulation.ipynb` — simulated co-adaptation for the 1st-order condition using the fitted human model.  Unpacks to:

```python
Hs_sim_parameters_1st, Hs_sim_1st,
Gs_sim_parameters_1st, Gs_sim_1st,
time_domain_y, time_domain_uH, time_domain_uG,
freq_domain_Y, freq_domain_UH, freq_domain_UG, freq_domain_D,
best_triple
```

`Gs_sim_1st` and `Hs_sim_1st` have shape `(N_trial, 8)` — interface/human TF at each simulated trial.

### `protocols/global_search_interfaces_2norm_cost.pkl`

Pre-computed grid of interface candidates used during the online global search.  Unpacks to:

```python
G_star0, G_star1, G_star2,        # optimal interfaces per order
zero_order_Gs, first_order_Gs, second_order_Gs  # full candidate grids
```

`first_order_Gs` has shape `(3, N_candidates)` — each column is a set of `[a, b0, b1]` parameters for `I = (b0z+b1)/(z+a)`.

---

## 8. Analysis Notebooks and Figures

All notebooks are in `analysis/`.  Run them in Jupyter with the working directory set to `analysis/` so that relative pickle paths resolve correctly.

```bash
cd analysis
jupyter notebook
```

### `generate_data_pickles.ipynb`

Reads all raw `.npz` files, computes FFT-based transfer function estimates, and saves `HCPS097_107_data.pkl`.  Run this first if reproducing from raw data.

### `H_I_coadaptation_figures.ipynb` → **Figure 4**

Plots the interface `|I|` and human `|H|` magnitude spectra, comparing:
- **Dashed black**: fixed baseline `I*` (average of fixed trials)
- **Solid blue/red**: co-adapted final interface/human (average of last 3 adaptive trials)
- Paired t-test significance stars at each frequency

Layout: 1×4 subplots (passthrough + 0th/1st/2nd-order conditions).

### `experiment_results_figures.ipynb` → **Figure 5**

Boxplot summaries of performance and control metrics across subjects, including:
- Task error, human effort, interface effort (normalised by disturbance)
- Nyquist stability margin `min_ω |L(iω) + 1|` where `L = H·I·M`
- One-way ANOVA and post-hoc paired t-tests comparing initial, final, and baseline

### `computational_results_figures.ipynb` → **Figure 6**

Computational validation:
- **Model fit** (cell `fc7792f8`): 2nd-order parametric `H` model vs empirical `H` (magnitude + phase Bode plot for 1st-order condition)
- **Simulation vs empirical** (cells `9bd82edf`, `cf5ee8e1`): simulated vs experimental `I` and `H` at convergence
- **Simulation convergence** (cell `bb58e7fb`): interface effort, human effort, and task error over 15 simulated trials
- **Inferred human cost** (cell `932a0e4a`): boxplot of `c_H(H,I) = (‖y‖ + 1.5·‖u_H‖) / ‖d‖` comparing initial, co-adapted, and fixed conditions

### `simulation.ipynb`

Runs the co-adaptation simulation loop using the fitted 2nd-order human model and saves `simulation_results.pkl`.

### `baseline_interface_search.ipynb`

Grid search over interface parameters to find the optimal initial interface `I*` for each condition; saves `protocols/global_search_interfaces_2norm_cost.pkl`.

---

## 9. Key Variables Reference

Defined in `analysis/globalVars.py` and available in all notebooks via `from globalVars import *`:

| Variable | Value | Description |
|----------|-------|-------------|
| `N` | 2400 | Time points per trial |
| `fs` | 60 Hz | Sampling rate |
| `T` | 40 s | Trial duration |
| `t` | `(2400,)` | Time vector |
| `primes` | `[2,3,5,7,11,13,17,19]` | Prime multipliers for stimulated frequencies |
| `base_freq` | 0.05 Hz | Base frequency |
| `freqs` | `primes × 0.05` | 8 stimulated frequencies (Hz) |
| `omegas` | `2π × freqs` | Stimulated frequencies (rad/s) |
| `IX` | `primes × 2` | FFT bin indices of stimulated frequencies |
| `xf` | `(1200,)` | Positive-frequency FFT axis |
| `soM` | `(8,)` complex | Plant `M` evaluated at stimulated frequencies (discrete-time) |
| `zero(G)` | function | Evaluates 0th-order `I = b` at stimulated frequencies |
| `first(G)` | function | Evaluates 1st-order `I = (b₀z+b₁)/(z+a)` |
| `second(G)` | function | Evaluates 2nd-order `I` at stimulated frequencies |
| `condition_orders` | `['0th','1st','2nd']` | Condition labels |

**Interface cost** (used for online co-adaptation and in `computational_results_figures.ipynb`):

```
c_I(H, I) = (‖y‖ + 1.5·‖u_H‖ + 0.5·‖u_G‖) / ‖d‖
```

**Human cost** (inferred, used in Figure 6):

```
c_H(H, I) = (‖y‖ + 1.5·‖u_H‖) / ‖d‖
```

Norms are computed over the 8 lowest stimulated frequencies (`IX[:8]`).
