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
    fig, ax = plt.subplots(
        figsize=FIG_SIZES[size],
        dpi=dpi,
        constrained_layout=True,
    )

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
    return first_by_time(
        a[quantity],
        a["det_time_start"],
        hit_mask
    )


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


branches = ['eventID',
            'muDecayDetID','muDecayTime','muTargetTime',
            'muDecayPosX','muDecayPosY','muDecayPosZ',
            'posIniMomZ', 'posIniMomZ',
            'det_ID','det_VrtxParticleID','det_VrtxTrackID',
            'det_x','det_y','det_z','det_time_start',
            ]

with uproot.open("../data/musr_d20mm_B6_3mT_N1e5.root")["t1"] as tree:
    arr = tree.arrays(branches, library="ak")



mask_truth_target = (
    (arr["muDecayDetID"] == TARGET_ID)
    & np.isfinite(ak.to_numpy(arr["muTargetTime"]))
    & np.isfinite(ak.to_numpy(arr["muDecayTime"]))
)

dt_truth = arr["muDecayTime"] - arr["muTargetTime"]

mask_truth_time = (dt_truth > 0) & (dt_truth < TGATE)
mask_truth = mask_truth_target & mask_truth_time

mask_pos_up_truth = arr["posIniMomZ"] < 0
mask_pos_down_truth = arr["posIniMomZ"] > 0

dt_truth_up = ak.to_numpy(dt_truth[mask_truth & mask_pos_up_truth])
dt_truth_down = ak.to_numpy(dt_truth[mask_truth & mask_pos_down_truth])

bins = np.linspace(0, TGATE, 261)
counts_truth_up, edges   = np.histogram(dt_truth_up, bins=bins)
counts_truth_down, edges = np.histogram(dt_truth_down, bins=bins)
centers = 0.5 * (edges[:-1] + edges[1:])

yerrors_up   = np.sqrt(np.maximum(counts_truth_up, 1))
yerrors_down = np.sqrt(np.maximum(counts_truth_down, 1))

plt.errorbar(centers,counts_truth_up,yerr=yerrors_up, c='k', fmt="o", markersize=3)
plt.errorbar(centers,counts_truth_down,yerr=yerrors_down, c='r', fmt="^", markersize=3)
plt.xlabel("t = muDecayTime - muTargetTime")
plt.ylabel("Counts")
plt.xlim(0,8)












