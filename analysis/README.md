# Analysis — Co-Adaptive Dynamic HMI

This folder contains the analysis pipeline for a human-machine co-adaptation experiment. The system studies how a dynamic interface (I) and a human operator (H) mutually adapt over trials in closed-loop, in series with a second-order non-minimum-phase machine (M).

## Experiment overview

- **Subjects:** 11 participants (HCPS_097–107), plus 6 pilot subjects (HCPS_088–095)
- **Conditions:** Three interface orders — 0th, 1st, and 2nd order — presented in counterbalanced order
- **Trials per condition:** 21 (3 initial fixed + 15 adaptive + 3 final fixed)
- **Baseline:** 12 pass-through trials (I = 1) interleave between conditions
- **Stimulus:** Multi-sine disturbance at 8 frequencies (0.10, 0.15, 0.25, 0.35, 0.55, 0.65, 0.85, 0.95 Hz), 40 s per trial at 60 Hz

---

## Recommended run to recreate paper figures

```
H_I_coadaptation_figures.ipynb
experiment_results_figures.ipynb
computational_results_figures.ipynb
```


## Notebooks

### 1. `parameter_search.ipynb`
**Purpose:** Grid search over all possible interface parameters to find the optimal baseline interface (I*) for each interface order. Done before the experiment.

- Constructs 0th-order (100 gains), 1st-order (8,546), and 2nd-order (87,038) set of candidate interfaces by discretizing high-pass filter parameters
- Filters out interfaces with negative DC gain (inverted game)
- Minimizes a 2-norm cost function over pilot subject data:  
  `loss = (||Y||² + λ_H·||U_H||² + λ_G·||U_I||²) / ||D||²`  
  with λ_H = 1.5, λ_G = 0.5
- Outputs: `G_star0`, `G_star1`, `G_star2` (one baseline interface per order)
- Saved to: `global_search_interfaces_2norm_cost.pkl` (see the data folder)
- Helper files: `G_find_sum_1st.txt`, `G_find_sum_2nd.txt` (saved DC-gain numerator sums for reproducibility across platforms)

### 2. `generate_data_pickles.ipynb`
**Purpose:** Load and organize raw experimental trial data into structured pickle files.

- Reads raw data using `collect_data.py` (`analyze()` function) for all subjects and conditions
- Organizes baseline (pass-through) and co-adaptation trials per subject, accounting for counterbalanced condition order
- Output arrays have shape `(subjects × conditions × trials × frequencies/timepoints)`
- Saves: `HCPS097_107_data.pkl` (all 11 subjects), `pilot_subjects_passthrough.pkl` (6 pilot subjects)

### 3. `human_model_fit.ipynb`
**Purpose:** Fit parametric transfer function models to empirical human frequency responses.

- Fits 1st-order and 2nd-order models with fixed delay τ = 0.321 sec
- Sweeps multiple initial conditions and bounds using `scipy.optimize.minimize` (L-BFGS-B). NOTE that this takes a while to run!
- Saves: `human_model_fit_data.pkl` — arrays of shape `(11 subjects × 3 conditions × 21 trials × 8 freqs)`

### 4. `simulation.ipynb`
**Purpose:** Simulate the co-adaptation process and tune cost function weights to match empirical data.

- Implements alternating optimization: interface grid-searches for the best G given the accumulated human model H; human optimizer fits the best H given the current G
- Runs 15 simulated trials starting from I* with learning rates αH = αG = 0.75
- **Lambda sweep:** coarse-to-fine grid search over (λ_HH, λ_GH, λ_GG) to minimize the L2 distance between simulated and empirical |H| and |G| in the last 3 trials; best fit: (2.04, 5.5, 1.32). NOTE that this takes a while to run!
- **Penalty sweep:** varies each of the 3 penalty weights independently across 50 values to show sensitivity of interface/human/task effort. NOTE that this takes a while to run!
- Penalty sweep figure: effect of each λ on final-trial interface/human/task energy (normalized to optimum)
- Saves: `simulation_results.pkl`, `simulated_results_sweep_penalty.pkl`

### 5. `H_I_coadaptation_figures.ipynb`
**Purpose:** Bode plot visualizations of interface and human co-adaptation, plus simulation comparison.

- Bode plots of |I| and |H| (magnitude and phase) comparing fixed vs. co-adapted trials across all conditions and the pass-through baseline
- Paired t-tests at each stimulus frequency marking significant changes with `*`
- Outputs: figures in the paper

### 6. `experiment_results_figures.ipynb`
**Purpose:** Generate figures of experimental outcomes with statistical tests.

Produces boxplots (initial vs. final co-adapted vs. fixed baseline) for:
- **Task error** `||ŷ||` — output norm at stimulated frequencies
- **Human effort** `||û_H||` — human input norm
- **Interface effort** `||û_I||` — interface input norm
- **Interface cost** `c_I(H,I) = (||y|| + 1.5·||u_H|| + 0.5·||u_I||) / ||d||`
- **Stability margin** — minimum Nyquist distance `min_ω |L(jω) + 1|` where L = H·M·I
- Outputs: figures in the paper
 

### 7. `computational_results_figures.ipynb`
**Purpose:** Generates the main computational results figures comparing simulation against experiment.

- Second-order human model fit Bode plots (model vs. empirical, first-order condition)
- Simulation vs. empirical overlays for interface I and human H 
- Simulation convergence plot: normalized change in interface effort, human effort, and task error across 15 trials
- Inferred human cost boxplot comparing initial, final, and baseline
- Outputs: figures in the paper

---

## Supporting scripts

| File | Description |
|---|---|
| `globalVars.py` | Global constants: sampling rate (60 Hz), trial length (2400 pts / 40 s), stimulus frequencies, machine TF (`soM`), interface TF constructors (`zero`, `first`, `second`) |
| `load_data_pickles.py` | Loads `HCPS097_107_data.pkl` and interface search results into the namespace shared across analysis notebooks |
| `analysis_functions.py` | `mean_and_interquartile()` and related summary statistics helpers |
| `collect_data.py` | Raw data I/O: `findFilename`, `getrawdata`, `get_data`, `analyze` |
| `plotting_variables.py` | Font sizes (`TINY_SIZE`, `SMALL_SIZE`, `MINI_SIZE`) and color settings |

## Data files (pickle)

| File | Contents |
|---|---|
| `HCPS097_107_data.pkl` | All experimental data for 11 subjects (G_parameters, Gs, Hs, Ds, UHs, UGs, Ys, ds, uhs, ugs, ys, errors + baseline equivalents) |
| `pilot_subjects_passthrough.pkl` | Pass-through (I=1) baseline data for 6 pilot subjects; used in `parameter_search.ipynb` |
| `human_model_fit_data.pkl` | Fitted 1st- and 2nd-order human model parameters and frequency responses |
| `simulation_results.pkl` | Best co-adaptation simulation (lambda = 2.04, 5.5, 1.32) |
| `simulated_results_sweep_penalty.pkl` | Penalty sweep results (3 × 50 simulate_alt calls) |



## Dependencies

See `requirements.txt`. Key packages: `numpy`, `scipy`, `matplotlib`, `pandas`, `statsmodels`, `seaborn`.