import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import AutoMinorLocator


# Detector IDs
DET_L1 = 101
DET_L2 = 102
DET_L3 = 103
DET_L4 = 104
TARGET_ID = 10

# PDG IDs used by musrSim in your files
PID_MUP = -13   # mu+
PID_POS = -11   # e+

TARGET_HALF_THICKNESS_Z = 0.5  # mm


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


# ============================================================
# Helping 
# ============================================================

def hit_mask(arr, pid, det_id):
    """
    Hit-level mask: selects detector-hit entries belonging to a given
    particle type and detector layer.
    """
    return (
        (arr["det_VrtxParticleID"] == pid) &
        (arr["det_ID"] == det_id)
    )


def compute_acceptance_masks(arr, require_single_hit=False):
    """
    Return event-level masks for muon and positron hit/tracklet acceptances.

    If require_single_hit=False:
        requires at least one selected hit in the layer.

    If require_single_hit=True:
        requires exactly one selected hit in the layer.
        This is stricter and closer to the clean reconstruction sample.
    """

    # ------------------------------------------------------------
    # Target decay / stop mask
    # ------------------------------------------------------------
    target_mask = (
        (arr["muDecayDetID"] == TARGET_ID) &
        (np.abs(arr["muDecayPosZ"]) <= TARGET_HALF_THICKNESS_Z)
    )

    # ------------------------------------------------------------
    # Hit-level masks
    # ------------------------------------------------------------
    hit_mu_L1  = hit_mask(arr, PID_MUP, DET_L1)
    hit_mu_L2  = hit_mask(arr, PID_MUP, DET_L2)

    hit_ep_L3  = hit_mask(arr, PID_POS, DET_L3)
    hit_ep_L4  = hit_mask(arr, PID_POS, DET_L4)

    # ------------------------------------------------------------
    # Number of selected hits per event
    # ------------------------------------------------------------
    n_mu_L1 = ak.sum(hit_mu_L1, axis=1)
    n_mu_L2 = ak.sum(hit_mu_L2, axis=1)

    n_ep_L3 = ak.sum(hit_ep_L3, axis=1)
    n_ep_L4 = ak.sum(hit_ep_L4, axis=1)

    # ------------------------------------------------------------
    # Event-level conditions
    # ------------------------------------------------------------
    if require_single_hit:
        has_mu_L1 = n_mu_L1 == 1
        has_mu_L2 = n_mu_L2 == 1

        has_ep_L3 = n_ep_L3 == 1
        has_ep_L4 = n_ep_L4 == 1
    else:
        has_mu_L1 = n_mu_L1 > 0
        has_mu_L2 = n_mu_L2 > 0

        has_ep_L3 = n_ep_L3 > 0
        has_ep_L4 = n_ep_L4 > 0

    # ------------------------------------------------------------
    # Four masks to report
    # ------------------------------------------------------------

    # 1. Muon upstream track acceptance:
    #    event has a reconstructable incoming muon tracklet from L1--L2.
    mask_mu_L1L2 = has_mu_L1 & has_mu_L2

    # 2. Positron L3 acceptance, conditional on useful muon target decay.
    mask_ep_L3_given_target = target_mask & has_ep_L3

    # 3. Positron L4 acceptance, conditional on useful muon target decay.
    mask_ep_L4_given_target = target_mask & has_ep_L4

    # 4. Positron downstream tracklet acceptance:
    #    target decay and valid L3--L4 positron tracklet.
    mask_ep_L3L4_given_target = target_mask & has_ep_L3 & has_ep_L4

    return {
        "target_mask": target_mask,

        "n_mu_L1": n_mu_L1,
        "n_mu_L2": n_mu_L2,
        "n_ep_L3": n_ep_L3,
        "n_ep_L4": n_ep_L4,

        "mask_mu_L1L2": mask_mu_L1L2,
        "mask_ep_L3_given_target": mask_ep_L3_given_target,
        "mask_ep_L4_given_target": mask_ep_L4_given_target,
        "mask_ep_L3L4_given_target": mask_ep_L3L4_given_target,
    }


def compute_acceptances(arr, require_single_hit=False):
    """
    Compute the four acceptances.

    Muon L1--L2 acceptance is reported globally, relative to all generated events.
    Positron acceptances are reported conditionally, relative to target decays.
    """

    masks = compute_acceptance_masks(arr, require_single_hit=require_single_hit)

    N_gen = len(arr["det_ID"])
    N_target = ak.sum(masks["target_mask"])

    if N_target == 0:
        raise ValueError("No muon target decays/stops found. Cannot normalize positron acceptances.")

    # ------------------------------------------------------------
    # Acceptance definitions
    # ------------------------------------------------------------

    A_mu_L1L2 = ak.sum(masks["mask_mu_L1L2"]) / N_gen

    A_ep_L3_given_target = ak.sum(masks["mask_ep_L3_given_target"]) / N_target

    A_ep_L4_given_target = ak.sum(masks["mask_ep_L4_given_target"]) / N_target

    A_ep_L3L4_given_target = ak.sum(masks["mask_ep_L3L4_given_target"]) / N_target

    return {
        "N_gen": int(N_gen),
        "N_target": int(N_target),

        "A_mu_L1L2": float(A_mu_L1L2),
        "A_ep_L3_given_target": float(A_ep_L3_given_target),
        "A_ep_L4_given_target": float(A_ep_L4_given_target),
        "A_ep_L3L4_given_target": float(A_ep_L3L4_given_target),
    }


# ==============================================================
# ==============================================================
# ==============================================================


branches = ["muDecayDetID","muDecayPosX","muDecayPosY","muDecayPosZ","det_ID",
    "det_x","det_y","det_z","det_edep","det_edep_mup","det_edep_pos","det_VrtxParticleID"]


d = [5.,10.,15.,20.,25.,30.,35.,40.]
#dd = 20

#with open('../data/acceptance1.dat','w') as f:
#    f.write('# d, N_events, N_target, A_mu_L1L2, A_ep_L3|target, A_ep_L4|target, A_ep_L3L4|target\n')
#    for dd in d:
#        with uproot.open(f"../data/musr_d{int(dd)}mm_B0_0mT_N1e5.root")["t1"] as tree:
#            arr = tree.arrays(branches, library="ak")
#        acc = compute_acceptances(arr, require_single_hit=True)        
#        f.write(f"{dd},{acc['N_gen']},{acc['N_target']},{100*acc['A_mu_L1L2']:.3f},")
#        f.write(f"{100*acc['A_ep_L3_given_target']:.3f},{100*acc['A_ep_L4_given_target']:.3f},")
#        f.write(f"{100*acc['A_ep_L3L4_given_target']:.3f}\n")
#        print("=========================")
#        print(f"d={dd} mm")
#        print(f"N generated = {acc['N_gen']}")
#        print(f"N target    = {acc['N_target']}")
#        print(f"A_mu_L1L2              = {100*acc['A_mu_L1L2']:.2f} %")
#        print(f"A_ep_L3 | target       = {100*acc['A_ep_L3_given_target']:.2f} %")
#        print(f"A_ep_L4 | target       = {100*acc['A_ep_L4_given_target']:.2f} %")
#        print(f"A_ep_L3L4 | target     = {100*acc['A_ep_L3L4_given_target']:.2f} %")


######################################################################################################
######################################################################################################
######################################################################################################

#data = np.loadtxt('../data/acceptance1.dat', delimiter=',')
##print(data)

#d         = data[:,0]
#N_events  = data[:,1]
#N_target  = data[:,2]
#A_mu_L1L2 = data[:,3]
#A_ep_L3   = data[:,4]
#A_ep_L4   = data[:,5]
#A_ep_L3L4 = data[:,6]

#figsave = 1

#fig,ax = plotting_header()
##ax.plot(d, 100*N_target/N_events, '-k', ms=3)
#ax.plot(d, A_mu_L1L2, '-m', label=r'$\mu^+$ track L1&L2')
#ax.plot(d, A_ep_L3, '-^c', ms=3, label=r'$e^+$ hit L3')
#ax.plot(d, A_ep_L4, '-vr', ms=3, label=r'$e^+$ hit L4')
#ax.plot(d, A_ep_L3L4, '--k', label=r'$e^+$ track L3&L4')
#ax.set_xlabel(r"$d \; \mathrm{[mm]}$")
#ax.set_ylabel("Geometrical Acceptance [%]")
#ax.set_xlim(5, 40)
#ax.set_ylim(0,101)
#ax.legend(loc=0)
#if figsave:
#    fig.savefig(f"../plots/SIMULATION_1/Acceptance_vs_d.pdf")

#plt.show()

##fig1,ax1 = plotting_header()
##ax1.plot(d, A_ep_L3, '-^c', ms=3)
##ax1.plot(d, A_ep_L4, '-vc', ms=5)
##ax1.plot(d, A_ep_L3L4, '--r', ms=3)
##plt.show()



######################################################################################################
######################################################################################################

figsave = 1

dataA = np.loadtxt('../data/acceptance1.dat', delimiter=',')
d         = dataA[:,0]
#N_events  = dataA[:,1]
#N_target  = dataA[:,2]
#A_mu_L1L2 = dataA[:,3]
#A_ep_L3   = dataA[:,4]
#A_ep_L4   = dataA[:,5]
A_ep_L3L4 = dataA[:,6]
#---------------------------
dataD = np.loadtxt('../data/deltas.dat',dtype=float, delimiter=',')
#d = data[:,0]
dmu_mean, dmu_std = dataD[:,1], dataD[:,2]
#dep_mean, dep_std = dataD[:,3], dataD[:,4]

FoM = A_ep_L3L4/dmu_std/dmu_std


fig,ax = plotting_header()
ax.plot(A_ep_L3L4, dmu_std, '-ok', ms=3)
ax.set_xlabel(r"$A_{e^+,\mathrm{L3L4}}$ [%]")
ax.set_ylabel(r"$\sigma(\delta_\mu) \; \mathrm{[mm]}$")
ax.set_xlim(6, 15)
ax.set_ylim(0.1,1)
if figsave:
    fig.savefig(f"../plots/SIMULATION_1/Sigma_mu_vs_Acceptance_pos.pdf")
plt.show()


fig1,ax1 = plotting_header()
ax1.plot(d, FoM/100, '-ok', ms=3)
ax1.set_xlabel(r"$d\; \mathrm{[mm]}$")
ax1.set_ylabel("FoM")
ax1.set_xlim(5, 40)
ax1.set_ylim(0,9)
if figsave:
    fig1.savefig(f"../plots/SIMULATION_1/FoM_vs_d.pdf")
plt.show()









