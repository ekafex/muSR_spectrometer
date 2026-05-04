#!/usr/bin/env python3
"""
analyze_mandok_vxmusr.py

PyROOT analysis for a Mandok2026-style Si-pixel vx-muSR musrSim run.

Main outputs:
  1. delta_mu distribution:
       delta_mu = | r_stop - r_ext |
     where r_ext is extrapolated from L1-L2 to z = 0.

  2. Layer-1 deposited-energy comparison:
       mu+ vs e+ energy deposition in L1.

  3. Reconstructed sample vertex map:
       incoming muon track L1-L2 extrapolated to z = 0.

  4. Optional muon-positron matching:
       incoming muon track matched to downstream/upstream e+ tracklet
       using d_match and a 13 us time gate.

  5. Optional vx-muSR time histogram fit:
       N(t) = N0 exp(-t/tau_mu) [1 + A cos(2*pi*f*t + phi)
              exp(-(sigma*t)^2/2)] + B

Usage:
  python analyze_mandok_vxmusr.py data/musr_001.root --out plots
  python analyze_mandok_vxmusr.py data/musr_001.root --print-branches
  python analyze_mandok_vxmusr.py data/musr_001.root --fit-musR
"""

import argparse
import math
import os
from collections import defaultdict

import ROOT

ROOT.gROOT.SetBatch(True)


# ---------------------------------------------------------------------
# User-adjustable defaults
# ---------------------------------------------------------------------

DEFAULT_LAYER_IDS = {
    "L1": 101,
    "L2": 102,
    "L3": 103,
    "L4": 104,
}

DEFAULT_LAYER_Z = {
    "L1": -30.0,
    "L2": -10.0,
    "L3": +10.0,
    "L4": +30.0,
}

MU_PLUS_PDG = -13
E_PLUS_PDG = -11

TAU_MU_US = 2.19703


# ---------------------------------------------------------------------
# Branch alias handling
# ---------------------------------------------------------------------

BRANCH_ALIASES = {
    # Detector-hit vectors
    "det_id": [
        "det_ID", "detID", "det_id", "DetectorID", "detectorID"
    ],
    "det_x": [
        "det_x", "detX", "det_X", "det_PosX", "detPosX",
        "det_VrtxX", "detVrtxX", "det_global_x"
    ],
    "det_y": [
        "det_y", "detY", "det_Y", "det_PosY", "detPosY",
        "det_VrtxY", "detVrtxY", "det_global_y"
    ],
    "det_z": [
        "det_z", "detZ", "det_Z", "det_PosZ", "detPosZ",
        "det_VrtxZ", "detVrtxZ", "det_global_z"
    ],
    "det_t": [
        "det_time", "det_t", "detTime", "det_time_start",
        "det_Time", "detGlobalTime"
    ],
    "det_edep": [
        "det_edep", "det_Edep", "det_edeposit", "detEdep",
        "det_Edep_MeV", "det_edep_musr"
    ],
    "det_pid": [
        "det_ParticleID", "det_particleID", "det_VrtxParticleID",
        "detVrtxParticleID", "det_pdgid", "det_PDG"
    ],
    "det_track": [
        "det_TrackID", "det_trackID", "det_VrtxTrackID",
        "detVrtxTrackID"
    ],

    # Target / stopping information.
    # These are the most useful for Fig. 4-style delta_mu.
    "target_x": [
        "muTargetX", "muTarget_x", "muTargetPosX",
        "muTarget_PositionX", "muTargetPolXPos"
    ],
    "target_y": [
        "muTargetY", "muTarget_y", "muTargetPosY",
        "muTarget_PositionY", "muTargetPolYPos"
    ],
    "target_z": [
        "muTargetZ", "muTarget_z", "muTargetPosZ",
        "muTarget_PositionZ"
    ],
    "target_t": [
        "muTargetTime", "muTarget_t", "muTargetStopTime"
    ],
}


def normalize_name(name):
    return name.lower().replace("_", "").replace(".", "")


def find_branch(tree, aliases, required=False):
    available = [b.GetName() for b in tree.GetListOfBranches()]
    norm_map = {normalize_name(b): b for b in available}

    for alias in aliases:
        key = normalize_name(alias)
        if key in norm_map:
            return norm_map[key]

    if required:
        raise RuntimeError(
            "Could not find required branch. Tried aliases:\n  "
            + "\n  ".join(aliases)
            + "\nAvailable branches:\n  "
            + "\n  ".join(available)
        )

    return None


def build_branch_map(tree):
    out = {}
    for key, aliases in BRANCH_ALIASES.items():
        out[key] = find_branch(tree, aliases, required=False)

    required = ["det_id", "det_x", "det_y", "det_edep"]
    missing = [k for k in required if out[k] is None]
    if missing:
        raise RuntimeError(
            f"Missing required branches: {missing}\n"
            "Run with --print-branches and adjust BRANCH_ALIASES."
        )

    return out


# ---------------------------------------------------------------------
# ROOT helpers
# ---------------------------------------------------------------------

def find_first_tree(root_file):
    """Find first TTree in a ROOT file."""
    for key in root_file.GetListOfKeys():
        obj = key.ReadObj()
        if obj.InheritsFrom("TTree"):
            return obj

    raise RuntimeError("No TTree found in input ROOT file.")


def as_list(value):
    """
    Convert scalar or ROOT vector-like object to Python list.
    """
    try:
        return list(value)
    except TypeError:
        return [value]


def get_event_array(event, branch_name):
    if branch_name is None:
        return None
    return as_list(getattr(event, branch_name))


# ---------------------------------------------------------------------
# Physics / reconstruction helpers
# ---------------------------------------------------------------------

def extrapolate_to_z(p1, p2, z_target=0.0):
    """
    Linear extrapolation from p1=(x,y,z,t) and p2=(x,y,z,t)
    to z = z_target.
    """
    x1, y1, z1, t1 = p1
    x2, y2, z2, t2 = p2

    if abs(z2 - z1) < 1e-12:
        return None

    a = (z_target - z1) / (z2 - z1)
    x = x1 + a * (x2 - x1)
    y = y1 + a * (y2 - y1)
    t = t1 + a * (t2 - t1)
    return x, y, z_target, t


def distance_xy(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def classify_particle(pid, time_us, mu_time_cut_us=0.05):
    """
    Return 'mu', 'ep', or 'unknown'.

    If PID exists:
      mu+ PDG = -13
      e+  PDG = -11

    If PID is absent, use a crude timing fallback:
      early hits are treated as incoming muon,
      delayed hits as decay positron.
    """
    if pid is not None:
        try:
            ipid = int(pid)
            if ipid == MU_PLUS_PDG:
                return "mu"
            if ipid == E_PLUS_PDG:
                return "ep"
        except Exception:
            pass

    if time_us is not None:
        try:
            if float(time_us) <= mu_time_cut_us:
                return "mu"
            if float(time_us) > mu_time_cut_us:
                return "ep"
        except Exception:
            pass

    return "unknown"


def choose_hit(hits, mode="earliest"):
    """
    Choose one hit from a list of hit dictionaries.
    """
    if not hits:
        return None

    if mode == "earliest":
        return min(hits, key=lambda h: h["t"] if h["t"] is not None else 1e99)

    if mode == "max_edep":
        return max(hits, key=lambda h: h["edep"] if h["edep"] is not None else -1e99)

    return hits[0]


def get_hits_by_layer(event, bm, layer_ids, layer_z, mu_time_cut_us):
    """
    Extract detector hits from one event and group by detector layer.

    Returns:
      hits_by_layer: dict layer_name -> list[hit]
    """
    det_id = get_event_array(event, bm["det_id"])
    det_x = get_event_array(event, bm["det_x"])
    det_y = get_event_array(event, bm["det_y"])

    if bm["det_z"] is not None:
        det_z = get_event_array(event, bm["det_z"])
    else:
        det_z = [None] * len(det_id)

    if bm["det_t"] is not None:
        det_t = get_event_array(event, bm["det_t"])
    else:
        det_t = [0.0] * len(det_id)

    if bm["det_edep"] is not None:
        det_edep = get_event_array(event, bm["det_edep"])
    else:
        det_edep = [None] * len(det_id)

    if bm["det_pid"] is not None:
        det_pid = get_event_array(event, bm["det_pid"])
    else:
        det_pid = [None] * len(det_id)

    if bm["det_track"] is not None:
        det_track = get_event_array(event, bm["det_track"])
    else:
        det_track = [None] * len(det_id)

    id_to_layer = {v: k for k, v in layer_ids.items()}
    hits_by_layer = defaultdict(list)

    n = len(det_id)
    for i in range(n):
        try:
            did = int(det_id[i])
        except Exception:
            continue

        if did not in id_to_layer:
            continue

        layer = id_to_layer[did]
        z_val = det_z[i]
        if z_val is None:
            z_val = layer_z[layer]

        t_val = det_t[i] if det_t[i] is not None else 0.0
        pid_val = det_pid[i] if det_pid[i] is not None else None

        hit = {
            "layer": layer,
            "id": did,
            "x": float(det_x[i]),
            "y": float(det_y[i]),
            "z": float(z_val),
            "t": float(t_val),
            "edep": float(det_edep[i]) if det_edep[i] is not None else None,
            "pid": pid_val,
            "track": det_track[i],
            "ptype": classify_particle(pid_val, t_val, mu_time_cut_us),
        }
        hits_by_layer[layer].append(hit)

    return hits_by_layer


def make_tracklet(hits_by_layer, la, lb, particle_type=None, choose="earliest"):
    """
    Build a two-hit tracklet from layers la and lb.

    particle_type:
      None, 'mu', or 'ep'
    """
    ha = hits_by_layer.get(la, [])
    hb = hits_by_layer.get(lb, [])

    if particle_type is not None:
        ha = [h for h in ha if h["ptype"] == particle_type]
        hb = [h for h in hb if h["ptype"] == particle_type]

    a = choose_hit(ha, choose)
    b = choose_hit(hb, choose)

    if a is None or b is None:
        return None

    p1 = (a["x"], a["y"], a["z"], a["t"])
    p2 = (b["x"], b["y"], b["z"], b["t"])

    return {
        "h1": a,
        "h2": b,
        "p1": p1,
        "p2": p2,
        "t": 0.5 * (a["t"] + b["t"]),
    }


def target_position(event, bm):
    """
    Return true muon stopping position in Target, if available.
    """
    if bm["target_x"] is None or bm["target_y"] is None:
        return None

    x = getattr(event, bm["target_x"])
    y = getattr(event, bm["target_y"])

    if bm["target_z"] is not None:
        z = getattr(event, bm["target_z"])
    else:
        z = 0.0

    try:
        return float(x), float(y), float(z)
    except Exception:
        arrx = as_list(x)
        arry = as_list(y)
        arrz = as_list(z)
        if len(arrx) == 0:
            return None
        return float(arrx[0]), float(arry[0]), float(arrz[0])


# ---------------------------------------------------------------------
# Plotting helpers using ROOT
# ---------------------------------------------------------------------

def save_canvas(canvas, outdir, name):
    os.makedirs(outdir, exist_ok=True)
    canvas.SaveAs(os.path.join(outdir, f"{name}.png"))
    canvas.SaveAs(os.path.join(outdir, f"{name}.pdf"))


def make_hist(name, title, values, nbins, xmin, xmax, xtitle, ytitle="Counts"):
    h = ROOT.TH1D(name, title, nbins, xmin, xmax)
    for v in values:
        if v is not None and math.isfinite(v):
            h.Fill(v)
    h.GetXaxis().SetTitle(xtitle)
    h.GetYaxis().SetTitle(ytitle)
    h.SetLineWidth(2)
    return h


def make_graph_xy(name, title, xs, ys, xtitle, ytitle):
    g = ROOT.TGraph(len(xs))
    g.SetName(name)
    g.SetTitle(title)
    for i, (x, y) in enumerate(zip(xs, ys)):
        g.SetPoint(i, x, y)
    g.GetXaxis().SetTitle(xtitle)
    g.GetYaxis().SetTitle(ytitle)
    g.SetMarkerStyle(20)
    g.SetMarkerSize(0.4)
    return g


def fit_musr_hist(h, tmin=0.0, tmax=8.0):
    """
    Fit Mandok-style single histogram function.

    Parameters:
      [0] N0
      [1] A
      [2] f_MHz
      [3] phi
      [4] sigma_1_per_us
      [5] B
    """
    f = ROOT.TF1(
        "musr_fit",
        "[0]*exp(-x/2.19703)*(1.0 + [1]*cos(2.0*TMath::Pi()*[2]*x + [3])"
        "*exp(-0.5*([4]*x)*([4]*x))) + [5]",
        tmin,
        tmax,
    )

    maxbin = h.GetMaximum()
    f.SetParameters(maxbin, 0.2, 0.85, 0.0, 0.3, 0.0)
    f.SetParNames("N0", "A", "f_MHz", "phi", "sigma", "B")

    f.SetParLimits(1, -1.0, 1.0)
    f.SetParLimits(2, 0.0, 5.0)
    f.SetParLimits(4, 0.0, 10.0)
    f.SetParLimits(5, 0.0, max(10.0, maxbin))

    result = h.Fit(f, "RSQ")
    return f, result


# ---------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------

def analyze(args):
    root_file = ROOT.TFile.Open(args.input)
    if not root_file or root_file.IsZombie():
        raise RuntimeError(f"Could not open ROOT file: {args.input}")

    tree = find_first_tree(root_file)

    if args.print_branches:
        print(f"Tree name: {tree.GetName()}")
        print("Branches:")
        for b in tree.GetListOfBranches():
            print(" ", b.GetName())
        return

    bm = build_branch_map(tree)

    print("Using tree:", tree.GetName())
    print("Using branches:")
    for k, v in bm.items():
        print(f"  {k:12s}: {v}")

    layer_ids = {
        "L1": args.L1,
        "L2": args.L2,
        "L3": args.L3,
        "L4": args.L4,
    }

    layer_z = {
        "L1": args.z1,
        "L2": args.z2,
        "L3": args.z3,
        "L4": args.z4,
    }

    delta_mu = []
    x_ext_mu = []
    y_ext_mu = []
    x_stop = []
    y_stop = []

    edep_mu_L1 = []
    edep_ep_L1 = []

    vx_x_all = []
    vx_y_all = []

    vx_x_matched = []
    vx_y_matched = []

    dt_downstream = []
    dt_upstream = []

    n_events = 0
    n_mu_track = 0
    n_delta = 0
    n_matched_down = 0
    n_matched_up = 0

    for event in tree:
        n_events += 1
        if args.max_events > 0 and n_events > args.max_events:
            break

        hits_by_layer = get_hits_by_layer(
            event,
            bm,
            layer_ids,
            layer_z,
            args.mu_time_cut_us,
        )

        # -------------------------------------------------------------
        # Energy deposition in L1: Fig. 5-type diagnostic
        # -------------------------------------------------------------
        for h in hits_by_layer.get("L1", []):
            if h["edep"] is None:
                continue
            if h["ptype"] == "mu":
                edep_mu_L1.append(h["edep"])
            elif h["ptype"] == "ep":
                edep_ep_L1.append(h["edep"])

        # -------------------------------------------------------------
        # Incoming muon tracklet L1-L2
        # -------------------------------------------------------------
        mu_tr = make_tracklet(
            hits_by_layer,
            "L1",
            "L2",
            particle_type="mu" if args.require_pid_or_time else None,
            choose="earliest",
        )

        if mu_tr is None:
            continue

        n_mu_track += 1

        mu_ext = extrapolate_to_z(mu_tr["p1"], mu_tr["p2"], args.target_z)
        if mu_ext is None:
            continue

        x_ext_mu.append(mu_ext[0])
        y_ext_mu.append(mu_ext[1])
        vx_x_all.append(mu_ext[0])
        vx_y_all.append(mu_ext[1])

        # -------------------------------------------------------------
        # True target stop vs extrapolated target position: Fig. 4
        # -------------------------------------------------------------
        tp = target_position(event, bm)
        if tp is not None:
            dx = tp[0] - mu_ext[0]
            dy = tp[1] - mu_ext[1]
            d = math.hypot(dx, dy)
            delta_mu.append(d)
            x_stop.append(tp[0])
            y_stop.append(tp[1])
            n_delta += 1

        # -------------------------------------------------------------
        # Positron matching: Fig. 6 / Fig. 7-style vx-muSR logic
        # -------------------------------------------------------------
        # Downstream positron: L3-L4
        ep_down = make_tracklet(
            hits_by_layer,
            "L3",
            "L4",
            particle_type="ep" if args.require_pid_or_time else None,
            choose="earliest",
        )

        if ep_down is not None:
            ep_ext = extrapolate_to_z(ep_down["p1"], ep_down["p2"], args.target_z)
            if ep_ext is not None:
                dmatch = distance_xy(mu_ext, ep_ext)
                dt = ep_down["t"] - mu_tr["t"]
                if 0.0 <= dt <= args.gate_us and dmatch <= args.dmatch:
                    dt_downstream.append(dt)
                    vx_x_matched.append(0.5 * (mu_ext[0] + ep_ext[0]))
                    vx_y_matched.append(0.5 * (mu_ext[1] + ep_ext[1]))
                    n_matched_down += 1

        # Upstream positron: L2-L1 after muon decay.
        # This is harder to separate without PID/time because L1-L2 also
        # contain the incoming muon. Works best if det_pid exists.
        ep_up = make_tracklet(
            hits_by_layer,
            "L2",
            "L1",
            particle_type="ep" if args.require_pid_or_time else None,
            choose="earliest",
        )

        if ep_up is not None:
            ep_ext = extrapolate_to_z(ep_up["p1"], ep_up["p2"], args.target_z)
            if ep_ext is not None:
                dmatch = distance_xy(mu_ext, ep_ext)
                dt = ep_up["t"] - mu_tr["t"]
                if 0.0 <= dt <= args.gate_us and dmatch <= args.dmatch:
                    dt_upstream.append(dt)
                    vx_x_matched.append(0.5 * (mu_ext[0] + ep_ext[0]))
                    vx_y_matched.append(0.5 * (mu_ext[1] + ep_ext[1]))
                    n_matched_up += 1

    os.makedirs(args.out, exist_ok=True)

    print("\nSummary")
    print("-------")
    print(f"Events scanned:              {n_events}")
    print(f"Muon L1-L2 tracklets:        {n_mu_track}")
    print(f"delta_mu entries:            {n_delta}")
    print(f"L1 mu+ edep entries:         {len(edep_mu_L1)}")
    print(f"L1 e+ edep entries:          {len(edep_ep_L1)}")
    print(f"Matched downstream e+ tracks:{n_matched_down}")
    print(f"Matched upstream e+ tracks:  {n_matched_up}")

    if delta_mu:
        mean = sum(delta_mu) / len(delta_mu)
        rms = math.sqrt(sum((x - mean) ** 2 for x in delta_mu) / len(delta_mu))
        print(f"\ndelta_mu mean:  {mean:.4f} mm")
        print(f"delta_mu std:   {rms:.4f} mm")
        print("Paper comparison: for d = 20 mm, expected order is below ~0.7 mm.")

    # -----------------------------------------------------------------
    # Plot 1: delta_mu
    # -----------------------------------------------------------------
    if delta_mu:
        c = ROOT.TCanvas("c_delta_mu", "delta_mu", 900, 700)
        h = make_hist(
            "h_delta_mu",
            ";#delta_{#mu} = |r_{stop} - r_{ext}| [mm];Counts",
            delta_mu,
            args.delta_bins,
            0.0,
            args.delta_max,
            "#delta_{#mu} [mm]",
        )
        h.Draw("HIST")
        save_canvas(c, args.out, "fig_delta_mu_distribution")

    # -----------------------------------------------------------------
    # Plot 2: true vs extrapolated target x-y
    # -----------------------------------------------------------------
    if x_stop and x_ext_mu:
        c = ROOT.TCanvas("c_true_ext", "true_vs_extrapolated", 900, 700)
        g_ext = make_graph_xy(
            "g_ext",
            ";x [mm];y [mm]",
            x_ext_mu,
            y_ext_mu,
            "x [mm]",
            "y [mm]",
        )
        g_true = make_graph_xy(
            "g_true",
            ";x [mm];y [mm]",
            x_stop,
            y_stop,
            "x [mm]",
            "y [mm]",
        )

        g_ext.SetMarkerColor(ROOT.kBlue + 1)
        g_true.SetMarkerColor(ROOT.kRed + 1)

        mg = ROOT.TMultiGraph()
        mg.Add(g_ext, "P")
        mg.Add(g_true, "P")
        mg.SetTitle(";x [mm];y [mm]")
        mg.Draw("A")

        leg = ROOT.TLegend(0.65, 0.75, 0.88, 0.88)
        leg.AddEntry(g_true, "true stop", "p")
        leg.AddEntry(g_ext, "L1-L2 extrapolated", "p")
        leg.Draw()

        save_canvas(c, args.out, "fig_true_vs_extrapolated_xy")

    # -----------------------------------------------------------------
    # Plot 3: deposited energy in L1, mu+ vs e+
    # -----------------------------------------------------------------
    if edep_mu_L1 or edep_ep_L1:
        c = ROOT.TCanvas("c_edep", "Layer-1 deposited energy", 900, 700)

        h_mu = make_hist(
            "h_edep_mu_L1",
            ";Deposited energy in L1 [MeV];Counts",
            edep_mu_L1,
            args.edep_bins,
            0.0,
            args.edep_max,
            "Deposited energy in L1 [MeV]",
        )
        h_ep = make_hist(
            "h_edep_ep_L1",
            ";Deposited energy in L1 [MeV];Counts",
            edep_ep_L1,
            args.edep_bins,
            0.0,
            args.edep_max,
            "Deposited energy in L1 [MeV]",
        )

        h_mu.SetLineColor(ROOT.kRed + 1)
        h_ep.SetLineColor(ROOT.kBlue + 1)

        maxy = max(h_mu.GetMaximum(), h_ep.GetMaximum())
        h_mu.SetMaximum(1.2 * maxy if maxy > 0 else 1.0)

        h_mu.Draw("HIST")
        h_ep.Draw("HIST SAME")

        leg = ROOT.TLegend(0.65, 0.75, 0.88, 0.88)
        leg.AddEntry(h_mu, "#mu^{+}", "l")
        leg.AddEntry(h_ep, "e^{+}", "l")
        leg.Draw()

        save_canvas(c, args.out, "fig_edep_layer1_mu_vs_ep")

    # -----------------------------------------------------------------
    # Plot 4: extrapolated incoming muon vertex map
    # -----------------------------------------------------------------
    if vx_x_all:
        c = ROOT.TCanvas("c_vx_all", "Extrapolated muon vertices", 900, 750)
        h2 = ROOT.TH2D(
            "h2_vx_mu",
            ";x_{ext}(z=0) [mm];y_{ext}(z=0) [mm]",
            args.xy_bins,
            -args.xy_range,
            args.xy_range,
            args.xy_bins,
            -args.xy_range,
            args.xy_range,
        )
        for x, y in zip(vx_x_all, vx_y_all):
            h2.Fill(x, y)

        h2.GetZaxis().SetTitle("Counts")
        h2.Draw("COLZ")
        save_canvas(c, args.out, "fig_muon_extrapolated_vertex_map")

    # -----------------------------------------------------------------
    # Plot 5: matched muon-positron vertex map
    # -----------------------------------------------------------------
    if vx_x_matched:
        c = ROOT.TCanvas("c_vx_matched", "Matched vertices", 900, 750)
        h2 = ROOT.TH2D(
            "h2_vx_matched",
            f";x_{{vtx}} [mm];y_{{vtx}} [mm]  d_{{match}} <= {args.dmatch} mm",
            args.xy_bins,
            -args.xy_range,
            args.xy_range,
            args.xy_bins,
            -args.xy_range,
            args.xy_range,
        )
        for x, y in zip(vx_x_matched, vx_y_matched):
            h2.Fill(x, y)

        h2.GetZaxis().SetTitle("Counts")
        h2.Draw("COLZ")
        save_canvas(c, args.out, "fig_matched_vertex_map")

    # -----------------------------------------------------------------
    # Plot 6: vx-muSR time histogram
    # -----------------------------------------------------------------
    all_dt = dt_downstream + dt_upstream
    if all_dt:
        c = ROOT.TCanvas("c_dt", "vx-muSR time spectrum", 900, 700)
        hdt = make_hist(
            "h_dt",
            ";t_{e^{+}} - t_{#mu^{+}} [#mus];Counts",
            all_dt,
            args.time_bins,
            0.0,
            args.gate_us,
            "t_{e^{+}} - t_{#mu^{+}} [#mus]",
        )

        hdt.SetMarkerStyle(20)
        hdt.SetMarkerSize(0.7)
        hdt.Draw("E")

        if args.fit_musR:
            f, fit_result = fit_musr_hist(hdt, args.fit_tmin, args.fit_tmax)
            f.Draw("SAME")

            print("\nmuSR fit parameters")
            print("-------------------")
            print(f"N0      = {f.GetParameter(0):.6g} +/- {f.GetParError(0):.3g}")
            print(f"A       = {f.GetParameter(1):.6g} +/- {f.GetParError(1):.3g}")
            print(f"f_MHz   = {f.GetParameter(2):.6g} +/- {f.GetParError(2):.3g}")
            print(f"phi     = {f.GetParameter(3):.6g} +/- {f.GetParError(3):.3g}")
            print(f"sigma   = {f.GetParameter(4):.6g} +/- {f.GetParError(4):.3g} 1/us")
            print(f"B       = {f.GetParameter(5):.6g} +/- {f.GetParError(5):.3g}")
            print(f"chi2/ndf= {f.GetChisquare():.3g}/{f.GetNDF()}")

        save_canvas(c, args.out, "fig_vx_musr_time_histogram")

    print(f"\nSaved plots to: {args.out}")


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Analyze Mandok2026-style Si-pixel vx-muSR musrSim ROOT output."
    )

    p.add_argument("input", help="Input musrSim ROOT file")
    p.add_argument("--out", default="plots_mandok", help="Output directory")
    p.add_argument("--print-branches", action="store_true", help="Print TTree branches and exit")
    p.add_argument("--max-events", type=int, default=-1, help="Maximum events to scan")

    # Detector IDs
    p.add_argument("--L1", type=int, default=DEFAULT_LAYER_IDS["L1"])
    p.add_argument("--L2", type=int, default=DEFAULT_LAYER_IDS["L2"])
    p.add_argument("--L3", type=int, default=DEFAULT_LAYER_IDS["L3"])
    p.add_argument("--L4", type=int, default=DEFAULT_LAYER_IDS["L4"])

    # Layer z positions
    p.add_argument("--z1", type=float, default=DEFAULT_LAYER_Z["L1"])
    p.add_argument("--z2", type=float, default=DEFAULT_LAYER_Z["L2"])
    p.add_argument("--z3", type=float, default=DEFAULT_LAYER_Z["L3"])
    p.add_argument("--z4", type=float, default=DEFAULT_LAYER_Z["L4"])
    p.add_argument("--target-z", type=float, default=0.0)

    # Matching / timing
    p.add_argument("--dmatch", type=float, default=1.0, help="Muon-positron matching distance [mm]")
    p.add_argument("--gate-us", type=float, default=13.0, help="Software data gate [us]")
    p.add_argument(
        "--mu-time-cut-us",
        type=float,
        default=0.05,
        help="Fallback early-time cut for muon classification if PID branch missing [us]",
    )
    p.add_argument(
        "--require-pid-or-time",
        action="store_true",
        default=True,
        help="Use PID/time classification for muon and positron tracklets",
    )

    # Plot binning
    p.add_argument("--delta-bins", type=int, default=120)
    p.add_argument("--delta-max", type=float, default=5.0)
    p.add_argument("--edep-bins", type=int, default=160)
    p.add_argument("--edep-max", type=float, default=0.8)
    p.add_argument("--xy-bins", type=int, default=120)
    p.add_argument("--xy-range", type=float, default=25.0)
    p.add_argument("--time-bins", type=int, default=260)

    # Fit
    p.add_argument("--fit-musR", action="store_true", help="Fit vx-muSR time histogram")
    p.add_argument("--fit-tmin", type=float, default=0.0)
    p.add_argument("--fit-tmax", type=float, default=8.0)

    args = p.parse_args()
    analyze(args)


if __name__ == "__main__":
    main()
