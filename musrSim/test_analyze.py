# -*- coding: utf-8 -*-
"""
Created on Mon May  4 19:10:31 2026

@author: drago

{"BFieldAtDecay.B3", "BFieldAtDecay.B4", "BFieldAtDecay.B5",
 "BFieldAtDecay.Bx", "BFieldAtDecay.By", "BFieldAtDecay.Bz", 
 "det_ID", "det_VrtxKine", "det_VrtxParticleID", "det_VrtxProcID", 
 "det_VrtxTrackID", "det_VrtxVolID", "det_VrtxX", "det_VrtxY", 
 "det_VrtxZ", "det_VvvKine", "det_VvvParticleID", "det_VvvProcID", 
 "det_VvvTrackID", "det_VvvVolID", "det_VvvX", "det_VvvY", "det_VvvZ", 
 "det_edep", "det_edep_el", "det_edep_gam", "det_edep_mup", 
 "det_edep_pos", "det_kine", "det_length", "det_n", "det_nsteps", 
 "det_time_end", "det_time_start", "det_x", "det_y", "det_z", 
 "eventID", "fieldNomVal", "muDecayDetID", "muDecayPolX", 
 "muDecayPolY", "muDecayPolZ", "muDecayPosX", "muDecayPosY", 
 "muDecayPosZ", "muDecayTime", "muIniMomX", "muIniMomY", "muIniMomZ", 
 "muIniPolX", "muIniPolY", "muIniPolZ", "muIniPosX", "muIniPosY", 
 "muIniPosZ", "muIniTime", "muTargetMomX", "muTargetMomY", 
 "muTargetMomZ", "muTargetPolX", "muTargetPolY", "muTargetPolZ", 
 "muTargetTime", "nFieldNomVal", "posIniMomX", "posIniMomY", 
 "posIniMomZ", "runID", "timeToNextEvent", "weight" }
"""

import ROOT
ROOT.EnableImplicitMT()
df = ROOT.RDataFrame("t1", "data/musr_0.root")
# print(df.GetColumnNames())

## ============================================================
#h1 = df.Histo1D(("h_Z", "Muon Decay Z;Z_{#mu} [mm];Events", 200, -0.4, -0.2),"muDecayPosZ")
#c1 = ROOT.TCanvas("c_Z_mu", "Z_mu", 900, 700)
#h1.SetLineWidth(2)
#h1.Draw("HIST")
#c1.SaveAs("mu_Decay_Z.pdf")

#h2 = df.Histo2D(("h_mu_decay_xy", "Muon decay positions;x [mm];y [mm]",
#     100, -20, 20, 100, -20, 20),"muDecayPosX","muDecayPosY")
#c2 = ROOT.TCanvas("c_XY_mu", "XY_mu", 900, 900)
#h2.Draw("COLZ")
#c2.SaveAs("Muon_XY.pdf")

#h3 = df.Histo1D(("h_ID", "Muon Decay Vol. ID; ID;Events", 200, 90, 110), "muDecayDetID")
#c3 = ROOT.TCanvas("c_ID_mu", "ID_mu", 900, 700)
#h3.SetLineWidth(2)
#h3.Draw("HIST")
#c3.SaveAs("Vol_mu_Decay_ID.pdf")


################
## Target Only
################

#df2 = (df.Define("muStopR", "std::sqrt(muDecayPosX*muDecayPosX + muDecayPosY*muDecayPosY)")
#      .Define("muStopAbsZ", "std::abs(muDecayPosZ)"))
#df_stop_target = df2.Filter("muStopAbsZ <= 0.5 && muStopR <= 10.0","Muon stopped inside target: |z| <= 0.5 mm and r <= 10 mm")

#N_events = df.Count().GetValue()
#N_target = df_stop_target.Count().GetValue()
#print(f"Efficiency of muons stopin in the target = {100*N_target/N_events}%")


#h1T = df_stop_target.Histo1D(("h_Z", "Muon Stop Target;Z [mm];Events", 200, -0.5, 0.5),"muDecayPosZ")
#c1T = ROOT.TCanvas("c_Z_mu", "Z_mu", 900, 700)
#h1T.SetLineWidth(2)
#h1T.Draw("HIST")
#c1T.SaveAs("mu_Stop_Target_Z.pdf")


#h2T = df_stop_target.Histo2D(("h_mu_decay_xy", "Muon Stop Target Position;x [mm];y [mm]",
#     100, -11, 11, 100, -11, 11),"muDecayPosX","muDecayPosY")
#c2T = ROOT.TCanvas("c_XY_mu", "XY_mu", 900, 900)
#h2T.Draw("COLZ")
#c2T.SaveAs("Muon_Target_XY.pdf")


######################
## Outside Target
######################

#df_stop_out_target = df2.Filter("muStopAbsZ >= 0.5","Muon stopped outside target: |z| > 0.5 mm")

#h1NT = df_stop_out_target.Histo1D(("h_Z", "Muon Stop Outside Target;Z [mm];Events", 200, -50, 35),"muDecayPosZ")
#c1NT = ROOT.TCanvas("c_out_Z_mu", "out_Z_mu", 900, 700)
#h1NT.SetLineWidth(2)
#h1NT.Draw("HIST")
#c1NT.SaveAs("mu_Stop_Outside_Target_Z.pdf")

#h2NT = df_stop_out_target.Histo2D(("h_mu_decay_xy", "Muon Stop Outside Target Position;x [mm];y [mm]",
#     100, -21, 21, 100, -21, 21),"muDecayPosX","muDecayPosY")
#c2NT = ROOT.TCanvas("c_XYout_mu", "XYout_mu", 900, 900)
#h2NT.Draw("COLZ")
#c2NT.SaveAs("Muon_Outside_Target_XY.pdf")

##############


##########################
## Energy Loss mu and e+
##########################


df_edep_hits = (
    df.Define("edep_mup_nonzero", "det_edep_mup[det_edep_mup > 1e-9]")
      .Define("edep_pos_nonzero", "det_edep_pos[det_edep_pos > 1e-9]")
)
h_mup = df_edep_hits.Histo1D(
    ("h_edep_mup","#mu^{+} energy deposition per detector hit;E_{dep} [MeV];Counts",
     100, 1e-6, 0.8),"edep_mup_nonzero")
h_pos = df_edep_hits.Histo1D(("h_edep_pos","e^{+} energy deposition per detector hit;E_{dep} [MeV];Counts",
     100, 1e-6, 0.8),"edep_pos_nonzero")
h_mup = h_mup.GetValue()
h_pos = h_pos.GetValue()
h_mup.SetLineColor(ROOT.kRed)
h_mup.SetLineWidth(2)
h_pos.SetLineColor(ROOT.kBlack)
h_pos.SetLineWidth(2)
c4 = ROOT.TCanvas("c_edep", "Nonzero energy deposition", 900, 700)
max_y = max(h_mup.GetMaximum(), h_pos.GetMaximum())
h_mup.SetMaximum(1.15 * max_y)
h_mup.Draw("HIST")
h_pos.Draw("HIST SAME")
leg = ROOT.TLegend(0.65, 0.75, 0.88, 0.88)
leg.AddEntry(h_mup, "#mu^{+}", "l")
leg.AddEntry(h_pos, "e^{+}", "l")
leg.Draw()
c4.Draw()

c4.SaveAs("Hit_DEnergy_Deposit.pdf")

#############
## ============================================================
## Detector geometry
## ============================================================
#L1_ID = 101
#L2_ID = 102
#L3_ID = 103
#L4_ID = 104

#Z_L1 = -30.0
#Z_L2 = -10.0
#Z_L3 = +10.0
#Z_L4 = +30.0
#Z_SAMPLE = 0.0

## PDG codes used by Geant4
#PID_MUP = -13
#PID_EP = -11

## ============================================================
## C++ helper functions used inside RDataFrame
## ============================================================

#ROOT.gInterpreter.Declare(f"""
##include <ROOT/RVec.hxx>
##include <cmath>

#using ROOT::VecOps::RVec;

#constexpr int L1_ID = {L1_ID};
#constexpr int L2_ID = {L2_ID};
#constexpr int L3_ID = {L3_ID};
#constexpr int L4_ID = {L4_ID};

#constexpr double Z_L1 = {Z_L1};
#constexpr double Z_L2 = {Z_L2};
#constexpr double Z_L3 = {Z_L3};
#constexpr double Z_L4 = {Z_L4};
#constexpr double Z_SAMPLE = {Z_SAMPLE};

#constexpr int PID_MUP = {PID_MUP};
#constexpr int PID_EP  = {PID_EP};

#int find_hit(const RVec<int>& detID,
#             const RVec<int>& pid,
#             int wanted_detID,
#             int wanted_pid)
#{{
#    for (size_t i = 0; i < detID.size(); ++i) {{
#        if (detID[i] == wanted_detID && pid[i] == wanted_pid) {{
#            return static_cast<int>(i);
#        }}
#    }}
#    return -1;
#}}

#bool has_muon_L1L2(const RVec<int>& detID,
#                   const RVec<int>& pid)
#{{
#    return find_hit(detID, pid, L1_ID, PID_MUP) >= 0 &&
#           find_hit(detID, pid, L2_ID, PID_MUP) >= 0;
#}}

#bool has_positron_L3L4(const RVec<int>& detID,
#                       const RVec<int>& pid)
#{{
#    return find_hit(detID, pid, L3_ID, PID_EP) >= 0 &&
#           find_hit(detID, pid, L4_ID, PID_EP) >= 0;
#}}

#double extrapolate(double q1, double z1,
#                   double q2, double z2,
#                   double z0)
#{{
#    return q1 + (z0 - z1) * (q2 - q1) / (z2 - z1);
#}}

#double mu_x_ext(const RVec<int>& detID,
#                const RVec<int>& pid,
#                const RVec<double>& x)
#{{
#    int i1 = find_hit(detID, pid, L1_ID, PID_MUP);
#    int i2 = find_hit(detID, pid, L2_ID, PID_MUP);
#    return extrapolate(x[i1], Z_L1, x[i2], Z_L2, Z_SAMPLE);
#}}

#double mu_y_ext(const RVec<int>& detID,
#                const RVec<int>& pid,
#                const RVec<double>& y)
#{{
#    int i1 = find_hit(detID, pid, L1_ID, PID_MUP);
#    int i2 = find_hit(detID, pid, L2_ID, PID_MUP);
#    return extrapolate(y[i1], Z_L1, y[i2], Z_L2, Z_SAMPLE);
#}}

#double e_x_ext(const RVec<int>& detID,
#               const RVec<int>& pid,
#               const RVec<double>& x)
#{{
#    int i3 = find_hit(detID, pid, L3_ID, PID_EP);
#    int i4 = find_hit(detID, pid, L4_ID, PID_EP);
#    return extrapolate(x[i3], Z_L3, x[i4], Z_L4, Z_SAMPLE);
#}}

#double e_y_ext(const RVec<int>& detID,
#               const RVec<int>& pid,
#               const RVec<double>& y)
#{{
#    int i3 = find_hit(detID, pid, L3_ID, PID_EP);
#    int i4 = find_hit(detID, pid, L4_ID, PID_EP);
#    return extrapolate(y[i3], Z_L3, y[i4], Z_L4, Z_SAMPLE);
#}}

#double dist2d(double x1, double y1,
#              double x2, double y2)
#{{
#    const double dx = x1 - x2;
#    const double dy = y1 - y2;
#    return std::sqrt(dx*dx + dy*dy);
#}}
#""")


## ============================================================
## Main
## ============================================================

## df = df.Filter(
##             f"muDecayDetID == muDecayDetID",
##             "muon decays in selected target volume"
##         )


#df_mu = (
#    df.Filter("has_muon_L1L2(det_ID, det_VrtxParticleID)",
#        "event has incoming mu+ hits in L1 and L2")
#    .Define("mu_x_at_sample","mu_x_ext(det_ID, det_VrtxParticleID, det_x)")
#    .Define("mu_y_at_sample","mu_y_ext(det_ID, det_VrtxParticleID, det_y)")
#    .Define("delta_mu","dist2d(mu_x_at_sample, mu_y_at_sample, muDecayPosX, muDecayPosY)")
#    )

#df_e = (
#    df.Filter("has_positron_L3L4(det_ID, det_VrtxParticleID)",
#        "event has outgoing e+ hits in L3 and L4")
#    .Define("e_x_at_sample","e_x_ext(det_ID, det_VrtxParticleID, det_x)")
#    .Define("e_y_at_sample","e_y_ext(det_ID, det_VrtxParticleID, det_y)")
#    .Define("delta_e","dist2d(e_x_at_sample, e_y_at_sample, muDecayPosX, muDecayPosY)")
#    )



#h_delta_mu = df_mu.Histo1D(("h_delta_mu", ";#delta_{#mu} [mm];Events", 120, 0.0, 5.0),"delta_mu")

#h_delta_e = df_e.Histo1D(("h_delta_e", ";#delta_{e} [mm];Events", 120, 0.0, 5.0),"delta_e")


#n_mu = df_mu.Count()
#n_e = df_e.Count()

## Trigger event loop
#n_mu_val = n_mu.GetValue()
#n_e_val = n_e.GetValue()

#print("Results")
#print("-------")
#print(f"N(delta_mu)      = {n_mu_val}")
#print(f"mean(delta_mu)   = {h_delta_mu.GetMean():.5f} mm")
#print(f"std(delta_mu)    = {h_delta_mu.GetStdDev():.5f} mm")
#print()
#print(f"N(delta_e)       = {n_e_val}")
#print(f"mean(delta_e)    = {h_delta_e.GetMean():.5f} mm")
#print(f"std(delta_e)     = {h_delta_e.GetStdDev():.5f} mm")


#c1 = ROOT.TCanvas("c_delta_mu", "delta_mu", 900, 700)
#h_delta_mu.SetLineWidth(2)
#h_delta_mu.Draw("HIST")
#c1.SaveAs("delta_mu.pdf")

#c2 = ROOT.TCanvas("c_delta_e", "delta_e", 900, 700)
#h_delta_e.SetLineWidth(2)
#h_delta_e.Draw("HIST")
#c2.SaveAs("delta_e.pdf")








