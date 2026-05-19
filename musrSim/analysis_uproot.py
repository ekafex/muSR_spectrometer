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
from matplotlib.gridspec import GridSpec

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
    # ------------------------
    set_publication_style()
    # ------------------------
    fig, ax = plt.subplots(figsize=FIG_SIZES[size], dpi=dpi, constrained_layout=True)
    for spine in ax.spines.values():
        spine.set_linewidth(mpl.rcParams["axes.linewidth"])
    ax.tick_params(axis="both", which="both", direction="in", top=True, right=True)
    if minor_ticks:
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
    return fig, ax


def plotting_joint_header(size="single", dpi=200):
    """
    Compact jointplot-like layout:
        ax_top   : X marginal
        ax_main  : 2D histogram
        ax_right : Y marginal, horizontal, sharing Y with ax_main
    """
    # ------------------------
    set_publication_style()
    # ------------------------
    fig = plt.figure(figsize=(3.35, 3.35), dpi=dpi)
    gs = GridSpec(2, 2, figure=fig, width_ratios=(4.0,0.8), height_ratios=(0.8,4.0), wspace=0.05, hspace=0.05)
    ax_top   = fig.add_subplot(gs[0, 0])
    ax_main  = fig.add_subplot(gs[1, 0], sharex=ax_top)
    ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)
    # Make marginal panels visually minimal
    ax_top.set_axis_off()
    ax_right.set_axis_off()
    ax_top.set_facecolor("none")
    ax_right.set_facecolor("none")
    for spine in ax_main.spines.values():
        spine.set_linewidth(mpl.rcParams["axes.linewidth"])
    ax_main.tick_params(axis="both", which="both", direction="in", top=True, right=True)
    ax_main.minorticks_on()
    ax_main.xaxis.set_minor_locator(AutoMinorLocator())
    ax_main.yaxis.set_minor_locator(AutoMinorLocator())
    # Important: keep main image physically square
    ax_main.set_aspect("equal", adjustable="box")
    return fig, ax_main, ax_top, ax_right

# ============================================================
# ============================================================
# ============================================================

def Plot_L1_E_dep_mu_pos(arr, savefig=False):
    hit_L1_mu=(arr["det_VrtxParticleID"] == PID_MUP) & (arr["det_ID"] == DET_L1)
    hit_L1_ep=(arr["det_VrtxParticleID"] == PID_POS) & (arr["det_ID"] == DET_L1)
    dep_mu_L1 = ak.to_numpy(ak.firsts(arr["det_edep"][hit_L1_mu]))
    dep_ep_L1 = ak.to_numpy(ak.firsts(arr["det_edep"][hit_L1_ep]))
    bins = np.linspace(0, 0.9, 241)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    h_mu_L1_edep, _ = np.histogram(dep_mu_L1, bins=bins)
    h_ep_L1_edep, _ = np.histogram(dep_ep_L1, bins=bins)
    fig, ax = plotting_header(size="single")
    ax.plot(bin_centers, h_mu_L1_edep, '-r', ds="steps-mid", label=r"$\mu^+$")
    ax.plot(bin_centers, h_ep_L1_edep, '-b', ds="steps-mid", label=r"$e^+$")
    ax.set_xlabel(r"L1 Energy Deposition $\mathrm{[MeV]}$")
    ax.set_ylabel("Counts")
    ax.set_xlim(0, 0.8)
    ax.set_ylim(bottom=0)
    ax.legend(loc=0)
    if savefig:
        fig.savefig('plots/Energy_Deposit_L1.pdf')

# **********************************************************
# **********************************************************

def Muon_Decay_Stop_Target(arr, figsave=False):
    hit_Target = (arr["muDecayDetID"] == TARGET_ID)
    dec_targ_mu_X = ak.to_numpy((arr["muDecayPosX"][hit_Target]))
    dec_targ_mu_Y = ak.to_numpy((arr["muDecayPosY"][hit_Target]))
    dec_targ_mu_Z = ak.to_numpy((arr["muDecayPosZ"][hit_Target]))
    # -------------------------------------
    bins = np.linspace(-0.51, 0.51, 200 + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    h_stop_Z, _ = np.histogram(dec_targ_mu_Z, bins=bins)
    fig, ax = plotting_header(size="single")
    ax.plot(bin_centers, h_stop_Z, '-k', ds="steps-mid", label=r"$\mu^+$ in Target")
    ax.set_xlabel(r"Z-Axis Decay $\mathrm{[mm]}$")
    ax.set_ylabel("Counts")
    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(1,1e4)
    ax.set_yscale('log')
    ax.legend(loc=0)
    if figsave:
        fig.savefig('plots/Z_target_decay.pdf')
    # --------------------------------------
    bins = np.linspace(-10.1, 10.1, 150 + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    h_stop_X, _ = np.histogram(dec_targ_mu_X, bins=bins)
    h_stop_Y, _ = np.histogram(dec_targ_mu_Y, bins=bins)
    h_stop_XY,_,_ = np.histogram2d(dec_targ_mu_X, dec_targ_mu_Y, bins=bins)
    fig, ax, ax_top, ax_right = plotting_joint_header(size="double")
    ax.imshow(h_stop_XY.T,cmap='Greys',interpolation='nearest',
              origin='lower',extent=[-10,10,-10,10], vmax=80)
    ax.hlines(0,-10,10,ls='--',color='k',lw=0.3,alpha=0.3)
    ax.vlines(0,-10,10,ls='--',color='k',lw=0.3,alpha=0.3)
    ax_top.plot(bin_centers, h_stop_X,  '-k', lw=0.8)
    ax_right.plot(h_stop_Y, bin_centers,'-k', lw=0.8)
    ax.text(-9,8,r'$\mu^+$ Decay in Target for d=%d mm'%dd)
    ax.set_xlabel(r"X-Axis $\mathrm{[mm]}$")
    ax.set_ylabel(r"Y-Axis $\mathrm{[mm]}$")
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax_top.set_ylim(bottom=0)
    ax_right.set_xlim(left=0)
    fig.align_labels()
    if figsave:
        fig.savefig(f'plots/2d_XY_target_decay_d={int(dd)}mm.pdf')

def Generate_XY_std_decay_inTarget():
    d = [5.,10.,15.,20.,25.,30.,35.,40.]
    with open('data/XY_std_decay_Target.dat', 'w') as ff:
        ff.write('# d, std(X), std(Y)\n')
        for dd in d:
            with uproot.open(f"data/musr_d{int(dd)}mm_B0_0mT_N1e5.root")["t1"] as tree:
                arr = tree.arrays(branches, library="ak")
            hit_Target = (arr["muDecayDetID"] == TARGET_ID)
            dec_targ_mu_X = ak.to_numpy((arr["muDecayPosX"][hit_Target]))
            dec_targ_mu_Y = ak.to_numpy((arr["muDecayPosY"][hit_Target]))
            ff.write(f'{dd:.2f},{dec_targ_mu_X.std():.2f},{dec_targ_mu_Y.std():.2f}\n')

def Plot_XY_std_decay_inTarget(savefig=False):
    XY_data = np.loadtxt('data/XY_std_decay_Target.dat', delimiter=',')
    xd = np.linspace(0,45,100)
    p_std_x = np.polyfit(XY_data[:,0],XY_data[:,1], 1)
    p_std_y = np.polyfit(XY_data[:,0],XY_data[:,2], 1)
    fit_std_x = np.poly1d(p_std_x)
    fit_std_y = np.poly1d(p_std_y)
    fig, ax = plotting_header(size="single")
    ax.plot(XY_data[:,0],XY_data[:,1],'ok',ms=3,label='X-axis')
    ax.plot(XY_data[:,0],XY_data[:,2],'dr',ms=3,label='Y-axis')
    ax.plot(xd,fit_std_x(xd),'-k',lw=1,label=r'fit $\sigma(X)=%.3f d +%.2f$'%(p_std_x[0],p_std_x[1]))
    ax.plot(xd,fit_std_y(xd),'--r',lw=1,label=r'fit $\sigma(Y)=%.3f d +%.2f$'%(p_std_y[0],p_std_y[1]))
    ax.set_xlabel(r"$d \; \mathrm{[mm]}$")
    ax.set_ylabel(r"Trasverse Spread of Stoped $\mu^+\; \mathrm{[mm]}$")
    ax.set_xlim(0, 45)
    ax.set_ylim(1.5, 3)
    ax.legend(loc=0)
    if savefig:
        fig.savefig('plots/Muon_Decay_Target_Transverse_Spread.pdf')


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
dd = 20

with uproot.open(f"data/musr_d{int(dd)}mm_B0_0mT_N1e5.root")["t1"] as tree:
    arr = tree.arrays(branches, library="ak")

###############################################
# Plot L1 Energy Deposition
#==============================================
# Plot_L1_E_dep_mu_pos(arr, savefig=0)

#==============================================

###############################################
# Plot muon Decay Position in Target
#==============================================
# Muon_Decay_Stop_Target(arr, figsave=0)

#==============================================


# Generate_XY_std_decay_inTarget()

Plot_XY_std_decay_inTarget(savefig=0)

