# -*- coding: utf-8 -*-
"""
Created on Sun May 17 19:32:02 2026

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
PID_MUP = -13
PID_POS = -11

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
# Load ROOT data
# ============================================================
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


branches = ["muDecayDetID","muDecayPosX","muDecayPosY","muDecayPosZ","det_ID",
    "det_x","det_y","det_z","det_edep","det_edep_mup","det_edep_pos","det_VrtxParticleID"]


# d = [5.,10.,15.,20.,25.,30.,35.,40.]
dd = 20.

with uproot.open(f"data/musr_d{int(dd)}mm_B0_0mT_N1e5.root")["t1"] as tree:
    arr = tree.arrays(branches, library="ak")



hit_L1_mu=(arr["det_VrtxParticleID"] == PID_MUP) & (arr["det_ID"] == DET_L1)
hit_L1_ep=(arr["det_VrtxParticleID"] == PID_POS) & (arr["det_ID"] == DET_L1)


arr["det_edep_mup"][hit_L1_mu]


# N_BINS = 100

# bins = np.linspace(-0.5, 0.5, N_BINS + 1)
# bin_centers = 0.5 * (bins[:-1] + bins[1:])

# h_edep_Z, _ = np.histogram(delta_mu_np, bins=bins)










