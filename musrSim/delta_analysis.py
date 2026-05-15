# -*- coding: utf-8 -*-
"""
Created on Thu May 14 18:12:55 2026

@author: drago
"""

import numpy as np
import uproot
import awkward as ak
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import AutoMinorLocator

mpl.rcParams["figure.dpi"] = 160


FIG_SIZES = {
    "single": (3.35, 2.45),
    "single_tall": (3.35, 3.0),
    "double": (6.9, 4.2),
    "square": (3.35, 3.35),
}


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
    "lines.markersize": 4,

    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,

    "xtick.major.size": 4,
    "ytick.major.size": 4,
    "xtick.minor.size": 2.5,
    "ytick.minor.size": 2.5,

    "xtick.major.width": 0.9,
    "ytick.major.width": 0.9,
    "xtick.minor.width": 0.7,
    "ytick.minor.width": 0.7,

    "legend.frameon": False,

    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,

    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
}


def set_publication_style():
    mpl.rcParams.update(PLOT_STYLE)


def PlottingHeader(size="single",WH=None,dpi=200,minor_ticks=True):
    if WH is None:
        WH = FIG_SIZES[size]
    fig, ax = plt.subplots(figsize=WH, dpi=dpi, constrained_layout=True)
    for spine in ax.spines.values():
        spine.set_linewidth(mpl.rcParams["axes.linewidth"])
    ax.tick_params(axis="both", which="both", direction="in", top=True, right=True)
    if minor_ticks:
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
    return fig, ax


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

with uproot.open("data/musr_d20mm_B0_0mT_N1e5.root")['t1'] as f:
    mudecay = f.arrays(['muDecayDetID','muDecayPosX','muDecayPosY','muDecayPosZ']) 
    det = f.arrays(['det_ID','det_edep','det_x','det_y','det_z'])
    vrtx = f.arrays(['det_VrtxX','det_VrtxY','det_VrtxZ','det_VrtxParticleID'])
    
    
# muDecay_z = muDecay_z[np.abs(muDecay_z) <= 0.5]
# det_z = det_z[np.abs(det_z) <= 0.5]

# h_decay_z, binedg_decay = np.histogram(muDecay_z, bins=150)
# h_det_z, binedg_det = np.histogram(det_z, bins=150)


# set_publication_style()
# # size="single",double
# fig1,ax1=PlottingHeader(size="single")
# ax1.plot(binedg_decay[:-1], h_decay_z,'-k', ds='steps-mid')
# ax1.plot(binedg_det[:-1], h_det_z,'-k', ds='steps-mid')
# ax1.set_xlim(-0.5, 0.5)
# ax1.set_ylim(bottom=1)
# ax1.set_xlabel('Z [mm]')
# ax1.set_ylabel('Counts')
# ax1.set_yscale('log')
# ax1.set_title(r'$\mu^+$ in target decay z distribution', fontsize=14)
# set_publication_style()

# fig1.savefig("muon_decay_Z_target.pdf")
# # fig1.savefig("figure.png", dpi=300)


