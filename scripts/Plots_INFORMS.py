import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

# Time horizon: hourly for 7 days
T = 24 * 7
t = np.arange(T)

# Synthetic reservoir level and tailwater producing head H_t
level = 200 + 1.5*np.sin(2*np.pi*t/T*3)  # reservoir level [m]
tailwater = 150 + 0.5*np.sin(2*np.pi*t/T*5)  # tailwater [m]
H = level - tailwater                      # net head [m], positive

# Synthetic efficiency bounds
eta_up = 0.92 - 0.03*np.cos(2*np.pi*t/T*2)  # upper bound
eta_dn = eta_up - 0.08                       # lower bound

# Flow limits dependent on head (stylized)
Qmax = 250 + 0.5*H     # [m^3/s], increases with head
Qmin = 40*np.ones(T)   # minimum flow [m^3/s]

rho, g = 1000.0, 9.81  # SI

# Compute head-dependent envelopes
Pmax = rho*g*eta_up*Qmax*H / 1e6  # MW
Pmin = rho*g*eta_dn*Qmin*H / 1e6  # MW

# Constant-head baseline for comparison
H_const = np.percentile(H, 50)
Pmax_const = rho*g*np.median(eta_up)*np.median(Qmax)*H_const/1e6 * np.ones(T)

# Synthetic PCM dispatch and reserves that respect envelopes (mostly)
P_dispatch = np.minimum(Pmax*0.85, Pmax - 10)  # MW
R_up = np.clip(0.1*Pmax, 0, Pmax - P_dispatch)
R_dn = np.clip(0.08*P_dispatch, 0, P_dispatch - Pmin)

fig, ax = plt.subplots(figsize=(10,4))
ax.plot(t, Pmax, color='tab:red', label='Pmax(H, η↑)')
ax.plot(t, Pmin, color='tab:orange', label='Pmin(H, η↓)')
ax.plot(t, Pmax_const, color='tab:red', ls='--', alpha=0.6, label='Pmax constant-head')
ax.plot(t, P_dispatch, color='tab:blue', lw=1.5, label='PCM dispatch')

# Plot reserves as bands
ax.fill_between(t, P_dispatch, P_dispatch+R_up, color='tab:blue', alpha=0.2, label='Up reserve')
ax.fill_between(t, P_dispatch-R_dn, P_dispatch, color='tab:blue', alpha=0.2, hatch='//', label='Down reserve')

ax.set_xlim(0, T-1)
ax.set_xlabel('Hour')
ax.set_ylabel('Power (MW)')
ax.set_title('Head- and efficiency-dependent envelopes vs constant-head')
ax.legend(ncol=3, fontsize=9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('fig_envelopes_dispatch_reserves.png', dpi=200)
plt.show()

#%%
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)

# Upstream release (stylized hydropeaking profile)
T = 96  # 4 days, hourly
t = np.arange(T)
R_up = 300 + 150*np.sin(2*np.pi*(t%24)/24)  # m^3/s

# FIR routing kernel: lag tau and dispersion with attenuation alpha
tau = 5     # hours
alpha = 0.85
kernel_len = 12
k = np.arange(kernel_len)
h = alpha * np.exp(-0.5*((k - tau)/2.0)**2)
h /= h.sum() / alpha  # normalize to attenuation alpha

# Convolution to get downstream inflow
I_down = np.convolve(R_up, h, mode='full')[:T]

# Simple head response due to downstream discharge (inverse relationship)
H_down = 60 + 10*np.sin(2*np.pi*(t%24)/24) - 0.02*(I_down - I_down.mean())

# Efficiency upper bound and Qmax function of head
eta_up = 0.90 - 0.02*np.cos(2*np.pi*t/T*3)
Qmax = 200 + 0.3*H_down
rho, g = 1000.0, 9.81

Pmax_down = rho*g*eta_up*Qmax*H_down/1e6  # MW

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

#%%
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(1)

# ROM sub-hourly step (15 min) and PCM hourly setpoints
T_hours = 24
rom_step_per_hour = 4
T_rom = T_hours * rom_step_per_hour

# PCM hourly setpoints (MW)
t_pcm = np.arange(T_hours)
P_pcm = 200 + 50*np.sin(2*np.pi*(t_pcm%24)/24)

# Disaggregation: bounded-slope profile within each hour
ramp_cap = 40.0  # MW per 15 min
t_rom = np.arange(T_rom)
P_rom = np.zeros(T_rom)

for h in range(T_hours):
    start = h*rom_step_per_hour
    end = start + rom_step_per_hour
    prev = P_pcm[h-1] if h>0 else P_pcm[h]
    target = P_pcm[h]
    # Create linear segments bounded by ramp_cap
    delta = (target - prev)
    step = np.clip(delta/rom_step_per_hour, -ramp_cap, ramp_cap)
    for s in range(rom_step_per_hour):
        P_rom[start+s] = prev + step*(s+1)

# Aggregation check: average power back to hourly
P_pcm_agg = P_rom.reshape(T_hours, rom_step_per_hour).mean(axis=1)

fig, axs = plt.subplots(2,1, figsize=(10,6), sharex=False)
axs[0].step(t_pcm, P_pcm, where='mid', label='PCM hourly setpoints', color='tab:blue')
axs[0].plot(t_rom/rom_step_per_hour, P_rom, '.', alpha=0.6, label='ROM 15-min disaggregation', color='tab:orange')
axs[0].set_ylabel('Power (MW)')
axs[0].legend()
axs[0].grid(alpha=0.3)
axs[0].set_title('Temporal alignment: bounded-slope disaggregation')

axs[1].plot(t_pcm, P_pcm, label='PCM original', color='tab:blue')
axs[1].plot(t_pcm, P_pcm_agg, '--', label='Aggregated from ROM', color='tab:green')
axs[1].set_xlabel('Hour')
axs[1].set_ylabel('Power (MW)')
axs[1].legend()
axs[1].grid(alpha=0.3)
axs[1].set_title('Aggregation consistency (ROM→PCM)')

plt.tight_layout()
plt.savefig('fig_temporal_alignment.png', dpi=200)
plt.show()

#%%
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(123)

iters = np.arange(1, 15)
# Synthetic residual decay: without and with under-relaxation
rP_no = 120*np.exp(-0.22*iters) + 5*np.random.randn(len(iters))
rS_no = 80*np.exp(-0.18*iters) + 3*np.random.randn(len(iters))
rP_relax = 120*np.exp(-0.35*iters) + 4*np.random.randn(len(iters))
rS_relax = 80*np.exp(-0.30*iters) + 2*np.random.randn(len(iters))

# Clip non-negative
rP_no = np.clip(rP_no, 0, None)
rS_no = np.clip(rS_no, 0, None)
rP_relax = np.clip(rP_relax, 0, None)
rS_relax = np.clip(rS_relax, 0, None)

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


#%%
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(7)

assets = [f'Plant_{i}' for i in range(1, 11)]
T = 72
# Synthetic violation magnitudes (MW or m^3/s equivalents)
viol_envelope = np.random.gamma(1.2, 2.0, size=(len(assets), T))
viol_ramp = np.random.gamma(0.8, 1.5, size=(len(assets), T))

# Combine or plot separately; here we show envelope violations
fig, ax = plt.subplots(figsize=(10,4.5))
im = ax.imshow(viol_envelope, aspect='auto', cmap='Reds', interpolation='nearest')
ax.set_yticks(np.arange(len(assets)))
ax.set_yticklabels(assets)
ax.set_xlabel('Hour')
ax.set_title('Envelope violation heatmap (magnitude)')
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Violation magnitude (units)', rotation=90)
plt.tight_layout()
plt.savefig('fig_violation_heatmap_envelope.png', dpi=200)
plt.show()

# Ramp violations heatmap
fig, ax = plt.subplots(figsize=(10,4.5))
im = ax.imshow(viol_ramp, aspect='auto', cmap='Purples', interpolation='nearest')
ax.set_yticks(np.arange(len(assets)))
ax.set_yticklabels(assets)
ax.set_xlabel('Hour')
ax.set_title('Ramp violation heatmap (magnitude)')
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Violation magnitude (units)', rotation=90)
plt.tight_layout()
plt.savefig('fig_violation_heatmap_ramp.png', dpi=200)
plt.show()


#%%
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(5)

# ROM kernel (15-min)
dt_rom_min = 15
kernel_len = 24  # 6 hours
k = np.arange(kernel_len)
tau = 10  # index
alpha = 0.9
h_rom = alpha * np.exp(-0.5*((k - tau)/2.5)**2)
h_rom /= h_rom.sum() / alpha  # normalize to attenuation alpha

# Resample to PCM hourly kernel by block-summing 4 ROM steps per hour
M = 4  # 4 * 15-min = 60-min
K_pcm = kernel_len // M
h_pcm = np.array([h_rom[i*M:(i+1)*M].sum() for i in range(K_pcm)])

fig, axs = plt.subplots(1,2, figsize=(10,3.5))
axs[0].stem(k*dt_rom_min/60.0, h_rom, basefmt=" ", use_line_collection=True)
axs[0].set_xlabel('Lag (hours)')
axs[0].set_ylabel('Kernel weight')
axs[0].set_title('ROM FIR kernel (15-min)')

axs[1].stem(np.arange(K_pcm), h_pcm, basefmt=" ", use_line_collection=True)
axs[1].set_xlabel('Lag (hours)')
axs[1].set_ylabel('Kernel weight')
axs[1].set_title('PCM resampled kernel (hourly)')
for ax in axs:
    ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('fig_routing_kernel_resampling.png', dpi=200)
plt.show()
