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

def Hit_Level_Particle_Mask(awk_arr, PID, Det_ID):
    """
    SUMMARY.

    Parameters
    ----------
    awk_arr : awkward array.
            Events read from ROOT file using uprrot lib.
    PID : int
        Particle PDG ID.
    Det_ID : int
        Detector ID as given in the ROOT file or musrSim macro file.

    Returns
    -------
    mask for awkward arrays for uproot.
    """
    return (awk_arr["det_VrtxParticleID"] == PID) & (awk_arr["det_ID"] == Det_ID)

# ---------------------------------------
def Event_Level_Mask(Hit_Mask1, Hit_Mask2, Decay_in_Target_Mask):
    """
    SUMMARY.

    Parameters
    ----------
    Hit_Mask1 : boolean awkward array for first layer detector
        Hitl level particle mask for first layer detector.
    Hit_Mask2 : boolean awkward array for second layer detector
        Hitl level particle mask for second layer detector.
    Decay_in_Target_Mask : boolean awkward array
        Hit level boolean array
    Returns
    -------
    Event level mask from hit level one requiring
    single hit for detector layer.
    """
    n_detect1 = ak.sum(Hit_Mask1, axis=1)
    n_detect2 = ak.sum(Hit_Mask2, axis=1)
    clean_mu_mask = ((n_detect1 == 1) & (n_detect2 == 1) & Decay_in_Target_Mask)
    return n_detect1, n_detect2, clean_mu_mask

# ---------------------------------------
def delta(awk_arr, Hit_Mask1, Hit_Mask2, Event_Mask):
    """
    SUMMARY.

    Parameters
    ----------
    awk_arr    : awkward array from ROOT file.
    Hit_Mask1  : boolean awkward array with hits in first layer detector.
    Hit_Mask2  : boolean awkward array with hits in second layer detector.
    Event_Mask : boolean awkward array with event level mask
    
    Returns
    -------
    Delta between extrapolated and real position in XY plane either muon or positron
    """
    x1 = first_hit(awk_arr["det_x"], Hit_Mask1, Event_Mask)
    y1 = first_hit(awk_arr["det_y"], Hit_Mask1, Event_Mask)
    z1 = first_hit(awk_arr["det_z"], Hit_Mask1, Event_Mask)
    x2 = first_hit(awk_arr["det_x"], Hit_Mask2, Event_Mask)
    y2 = first_hit(awk_arr["det_y"], Hit_Mask2, Event_Mask)
    z2 = first_hit(awk_arr["det_z"], Hit_Mask2, Event_Mask)
    x_true = awk_arr["muDecayPosX"][Event_Mask]
    y_true = awk_arr["muDecayPosY"][Event_Mask]
    z_true = awk_arr["muDecayPosZ"][Event_Mask]
    x_ext, y_ext = extrapolate_to_z(x1,y1, z1,x2,y2,z2,z_true)
    delta_awk = delta_xy(x_true, y_true, x_ext, y_ext)
    return ak.to_numpy(ak.drop_none(delta_awk))

# ---------------------------------------
def first_hit(branch, hit_mask, event_mask):
    """
    Return first selected hit per selected event.
    Assumes event_mask already enforces exactly one selected hit,
    but ak.firsts is still convenient and safe.
    """
    return ak.firsts(branch[hit_mask][event_mask])

# ---------------------------------------
def extrapolate_to_z(x1, y1, z1, x2, y2, z2, z_target):
    """
    Straight-line extrapolation from point 1 and point 2 to z_target.
    """
    alpha = (z_target - z1) / (z2 - z1)

    x_ext = x1 + alpha * (x2 - x1)
    y_ext = y1 + alpha * (y2 - y1)

    return x_ext, y_ext

# ---------------------------------------
def delta_xy(x_true, y_true, x_ext, y_ext):
    """
    Lateral distance in the XY plane.
    """
    return np.sqrt((x_true - x_ext)**2 + (y_true - y_ext)**2)

# ---------------------------------------
def summarize(name, values):
    values = np.asarray(values)
    print()
    print(f"{name}")
    print("-" * len(name))
    print(f"N      = {len(values)}")
    print(f"mean   = {np.mean(values):.6f} mm")
    print(f"std    = {np.std(values):.6f} mm")
    print(f"median = {np.median(values):.6f} mm")
    print("quantiles [0.68, 0.90, 0.95, 0.99] =",
          np.quantile(values, [0.68, 0.90, 0.95, 0.99]))

# ---------------------------------------
def Calc_deltas(dd):
    branches = ["muDecayDetID","muDecayPosX","muDecayPosY","muDecayPosZ","det_ID",
    "det_x","det_y","det_z","det_edep","det_edep_mup","det_edep_pos","det_VrtxParticleID"]
    with uproot.open(f"data/musr_d{int(dd)}mm_B0_0mT_N1e5.root")["t1"] as tree:
        arr = tree.arrays(branches, library="ak")
    # Hit-level particle masks
    hit_L1_mu  = Hit_Level_Particle_Mask(arr, PID_MUP, DET_L1)
    hit_L2_mu  = Hit_Level_Particle_Mask(arr, PID_MUP, DET_L2)
    hit_L3_pos = Hit_Level_Particle_Mask(arr, PID_POS, DET_L3)
    hit_L4_pos = Hit_Level_Particle_Mask(arr, PID_POS, DET_L4)
    # Actual sample/decay point.
    # For muons: stopping/decay point.
    # For positrons: production point of the positron.
    decay_in_target = ((arr["muDecayDetID"] == TARGET_ID) &
                       (np.abs(arr["muDecayPosZ"]) <= TARGET_HALF_THICKNESS_Z))
    # Event-level masks
    n_mu_L1,n_mu_L2,clean_mu_mask = Event_Level_Mask(hit_L1_mu, hit_L2_mu, decay_in_target)
    n_pos_L3,n_pos_L4,clean_pos_mask = Event_Level_Mask(hit_L3_pos, hit_L4_pos, decay_in_target)
    # Muon delta: L1-L2 extrapolated to decay/sample point
    delta_mu_np  = delta(arr, hit_L1_mu, hit_L2_mu, clean_mu_mask)
    # Positron delta: L3-L4 extrapolated back to decay/sample point
    delta_pos_np = delta(arr, hit_L3_pos, hit_L4_pos, clean_pos_mask)
    # Summary statistics
    summarize("delta_mu",  delta_mu_np)
    summarize("delta_pos", delta_pos_np)
    #------------
    nn = [n_mu_L1, n_mu_L2, n_pos_L3, n_pos_L4]
    deltas = [delta_mu_np, delta_pos_np]
    masks = [clean_mu_mask, clean_pos_mask]
    return arr, nn, deltas, decay_in_target, masks

# ---------------------------------------
def Save_Plot_Deltas(d:list, DELTA_MAX:float=5.0, N_BINS:int=150, SAVE_FIGURE:bool=False):
    set_publication_style()
    with open('data/deltas.dat','w') as f:
        f.write('#d,delta_mu_mean, delta_mu_std, delta_ep_mean, delta_ep_std, NmuL1, Nmu_L2, Nep_L3, Nep_L4, Nmu_clean, Nep_clean, Ntot\n')
        for dd in d:
            arr, nn, deltas, decay_in_target, masks = Calc_deltas(dd)
            n_mu_L1, n_mu_L2, n_pos_L3, n_pos_L4 = nn
            delta_mu_np, delta_pos_np = deltas
            clean_mu_mask, clean_pos_mask = masks
            if len(delta_mu_np) == 0 or len(delta_pos_np) == 0:
                print(f"WARNING: empty delta array for d = {dd} mm")
                continue
            #---------------
            dmu_mean,dmu_std = delta_mu_np.mean(), delta_mu_np.std()
            dep_mean,dep_std = delta_pos_np.mean(), delta_pos_np.std()
            Ntot = len(arr["det_ID"])
            NmuL1,NmuL2=ak.sum(n_mu_L1 > 0), ak.sum(n_mu_L2 > 0)
            NepL3,NepL4=ak.sum(n_pos_L3 > 0), ak.sum(n_pos_L4 > 0)
            Nmu_clean, Nep_clean = ak.sum(clean_mu_mask), ak.sum(clean_pos_mask)
            #----
            f.write(f'{dd:.1f},{dmu_mean:.3f},{dmu_std:.3f},{dep_mean:.3f},{dep_std:.3f},')
            f.write(f'{NmuL1},{NmuL2},{NepL3},{NepL4},{Nmu_clean},{Nep_clean},{Ntot}\n')
            #---------------
            # Histograms
            bins = np.linspace(0.0, DELTA_MAX, N_BINS + 1)
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            h_mu, _ = np.histogram(delta_mu_np, bins=bins)
            h_pos, _ = np.histogram(delta_pos_np, bins=bins)
            #---------------
            fig, ax = plotting_header(size="single")
            ax.plot(bin_centers, h_mu, "-r", ds="steps-mid", label=r"$\mu^+$")
            ax.plot(bin_centers, h_pos, "-k", ds="steps-mid", label=r"$e^+$")
            ax.set_xlabel(r"$\delta \; \mathrm{[mm]}$")
            ax.set_ylabel("Counts")
            ax.set_xlim(0, DELTA_MAX)
            ax.set_ylim(bottom=0)
            ax.legend()
            # Uncomment if tails matter:
            # ax.set_yscale("log")
            if SAVE_FIGURE:
                fig.savefig(f"delta_d{int(dd)}mm.pdf")
            plt.show()
            plt.close(fig)
            #---------------

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

# =================================
# Save data and plot histograms
# =================================
# d = [5.,10.,15.,20.,25.,30.,35.,40.]
# Save_Plot_Deltas(d, DELTA_MAX=5.0,N_BINS=150, SAVE_FIGURE=False)


# =====================================================================

# ==========================
# Plot delta mean and std
# ==========================

# data = np.loadtxt('data/deltas.dat',dtype=float, delimiter=',')

# SAVE_FIGS = False

# d = data[:,0]
# dmu_mean, dmu_std = data[:,1], data[:,2]
# dep_mean, dep_std = data[:,3], data[:,4]

# xd = np.linspace(0,45,100)
# p_std_mu = np.polyfit(d, dmu_std, 1)
# p_std_ep = np.polyfit(d, dep_std, 1)
# fit_std_mu = np.poly1d(p_std_mu)
# fit_std_ep = np.poly1d(p_std_ep)

# MandokFig4 = np.array([[5.0,0.16],[10.0,0.33],[20.0,0.66],[30.0,0.96],[40.0,1.26]]) 
# set_publication_style()

# fig1, ax1 = plotting_header(size="single")
# ax1.plot(d, dmu_std, "ok", ms=3, label=r"$\sigma\left(\delta_\mu\right)$")
# ax1.plot(d, dep_std, "or", ms=3, label=r"$\sigma\left(\delta_e\right)$")
# ax1.plot(MandokFig4[:,0], MandokFig4[:,1],"^b", ms=3, label=r"Mandok(2026) $\sigma\left(\delta_\mu\right)$")
# ax1.plot(xd, fit_std_mu(xd), "-k", label=r"$\sigma\left(\delta_\mu\right)=%.3f d+ %.2f$"%(p_std_mu[0],p_std_mu[1]))
# ax1.plot(xd, fit_std_ep(xd), "-r", label=r"$\sigma\left(\delta_e\right)=%.3f d+ %.2f$"%(p_std_ep[0],p_std_ep[1]))
# ax1.set_xlabel(r"$d \; \mathrm{[mm]}$")
# ax1.set_ylabel(r"$\sigma\left(\delta \right) \; \mathrm{[mm]}$")
# ax1.set_xlim(0, 45)
# ax1.set_ylim(0, 1.3)
# ax1.legend(loc=0)
# if SAVE_FIGS:
#     fig1.savefig("plots/Std_deltas.pdf")

# p_mean_mu = np.polyfit(d, dmu_mean, 1)
# p_mean_ep = np.polyfit(d, dep_mean, 1)
# fit_mean_mu = np.poly1d(p_mean_mu)
# fit_mean_ep = np.poly1d(p_mean_ep)

# fig2, ax2 = plotting_header(size="single")
# ax2.plot(d, dmu_mean, "ok", ms=3, label=r"$\left\langle\delta_\mu\right\rangle$")
# ax2.plot(d, dep_mean, "or", ms=3, label=r"$\left\langle\delta_e\right\rangle$")
# ax2.plot(xd, fit_mean_mu(xd), "-k", label=r"$\left\langle\delta_\mu\right\rangle= %.3f d %.2f$"%(p_mean_mu[0],p_mean_mu[1]))
# ax2.plot(xd, fit_mean_ep(xd), "-r", label=r"$\left\langle\delta_e\right\rangle = %.3f d+ %.2f$"%(p_mean_ep[0],p_mean_ep[1]))
# ax2.set_xlabel(r"$d \; \mathrm{[mm]}$")
# ax2.set_ylabel(r"$\left\langle\delta\right\rangle \; \mathrm{[mm]}$")
# ax2.set_xlim(0, 45)
# ax2.set_ylim(0, 1.6)
# ax2.legend(loc=0)
# if SAVE_FIGS:
#     fig2.savefig("plots/Mean_deltas.pdf")


# =====================================================================

# ================================
# Plot efficiency in each layer
# ================================

data = np.loadtxt('data/deltas.dat',dtype=float, delimiter=',')

SAVE_FIGS = False

d = data[:,0]
Nmu_L1,Nmu_L2,Nep_L3,Nep_L4 = data[:,5],data[:,6],data[:,7],data[:,8]
Nmu_clean,Nep_clean = data[:,9],data[:,10]
Ntot = data[:,11]

fig3, ax3 = plotting_header(size="single")
ax3.plot(d, 100*Nmu_L1/Ntot,'-k',label=r'$\mu^+$ L1')
ax3.plot(d, 100*Nmu_L2/Ntot,'--r',label=r'$\mu^+$ L2')
ax3.plot(d, 100*Nep_L3/Ntot,'-c',label=r'$e^+$ L3')
ax3.plot(d, 100*Nep_L4/Ntot,'-m',label=r'$e^+$ L4')
ax3.set_xlabel(r"$d \; \mathrm{[mm]}$")
ax3.set_ylabel(r"Efficiency $N_{\rm Layer} / N_{\rm Events}$ in %")
ax3.set_xlim(5, 40)
ax3.set_ylim(0, 101)
ax3.legend(loc=0)
if SAVE_FIGS:
    fig3.savefig("plots/Layer_efficiency.pdf")











