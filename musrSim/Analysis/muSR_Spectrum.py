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
from matplotlib.gridspec import GridSpec

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
# Helper functions
# ============================================================

def first_hit_quantity(awk_arr, hit_mask, quantity):
    """
    Return the earliest selected hit quantity per event.

    hit_mask must be a jagged hit-level mask with the same structure as det_ID.
    Output is event-level: one value per event, or None if no selected hit exists.
    """
    selected_values = awk_arr[quantity][hit_mask]
    selected_times  = awk_arr["det_time_start"][hit_mask]
    order = ak.argsort(selected_times, axis=1)
    selected_values = selected_values[order]
    return ak.firsts(selected_values)


def Mask_Particle_Track_2Layers_Hits(awk_arr, D1_ID, D2_ID, PID):
    """
    Build hit-level masks for a particle crossing two detector layers,
    plus event-level masks telling whether each layer has at least one hit.
    """
    is_particle = (awk_arr["det_VrtxParticleID"] == PID)
    D1_hit_mask = (awk_arr["det_ID"] == D1_ID) & is_particle
    D2_hit_mask = (awk_arr["det_ID"] == D2_ID) & is_particle
    has_hit_D1 = ak.num(awk_arr["det_ID"][D1_hit_mask], axis=1) > 0
    has_hit_D2 = ak.num(awk_arr["det_ID"][D2_hit_mask], axis=1) > 0
    has_track = has_hit_D1 & has_hit_D2
    return D1_hit_mask, D2_hit_mask, has_hit_D1, has_hit_D2, has_track


def first_Hits_Coordinates(awk_arr, hit_mask):
    hit_t = first_hit_quantity(awk_arr, hit_mask, "det_time_start")
    hit_x = first_hit_quantity(awk_arr, hit_mask, "det_x")
    hit_y = first_hit_quantity(awk_arr, hit_mask, "det_y")
    hit_z = first_hit_quantity(awk_arr, hit_mask, "det_z")
    return hit_t, hit_x, hit_y, hit_z

def Track_Extrapolation(awk_arr, D1_ID, D2_ID, PID, ztarg):
    """
    Build a two-layer tracklet for a given particle PID and extrapolate to ztarg.

    Returns
    -------
    t_rec : event-level array
        Reconstructed track time.
    x_ext, y_ext : event-level arrays
        Extrapolated coordinates at z = ztarg.
    has_track : event-level bool array
        True if both layers have at least one selected hit.
    """

    D1_hit_mask, D2_hit_mask, has_hit_D1, has_hit_D2, has_track = (
        Mask_Particle_Track_2Layers_Hits(awk_arr, D1_ID, D2_ID, PID)
    )
    D1t, D1x, D1y, D1z = first_Hits_Coordinates(awk_arr, D1_hit_mask)
    D2t, D2x, D2y, D2z = first_Hits_Coordinates(awk_arr, D2_hit_mask)
    t_rec = 0.5 * (D1t + D2t)
    x_ext, y_ext = extrapolate_to_z(D1x, D1y, D1z, D2x, D2y, D2z, ztarg)
    return t_rec, x_ext, y_ext, has_track

def extrapolate_to_z(x1, y1, z1, x2, y2, z2, z_sample=0.0):
    dz = z2 - z1
    alpha = (z_sample - z1) / dz
    x = x1 + alpha * (x2 - x1)
    y = y1 + alpha * (y2 - y1)
    return x, y

def dist_xy(xa, ya, xb, yb):
    return np.sqrt((xa - xb)**2 + (ya - yb)**2)


def muSR_spectrum_Ideal(awk_arr):
    mask_truth_target = ((awk_arr["muDecayDetID"] == TARGET_ID)
        & np.isfinite(ak.to_numpy(awk_arr["muTargetTime"]))
        & np.isfinite(ak.to_numpy(awk_arr["muDecayTime"])))
    #--------------------------------
    dt_truth = awk_arr["muDecayTime"] - awk_arr["muTargetTime"]
    #--------------------------------
    mask_truth_time     = (dt_truth > 0) & (dt_truth < TGATE)
    mask_truth          = mask_truth_target & mask_truth_time
    mask_pos_up_truth   = awk_arr["posIniMomZ"] < 0
    mask_pos_down_truth = awk_arr["posIniMomZ"] > 0
    #--------------------------------
    dt_truth_up   = ak.to_numpy(dt_truth[mask_truth & mask_pos_up_truth])
    dt_truth_down = ak.to_numpy(dt_truth[mask_truth & mask_pos_down_truth])
    return dt_truth_up, dt_truth_down
    

def muSR_spectrum(awk_arr, d_match, Detector_IDs, PIDs, TargetID, Gate_open_time, Z_target_extrap):
    D1, D2, D3, D4 = Detector_IDs
    PID_MU, PID_E  = PIDs
    mask_mu_stops_target = awk_arr["muDecayDetID"] == TargetID
    #--------------------------------
    t_mu_rec, x_mu_ext, y_mu_ext, mu_has_track = Track_Extrapolation(awk_arr, D1, D2, PID_MU, Z_target_extrap)
    t_pos_up_rec, x_pos_up_ext, y_pos_up_ext, pos_up_has_track = Track_Extrapolation(awk_arr, D1, D2, PID_E, Z_target_extrap)
    t_pos_down_rec, x_pos_down_ext, y_pos_down_ext, pos_down_has_track = Track_Extrapolation(awk_arr, D3, D4, PID_E, Z_target_extrap)
    #--------------------------------
    dt_up_rec = t_pos_up_rec - t_mu_rec
    dt_down_rec = t_pos_down_rec - t_mu_rec
    #--------------------------------
    dmatch_up = dist_xy(x_mu_ext, y_mu_ext, x_pos_up_ext, y_pos_up_ext)
    dmatch_down = dist_xy(x_mu_ext, y_mu_ext,x_pos_down_ext, y_pos_down_ext)
    #--------------------------------
    mask_rec_up = (mu_has_track & pos_up_has_track & mask_mu_stops_target
        & (dmatch_up <= d_match) & (dt_up_rec > 0) & (dt_up_rec < Gate_open_time))
    mask_rec_down = (mu_has_track & pos_down_has_track & mask_mu_stops_target
        & (dmatch_down <= d_match) & (dt_down_rec > 0) & (dt_down_rec < Gate_open_time))
    #--------------------------------
    dt_up_selected = ak.to_numpy(dt_up_rec[mask_rec_up])
    dt_down_selected = ak.to_numpy(dt_down_rec[mask_rec_down])
    #--------------------------------
    return dt_up_selected, dt_down_selected, mask_rec_up, mask_rec_down


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



def fit_plot_spectrum(dt_up, dt_down, time_thresh, gate_time, fname, Fit_B_sigma, NBINS=200, savefig=False):
    bins = np.linspace(0, gate_time, NBINS+1)
    centers = 0.5 * (bins[:-1] + bins[1:])
    counts_up,   _ = np.histogram(dt_up,   bins=bins)
    counts_down, _ = np.histogram(dt_down, bins=bins)
    #--------------------------------
    yerrors_up   = np.sqrt(np.maximum(counts_up, 1))
    yerrors_down = np.sqrt(np.maximum(counts_down, 1))
    #--------------------------------
    if Fit_B_sigma == 1:
        # N0, A, B, omega, phi, sigma
        Bounds =([1,-1,0,0.1,-np.pi,0],[1e5,1,100,10,np.pi,1])
        ic = centers > time_thresh
        popt_up, pcov_up      = curve_fit(musrSpec, centers[ic],   counts_up[ic], p0=[153.,-0.29, 0.46,5.34,-1.6,0.], bounds=Bounds)
        popt_down, pcov_down  = curve_fit(musrSpec, centers[ic], counts_down[ic], p0=[153.,-0.35, 0.36,5.34, 1.6,0.], bounds=Bounds)
        N0_up,     A_up,   B_up,   omega_up,   phi_up,   sigma_up = popt_up
        N0_down, A_down, B_down, omega_down, phi_down, sigma_down = popt_down
        txt = f'''
        param | Upstream | Downstream |
        ===============================
        N0    | {N0_up:.3f}  | {N0_down:.3f}    |
        A     | {A_up:.3f}   | {A_down:.3f}     |
        B     | {B_up:.3f}    | {B_down:.3f}     |
        omega | {omega_up:.3f}    | {omega_down:.3f}      |
        phi   | {phi_up:.3f}   | {phi_down:.3f}      |
        sigma | {sigma_up:.3f}    | {sigma_down:.3f}      |
        '''
    #----------------------------------------------------------
    elif Fit_B_sigma == 2:
        # N0, A, B, omega, phi (no sigma)
        Bounds =([1,-1,0,0.1,-np.pi],[1e5,1,100,10,np.pi])
        ic = centers > time_thresh
        popt_up, pcov_up      = curve_fit(musrSpec1, centers[ic],   counts_up[ic], p0=[153.,-0.29, 0.46,5.34,-1.6], bounds=Bounds)
        popt_down, pcov_down  = curve_fit(musrSpec1, centers[ic], counts_down[ic], p0=[153.,-0.35, 0.36,5.34, 1.6], bounds=Bounds)
        N0_up,     A_up,   B_up,   omega_up,   phi_up = popt_up
        N0_down, A_down, B_down, omega_down, phi_down = popt_down
        txt = f'''
        param | Upstream | Downstream |
        ===============================
        N0    | {N0_up:.3f}  | {N0_down:.3f}    |
        A     | {A_up:.3f}   | {A_down:.3f}     |
        B     | {B_up:.3f}    | {B_down:.3f}     |
        omega | {omega_up:.3f}    | {omega_down:.3f}      |
        phi   | {phi_up:.3f}   | {phi_down:.3f}      |
        '''
    #----------------------------------------------------------
    else:
        # N0, A, omega, phi (no B and no sigma)
        Bounds=([1,-1,0.1,-np.pi],[1e5,1,10,np.pi])
        ic = centers > time_thresh
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
    # print fit parameters
    print(txt)
    #----------------------------------------------------------
    tt = np.linspace(0, gate_time, 300)
    fig, ax = plotting_header(size="single")
    ax.errorbar(centers,counts_up/N0_up,yerr=yerrors_up/N0_up, lw=0.8, c='k', fmt="o", ms=1.5, label='Upstream')
    ax.errorbar(centers,counts_down/N0_down,yerr=yerrors_down/N0_down, lw=0.8, c='r', fmt="^", ms=1.5, label='Downstream')
    if Fit_B_sigma == 1:
        ax.plot(tt, musrSpec(tt, N0_up,     A_up,   B_up,   omega_up,   phi_up,   sigma_up)/N0_up,  '-c', lw=1, label='Upstream fit')
        ax.plot(tt, musrSpec(tt, N0_down, A_down, B_down, omega_down, phi_down, sigma_down)/N0_down,'-b', lw=1, label='Downstream fit')
    elif Fit_B_sigma == 2:
        ax.plot(tt, musrSpec1(tt,   N0_up,   A_up,   B_up,   omega_up,   phi_up)/N0_up,  '-c', lw=1, label='Upstream fit')
        ax.plot(tt, musrSpec1(tt, N0_down, A_down, B_down, omega_down, phi_down)/N0_down,'-b', lw=1, label='Downstream fit')
    else:
        ax.plot(tt, musrSpec2(tt,   N0_up,   A_up,   omega_up,   phi_up)/N0_up,  '-c', lw=1, label='Upstream fit')
        ax.plot(tt, musrSpec2(tt, N0_down, A_down, omega_down, phi_down)/N0_down,'-b', lw=1, label='Downstream fit')
    ax.set_xlabel(r"$t \; {\rm [\mu\,s]}$")
    ax.set_ylabel(r"$N(t)/N_0$")
    ax.set_xlim(0,8)
    ax.set_ylim(bottom=0)
    ax.legend(loc=0)
    plt.show()
    if savefig:
        fig.savefig('../plots/SIMULATION_2/'+fname)


def Plot_Asymmetry(dt_up, dt_down, gate_time, fname, NBINS=200, savefig=False):
    bins = np.linspace(0, gate_time, NBINS+1)
    centers = 0.5 * (bins[:-1] + bins[1:])
    counts_up,   _ = np.histogram(dt_up,   bins=bins)
    counts_down, _ = np.histogram(dt_down, bins=bins)
    alpha = counts_up.sum()/counts_down.sum()    
    #------------------------------------------------
    num = counts_up - alpha * counts_down
    den = counts_up + alpha * counts_down
    A = np.full_like(den, np.nan, dtype=float)
    mask_nonzero = den > 0
    A[mask_nonzero] = num[mask_nonzero]/den[mask_nonzero]
    fig, ax = plotting_header(size="single")
    ax.plot(centers, A, '-ok', ms=3,label=r'$\alpha=%.3f$'%alpha)
    ax.set_xlabel(r"$t \; {\rm [\mu\,s]}$")
    ax.set_ylabel(r"$A(t)=\frac{N_{\rm up}-\alpha N_{\rm down}}{N_{\rm up}+\alpha N_{\rm down}}$")
    ax.set_xlim(0, 8)
    ax.set_ylim(-1,1)
    ax.legend(loc=0)
    plt.show()
    if savefig:
        fig.savefig('../plots/SIMULATION_2/'+fname)


def Muon_Decay_Stop_Target(arr, savefig=False):
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
    ax.set_ylim(1,7e3)
    #ax.set_yscale('log')
    ax.legend(loc=0)
    #plt.show()
    if savefig:
        fig.savefig('../plots/SIMULATION_2/Z_target_decay_B6_3mT.pdf')
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
    ax.text(-9,8,r'$\mu^+$ Decay in Target')
    ax.set_xlabel(r"X-Axis $\mathrm{[mm]}$")
    ax.set_ylabel(r"Y-Axis $\mathrm{[mm]}$")
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax_top.set_ylim(bottom=0)
    ax_right.set_xlim(left=0)
    fig.align_labels()
    #plt.show()
    if savefig:
        fig.savefig(f'../plots/SIMULATION_2/2d_XY_target_decay_B6_3mT.pdf')

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

with uproot.open("../data/musr_TargetD6mm_d20mm_B6_3mT_N1e5.root")["t1"] as tree:
    arr = tree.arrays(branches, library="ak")



Detector_IDs = [DET_L1, DET_L2, DET_L3, DET_L4]
PIDs = [PID_MUP, PID_POS]


savefig = 1
Fit_B_sigma = 3
Tthresh = 0.1
statistics = 1
NBINS = 80

fname_ideal = 'vx_muSR_spectrum_ideal.pdf'
dt_up_ideal, dt_down_ideal = muSR_spectrum_Ideal(arr)
fit_plot_spectrum(dt_up_ideal, dt_down_ideal, Tthresh, TGATE, fname_ideal, Fit_B_sigma, NBINS, savefig)
    

fname_sel='vx_muSR_spectrum_simulation.pdf'
dt_up_sel, dt_down_sel, mask_rec_up, mask_rec_down = muSR_spectrum(arr, DMATCH, Detector_IDs, PIDs, TARGET_ID, TGATE, Z_TARGET)
fit_plot_spectrum(dt_up_sel, dt_down_sel, Tthresh, TGATE, fname_sel, Fit_B_sigma, NBINS, savefig)

#=================================
#=================================

    
fname='Asymmetry_param_ideal.pdf'
Plot_Asymmetry(dt_up_ideal, dt_down_ideal, TGATE, fname, NBINS, savefig)

fname='Asymmetry_param.pdf'
Plot_Asymmetry(dt_up_sel, dt_down_sel, TGATE,fname, NBINS, savefig) 

#=================================
#=================================

Muon_Decay_Stop_Target(arr, savefig)

#=================================
#=================================
if statistics:
    Ntot = len(arr["eventID"])
    mask_mu_stops_target = arr["muDecayDetID"] == TARGET_ID
    muL1_hit, muL2_hit, has_mu_hit_L1, has_mu_hit_L2, has_mu_track = Mask_Particle_Track_2Layers_Hits(arr,DET_L1,DET_L2,PID_MUP)
    posL1_up_hit,  posL2_up_hit,   has_pos_hit_L1, has_pos_hit_L2, has_pos_up_track   = Mask_Particle_Track_2Layers_Hits(arr,DET_L1,DET_L2,PID_POS)
    posL3_down_hit,posL4_down_hit, has_pos_hit_L3, has_pos_hit_L4, has_pos_down_track = Mask_Particle_Track_2Layers_Hits(arr,DET_L3,DET_L4,PID_POS)

    Nmu_L1L2_track  = ak.sum(has_mu_track)
    Nmu_stop_target = ak.sum(mask_mu_stops_target)
    Npos_Up_L1L2    = ak.sum(has_pos_up_track)
    Npos_Down_L3L4  = ak.sum(has_pos_down_track)
    N_vx_up         = ak.sum(mask_rec_up)
    N_vx_down       = ak.sum(mask_rec_down)

    print("===================================================")
    print(f"Total events: {Ntot}")
    print(f"Muon L1-L2 tracks: {Nmu_L1L2_track}")
    print(f"Muon stops target: {Nmu_stop_target}")
    print(f"Upstream positron tracks: {Npos_Up_L1L2}:")
    print(f"Downstream positron tracks: {Npos_Down_L3L4}")
    print(f"Accepted upstream vx events: {N_vx_up}")
    print(f"Accepted downstream vx events: {N_vx_down}")
    print("===================================================")
    print(f'Upstream muon track reconstruction: {100*Nmu_L1L2_track/Ntot:.2f}%')
    print(f'Muon stop in target: {100*Nmu_stop_target/Ntot:.2f}%')
    print(f'Muon stop from reconstructed tracks: {100*Nmu_stop_target/Nmu_L1L2_track:.2f}%')
    print(f'Upstream positron track from strop muons: {100*Npos_Up_L1L2/Nmu_stop_target:.2f}%')
    print(f'Downstream positron track from strop muons: {100*Npos_Down_L3L4/Nmu_stop_target:.2f}%')
    print(f'Accepted upstream vx-events (N_vx/N_up): {100*N_vx_up/Npos_Up_L1L2:.2f}%')
    print(f'Accepted downstream vx-events: {100*N_vx_down/Npos_Down_L3L4:.2f}%')
    print("===================================================")


