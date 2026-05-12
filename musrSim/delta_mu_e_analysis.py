# -*- coding: utf-8 -*-
"""
Created on Sun May 10 11:05:59 2026

@author: EK
"""

#import ROOT
#ROOT.EnableImplicitMT()

##====================================================
## Declare helper functions only once
#if not hasattr(ROOT, "_VX_MUSR_HELPERS_DECLARED"):
#    ROOT.gInterpreter.Declare(r"""
#    #include <ROOT/RVec.hxx>
#    #include <cmath>
#    #include <limits>

#    using ROOT::VecOps::RVec;

#    int count_hits_pid_det(const RVec<int>& detID, const RVec<int>& pid, 
#                           int wanted_detID, int wanted_pid)
#    {
#        int n = 0;
#        for (size_t i = 0; i < detID.size(); ++i) {
#            if (detID[i] == wanted_detID && pid[i] == wanted_pid) {
#                ++n;
#            }
#        }
#        return n;
#    }

#    int find_unique_hit_pid_det(const RVec<int>& detID, const RVec<int>& pid, 
#                                int wanted_detID, int wanted_pid)
#    {
#        int found = -1;
#        int n = 0;
#        for (size_t i = 0; i < detID.size(); ++i) {
#            if (detID[i] == wanted_detID && pid[i] == wanted_pid) {
#                found = static_cast<int>(i);
#                ++n;
#            }
#        }

#        if (n == 1) return found;
#        return -1;
#    }

#    bool has_unique_hit_pid_det(const RVec<int>& detID, const RVec<int>& pid, 
#                                int wanted_detID, int wanted_pid)
#    {
#        return count_hits_pid_det(detID, pid, wanted_detID, wanted_pid) == 1;
#    }

#    bool has_unique_tracklet(const RVec<int>& detID,const RVec<int>& pid,
#                             int det1, int det2, int wanted_pid)
#    {
#        return has_unique_hit_pid_det(detID, pid, det1, wanted_pid)
#            && has_unique_hit_pid_det(detID, pid, det2, wanted_pid);
#    }

#    double extrapolate_linear(double q1, double z1, double q2, double z2, double z0)
#    {
#        return q1 + (z0 - z1) * (q2 - q1) / (z2 - z1);
#    }

#    double extrapolate_coord_to_z0(const RVec<int>& detID, const RVec<int>& pid, const RVec<double>& q,
#                                   int det1, int det2, int wanted_pid,
#                                   double z1, double z2, double z0)
#    {
#        int i1 = find_unique_hit_pid_det(detID, pid, det1, wanted_pid);
#        int i2 = find_unique_hit_pid_det(detID, pid, det2, wanted_pid);

#        if (i1 < 0 || i2 < 0) {
#            return std::numeric_limits<double>::quiet_NaN();
#        }

#        return extrapolate_linear(q[i1], z1, q[i2], z2, z0);
#    }

#    double dist2d(double x1, double y1, double x2, double y2)
#    {
#        const double dx = x1 - x2;
#        const double dy = y1 - y2;
#        return std::sqrt(dx*dx + dy*dy);
#    }

#    bool point_inside_cylinder_xy_z(double x, double y, double z, double radius,
#                                    double half_thickness)
#    {
#        return (x*x + y*y <= radius*radius) && (std::abs(z) <= half_thickness);
#    }
#    """)
#    ROOT._VX_MUSR_HELPERS_DECLARED = True


##====================================================
##====================================================


#def build_delta(dframe, Detect, Targ, use_target_stop=True, target_det_id=None, dmatch=1.0):
#    """
#    Build RDataFrames for:

#    1. delta_mu = distance between true muon decay/stop position and
#                  L1-L2 extrapolated muon position at z = 0.

#    2. delta_e = distance between true muon decay/stop position and
#                 L3-L4 extrapolated positron position at z = 0.

#    3. Full vx-muSR matched events:
#       incoming muon L1-L2 tracklet + target stop + outgoing positron L3-L4
#       tracklet + spatial matching at z = 0.

#    Parameters
#    ----------
#    dframe : RDataFrame from ROOT file. 
#    Detect : Detector parameters (layers IDs & distances)
#    Targ   : Target/Sample parameters (dimensions & z position)

#    sample_radius : float
#        Sample radius in mm. For a 20 mm diameter target, use 10 mm.

#    sample_half_thickness : float
#        Half-thickness of the sample around z = 0 in mm.
#        Use your actual target half-thickness.

#    target_det_id : int or None
#        If muDecayDetID reliably identifies the target detector/volume,
#        pass that ID. Otherwise leave None and use geometric selection.

#    dmatch : float
#        Matching distance between extrapolated muon and positron positions
#        at z = 0, in mm.
#    """
#    
#    L1_ID = Detect['ID']['L1']
#    L2_ID = Detect['ID']['L2']
#    L3_ID = Detect['ID']['L3']
#    L4_ID = Detect['ID']['L4']
#    PID_MUP = -13 #mu+ pid
#    PID_EP  = -11 #e+  pid
#    
#    # z-position of each detector layer
#    Z_L1 = -Detect['Distances']['L1-L2'] -Detect['Distances']['L2-L3']/2.0
#    Z_L2 = -Detect['Distances']['L2-L3']/2.0
#    Z_L3 = +Detect['Distances']['L2-L3']/2.0
#    Z_L4 = +Detect['Distances']['L3-L4'] +Detect['Distances']['L2-L3']/2.0
#    
#    Z_SAMPLE = Targ['z'] # target z position
#    sample_radius = Targ['diameter']/2.0 # sample radius
#    sample_half_thickness = Targ['thickness']/2.0 # sample half-thickness (z-direction)
#    
#    # ------------------------------------------------------------
#    # Target-stop condition
#    # ------------------------------------------------------------
#    if not use_target_stop:
#        target_stop_cut = "true"
#    elif target_det_id is not None:
#        target_stop_cut = f"muDecayDetID == {int(target_det_id)}"
#    else:
#        # Geometric target-stop selection using muon decay position.
#        # For stopped muons, muDecayPosX/Y/Z is the physical decay/stop position.
#        target_stop_cut = (
#            f"point_inside_cylinder_xy_z("
#            f"muDecayPosX, muDecayPosY, muDecayPosZ, "
#            f"{sample_radius}, {sample_half_thickness})"
#        )

#    # ------------------------------------------------------------
#    # Clean incoming muon tracklet: exactly one mu+ hit in L1 and L2
#    # ------------------------------------------------------------
#    mu_tracklet_cut = (
#        f"has_unique_tracklet(det_ID, det_VrtxParticleID, "
#        f"{L1_ID}, {L2_ID}, {PID_MUP})"
#    )

#    # ------------------------------------------------------------
#    # Clean outgoing positron tracklet: exactly one e+ hit in L3 and L4
#    # ------------------------------------------------------------
#    pos_tracklet_cut = (
#        f"has_unique_tracklet(det_ID, det_VrtxParticleID, "
#        f"{L3_ID}, {L4_ID}, {PID_EP})"
#    )

#    # ------------------------------------------------------------
#    # Muon extrapolation resolution dataframe
#    # ------------------------------------------------------------
#    df_mu = (
#        dframe
#        .Filter(target_stop_cut, "muon decay/stop position inside target")
#        .Filter(mu_tracklet_cut, "unique incoming mu+ L1-L2 tracklet")
#        .Define(
#            "mu_x_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_x, "
#            f"{L1_ID}, {L2_ID}, {PID_MUP}, {Z_L1}, {Z_L2}, {Z_SAMPLE})"
#        )
#        .Define(
#            "mu_y_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_y, "
#            f"{L1_ID}, {L2_ID}, {PID_MUP}, {Z_L1}, {Z_L2}, {Z_SAMPLE})"
#        )
#        .Define("dx_mu", "mu_x_at_sample - muDecayPosX")
#        .Define("dy_mu", "mu_y_at_sample - muDecayPosY")
#        .Define("delta_mu", "dist2d(mu_x_at_sample, mu_y_at_sample, muDecayPosX, muDecayPosY)")
#    )

#    # ------------------------------------------------------------
#    # Positron extrapolation resolution dataframe
#    # ------------------------------------------------------------
#    df_pos = (
#        dframe
#        .Filter(target_stop_cut, "muon decay/stop position inside target")
#        .Filter(pos_tracklet_cut, "unique outgoing e+ L3-L4 tracklet")
#        .Define(
#            "pos_x_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_x, "
#            f"{L3_ID}, {L4_ID}, {PID_EP}, {Z_L3}, {Z_L4}, {Z_SAMPLE})"
#        )
#        .Define(
#            "pos_y_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_y, "
#            f"{L3_ID}, {L4_ID}, {PID_EP}, {Z_L3}, {Z_L4}, {Z_SAMPLE})"
#        )
#        .Define("dx_pos", "pos_x_at_sample - muDecayPosX")
#        .Define("dy_pos", "pos_y_at_sample - muDecayPosY")
#        .Define("delta_pos", "dist2d(pos_x_at_sample, pos_y_at_sample, muDecayPosX, muDecayPosY)")
#    )

#    # ------------------------------------------------------------
#    # Full matched vx-muSR event dataframe
#    # ------------------------------------------------------------
#    df_vx = (
#        dframe
#        .Filter(target_stop_cut, "muon decay/stop position inside target")
#        .Filter(mu_tracklet_cut, "unique incoming mu+ L1-L2 tracklet")
#        .Filter(pos_tracklet_cut, "unique outgoing e+ L3-L4 tracklet")
#        .Define(
#            "mu_x_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_x, "
#            f"{L1_ID}, {L2_ID}, {PID_MUP}, {Z_L1}, {Z_L2}, {Z_SAMPLE})"
#        )
#        .Define(
#            "mu_y_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_y, "
#            f"{L1_ID}, {L2_ID}, {PID_MUP}, {Z_L1}, {Z_L2}, {Z_SAMPLE})"
#        )
#        .Define(
#            "pos_x_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_x, "
#            f"{L3_ID}, {L4_ID}, {PID_EP}, {Z_L3}, {Z_L4}, {Z_SAMPLE})"
#        )
#        .Define(
#            "pos_y_at_sample",
#            f"extrapolate_coord_to_z0(det_ID, det_VrtxParticleID, det_y, "
#            f"{L3_ID}, {L4_ID}, {PID_EP}, {Z_L3}, {Z_L4}, {Z_SAMPLE})"
#        )
#        .Define(
#            "track_match_distance",
#            "dist2d(mu_x_at_sample, mu_y_at_sample, pos_x_at_sample, pos_y_at_sample)"
#        )
#        .Filter(f"track_match_distance <= {dmatch}", "muon-positron vertex match at sample")
#        .Define("delta_mu", "dist2d(mu_x_at_sample, mu_y_at_sample, muDecayPosX, muDecayPosY)")
#        .Define("delta_pos", "dist2d(pos_x_at_sample, pos_y_at_sample, muDecayPosX, muDecayPosY)")
#        .Define("decay_time", "muDecayTime - muIniTime")
#    )

#    return df_mu, df_pos, df_vx



##=======================================================================
##=======================================================================
##=======================================================================
##=======================================================================

#def Plot_delta(d):
#    c7 = ROOT.TCanvas("c_delta_mu_pos", "delta_mu", 900, 700)
#    for i in range(len(d)):
#        print(f'{d[i]}')
#        Targ= {'diameter':20.,'thickness':1.0,'z':0.} # Target/Sample diameter and thickness (of cylinder)    
#        Detect = {
#            'ID':{'L1':101, 'L2':102, 'L3':103, 'L4':104},       # Detector Layers IDs
#            'Distances':{'L1-L2':20., 'L2-L3':d[i], 'L3-L4':20.} # distances between layers
#            }
#        df = ROOT.RDataFrame("t1", f"data/musr_d{int(d[i])}mm_B0_0mT_N1e5.root")
#        df_mu, df_e, df_vx = build_delta(df, Detect, Targ,use_target_stop=True, target_det_id=None, dmatch=1.0)
#        h_delta_mu    = df_mu.Histo1D(("h_delta_mu", ";#delta_{#mu} [mm];Events", 120, 0.0, 5.0), "delta_mu")
#        h_delta_e     = df_e.Histo1D(("h_delta_e", ";#delta_{e} [mm];Events", 120, 0.0, 5.0), "delta_pos")
#        h_delta_vx_mu = df_vx.Histo1D(("h_delta_vx_mu", ";#delta_{#mu} [mm];Events", 120, 0.0, 5.0), "delta_mu")
#        h_delta_vx_e  = df_vx.Histo1D(("h_delta_vx_e", ";#delta_{e} [mm];Events", 120, 0.0, 5.0), "delta_pos")
#        h_delta_mu.SetLineWidth(2)
#        h_delta_e.SetLineWidth(2)
#        h_delta_vx_mu.SetLineWidth(2)
#        h_delta_vx_e.SetLineWidth(2)
#        h_delta_mu.SetLineColor(ROOT.kRed)
#        h_delta_e.SetLineColor(ROOT.kBlack)
#        h_delta_vx_mu.SetLineColor(ROOT.kMagenta)
#        h_delta_vx_e.SetLineColor(ROOT.kGray)
#        h_delta_mu.Draw("HIST")
#        h_delta_e.Draw("HIST SAME")
#        h_delta_vx_mu.Draw("HIST SAME")
#        h_delta_vx_e.Draw("HIST SAME")
#        c7.SaveAs(f"delta_d={int(d[i])}mm.png")


#def file_delta_save(d):
#    with open('data/delta_mu_e.dat','w') as f:
#        f.write('# d, delta_mu_mean, delta_mu_std, delta_e_mean, delta_e_std, delta_mu_vx_mean, delta_mu_vx_std, delta_e_vx_mean, delta_e_vx_std, N_mu, N_e, N_vx_mu_e, Ntot\n')
#        f.write('# d & deltas are in mm. delta_*_vx is obtained from selecting events with L1&L2 muon and L3&L4 positron hits\n')
#        for i in range(len(d)):
#            print(f'{d[i]}')
#            Targ= {'diameter':20.,'thickness':1.0,'z':0.} # Target/Sample diameter and thickness (of cylinder)    
#            Detect = {
#                'ID':{'L1':101, 'L2':102, 'L3':103, 'L4':104},       # Detector Layers IDs
#                'Distances':{'L1-L2':20., 'L2-L3':d[i], 'L3-L4':20.} # distances between layers
#                }
#            df = ROOT.RDataFrame("t1", f"data/musr_d{int(d[i])}mm_B0_0mT_N1e5.root")
#            df_mu, df_e, df_vx = build_delta(df, Detect, Targ,use_target_stop=True, target_det_id=None, dmatch=1.0)
#            
#            Ntot      = df.Count().GetValue()
#            n_mu      = df_mu.Count().GetValue()
#            n_e       = df_e.Count().GetValue()
#            n_mu_e_vx = df_vx.Count().GetValue()
#            
#            delta_mu_mean    = df_mu.Mean("delta_mu").GetValue()
#            delta_e_mean     = df_e.Mean("delta_pos").GetValue()
#            delta_mu_vx_mean = df_vx.Mean("delta_mu").GetValue()
#            delta_e_vx_mean  = df_vx.Mean("delta_pos").GetValue()
#            
#            delta_mu_std    = df_mu.StdDev("delta_mu").GetValue()
#            delta_e_std     = df_e.StdDev("delta_pos").GetValue()
#            delta_mu_vx_std = df_vx.StdDev("delta_mu").GetValue()
#            delta_e_vx_std  = df_vx.StdDev("delta_pos").GetValue()
#            
#            f.write(f'{d[i]:.3f},{delta_mu_mean:.3f},{delta_mu_std:.3f},{delta_e_mean:.3f},{delta_e_std:.3f},{delta_mu_vx_mean:.3f},{delta_mu_vx_std:.3f},{delta_e_vx_mean:.3f},{delta_e_vx_std:.3f},{n_mu},{n_e},{n_mu_e_vx},{Ntot}\n')
#            del df, df_mu, df_e, df_vx



#===================================================================
#===================================================================
#===================================================================

#d = [5.,10.,15.,20.,25.,30.,35.,40.]

#Plot_delta(d)

#file_delta_save(d)

#===================================================================
#===================================================================
#===================================================================


import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt('data/delta_mu_e.dat',dtype=float, delimiter=',')


d = data[:,0]
delta_mu = data[:,1:3]
delta_e = data[:,3:5]
delta_mu_vx = data[:,5:7]
delta_e_vx  = data[:,7:9]
NN = data[:,9:]
N_events = NN[:,-1]

xd = np.linspace(0,45,100)

plt.figure()
p_mean_mu = np.polyfit(d, delta_mu[:,0], 1)
p_mean_e  = np.polyfit(d, delta_e[:,0], 1)
d_mean_mu_fit = np.poly1d(p_mean_mu)
d_mean_e_fit  = np.poly1d(p_mean_e)

plt.plot(d,delta_mu[:,0],'or',lw=2,label=r'$\mu^+$')
plt.plot(d,delta_e[:,0],'ob',lw=2,label=r'$e^+$')
plt.plot(xd,d_mean_mu_fit(xd),'-k',lw=2,label=r'fit $\mu^+$')
plt.plot(xd,d_mean_e_fit(xd),'-c',lw=2,label=r'fit $e^+$')
plt.xlabel(r'$d\;{\rm [mm]}$')
plt.ylabel(r'$\bar{\delta}_{\mu^+/e^+};{\rm [mm]}$')
plt.legend()


plt.figure()
p_std_mu = np.polyfit(d, delta_mu[:,1], 1)
p_std_e  = np.polyfit(d, delta_e[:,1], 1)
d_std_mu_fit = np.poly1d(p_std_mu)
d_std_e_fit  = np.poly1d(p_std_e)

plt.plot(d,delta_mu[:,1],'or',lw=2,label=r'$\mu^+$')
plt.plot(d,delta_e[:,1],'ob',lw=2,label=r'$e^+$')
plt.plot(xd,d_std_mu_fit(xd),'-k',lw=2,label=r'fit $\mu^+$')
plt.plot(xd,d_std_e_fit(xd),'-c',lw=2,label=r'fit $e^+$')
plt.xlabel(r'$d\;{\rm [mm]}$')
plt.ylabel(r'$\Delta\delta_{\mu^+/e^+};{\rm [mm]}$')
plt.legend()


plt.figure()
p_mean_mu_vx = np.polyfit(d, delta_mu[:,0], 1)
p_mean_e_vx  = np.polyfit(d, delta_e[:,0], 1)
d_mean_mu_vx_fit = np.poly1d(p_mean_mu_vx)
d_mean_e_vx_fit  = np.poly1d(p_mean_e_vx)
plt.plot(d,delta_mu_vx[:,0],'or',lw=2,label=r'vx-SR $\mu^+$')
plt.plot(d,delta_e_vx[:,0],'ob',lw=2,label=r'vx-SR $e^+$')
plt.plot(xd,d_mean_mu_vx_fit(xd),'-k',lw=2,label=r'fit vx-SR $\mu^+$')
plt.plot(xd,d_mean_e_vx_fit(xd),'-c',lw=2,label=r'fit vx-SR $e^+$')
plt.xlabel(r'$d\;{\rm [mm]}$')
plt.ylabel(r'$\bar{\delta}_{\mu^+/e^+}\;{\rm [mm]}$')
plt.legend()


plt.figure()
p_std_mu_vx = np.polyfit(d, delta_mu[:,1], 1)
p_std_e_vx  = np.polyfit(d, delta_e[:,1], 1)
d_std_mu_vx_fit = np.poly1d(p_std_mu_vx)
d_std_e_vx_fit  = np.poly1d(p_std_e_vx)
plt.plot(d,delta_mu_vx[:,1],'om',lw=2,label=r'vx-SR $\mu^+$')
plt.plot(d,delta_e_vx[:,1],'og',lw=2,label=r'vx-SR $e^+$')
plt.plot(xd,d_std_mu_vx_fit(xd),'-k',lw=2,label=r'fit vx-SR $\mu^+$')
plt.plot(xd,d_std_e_vx_fit(xd),'-c',lw=2,label=r'fit vx-SR $e^+$')
plt.xlabel(r'$d\;{\rm [mm]}$')
plt.ylabel(r'$\Delta\delta_{\mu^+/e^+};{\rm [mm]}$')
plt.legend()



plt.show()




for i in range(len(NN[:,0])):
    print(f'd={d[i]}, mu+={(100*NN[i,0]/N_events[i]):.1f}%, e+={(100*NN[i,1]/N_events[i]):.1f}%,mu+&e+={(100*NN[i,2]/N_events[i]):.1f}%')






