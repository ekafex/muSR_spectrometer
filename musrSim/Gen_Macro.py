# -*- coding: utf-8 -*-
"""
Created on Thu May  7 16:29:16 2026

@author: drago

Generate musrSim template
"""

def Header():
    return """############################################################
# This macro is generated via Gen_Macro.py!
############################################################
# Goal:
#   Approximate simulation of the Si-pixel vx-muSR spectrometer 
#   described in Mandok et al.(2026)
#
# Convention:
#   Beam direction = z-axis
#   Sample centered at z = 0
#   upstream detectors   (Layer 1 and 2)
#   downstream detectors (Layer 3 and 4)
#   muon spin perpendicular to beam, along +x-axis
#
# Detector:
# In the paper Si-pixel chip of one detector is a quad-module of 4 MuPix11 chips.
# Here we approximate as one single module with:
#   - Si thickness: 100 um
#   - Polyimide foil: 25 um
#   - Polyimide/Kapton is represented using G4_KAPTON
#   - Si is represented using G4_Si
#
# Beam:
# Pointlike muon beam incident perpendicular with layer 1 (upstream).
#   - Muons are surface muons with kinetic energy 4.1 MeV
#   - For a more beamline-like run: 
#       + use a small Gaussian or uniform transverse beam spot 
#       + let the Pb jaws define/clean the aperture.
#   - We have simplified here the beam, no Pb collimators!
#
# Sample: 
#   - Sample in middle at z = 0
#   - Simulation sample: 20 mm diameter
#   - vx-muSR test sample: 6 mm diameter Al disk
#
# Magnets:
# Permanent magnets field
# Uniform transverse field of about 6.3 mT around the sample.
#
############################################################
    """

# ==============================

def Initialization():
    return """
############################################################
# GENERAL INITIALIZATION
############################################################

/control/verbose 0
/run/verbose 0
/tracking/verbose 0

    """

# ==============================

def Physics():
    return """
############################################################
# PHYSICS CONFIGURATION
############################################################

# gamma
/musr/command process addDiscreteProcess gamma G4PhotoElectricEffect
/musr/command process addDiscreteProcess gamma G4ComptonScattering
/musr/command process addDiscreteProcess gamma G4GammaConversion
/musr/command process addDiscreteProcess gamma G4RayleighScattering

# electrons
/musr/command process addProcess e- G4eMultipleScattering -1 1 1
/musr/command process addProcess e- G4eIonisation         -1 2 2
/musr/command process addProcess e- G4eBremsstrahlung     -1 3 3

# positrons
/musr/command process addProcess e+ G4eMultipleScattering -1 1 1
/musr/command process addProcess e+ G4eIonisation         -1 2 2
/musr/command process addProcess e+ G4eBremsstrahlung     -1 3 3
/musr/command process addProcess e+ G4eplusAnnihilation    0 -1 4

# positive muons
/musr/command process addProcess mu+ G4MuMultipleScattering -1 1 1
/musr/command process addProcess mu+ G4MuIonisation         -1 2 2
/musr/command process addProcess mu+ G4MuBremsstrahlung     -1 3 3
/musr/command process addProcess mu+ G4MuPairProduction     -1 4 4

# Step limiter helps in thin detector layers. Keep post-step ordering after EM processes.
/musr/command process addProcess mu+ G4StepLimiter -1 -1 6
/musr/command process addProcess e+  G4StepLimiter -1 -1 6
/musr/command process addProcess e-  G4StepLimiter -1 -1 6

    """

# ==============================

def Limits_Cuts():
    return """
############################################################
# USER LIMITS AND CUTS
############################################################

#/run/setCut 0.01 mm
/musr/command SetUserLimits log_L1_Chip 0.01
/musr/command SetUserLimits log_L2_Chip 0.01
/musr/command SetUserLimits log_L3_Chip 0.01
/musr/command SetUserLimits log_L4_Chip 0.01
/musr/command SetUserLimits log_Target 0.01

    """

# ==============================

def Primary_Beam():
    return """
############################################################
# PRIMARY BEAM
############################################################

# Primary particle
/gun/particle mu+

# Start upstream of collimator and layer 1.
/gun/position 0 0 -100 mm

# Beam along +z.
/gun/direction 0 0 1

# Surface muon kinetic energy.
/gun/kenergy 4.1 MeV

# Initial muon spin perpendicular to beam.
/gun/polarization 1 0 0
/gun/muonPolarizFraction 1.0

    """
    
# Pointlike beam: closest to paper Sec. III simulation.
# No vertex smearing command needed if position is fixed.

# Optional: finite beam spot.
# Positive values = Gaussian sigma in mm.
# Use sigma about 1 mm to stay mostly inside the 3 mm collimator aperture.
#/gun/vertexsigma 1.0 1.0 0 mm

# Optional: approximate continuous source timing.
# 40 kHz corresponds to mean separation 25 us.
# Use only if your musrSim primary generator supports this command.
#/gun/meanarrivaltime 25 microsecond

# ==============================

def ROOT_Output(Det : dict, onlyStoreEventsWithHits : bool = False):
    """
    Controls the Output of the ROOT file tree and data that are saved.

    Parameters
    ----------
    Det is a dictionary with all detector parameters.
    Det['ID'] : dict, the IDs of each detector Layer
    onlyStoreEventsWithHits : bool, optional
        Turns On or Off if we would like to save only events with hits. 
        The default is False.

    Returns
    -------
    Output settings string for the macro file.
    """
    
    ID_L = Det['ID']
    flag = "true" if onlyStoreEventsWithHits else "false"
    
    s = f"""
############################################################
# OUTPUT SETTINGS
############################################################

/musr/command rootOutputDirectoryName data
/musr/command storeOnlyEventsWithHits {flag}

    """
    
    if onlyStoreEventsWithHits:
        s += f"""
# If using store-only filters, apply to all Si layers.
/musr/onlyStoreEventsWithHits {ID_L['L1']}
/musr/onlyStoreEventsWithHits {ID_L['L2']}
/musr/onlyStoreEventsWithHits {ID_L['L3']}
/musr/onlyStoreEventsWithHits {ID_L['L4']}

    """
    return s

# ==============================

def Visual(Det, vis_enable : bool = False):
    L_Name = Det['Names']
    F_Name = Det['Foil']['Names']
    s = """/vis/open OGLIX 1000x800-0+0
/vis/drawVolume
#/vis/viewer/set/style wireframe 
/vis/viewer/set/style surface
/vis/viewer/set/auxiliaryEdge true
/vis/viewer/set/background black
/vis/viewer/set/viewpointThetaPhi 140 30 deg

/vis/scene/add/axes 0 0 0 60 mm

/vis/scene/add/trajectories
/vis/scene/endOfEventAction refresh
#/vis/scene/endOfEventAction  accumulate
/vis/scene/add/trajectories smooth
/vis/modeling/trajectories/create/drawByParticleID
/vis/scene/add/hits

/vis/viewer/set/autoRefresh true
/vis/viewer/flush
    """

    if vis_enable:
        # Write vis.mac file
        with open('vis.mac','w') as f:
            f.write(s)
        s = f"""
############################################################
# VISUALIZATION ATTRIBUTES
############################################################

/musr/command visattributes log_World invisible

/musr/command visattributes log_Target red

/musr/command visattributes log_Magnet_Top blue
/musr/command visattributes log_Magnet_Bottom blue

/musr/command visattributes log_{L_Name['L1']} yellow
/musr/command visattributes log_{L_Name['L2']} yellow
/musr/command visattributes log_{L_Name['L3']} cyan
/musr/command visattributes log_{L_Name['L4']} cyan

/musr/command visattributes log_{F_Name['L1']} green
/musr/command visattributes log_{F_Name['L2']} green
/musr/command visattributes log_{F_Name['L3']} green
/musr/command visattributes log_{F_Name['L4']} green


# Disable visualization for production.
/control/execute vis.mac

        """
    else:
        s = """
# Disable visualization for production.
/vis/disable

        """
    return s

# ==============================


def run(N_events : int = 100000, printFreq:int=10000):
    """
    Define Beam Run parameters.

    Parameters
    ----------
    N_events: int, optional
        Number of events. The default is 100000.
    printFreq : int, optional
        Printing run statistics with printFreq frequency. The default is 10000.

    Returns
    -------
    Initialize and run parameters of macro.
    """
    return f"""
############################################################
# INITIALIZE AND RUN
############################################################

/run/initialize

# Print frequency.
/musr/run/howOftenToPrintEvent {printFreq}

# Production: /run/beamOn 10M
# Start with 100k for debugging
/run/beamOn {N_events}

"""

# ==============================

def Construc_World(W):
    return f"""
############################################################
# WORLD
############################################################

# Large world volume with {W['Material']}.
/musr/command construct box World {W['l']} {W['w']} {W['h']} {W['Material']} 0 0 0 no_logical_volume norot dead -1

    """

# ==============================

def Detector(Det : dict):
    """
    Generates the detector part of the macro file.

    Parameters
    ----------
    Det['ID'] : dictionary, every layer L1-L4 IDs
    Det['Dimensions'] : dictionary, full dimensions of the Si-pixel 
                        active area for every layer.
    Det['Distances'] : dictionary, distances between layers.
    Det['z_offset']  : float, offset center of detector in the z-direction. 
                       z=0 may not be the center of the detector.
    Det['Material'] : str, material of the Si-pixel active area.
    Det['Foil'] : dictionary, thickness and material of the Polyimide foil 
                  for each layer behind the chip in the +z direction.

    Returns
    -------
    Multi-line string that describes the detector construction part of the macro. 
    """
    # ---------------------------
    # dictionaries
    ID_L   = Det['ID'] 
    Dim    = Det['Dimensions']
    Foil   = Det['Foil']
    Dist   = Det['Distances']
    L_Name = Det['Names']
    F_Name = Foil['Names']
    # ---------------------------
    z_L1 = Det['z_offset'] -Dist['L1-L2'] -Dist['L2-L3']/2 # mm z of Layer L1
    z_L2 = Det['z_offset'] -Dist['L2-L3']/2                # mm z of Layer L2
    z_L3 = Det['z_offset'] +Dist['L2-L3']/2                # mm z of Layer L3
    z_L4 = Det['z_offset'] +Dist['L3-L4'] +Dist['L2-L3']/2 # mm z of Layer L4
    # ---------------------------
    ################################################
    # option A: all foils geometrically on +z side
    # option B: foils away from sample
    # option C: foils behind chip relative to local detector orientation
    ################################################
    # I am choosing Foils away from Sample like Fig.1 Mandok et al(2026)
    # upstream face the beam, downstream away from beam.
    z_P1 = z_L1 - (Dim['h'] + Foil['h_foil'])/2 # mm z of L1 polyimide foil (upstream)
    z_P2 = z_L2 - (Dim['h'] + Foil['h_foil'])/2 # mm z of L2 polyimide foil (upstream)
    z_P3 = z_L3 + (Dim['h'] + Foil['h_foil'])/2 # mm z of L3 polyimide foil (downstream)
    z_P4 = z_L4 + (Dim['h'] + Foil['h_foil'])/2 # mm z of L4 polyimide foil (downstream)
    # ---------------------------
    
    s = f"""
############################################################
# Si-PIXEL DETECTORS
############################################################

# MuPix11 active matrix approximation:
#  - active area approximately {Dim['l']:.1f} x {Dim['w']:.1f} mm²
#  - full thickness = {1e3*Dim['h']:.1f} um
#  - Polyimide foil (Kapton): {1e3*Foil['h_foil']:.1f} um
# 
# One Layer Si-pixel detector has quad-module of 4 MuPix11 chips
#
# Layer positions:
#   L1 z = {z_L1:.1f} mm
#   L2 z = {z_L2:.1f} mm
#   L3 z = +{z_L3:.1f} mm
#   L4 z = +{z_L4} mm
# 
# Mandok et al. (2026) does not describe the position of foils
# From Fig.1 I belive the Polyimide foils are away from Target  

# Layer 1:
/musr/command construct box {L_Name['L1']} {Dim['l']/2} {Dim['w']/2} {Dim['h']/2} {Det['Material']} 0 0 {z_L1} log_World norot musr/ScintSD {ID_L['L1']}
/musr/command construct box {F_Name['L1']} {Dim['l']/2} {Dim['w']/2} {Foil['h_foil']/2} {Foil['Material']} 0 0 {z_P1} log_World norot dead -1

# Layer 2:
/musr/command construct box {L_Name['L2']} {Dim['l']/2} {Dim['w']/2} {Dim['h']/2} {Det['Material']} 0 0 {z_L2} log_World norot musr/ScintSD {ID_L['L2']}
/musr/command construct box {F_Name['L2']} {Dim['l']/2} {Dim['w']/2} {Foil['h_foil']/2} {Foil['Material']} 0 0 {z_P2} log_World norot dead -1

# Layer 3:
/musr/command construct box {L_Name['L3']} {Dim['l']/2} {Dim['w']/2} {Dim['h']/2} {Det['Material']} 0 0 {z_L3} log_World norot musr/ScintSD {ID_L['L3']}
/musr/command construct box {F_Name['L3']} {Dim['l']/2} {Dim['w']/2} {Foil['h_foil']/2} {Foil['Material']} 0 0 {z_P3} log_World norot dead -1

# Layer 4:
/musr/command construct box {L_Name['L4']} {Dim['l']/2} {Dim['w']/2} {Dim['h']/2} {Det['Material']} 0 0 {z_L4} log_World norot musr/ScintSD {ID_L['L4']}
/musr/command construct box {F_Name['L4']} {Dim['l']/2} {Dim['w']/2} {Foil['h_foil']/2} {Foil['Material']} 0 0 {z_P4} log_World norot dead -1

    """
    return s

# ==============================
 
def Target(Targ : dict):
    """
    Target description (cylindrical geometry).

    Parameters
    ----------
    Targ['diameter'] : float, diameter of the cylinder.
    Targ['thickness'] : float, height of the cylinder.
    Targ['Material'] : str, musrSim defined material.
    Targ['z'] : float, in case one need to offset target/sample from z=0.

    Returns
    -------
    String of the macro description of the target 
    for evaluating vertex extrapolation uncertainty.
    """
    
    s = f"""
############################################################
# SAMPLE / TARGET
############################################################

/musr/command construct tubs Target 0 {Targ['diameter']/2} {Targ['thickness']/2} 0 360 {Targ['Material']} 0 0 {Targ['z']} log_World norot dead 10

    """
    return s

# ==============================

Magnet={'l':10.,'w':2.,'h':10.,'x':0.,'y':15.,'z':0.,          # Permanent magnet dimensions and position
        'Material':'G4_Fe', 'B_field':[0, 6.3e-3, 0]} 

def Magnets(Magnet : dict):
    """
    Magnetic field definition from permanent magnets (assume uniform).

    Parameters
    ----------
    Magnet['l'] : float, length of the permanent magnet in the x direction.
    Magnet['w'] : float, width of the permanent magnet in the y direction.
    Magnet['h'] : float, height of the permanent magnet in the z direction.
    Magnet['x'] : float, position in x.
    Magnet['y'] : float, position in y.
    Magnet['z'] : float, position in z.
    Magnet['Material'] : str, permanent magnet material as defined in musrSim.
    Magnet['B_field'] : list, magnetic field vector [Bx,By,Bz] in Tesla.

    Returns
    -------
    String of the macro describing magnet and uniform magnetic field.
    """
    
    Bx, By, Bz = Magnet['B_field']
    box        = Magnet['field_box']
      
    s = f"""
############################################################
# MAGNET and Magnetic Field
############################################################

/musr/command construct box Magnet_Top    {Magnet['l']/2} {Magnet['w']/2} {Magnet['h']/2} {Magnet['Material']} {Magnet['x']} {Magnet['y']}  {Magnet['z']} log_World norot dead -1
/musr/command construct box Magnet_Bottom {Magnet['l']/2} {Magnet['w']/2} {Magnet['h']/2} {Magnet['Material']} {Magnet['x']} {-Magnet['y']} {Magnet['z']} log_World norot dead -1

/musr/command globalfield Magnets {box['l']/2} {box['w']/2} {box['h']/2} uniform {Magnet['x']} 0 {Magnet['z']} log_Target {Bx} {By} {Bz} 0 0 0

/musr/command globalfield printFieldValueAtPoint 0 0 0
/musr/command globalfield printFieldValueAtPoint 0 0 14
/musr/command globalfield printFieldValueAtPoint 0 0 16
/musr/command globalfield printparameters

    """
    return s

# ===============================================================


def Geometry_Sanity_Check(Detect:dict, Targ:dict, Magnet:dict):
    # ===============================================================
    # Geometry sanity checks
    # ===============================================================
    
    # --- Basic detector/material dimensions ---
    chip_h = Detect['Dimensions']['h']          # full Si chip thickness [mm]
    foil_h = Detect['Foil']['h_foil']           # full foil thickness [mm]
    target_h = Targ['thickness']                # full target thickness [mm]
    target_r = Targ['diameter'] / 2             # target radius [mm]
    
    # --- Layer spacings ---
    d12 = Detect['Distances']['L1-L2']
    d23 = Detect['Distances']['L2-L3']
    d34 = Detect['Distances']['L3-L4']
    
    # --- Magnet clearance ---
    magnet_y = abs(Magnet['y'])                 # magnet centre distance from beam axis [mm]
    magnet_half_w = Magnet['w'] / 2             # magnet half-width in y [mm]
    magnet_inner_face_y = magnet_y - magnet_half_w
    
    
    # ===============================================================
    # 1. Check neighbouring detector-layer overlaps
    # ===============================================================
    # Each neighbouring pair must have enough centre-to-centre spacing
    # to contain one chip plus one foil clearance, since the foil is attached
    # outside the chip.
    
    min_layer_spacing = chip_h + foil_h
    
    if d12 <= min_layer_spacing:
        raise ValueError(
            f"L1-L2 distance too small: d12={d12} mm, "
            f"minimum required > {min_layer_spacing} mm."
        )
    
    if d34 <= min_layer_spacing:
        raise ValueError(
            f"L3-L4 distance too small: d34={d34} mm, "
            f"minimum required > {min_layer_spacing} mm."
        )
    
    
    # ===============================================================
    # 2. Check target clearance between inner detector layers L2 and L3
    # ===============================================================
    # L2 and L3 are separated by d23, centered around the target.
    # The target must fit between the inner silicon faces.
    # Since your foils are placed away from the target, they are not included
    # in this inner-clearance condition.
    
    inner_half_gap = d23 / 2
    target_half_h = target_h / 2
    chip_half_h = chip_h / 2
    
    available_clearance_to_inner_chip_face = inner_half_gap - chip_half_h
    
    if target_half_h >= available_clearance_to_inner_chip_face:
        raise ValueError(
            f"Target overlaps inner detector layers: target half-thickness={target_half_h} mm, "
            f"available clearance={available_clearance_to_inner_chip_face} mm."
        )
    
    
    # ===============================================================
    # 3. Check target radial clearance between permanent magnets
    # ===============================================================
    # Magnet inner face is at |y_magnet| - magnet_width/2.
    # Target radius must be smaller than this.
    
    if target_r >= magnet_inner_face_y:
        raise ValueError(
            f"Target overlaps magnet inner faces: target radius={target_r} mm, "
            f"magnet inner face at y={magnet_inner_face_y} mm."
        )



# === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === ===
# === === === === === === === === === === === === === === ===


# ===============================================================

# =========================
# Spectrometer Parameters #
# =========================

# The paper discusses two relevant sample cases:
#
# A) Simulation geometry:
#      sample diameter = 20 mm
#      used for evaluating vertex extrapolation uncertainty.
#
# B) First vx-muSR spectrum:
#      6 mm diameter Al disk between permanent magnets,
#      transverse field about 6.3 mT.


# ---------------------
# ---------------------

N_events = int(1e5) # Production: /run/beamOn 10M

onlyStoreEventsWithHits = False # If using store-only filters, apply to all Si layers.
vis_enable = False              # Disable visualization for production.


World  = {'l':500,'w':500,'h':750,'Material':'Air'}            # World dimensions and material

Detect = {'ID':{'L1':101, 'L2':102, 'L3':103, 'L4':104},       # Layers IDs
          'Names':{'L1':'L1_Chip', 'L2':'L2_Chip', 
                   'L3':'L3_Chip', 'L4':'L4_Chip'},            # Name of each layer (construct name)
          'Dimensions': {'l':40., 'w':40., 'h':0.1},           # full dimensions of 2x2 MuPix11 chips/layer
          'Distances':{'L1-L2':20., 'L2-L3':20., 'L3-L4':20.}, # distances between layers
          'z_offset':0.0,                                      # offset in z-direction from z=0 being the center of detector.
          'Material':'G4_Si',                                  # Material of Si-pixel layers
          'Foil':{'h_foil':0.025,'Material':'G4_KAPTON',       # Polyimide foil thickness and material glued behind the chip in the +z direction
                  'Names':{'L1':'L1_PolyimideFoil', 
                           'L2':'L2_PolyimideFoil', 
                           'L3':'L3_PolyimideFoil', 
                           'L4':'L4_PolyimideFoil'            # Names of Polyimide foil layers (construct)
                          }
                 }
         }


Targ= {'diameter':20.,'thickness':1.0,                         # Target/Sample diameter and thickness (modeled as cylinder)
       'Material':'G4_Al','z':0.}                              # Target/Sample material and offset from z=0 center

Magnet={'l':10.,'w':2.,'h':10.,'x':0.,'y':15.,'z':0.,          # Permanent magnet dimensions and position
        'Material':'G4_Fe',                                    # Permanent magnet material
        'B_field':[0, 6.3e-3, 0],                              # Permanent magnet magnetic field vector
        'field_box':{'l':30.,'w':30.,'h':30.}                  # Permanent magnet field box distribution
        }

# ===============================================================


# Geometry sanity checks
Geometry_Sanity_Check(Detect, Targ, Magnet)
#-------


ss = Header() + Initialization()
ss += Construc_World(World)
ss += Detector(Detect)
ss += Target(Targ)
ss += Magnets(Magnet)
ss += Physics()
ss += Limits_Cuts()
ss += Primary_Beam()
ss += ROOT_Output(Detect, onlyStoreEventsWithHits)
ss += Visual(Detect, vis_enable)
ss += run(N_events, printFreq=10000)


with open('run.mac','w') as f:
    f.write(ss)



