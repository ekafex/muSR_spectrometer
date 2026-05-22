# -*- coding: utf-8 -*-
"""
Created on Wed May 20 10:42:48 2026

@author: drago
"""

import numpy as np
import uproot
import awkward as ak
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import AutoMinorLocator

from scipy.optimize import curve_fit

# ============================================================
# User settings
# ============================================================

DET_L1 = 101
DET_L2 = 102
DET_L3 = 103
DET_L4 = 104
TARGET_ID = 10

# PDG convention:
PID_MUP = -13 # mu+
PID_POS = -11 # e+

# target half-thickness cut around z = 0, in mm
TARGET_HALF_THICKNESS_Z = 0.5
Z_TARGET = 0.

TGATE = 13.0   # µs gate timing.

DMATCH = 1.0 # mm

# ============================================================
# Plot style
# ============================================================

mpl.rcParams["figure.dpi"] = 160

FIG_SIZES = {
    "single": (3.35, 2.45),
    "double": (6.9, 4.2),
}

# ---------------------------------------
PLOT_STYLE = {
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "STIX Two Text", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.linewidth": 1.0,
    "lines.linewidth": 1.4,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "legend.frameon": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
}

# ---------------------------------------
def set_publication_style():
    mpl.rcParams.update(PLOT_STYLE)

# ---------------------------------------
def plotting_header(size="single", dpi=200, minor_ticks=True):
    set_publication_style()
    fig, ax = plt.subplots(figsize=FIG_SIZES[size], dpi=dpi, constrained_layout=True)
    for spine in ax.spines.values():
        spine.set_linewidth(mpl.rcParams["axes.linewidth"])
    ax.tick_params(axis="both", which="both", direction="in", top=True, right=True)
    if minor_ticks:
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
    return fig, ax

# ============================================================
# Helper functions
# ============================================================

def first_by_time(values, times, mask):
    """
    Return first value per event after applying a jagged mask and sorting by time.
    values, times, mask are jagged arrays with same structure.
    """
    selected_values = values[mask]
    selected_times = times[mask]
    order = ak.argsort(selected_times, axis=1)
    selected_values = selected_values[order]
    return ak.firsts(selected_values)


def first_hit_quantity(a, hit_mask, quantity):
    return first_by_time(a[quantity], a["det_time_start"], hit_mask)


def has_hit(awk_arr, hit_mask):
    return ak.num(awk_arr["det_ID"][hit_mask], axis=1) > 0


def extrapolate_to_z(x1, y1, z1, x2, y2, z2, z_sample=0.0):
    alpha = (z_sample - z1) / (z2 - z1)
    x = x1 + alpha * (x2 - x1)
    y = y1 + alpha * (y2 - y1)
    return x, y


def dist_xy(xa, ya, xb, yb):
    return np.sqrt((xa - xb)**2 + (ya - yb)**2)


# ============================================================
# Load ROOT data
# ============================================================
# =====================================================================
# keys = ['runID','eventID','weight','timeToNextEvent','BFieldAtDecay',
#  'muIniTime','muIniPosX','muIniPosY','muIniPosZ',
#  'muIniMomX','muIniMomY','muIniMomZ','muIniPolX','muIniPolY','muIniPolZ',
#  'muDecayDetID',
#  'muDecayPosX','muDecayPosY','muDecayPosZ','muDecayTime',
#  'muDecayPolX','muDecayPolY','muDecayPolZ',
#  'muTargetTime','muTargetPolX','muTargetPolY','muTargetPolZ',
#  'muTargetMomX','muTargetMomY','muTargetMomZ',
#  'posIniMomX','posIniMomY','posIniMomZ',
#  'nFieldNomVal', 'fieldNomVal',
#  'det_n','det_ID','det_edep','det_edep_el','det_edep_pos','det_edep_gam',
#  'det_edep_mup','det_nsteps','det_length','det_time_start','det_time_end',
#  'det_x','det_y','det_z','det_kine',
#  'det_VrtxX','det_VrtxY','det_VrtxZ','det_VrtxKine',
#  'det_VrtxVolID','det_VrtxProcID','det_VrtxTrackID','det_VrtxParticleID',
#  'det_VvvKine','det_VvvX','det_VvvY','det_VvvZ','det_VvvVolID',
#  'det_VvvProcID','det_VvvTrackID','det_VvvParticleID']
# =====================================================================
# =====================================================================
# =====================================================================

def musrSpec(t, N0, A, B, omega, phi, sigma):
    tau_mu = 2.197 # us muon lifetime
    # B_mag_y= 6.3e-3# T
    return N0*np.exp(-t/tau_mu)*(1+A*np.cos(omega*t+phi)*np.exp(-(sigma*t)**2/2)) + B

def musrSpec1(t, N0, A, B, omega, phi):
    tau_mu = 2.197 # us muon lifetime
    # B_mag_y= 6.3e-3# T
    return N0*np.exp(-t/tau_mu)*(1 + A*np.cos(omega*t+phi)) + B

def musrSpec2(t, N0, A, omega, phi):
    tau_mu = 2.197 # us muon lifetime
    # B_mag_y= 6.3e-3# T
    return N0*np.exp(-t/tau_mu)*(1 + A*np.cos(omega*t+phi))


branches = ['eventID',
            'muDecayDetID','muDecayTime','muTargetTime',
            'muDecayPosX','muDecayPosY','muDecayPosZ',
            'posIniMomZ', 'posIniMomZ',
            'det_ID','det_VrtxParticleID','det_VrtxTrackID',
            'det_x','det_y','det_z','det_time_start',
            ]

with uproot.open("../data/musr_TargetD6mm_d20mm_B6_3mT_N1e5.root")["t1"] as tree:
    arr = tree.arrays(branches, library="ak")


# savefig = 0

# mask_truth_target = (
#     (arr["muDecayDetID"] == TARGET_ID)
#     & np.isfinite(ak.to_numpy(arr["muTargetTime"]))
#     & np.isfinite(ak.to_numpy(arr["muDecayTime"]))
# )

# dt_truth = arr["muDecayTime"] - arr["muTargetTime"]

# mask_truth_time = (dt_truth > 0) & (dt_truth < TGATE)
# mask_truth = mask_truth_target & mask_truth_time

# mask_pos_up_truth = arr["posIniMomZ"] < 0
# mask_pos_down_truth = arr["posIniMomZ"] > 0

# dt_truth_up = ak.to_numpy(dt_truth[mask_truth & mask_pos_up_truth])
# dt_truth_down = ak.to_numpy(dt_truth[mask_truth & mask_pos_down_truth])

# bins = np.linspace(0, TGATE, 261)
# counts_truth_up, edges   = np.histogram(dt_truth_up, bins=bins)
# counts_truth_down, edges = np.histogram(dt_truth_down, bins=bins)
# centers = 0.5 * (edges[:-1] + edges[1:])

# yerrors_up   = np.sqrt(np.maximum(counts_truth_up, 1))
# yerrors_down = np.sqrt(np.maximum(counts_truth_down, 1))


# # N0, A, B, omega, phi, sigma
# popt_up, pcov_up  = curve_fit(musrSpec, centers, counts_truth_up, p0=[750.,9,3,1,0.1,0.3])
# popt_down, pcov_down  = curve_fit(musrSpec, centers, counts_truth_down, p0=[750.,9,3,1,0.1,0.3])

# N0_up, A_up, B_up, omega_up, phi_up, sigma_up = popt_up
# N0_down, A_down, B_down, omega_down, phi_down, sigma_down = popt_down
# tt = np.linspace(0,10,300)


# fig, ax = plotting_header(size="single")
# ax.errorbar(centers,counts_truth_up/N0_up,yerr=yerrors_up/N0_up, lw=0.8, c='k', fmt="o", ms=1.5, label='Upstream')
# ax.plot(tt, musrSpec(tt, N0_up, A_up, B_up, omega_up, phi_up, sigma_up)/N0_up,'-k',lw=1)
# ax.errorbar(centers,counts_truth_down/N0_down,yerr=yerrors_down/N0_down, lw=0.8, c='r', fmt="^", ms=1.5, label='Downstream')
# ax.plot(tt, musrSpec(tt, N0_down, A_down, B_down, omega_down, phi_down, sigma_down)/N0_down,'-r',lw=1)
# ax.set_xlabel(r"$t \; {\rm [\mu\,s]}$")
# ax.set_ylabel(r"$N(t)/N_0$")
# ax.set_xlim(0,8)
# ax.set_ylim(bottom=0)
# ax.legend(loc=0)
# if savefig:
#     fig.savefig('../plots/vx_muSR_spectrum_ideal.pdf')





savefig = 0

beam_radius_cut = 5.0  # mm, equivalent to 4 mm diameter

is_mup = (arr["det_VrtxParticleID"] == PID_MUP)
mask_mu_stops_target = (arr["muDecayDetID"] == TARGET_ID)
mu_L1_mask = (arr["det_ID"] == DET_L1) & is_mup
mu_L2_mask = (arr["det_ID"] == DET_L2) & is_mup

has_mu_L1  = has_hit(arr, mu_L1_mask)
has_mu_L2  = has_hit(arr, mu_L2_mask)

has_mu_track = has_mu_L1 & has_mu_L2

mu_L1_t = first_hit_quantity(arr, mu_L1_mask, "det_time_start")
mu_L1_x = first_hit_quantity(arr, mu_L1_mask, "det_x")
mu_L1_y = first_hit_quantity(arr, mu_L1_mask, "det_y")
mu_L1_z = first_hit_quantity(arr, mu_L1_mask, "det_z")
mu_L2_t = first_hit_quantity(arr, mu_L2_mask, "det_time_start")
mu_L2_x = first_hit_quantity(arr, mu_L2_mask, "det_x")
mu_L2_y = first_hit_quantity(arr, mu_L2_mask, "det_y")
mu_L2_z = first_hit_quantity(arr, mu_L2_mask, "det_z")


t_mu_rec = 0.5 * (mu_L1_t + mu_L2_t)
xmu_ext, ymu_ext = extrapolate_to_z(mu_L1_x, mu_L1_y, mu_L1_z, mu_L2_x, mu_L2_y, mu_L2_z, Z_TARGET)


mask_beam_region = np.sqrt(mu_L1_x**2 + mu_L1_y**2) < beam_radius_cut

#=================================


is_pos = arr["det_VrtxParticleID"] == PID_POS
pos_L1_mask = (arr["det_ID"] == DET_L1) & is_pos
pos_L2_mask = (arr["det_ID"] == DET_L2) & is_pos
pos_L3_mask = (arr["det_ID"] == DET_L3) & is_pos
pos_L4_mask = (arr["det_ID"] == DET_L4) & is_pos

has_pos_L1 = has_hit(arr, pos_L1_mask)
has_pos_L2 = has_hit(arr, pos_L2_mask)
has_pos_L3 = has_hit(arr, pos_L3_mask)
has_pos_L4 = has_hit(arr, pos_L4_mask)

has_pos_up_track = has_pos_L1 & has_pos_L2
has_pos_down_track = has_pos_L3 & has_pos_L4

pos_L1_t = first_hit_quantity(arr, pos_L1_mask, "det_time_start")
pos_L1_x = first_hit_quantity(arr, pos_L1_mask, "det_x")
pos_L1_y = first_hit_quantity(arr, pos_L1_mask, "det_y")
pos_L1_z = first_hit_quantity(arr, pos_L1_mask, "det_z")
pos_L2_t = first_hit_quantity(arr, pos_L2_mask, "det_time_start")
pos_L2_x = first_hit_quantity(arr, pos_L2_mask, "det_x")
pos_L2_y = first_hit_quantity(arr, pos_L2_mask, "det_y")
pos_L2_z = first_hit_quantity(arr, pos_L2_mask, "det_z")
pos_L3_t = first_hit_quantity(arr, pos_L3_mask, "det_time_start")
pos_L3_x = first_hit_quantity(arr, pos_L3_mask, "det_x")
pos_L3_y = first_hit_quantity(arr, pos_L3_mask, "det_y")
pos_L3_z = first_hit_quantity(arr, pos_L3_mask, "det_z")
pos_L4_t = first_hit_quantity(arr, pos_L4_mask, "det_time_start")
pos_L4_x = first_hit_quantity(arr, pos_L4_mask, "det_x")
pos_L4_y = first_hit_quantity(arr, pos_L4_mask, "det_y")
pos_L4_z = first_hit_quantity(arr, pos_L4_mask, "det_z")


t_pos_up_rec = 0.5 * (pos_L1_t + pos_L2_t)
xpos_up_ext, ypos_up_ext = extrapolate_to_z(pos_L2_x, pos_L2_y, pos_L2_z, pos_L1_x, pos_L1_y, pos_L1_z, Z_TARGET)

t_pos_down_rec = 0.5 * (pos_L3_t + pos_L4_t)
xpos_down_ext, ypos_down_ext = extrapolate_to_z(pos_L3_x, pos_L3_y, pos_L3_z, pos_L4_x, pos_L4_y, pos_L4_z, Z_TARGET)

#=================================

dmatch_up = dist_xy(xmu_ext, ymu_ext, xpos_up_ext, ypos_up_ext)
dmatch_down = dist_xy(xmu_ext, ymu_ext, xpos_down_ext, ypos_down_ext)

#=================================
dt_up_rec = t_pos_up_rec - t_mu_rec
dt_down_rec = t_pos_down_rec - t_mu_rec

#=================================
mask_rec_up = (has_mu_track & has_pos_up_track & mask_mu_stops_target
    & mask_beam_region & (dmatch_up <= DMATCH) & (dt_up_rec > 0)
    & (dt_up_rec < TGATE))

mask_rec_down = (has_mu_track & has_pos_down_track & mask_mu_stops_target
    & mask_beam_region & (dmatch_down <= DMATCH) & (dt_down_rec > 0)
    & (dt_down_rec < TGATE))

dt_up_selected = ak.to_numpy(dt_up_rec[mask_rec_up])
dt_down_selected = ak.to_numpy(dt_down_rec[mask_rec_down])

#=================================
#=================================

Ntot = len(arr["eventID"])
print("Total events:", Ntot)
print("Muon L1-L2 tracks:", ak.sum(has_mu_track))
print("Muon stops target:", ak.sum(mask_mu_stops_target))
print("Upstream positron tracks:", ak.sum(has_pos_up_track))
print("Downstream positron tracks:", ak.sum(has_pos_down_track))
print("Accepted upstream vx events:", ak.sum(mask_rec_up))
print("Accepted downstream vx events:", ak.sum(mask_rec_down))




bins = np.linspace(0, TGATE, 201)
centers = 0.5 * (bins[:-1] + bins[1:])

counts_up, _ = np.histogram(dt_up_selected, bins=bins)
counts_down, _ = np.histogram(dt_down_selected, bins=bins)

yerrors_up   = np.sqrt(np.maximum(counts_up, 1))
yerrors_down = np.sqrt(np.maximum(counts_down, 1))

#----------------------------------------------------------
# Bounds =([  1,-1,   0, 0.1,-np.pi, 0], # lower bounds
#          [500, 1, 100,  10, np.pi, 1]  # upper bounds
#         )

# ic = centers > 0.1
# # N0, A, B, omega, phi, sigma
# popt_up, pcov_up      = curve_fit(musrSpec, centers[ic],   counts_up[ic], p0=[153.,-0.29, 0.46,5.34,-1.6,0.], bounds=Bounds)
# popt_down, pcov_down  = curve_fit(musrSpec, centers[ic], counts_down[ic], p0=[153.,-0.35, 0.36,5.34, 1.6,0.], bounds=Bounds)

# N0_up,     A_up,   B_up,   omega_up,   phi_up,   sigma_up = popt_up
# N0_down, A_down, B_down, omega_down, phi_down, sigma_down = popt_down

# txt = f'''
# param | Upstream | Downstream |
# ===============================
# N0    | {N0_up:.3f}  | {N0_down:.3f}    |
# A     | {A_up:.3f}   | {A_down:.3f}     |
# B     | {B_up:.3f}    | {B_down:.3f}     |
# omega | {omega_up:.3f}    | {omega_down:.3f}      |
# phi   | {phi_up:.3f}   | {phi_down:.3f}      |
# sigma | {sigma_up:.3f}    | {sigma_down:.3f}      |
# '''

#----------------------------------------------------------

# Bounds =([  1,-1,  0, 0.1,-np.pi], # lower bounds
#          [500, 1, 100,  10, np.pi]  # upper bounds
#         )
# ic = centers > 0.1
# # N0, A, B, omega, phi
# popt_up, pcov_up      = curve_fit(musrSpec1, centers[ic],   counts_up[ic], p0=[153.,-0.29, 0.46,5.34,-1.6], bounds=Bounds)
# popt_down, pcov_down  = curve_fit(musrSpec1, centers[ic], counts_down[ic], p0=[153.,-0.35, 0.36,5.34, 1.6], bounds=Bounds)

# N0_up,     A_up,   B_up,   omega_up,   phi_up = popt_up
# N0_down, A_down, B_down, omega_down, phi_down = popt_down

# txt = f'''
# param | Upstream | Downstream |
# ===============================
# N0    | {N0_up:.3f}  | {N0_down:.3f}    |
# A     | {A_up:.3f}   | {A_down:.3f}     |
# B     | {B_up:.3f}    | {B_down:.3f}     |
# omega | {omega_up:.3f}    | {omega_down:.3f}      |
# phi   | {phi_up:.3f}   | {phi_down:.3f}      |
# '''


#----------------------------------------------------------

Bounds =([  1,-1, 0.1,-np.pi], # lower bounds
         [500, 1,  10, np.pi]  # upper bounds
        )
ic = centers > 0.1
# N0, A, omega, phi
popt_up, pcov_up      = curve_fit(musrSpec2, centers[ic],   counts_up[ic], p0=[153.,-0.29, 5.34,-1.6], bounds=Bounds)
popt_down, pcov_down  = curve_fit(musrSpec2, centers[ic], counts_down[ic], p0=[153.,-0.35, 5.34, 1.6], bounds=Bounds)

N0_up,     A_up, omega_up,   phi_up = popt_up
N0_down, A_down, omega_down, phi_down = popt_down

txt = f'''
param | Upstream | Downstream |
===============================
N0    | {N0_up:.3f}  | {N0_down:.3f}    |
A     | {A_up:.3f}   | {A_down:.3f}     |
omega | {omega_up:.3f}    | {omega_down:.3f}      |
phi   | {phi_up:.3f}   | {phi_down:.3f}      |
'''

#----------------------------------------------------------



print(txt)


tt = np.linspace(0,10,300)

fig, ax = plotting_header(size="single")
ax.errorbar(centers,counts_up/N0_up,yerr=yerrors_up/N0_up, lw=0.8, c='k', fmt="o", ms=1.5, label='Upstream')
# ax.plot(tt, musrSpec(tt, N0_up, A_up, B_up, omega_up, phi_up, sigma_up)/N0_up,'-c',lw=1, label='Upstream fit')
# ax.plot(tt, musrSpec1(tt, N0_up, A_up, B_up, omega_up, phi_up)/N0_up,'-c',lw=1, label='Upstream fit')
ax.plot(tt, musrSpec2(tt, N0_up, A_up, omega_up, phi_up)/N0_up,'-c',lw=1, label='Upstream fit')
ax.errorbar(centers,counts_down/N0_down,yerr=yerrors_down/N0_down, lw=0.8, c='r', fmt="^", ms=1.5, label='Downstream')
# ax.plot(tt, musrSpec(tt, N0_down, A_down, B_down, omega_down, phi_down, sigma_down)/N0_down,'-b',lw=1, label='Downstream fit')
# ax.plot(tt, musrSpec1(tt, N0_down, A_down, B_down, omega_down, phi_down)/N0_down,'-b',lw=1, label='Downstream fit')
ax.plot(tt, musrSpec2(tt, N0_down, A_down, omega_down, phi_down)/N0_down,'-b',lw=1, label='Downstream fit')
ax.set_xlabel(r"$t \; {\rm [\mu\,s]}$")
ax.set_ylabel(r"$N(t)/N_0$")
ax.set_xlim(0,8)
ax.set_ylim(bottom=0)
ax.legend(loc=0)
if savefig:
    fig.savefig('../plots/vx_muSR_spectrum_simulation.pdf')


# ri_up = (counts_up[ic]-musrSpec2(centers[ic], N0_up, A_up, omega_up, phi_up))/yerrors_up[ic]
# ri_down = (counts_down[ic]-musrSpec2(centers[ic], N0_down, A_down, omega_down, phi_down))/yerrors_down[ic]

# xbins = np.linspace(-4,4,61)
# hri_up,  xb_up   = np.histogram(ri_up,   bins=xbins)
# hri_down,xb_down = np.histogram(ri_down, bins=xbins)

# xb   = 0.5*(xbins[:-1]   + xbins[1:])
# plt.plot(xb, hri_up, '-k', ds='steps-mid')
# plt.plot(xb, hri_down, '-r', ds='steps-mid')





