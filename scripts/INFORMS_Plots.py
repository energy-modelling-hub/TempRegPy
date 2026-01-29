import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# Global settings and helpers
# ---------------------------------------------------------

np.random.seed(101)

rho, g = 1000.0, 9.81  # SI
DT_HOUR = 1.0          # hours
ROM_SUBSTEPS_PER_HOUR = 4  # 15-min ROM steps

def bounded_slope_disaggregation(prev, target, n_steps, ramp_cap):
    """Generate a bounded-slope profile from prev to target over n_steps."""
    delta = (target - prev)
    step = np.clip(delta / n_steps, -ramp_cap, ramp_cap)
    return np.array([prev + step*(s+1) for s in range(n_steps)])

def resample_kernel_blocksum(h_rom, M):
    """Block-sum resampling of ROM kernel (length multiple of M) to PCM resolution."""
    K_pcm = len(h_rom) // M
    return np.array([h_rom[i*M:(i+1)*M].sum() for i in range(K_pcm)])

# ---------------------------------------------------------
# Build dataset: upstream and downstream plants in a cascade
# ---------------------------------------------------------

def build_dataset(T_hours=96):
    # Time arrays
    t = np.arange(T_hours)           # hourly PCM time
    t_rom = np.arange(T_hours * ROM_SUBSTEPS_PER_HOUR)  # 15-min ROM time
    # Upstream hydropeaking release (m^3/s)
    R_up = 300 + 150*np.sin(2*np.pi*(t % 24)/24.0)
    # FIR routing kernel for downstream (lag + dispersion + attenuation)
    tau = 5                 # hours lag center
    alpha = 0.85            # attenuation
    kernel_len_hours = 12
    k = np.arange(kernel_len_hours)
    h = alpha * np.exp(-0.5*((k - tau)/2.0)**2)  # Gaussian-like
    h /= h.sum() / alpha  # normalize weights to total attenuation alpha

    # Lateral inflow at downstream reach (m^3/s)
    L_down = 40 + 20*np.sin(2*np.pi*(t % 24)/24.0 + 0.6)

    # Downstream inflow via routing superposition
    I_down = np.convolve(R_up, h, mode='full')[:T_hours] + L_down

    # Upstream head: level - tailwater
    level_up = 200 + 1.4*np.sin(2*np.pi*t/T_hours*3)
    tail_up = 150 + 0.6*np.sin(2*np.pi*t/T_hours*5)
    H_up = level_up - tail_up

    # Downstream head depends mildly on routed inflow (tailwater rises with flow)
    level_down = 180 + 1.0*np.sin(2*np.pi*(t % 24)/24.0 + 0.3)
    tail_down = 140 + 0.004*(I_down - I_down.mean())
    H_down = level_down - tail_down

    # Efficiency bounds (upper/lower) for each plant
    eta_upstream_up = 0.93 - 0.02*np.cos(2*np.pi*t/T_hours*2)
    eta_upstream_dn = eta_upstream_up - 0.08

    eta_downstream_up = 0.90 - 0.02*np.cos(2*np.pi*t/T_hours*3)
    eta_downstream_dn = eta_downstream_up - 0.07

    # Flow limits depending on head
    Qmax_up = 260 + 0.4*H_up
    Qmin_up = 50*np.ones(T_hours)

    Qmax_down = 220 + 0.3*H_down
    Qmin_down = 40*np.ones(T_hours)

    # Envelopes (MW)
    Pmax_up = rho*g*eta_upstream_up*Qmax_up*H_up/1e6
    Pmin_up = rho*g*eta_upstream_dn*Qmin_up*H_up/1e6

    Pmax_down = rho*g*eta_downstream_up*Qmax_down*H_down/1e6
    Pmin_down = rho*g*eta_downstream_dn*Qmin_down*H_down/1e6

    # Constant-head baseline for upstream for comparison (median head)
    H_up_const = np.median(H_up)
    Pmax_up_const = rho*g*np.median(eta_upstream_up)*np.median(Qmax_up)*H_up_const/1e6 * np.ones(T_hours)

    # PCM dispatch and reserves (stylized, mostly within envelopes)
    P_dispatch_up = np.minimum(Pmax_up - 8.0, 0.85*Pmax_up)
    R_up_cap_up = np.clip(0.10*Pmax_up, 0, Pmax_up - P_dispatch_up)
    R_dn_cap_up = np.clip(0.08*P_dispatch_up, 0, P_dispatch_up - Pmin_up)

    P_dispatch_down = np.minimum(Pmax_down - 6.0, 0.83*Pmax_down)
    R_up_cap_down = np.clip(0.12*Pmax_down, 0, Pmax_down - P_dispatch_down)
    R_dn_cap_down = np.clip(0.10*P_dispatch_down, 0, P_dispatch_down - Pmin_down)

    # Ramp caps (MW/h) derived heuristically from head/flow changes
    # ROM publishes power ramp caps; we approximate here
    dQmax_up = np.diff(Qmax_up, prepend=Qmax_up[0])
    dH_up = np.diff(H_up, prepend=H_up[0])
    dQmax_down = np.diff(Qmax_down, prepend=Qmax_down[0])
    dH_down = np.diff(H_down, prepend=H_down[0])

    # Effective efficiency for ramp mapping
    eta_eff_up = (eta_upstream_up + eta_upstream_dn)/2
    eta_eff_down = (eta_downstream_up + eta_downstream_dn)/2

    dPcap_up = rho*g*(eta_eff_up*(H_up*np.abs(dQmax_up) + Qmax_up*np.abs(dH_up)))/1e6
    dPcap_down = rho*g*(eta_eff_down*(H_down*np.abs(dQmax_down) + Qmax_down*np.abs(dH_down)))/1e6
    # use a smoothed bound
    DeltaPmax_up = np.maximum(15.0, 0.5*np.abs(dPcap_up) + 20.0)
    DeltaPmax_down = np.maximum(12.0, 0.5*np.abs(dPcap_down) + 18.0)

    # Temporal alignment: use downstream dispatch as PCM hourly setpoints; disaggregate to ROM
    ramp_cap_15min = 40.0  # MW per 15 min
    P_rom_15min = np.zeros(T_hours * ROM_SUBSTEPS_PER_HOUR)
    for h in range(T_hours):
        start = h*ROM_SUBSTEPS_PER_HOUR
        prev = P_dispatch_down[h-1] if h > 0 else P_dispatch_down[h]
        target = P_dispatch_down[h]
        P_rom_15min[start:start+ROM_SUBSTEPS_PER_HOUR] = bounded_slope_disaggregation(
            prev, target, ROM_SUBSTEPS_PER_HOUR, ramp_cap_15min
        )
    # Aggregation consistency
    P_pcm_agg = P_rom_15min.reshape(T_hours, ROM_SUBSTEPS_PER_HOUR).mean(axis=1)

    # Convergence residuals (illustrative): simulate envelope iteration with/without under-relaxation
    iters = np.arange(1, 13)
    # Emulate new ROM envelopes as base Pmax_down plus small perturbations
    noise = 0.03*np.random.randn(len(iters), T_hours)
    Pmax_rom_iter = np.array([Pmax_down*(1 + noise[k-1]) for k in iters])

    # Without under-relaxation: direct replace
    Pmax_no = Pmax_rom_iter.copy()
    rP_no = np.array([np.max(np.abs(Pmax_no[k-1] - (Pmax_no[k-2] if k > 1 else Pmax_no[k-1]))) for k in iters])
    # With under-relaxation: lambda=0.5
    lam = 0.5
    Pmax_relax = np.zeros_like(Pmax_rom_iter)
    for k_idx, k in enumerate(iters):
        prev = Pmax_relax[k_idx-1] if k_idx > 0 else Pmax_down
        Pmax_relax[k_idx] = lam*Pmax_rom_iter[k_idx] + (1-lam)*prev
    rP_relax = np.array([np.max(np.abs(Pmax_relax[k-1] - (Pmax_relax[k-2] if k > 1 else Pmax_relax[k-1]))) for k in iters])

    # Storage series (upstream) for residual proxy: simple integration of mass balance (stylized inflow)
    I_nat_up = 100 + 30*np.sin(2*np.pi*(t % 24)/24.0 + 0.2)
    # turbine flow from dispatch: Q = P / (rho g eta H)
    Q_turb_up = (P_dispatch_up*1e6)/(rho*g*eta_eff_up*H_up)
    Spill_up = np.maximum(0.0, Q_turb_up - Qmax_up) * 0.1  # small spill if over turbine cap
    Evap_up = 2.0*np.ones(T_hours)  # m^3/s equivalent
    Pump_up = np.zeros(T_hours)     # no pumping at upstream
    S_up = np.zeros(T_hours)
    S_up[0] = 50e6
    for tt in range(1, T_hours):
        net = (I_nat_up[tt-1] - Q_turb_up[tt-1] - Spill_up[tt-1] - Evap_up[tt-1] + Pump_up[tt-1]) * 3600.0
        S_up[tt] = S_up[tt-1] + net
    # Residual proxy for storage (differences due to envelope/dispatch changes)
    # Recompute Q_turb_up with relaxed envelopes (scaled dispatch)
    P_dispatch_up_relaxed = P_dispatch_up * (1 + 0.02*np.sin(2*np.pi*iters[-1]/T_hours))
    Q_turb_up_relaxed = (P_dispatch_up_relaxed*1e6)/(rho*g*eta_eff_up*H_up)
    S_up_relaxed = np.zeros(T_hours)
    S_up_relaxed[0] = 50e6
    for tt in range(1, T_hours):
        net = (I_nat_up[tt-1] - Q_turb_up_relaxed[tt-1] - Spill_up[tt-1] - Evap_up[tt-1] + Pump_up[tt-1]) * 3600.0
        S_up_relaxed[tt] = S_up_relaxed[tt-1] + net
    rS_no = np.array([np.max(np.abs(S_up - S_up_relaxed)) for _ in iters])  # illustrative constant across iterations
    rS_relax = 0.7*rS_no  # assume reduced residual with under-relaxation

    # Violation heatmaps: construct per-plant metrics from base series with noise
    n_plants = 10
    plants = [f'Plant_{i}' for i in range(1, n_plants+1)]
    # Base dispatch and envelopes for two reference plants (upstream, downstream)
    P_dispatch_base = np.vstack([P_dispatch_up, P_dispatch_down])
    Pmin_base = np.vstack([Pmin_up, Pmin_down])
    Pmax_base = np.vstack([Pmax_up, Pmax_down])
    DeltaPmax_base = np.vstack([DeltaPmax_up, DeltaPmax_down])

    # Replicate to 10 plants with small multiplicative noise
    P_dispatch_all = np.array([P_dispatch_base[i % 2] * (1 + 0.05*np.random.randn(T_hours)) for i in range(n_plants)])
    Pmin_all = np.array([Pmin_base[i % 2] * (1 + 0.03*np.random.randn(T_hours)) for i in range(n_plants)])
    Pmax_all = np.array([Pmax_base[i % 2] * (1 + 0.03*np.random.randn(T_hours)) for i in range(n_plants)])
    DeltaPmax_all = np.array([DeltaPmax_base[i % 2] * (1 + 0.1*np.random.randn(T_hours)) for i in range(n_plants)])

    # Envelope violation magnitude: max of upper or lower breach
    viol_env = np.maximum(P_dispatch_all - Pmax_all, Pmin_all - P_dispatch_all)
    viol_env = np.clip(viol_env, 0, None)

    # Ramp violation: max(|ΔP|-ΔPmax, 0)
    dP_all = np.diff(P_dispatch_all, axis=1, prepend=P_dispatch_all[:, [0]])
    viol_ramp = np.clip(np.abs(dP_all) - DeltaPmax_all, 0, None)

    # Kernel resampling from ROM 15-min to PCM hourly
    # Build a 15-min ROM kernel (length must be multiple of 4)
    dt_rom_min = 15
    kernel_len_rom = 24  # 6 hours
    k_rom = np.arange(kernel_len_rom)
    tau_rom = 10
    alpha_rom = 0.9
    h_rom = alpha_rom * np.exp(-0.5*((k_rom - tau_rom)/2.5)**2)
    h_rom /= h_rom.sum() / alpha_rom
    h_pcm = resample_kernel_blocksum(h_rom, ROM_SUBSTEPS_PER_HOUR)

    return {
        't': t, 't_rom': t_rom,
        'R_up': R_up, 'L_down': L_down, 'h': h, 'I_down': I_down,
        'H_up': H_up, 'H_down': H_down,
        'eta_upstream_up': eta_upstream_up, 'eta_upstream_dn': eta_upstream_dn,
        'eta_downstream_up': eta_downstream_up, 'eta_downstream_dn': eta_downstream_dn,
        'Qmax_up': Qmax_up, 'Qmin_up': Qmin_up, 'Qmax_down': Qmax_down, 'Qmin_down': Qmin_down,
        'Pmax_up': Pmax_up, 'Pmin_up': Pmin_up, 'Pmax_up_const': Pmax_up_const,
        'Pmax_down': Pmax_down, 'Pmin_down': Pmin_down,
        'P_dispatch_up': P_dispatch_up, 'R_up_cap_up': R_up_cap_up, 'R_dn_cap_up': R_dn_cap_up,
        'P_dispatch_down': P_dispatch_down, 'R_up_cap_down': R_up_cap_down, 'R_dn_cap_down': R_dn_cap_down,
        'DeltaPmax_up': DeltaPmax_up, 'DeltaPmax_down': DeltaPmax_down,
        'P_rom_15min': P_rom_15min, 'P_pcm_agg': P_pcm_agg,
        'iters': iters, 'Pmax_no': Pmax_no, 'Pmax_relax': Pmax_relax,
        'rP_no': rP_no, 'rP_relax': rP_relax, 'rS_no': rS_no, 'rS_relax': rS_relax,
        'plants': plants, 'viol_env': viol_env, 'viol_ramp': viol_ramp,
        'h_rom': h_rom, 'h_pcm': h_pcm
    }

# ---------------------------------------------------------
# Plotting functions (all consume the dataset)
# ---------------------------------------------------------

def plot_envelopes_dispatch_reserves(data):
    t = data['t']
    Pmax = data['Pmax_up']
    Pmin = data['Pmin_up']
    Pmax_const = data['Pmax_up_const']
    P_dispatch = data['P_dispatch_up']
    R_up = data['R_up_cap_up']
    R_dn = data['R_dn_cap_up']

    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(t, Pmax, color='tab:red', label='Pmax(H, η↑)')
    ax.plot(t, Pmin, color='tab:orange', label='Pmin(H, η↓)')
    ax.plot(t, Pmax_const, color='tab:red', ls='--', alpha=0.6, label='Pmax constant-head')
    ax.plot(t, P_dispatch, color='tab:blue', lw=1.5, label='PCM dispatch')

    ax.fill_between(t, P_dispatch, P_dispatch+R_up, color='tab:blue', alpha=0.2, label='Up reserve')
    ax.fill_between(t, P_dispatch-R_dn, P_dispatch, color='tab:blue', alpha=0.2, hatch='//', label='Down reserve')

    ax.set_xlim(0, t[-1])
    ax.set_xlabel('Hour')
    ax.set_ylabel('Power (MW)')
    ax.set_title('Head- and efficiency-dependent envelopes vs constant-head (Upstream)')
    ax.legend(ncol=3, fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('fig_envelopes_dispatch_reserves.png', dpi=200)
    plt.show()

def plot_routing_envelope_shift(data):
    t = data['t']
    R_up = data['R_up']
    I_down = data['I_down']
    Pmax_down = data['Pmax_down']

    fig, axs = plt.subplots(2,1, figsize=(10,6), sharex=True)
    axs[0].plot(t, R_up, label='Upstream release R_up (m³/s)')
    axs[0].plot(t, I_down, label='Downstream inflow I_down (m³/s)')
    axs[0].set_ylabel('Flow (m³/s)')
    axs[0].legend()
    axs[0].grid(alpha=0.3)
    axs[0].set_title('Routing with lag and attenuation (FIR kernel)')

    axs[1].plot(t, Pmax_down, color='tab:red', label='Downstream Pmax(H(I_down))')
    axs[1].set_xlabel('Hour')
    axs[1].set_ylabel('Power (MW)')
    axs[1].legend()
    axs[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('fig_routing_envelope_shift.png', dpi=200)
    plt.show()

def plot_temporal_alignment(data):
    t = data['t']
    t_rom_hours = np.arange(len(data['P_rom_15min'])) / ROM_SUBSTEPS_PER_HOUR
    P_pcm = data['P_dispatch_down']    # hourly PCM setpoints chosen as downstream dispatch
    P_rom = data['P_rom_15min']
    P_pcm_agg = data['P_pcm_agg']

    fig, axs = plt.subplots(2,1, figsize=(10,6), sharex=False)
    axs[0].step(t, P_pcm, where='mid', label='PCM hourly setpoints', color='tab:blue')
    axs[0].plot(t_rom_hours, P_rom, '.', alpha=0.6, label='ROM 15-min disaggregation', color='tab:orange')
    axs[0].set_ylabel('Power (MW)')
    axs[0].legend()
    axs[0].grid(alpha=0.3)
    axs[0].set_title('Temporal alignment: bounded-slope disaggregation')

    axs[1].plot(t, P_pcm, label='PCM original', color='tab:blue')
    axs[1].plot(t, P_pcm_agg, '--', label='Aggregated from ROM', color='tab:green')
    axs[1].set_xlabel('Hour')
    axs[1].set_ylabel('Power (MW)')
    axs[1].legend()
    axs[1].grid(alpha=0.3)
    axs[1].set_title('Aggregation consistency (ROM→PCM)')

    plt.tight_layout()
    plt.savefig('fig_temporal_alignment.png', dpi=200)
    plt.show()

def plot_convergence_residuals(data):
    iters = data['iters']
    rP_no = data['rP_no']
    rS_no = data['rS_no']
    rP_relax = data['rP_relax']
    rS_relax = data['rS_relax']

    fig, ax = plt.subplots(figsize=(9,4))
    ax.plot(iters, rP_no, 'o-', label='||ΔP||∞ (no under-relaxation)')
    ax.plot(iters, rS_no, 'o-', label='||ΔS||∞ (no under-relaxation)')
    ax.plot(iters, rP_relax, 's-', label='||ΔP||∞ (with under-relaxation)')
    ax.plot(iters, rS_relax, 's-', label='||ΔS||∞ (with under-relaxation)')
    ax.set_xlabel('Iteration k')
    ax.set_ylabel('Residual (units)')
    ax.set_title('Convergence residuals with and without under-relaxation')
    ax.grid(alpha=0.3)
    ax.legend(ncol=2, fontsize=9)
    plt.tight_layout()
    plt.savefig('fig_convergence_residuals.png', dpi=200)
    plt.show()

def plot_violation_heatmaps(data):
    plants = data['plants']
    viol_env = data['viol_env']
    viol_ramp = data['viol_ramp']

    # Envelope violations
    fig, ax = plt.subplots(figsize=(10,4.5))
    im = ax.imshow(viol_env, aspect='auto', cmap='Reds', interpolation='nearest')
    ax.set_yticks(np.arange(len(plants)))
    ax.set_yticklabels(plants)
    ax.set_xlabel('Hour')
    ax.set_title('Envelope violation heatmap (magnitude)')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Violation magnitude (MW)', rotation=90)
    plt.tight_layout()
    plt.savefig('fig_violation_heatmap_envelope.png', dpi=200)
    plt.show()

    # Ramp violations
    fig, ax = plt.subplots(figsize=(10,4.5))
    im = ax.imshow(viol_ramp, aspect='auto', cmap='Purples', interpolation='nearest')
    ax.set_yticks(np.arange(len(plants)))
    ax.set_yticklabels(plants)
    ax.set_xlabel('Hour')
    ax.set_title('Ramp violation heatmap (magnitude)')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Violation magnitude (MW)', rotation=90)
    plt.tight_layout()
    plt.savefig('fig_violation_heatmap_ramp.png', dpi=200)
    plt.show()

def plot_kernel_resampling(data):
    # Show ROM 15-min kernel and PCM hourly resampled kernel
    h_rom = data['h_rom']
    h_pcm = data['h_pcm']
    dt_rom_min = 15
    k_rom_hours = np.arange(len(h_rom)) * dt_rom_min / 60.0
    k_pcm_hours = np.arange(len(h_pcm))

    fig, axs = plt.subplots(1,2, figsize=(10,3.5))
    axs[0].stem(k_rom_hours, h_rom, basefmt=" ")
    axs[0].set_xlabel('Lag (hours)')
    axs[0].set_ylabel('Kernel weight')
    axs[0].set_title('ROM FIR kernel (15-min)')

    axs[1].stem(k_pcm_hours, h_pcm, basefmt=" ")
    axs[1].set_xlabel('Lag (hours)')
    axs[1].set_ylabel('Kernel weight')
    axs[1].set_title('PCM resampled kernel (hourly)')
    for ax in axs:
        ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('fig_routing_kernel_resampling.png', dpi=200)
    plt.show()

# ---------------------------------------------------------
# Main: build dataset and generate all plots
# ---------------------------------------------------------

if __name__ == '__main__':
    data = build_dataset(T_hours=96)  # 4 days

    plot_envelopes_dispatch_reserves(data)
    plot_routing_envelope_shift(data)
    plot_temporal_alignment(data)
    plot_convergence_residuals(data)
    plot_violation_heatmaps(data)
    plot_kernel_resampling(data)
