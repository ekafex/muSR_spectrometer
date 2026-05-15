# -*- coding: utf-8 -*-
"""
Created on Mon May  4 19:10:31 2026

@author: drago

{"nFieldNomVal", "BFieldAtDecay.Bx", "BFieldAtDecay.By", "BFieldAtDecay.Bz",
 "fieldNomVal",  "BFieldAtDecay.B3", "BFieldAtDecay.B4", "BFieldAtDecay.B5",
 
 "det_ID", "det_VrtxProcID", "det_VrtxParticleID", "det_VrtxTrackID", "det_VrtxVolID",
 "det_VrtxKine", "det_VrtxX", "det_VrtxY", "det_VrtxZ", 
 
 "det_VvvParticleID", "det_VvvProcID", "det_VvvTrackID", "det_VvvVolID", 
 "det_VvvKine", "det_VvvX", "det_VvvY", "det_VvvZ", 
 
 "det_edep", "det_edep_el", "det_edep_gam", "det_edep_mup", "det_edep_pos", 
 
 "det_kine", "det_length", "det_n", "det_nsteps", 
 "det_time_end", "det_time_start", "det_x", "det_y", "det_z", 
 
 "runID", "eventID", 
 
 "muDecayDetID", "muDecayPolX", "muDecayPolY", "muDecayPolZ", 
 "muDecayPosX", "muDecayPosY", "muDecayPosZ", "muDecayTime", 
 
 "muIniMomX", "muIniMomY", "muIniMomZ", "muIniPolX", "muIniPolY", "muIniPolZ", 
 "muIniPosX", "muIniPosY", "muIniPosZ", "muIniTime", 
 
 "muTargetMomX", "muTargetMomY", "muTargetMomZ", 
 "muTargetPolX", "muTargetPolY", "muTargetPolZ", "muTargetTime",  
 
 "posIniMomX", "posIniMomY", "posIniMomZ", 
 
 "timeToNextEvent", "weight" }
"""

import ROOT
ROOT.EnableImplicitMT()


#"musr_d20mm_B6_3mT_N1e5.root"

fname = ["musr_d5mm_B0_0mT_N1e5.root",
         "musr_d10mm_B0_0mT_N1e5.root",
         "musr_d15mm_B0_0mT_N1e5.root",
         "musr_d20mm_B0_0mT_N1e5.root",
         "musr_d25mm_B0_0mT_N1e5.root",
         "musr_d30mm_B0_0mT_N1e5.root",
         "musr_d35mm_B0_0mT_N1e5.root",
         "musr_d40mm_B0_0mT_N1e5.root"]

ifname = 0

df = ROOT.RDataFrame("t1", "data/"+fname[ifname])
print(df.GetColumnNames())

#============================================================
h1 = df.Histo1D(("h_Z", "Muon Decay Z-Axis;Z_{#mu} [mm];Events", 200, -0.5, 0.5),"muDecayPosZ")
c1 = ROOT.TCanvas("c_Z_mu", "Z_mu", 900, 700)
h1.SetLineWidth(2)
h1.SetLineColor(ROOT.kBlack)
h1.Draw("HIST")
c1.SaveAs("mu_Decay_Z.pdf")

h2 = df.Histo2D(("h_mu_decay_xy", "Muon decay X-Y plane;x [mm];y [mm]",
     100, -20, 20, 100, -20, 20),"muDecayPosX","muDecayPosY")
c2 = ROOT.TCanvas("c_XY_mu", "XY_mu", 900, 900)
h2.Draw("COLZ")
c2.SaveAs("Muon_XY.pdf")

h3 = df.Histo1D(("h_ID", "Muon Decay Layer ID; ID;Events", 200, 100, 105), "muDecayDetID")
c3 = ROOT.TCanvas("c_ID_mu", "ID_mu", 900, 700)
h3.SetLineWidth(2)
h3.SetLineColor(ROOT.kBlack)
h3.Draw("HIST")
c3.SaveAs("Vol_mu_Decay_ID.pdf")


###############
# Target Only
###############

df2 = (df.Define("muStopR", "std::sqrt(muDecayPosX*muDecayPosX + muDecayPosY*muDecayPosY)")
         .Define("muStopAbsZ", "std::abs(muDecayPosZ)"))
df_stop_target = df2.Filter("muStopAbsZ <= 0.5 && muStopR <= 10.0","Muon stopped inside target: |z| <= 0.5 mm and r <= 10 mm")

N_events = df.Count().GetValue()
N_target = df_stop_target.Count().GetValue()
print(f"Efficiency of muons stopin in the target = {100*N_target/N_events}%")


h1T = df_stop_target.Histo1D(("h_Z", "Muon Stop Target Depth;Z [mm];Events", 200, -0.5, 0.5),"muDecayPosZ")
c1T = ROOT.TCanvas("c_Z_mu", "Z_mu", 900, 700)
h1T.SetLineWidth(2)
h1T.SetLineColor(ROOT.kBlack)
h1T.Draw("HIST")
c1T.SaveAs("mu_Stop_Target_Z.pdf")


h2T = df_stop_target.Histo2D(("h_mu_decay_xy", "Muon Stop Target X-Y Plane;x [mm];y [mm]",
      100, -11, 11, 100, -11, 11),"muDecayPosX","muDecayPosY")
c2T = ROOT.TCanvas("c_XY_mu", "XY_mu", 900, 900)
h2T.Draw("COLZ")
c2T.SaveAs("Muon_Target_XY.pdf")


# #####################
# # Outside Target
# #####################

df_stop_out_target = df2.Filter("muStopAbsZ >= 0.5","Muon stopped outside target: |z| > 0.5 mm")

h1NT = df_stop_out_target.Histo1D(("h_Z", "Muon Stop Outside Target;Z [mm];Events", 200, -50, 35),"muDecayPosZ")
c1NT = ROOT.TCanvas("c_out_Z_mu", "out_Z_mu", 900, 700)
h1NT.SetLineWidth(2)
h1NT.SetLineColor(ROOT.kBlack)
h1NT.Draw("HIST")
c1NT.SaveAs("mu_Stop_Outside_Target_Z.pdf")

h2NT = df_stop_out_target.Histo2D(("h_mu_decay_xy", "Muon Stop Outside Target X-Y Plane;x [mm];y [mm]",
      100, -21, 21, 100, -21, 21),"muDecayPosX","muDecayPosY")
c2NT = ROOT.TCanvas("c_XYout_mu", "XYout_mu", 900, 900)
h2NT.Draw("COLZ")
c2NT.SaveAs("Muon_Outside_Target_XY.pdf")


##############

#########################
# Energy Loss mu and e+
#########################

L_ID = {'L1':101, 'L2':102, 'L3':103, 'L4':104}
L_ID   = [101, 102, 103, 104]
L_Name = ['L1', 'L2', 'L3', 'L4']

i_ID = 0
DET_ID = L_ID[i_ID]
DET_Name = L_Name[i_ID]
thr = 1e-9

df_edep_hits = (
    df.Define("mask_mup_det", f"(det_ID == {DET_ID}) && (det_edep_mup > {thr})")
      .Define("mask_pos_det", f"(det_ID == {DET_ID}) && (det_edep_pos > {thr})")
      .Define("edep_mup_nonzero", "det_edep_mup[mask_mup_det]")
      .Define("edep_pos_nonzero", "det_edep_pos[mask_pos_det]")
)

#df_edep_hits = (
#      df.Define("edep_mup_nonzero", f"det_edep_mup[det_edep_mup > {thr}]")
#      .Define("edep_pos_nonzero", f"det_edep_pos[det_edep_pos > {thr}]")
#)


h_mup = df_edep_hits.Histo1D(
    ("h_edep_mup", "Energy deposition per hit in %s;E_{dep} [MeV];Counts"%(DET_Name),
     100, 1e-6, 0.8),"edep_mup_nonzero")
h_pos = df_edep_hits.Histo1D(("h_edep_pos",";E_{dep} [MeV];Counts",
     100, 1e-6, 0.8),"edep_pos_nonzero")
h_mup = h_mup.GetValue()
h_pos = h_pos.GetValue()
h_mup.SetLineColor(ROOT.kRed)
h_mup.SetLineWidth(2)
h_pos.SetLineColor(ROOT.kBlack)
h_pos.SetLineWidth(2)
c4 = ROOT.TCanvas("c_edep", "Nonzero energy deposition", 900, 700)
max_y = max(h_mup.GetMaximum(), h_pos.GetMaximum())
h_mup.SetMaximum(1.1*max_y)
h_mup.Draw("HIST")
h_pos.Draw("HIST SAME")
leg = ROOT.TLegend(0.65, 0.75, 0.88, 0.88)
leg.AddEntry(h_mup, "#mu^{+}", "l")
leg.AddEntry(h_pos, "e^{+}", "l")
leg.Draw()
c4.Draw()

c4.SaveAs(f"{DET_Name}_Hit_Energy_Deposit.pdf")



############



#fname = ["musr_d5mm_B0_0mT_N1e5.root",
#         "musr_d10mm_B0_0mT_N1e5.root",
#         "musr_d15mm_B0_0mT_N1e5.root",
#         "musr_d20mm_B0_0mT_N1e5.root",
#         "musr_d25mm_B0_0mT_N1e5.root",
#         "musr_d30mm_B0_0mT_N1e5.root",
#         "musr_d35mm_B0_0mT_N1e5.root",
#         "musr_d40mm_B0_0mT_N1e5.root"]


d = [5.,10.,15.,20.,25.,30.,35.,40.]

i = 0

Detect = {'ID':{'L1':101, 'L2':102, 'L3':103, 'L4':104},       # Detector Layers IDs
          'Distances':{'L1-L2':20., 'L2-L3':d[i], 'L3-L4':20.} # distances between layers
         }

Targ= {'diameter':20.,'thickness':1.0,'z':0.}                 # Target/Sample diameter and thickness (modeled as cylinder)    


df = ROOT.RDataFrame("t1", f"data/musr_d{int(d[i])}mm_B0_0mT_N1e5.root")



df_mu, df_pos, df_vx = build_delta_dataframes(dframe, Detect, Targ, use_target_stop=True, target_det_id=None)

n_mu = df_mu.Count().GetValue()
sigma_delta_mu = df_mu.StdDev("delta_mu").GetValue()
mean_delta_mu = df_mu.Mean("delta_mu").GetValue()

print("d =", d)
print("N mu =", n_mu)
print("mean(delta_mu) =", mean_delta_mu)
print("std(delta_mu) =", sigma_delta_mu)

h_delta_mu = df_mu.Histo1D(("h_delta_mu", ";#delta_{#mu} [mm];Events", 120, 0.0, 5.0), "delta_mu")
h_delta_e = df_e.Histo1D(("h_delta_e", ";#delta_{e} [mm];Events", 120, 0.0, 5.0), "delta_e")

n_mu = df_mu.Count()
n_e = df_e.Count()

# Trigger event loop
n_mu_val = n_mu.GetValue()
n_e_val = n_e.GetValue()

print("Results")
print("-------")
print(f"N(delta_mu)    = {n_mu_val}")
print(f"mean(delta_mu) = {h_delta_mu.GetMean():.5f} mm")
print(f"std(delta_mu)  = {h_delta_mu.GetStdDev():.5f} mm")
print()
print(f"N(delta_e)     = {n_e_val}")
print(f"mean(delta_e)  = {h_delta_e.GetMean():.5f} mm")
print(f"std(delta_e)   = {h_delta_e.GetStdDev():.5f} mm")


c7 = ROOT.TCanvas("c_delta_mu", "delta_mu", 900, 700)
h_delta_mu.SetLineWidth(2)
h_delta_mu.SetLineColor(ROOT.kBlack)
h_delta_mu.Draw("HIST")
c7.SaveAs(f"delta_mu_d={int(d[i])}mm.pdf")

c8 = ROOT.TCanvas("c_delta_e", "delta_e", 900, 700)
h_delta_e.SetLineWidth(2)
h_delta_e.SetLineColor(ROOT.kRed)
h_delta_e.Draw("HIST")
c8.SaveAs(f"delta_e_d={int(d[i])}mm.pdf")








