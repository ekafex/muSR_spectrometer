# -*- coding: utf-8 -*-
"""
Created on Sun May  3 14:54:38 2026

Si-pixel vx-muSR simulation analysis from musrSim run.

Main outputs:
  1. delta_mu distribution:
       delta_mu = | r_stop - r_ext |
     where r_ext is extrapolated from L1-L2 to z = 0.

  2. Layer-1 deposited-energy comparison:
       mu+ vs e+ energy deposition in L1.

  3. Reconstructed sample vertex map:
       incoming muon track L1-L2 extrapolated to z = 0.

"""


import argparse
import ROOT

ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)


# ============================================================
# Detector geometry
# ============================================================

L1_ID = 101
L2_ID = 102
L3_ID = 103
L4_ID = 104

Z_L1 = -30.0
Z_L2 = -10.0
Z_L3 = +10.0
Z_L4 = +30.0
Z_SAMPLE = 0.0

# PDG codes used by Geant4
PID_MUP = -13
PID_EP = -11


# ============================================================
# C++ helper functions used inside RDataFrame
# ============================================================

ROOT.gInterpreter.Declare(f"""
#include <ROOT/RVec.hxx>
#include <cmath>

using ROOT::VecOps::RVec;

constexpr int L1_ID = {L1_ID};
constexpr int L2_ID = {L2_ID};
constexpr int L3_ID = {L3_ID};
constexpr int L4_ID = {L4_ID};

constexpr double Z_L1 = {Z_L1};
constexpr double Z_L2 = {Z_L2};
constexpr double Z_L3 = {Z_L3};
constexpr double Z_L4 = {Z_L4};
constexpr double Z_SAMPLE = {Z_SAMPLE};

constexpr int PID_MUP = {PID_MUP};
constexpr int PID_EP  = {PID_EP};

int find_hit(const RVec<int>& detID,
             const RVec<int>& pid,
             int wanted_detID,
             int wanted_pid)
{{
    for (size_t i = 0; i < detID.size(); ++i) {{
        if (detID[i] == wanted_detID && pid[i] == wanted_pid) {{
            return static_cast<int>(i);
        }}
    }}
    return -1;
}}

bool has_muon_L1L2(const RVec<int>& detID,
                   const RVec<int>& pid)
{{
    return find_hit(detID, pid, L1_ID, PID_MUP) >= 0 &&
           find_hit(detID, pid, L2_ID, PID_MUP) >= 0;
}}

bool has_positron_L3L4(const RVec<int>& detID,
                       const RVec<int>& pid)
{{
    return find_hit(detID, pid, L3_ID, PID_EP) >= 0 &&
           find_hit(detID, pid, L4_ID, PID_EP) >= 0;
}}

double extrapolate(double q1, double z1,
                   double q2, double z2,
                   double z0)
{{
    return q1 + (z0 - z1) * (q2 - q1) / (z2 - z1);
}}

double mu_x_ext(const RVec<int>& detID,
                const RVec<int>& pid,
                const RVec<double>& x)
{{
    int i1 = find_hit(detID, pid, L1_ID, PID_MUP);
    int i2 = find_hit(detID, pid, L2_ID, PID_MUP);
    return extrapolate(x[i1], Z_L1, x[i2], Z_L2, Z_SAMPLE);
}}

double mu_y_ext(const RVec<int>& detID,
                const RVec<int>& pid,
                const RVec<double>& y)
{{
    int i1 = find_hit(detID, pid, L1_ID, PID_MUP);
    int i2 = find_hit(detID, pid, L2_ID, PID_MUP);
    return extrapolate(y[i1], Z_L1, y[i2], Z_L2, Z_SAMPLE);
}}

double e_x_ext(const RVec<int>& detID,
               const RVec<int>& pid,
               const RVec<double>& x)
{{
    int i3 = find_hit(detID, pid, L3_ID, PID_EP);
    int i4 = find_hit(detID, pid, L4_ID, PID_EP);
    return extrapolate(x[i3], Z_L3, x[i4], Z_L4, Z_SAMPLE);
}}

double e_y_ext(const RVec<int>& detID,
               const RVec<int>& pid,
               const RVec<double>& y)
{{
    int i3 = find_hit(detID, pid, L3_ID, PID_EP);
    int i4 = find_hit(detID, pid, L4_ID, PID_EP);
    return extrapolate(y[i3], Z_L3, y[i4], Z_L4, Z_SAMPLE);
}}

double dist2d(double x1, double y1,
              double x2, double y2)
{{
    const double dx = x1 - x2;
    const double dy = y1 - y2;
    return std::sqrt(dx*dx + dy*dy);
}}
""")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rootfile")
    parser.add_argument("--tree", default="t1")
    parser.add_argument("--out", default="delta_results.root")
    parser.add_argument("--target-detid", type=int, default=None)
    args = parser.parse_args()

    df = ROOT.RDataFrame(args.tree, args.rootfile)

    # Optional: require muon decay in a given detector/target volume.
    # Use this only if you know that muDecayDetID corresponds to your Target.
    if args.target_detid is not None:
        df = df.Filter(
            f"muDecayDetID == {args.target_detid}",
            "muon decays in selected target volume"
        )

    df_mu = (
        df
        .Filter(
            "has_muon_L1L2(det_ID, det_VrtxParticleID)",
            "event has incoming mu+ hits in L1 and L2"
        )
        .Define(
            "mu_x_at_sample",
            "mu_x_ext(det_ID, det_VrtxParticleID, det_x)"
        )
        .Define(
            "mu_y_at_sample",
            "mu_y_ext(det_ID, det_VrtxParticleID, det_y)"
        )
        .Define(
            "delta_mu",
            "dist2d(mu_x_at_sample, mu_y_at_sample, muDecayPosX, muDecayPosY)"
        )
    )

    df_e = (
        df
        .Filter(
            "has_positron_L3L4(det_ID, det_VrtxParticleID)",
            "event has outgoing e+ hits in L3 and L4"
        )
        .Define(
            "e_x_at_sample",
            "e_x_ext(det_ID, det_VrtxParticleID, det_x)"
        )
        .Define(
            "e_y_at_sample",
            "e_y_ext(det_ID, det_VrtxParticleID, det_y)"
        )
        .Define(
            "delta_e",
            "dist2d(e_x_at_sample, e_y_at_sample, muDecayPosX, muDecayPosY)"
        )
    )

    h_delta_mu = df_mu.Histo1D(
        ("h_delta_mu", ";#delta_{#mu} [mm];Events", 120, 0.0, 5.0),
        "delta_mu"
    )

    h_delta_e = df_e.Histo1D(
        ("h_delta_e", ";#delta_{e} [mm];Events", 120, 0.0, 5.0),
        "delta_e"
    )

    n_mu = df_mu.Count()
    n_e = df_e.Count()

    # Trigger event loop
    n_mu_val = n_mu.GetValue()
    n_e_val = n_e.GetValue()

    print()
    print("Results")
    print("-------")
    print(f"N(delta_mu)      = {n_mu_val}")
    print(f"mean(delta_mu)   = {h_delta_mu.GetMean():.5f} mm")
    print(f"std(delta_mu)    = {h_delta_mu.GetStdDev():.5f} mm")
    print()
    print(f"N(delta_e)       = {n_e_val}")
    print(f"mean(delta_e)    = {h_delta_e.GetMean():.5f} mm")
    print(f"std(delta_e)     = {h_delta_e.GetStdDev():.5f} mm")

    # fout = ROOT.TFile(args.out, "RECREATE")
    # h_delta_mu.Write()
    # h_delta_e.Write()
    # fout.Close()

    c1 = ROOT.TCanvas("c_delta_mu", "delta_mu", 900, 700)
    h_delta_mu.SetLineWidth(2)
    h_delta_mu.Draw("HIST")
    c1.SaveAs("delta_mu.pdf")

    c2 = ROOT.TCanvas("c_delta_e", "delta_e", 900, 700)
    h_delta_e.SetLineWidth(2)
    h_delta_e.Draw("HIST")
    c2.SaveAs("delta_e.pdf")


if __name__ == "__main__":
    main()