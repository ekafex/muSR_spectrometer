# Si-Pixel vx-µSR musrSim (Mandok et.al. 2026)

## Purpose

This macro is a simplified musrSim model of the Si-pixel vertex-reconstructed µSR prototype described by Mandok et al. (2026). The goal is not to reproduce the full mechanical detector module, but to simulate the essential scattering and tracking geometry used for vertex reconstruction studies.

The model is intended primarily for studying:

- muon multiple Coulomb scattering in thin Si-pixel detector layers;
- reconstruction of the incoming muon track from upstream layers;
- extrapolation of the muon trajectory to the sample plane;
- comparison between the true muon stopping position and the extrapolated position;
- later extension to positron tracking and vx-µSR event matching.


## Coordinate Convention

The macro uses the following coordinate system:

| Axis | Meaning |
|---|---|
| `z` | beam direction |
| `x` | transverse horizontal direction |
| `y` | transverse vertical direction |

The sample is centered at:

```text
z = 0 mm
````

The incoming surface muon beam travels along:

```text
+z
```

The initial muon spin polarization is set perpendicular to the beam:

```text
spin along +x
```


## Geometry Overview

The simplified geometry contains:

1. an air world volume;
2. four thin Si-pixel detector layers;
3. one polyimide/Kapton support foil behind each Si layer;
4. a central Al target/sample;
5. optional Mylar tape supports;
6. optional placeholder permanent magnets;
7. no Pb collimator in this simplified version.

The geometry is deliberately simpler than the real instrument. In the paper, each detector layer is a Quad module containing four MuPix11 chips. In this macro, each layer is approximated as one continuous Si-pixel plane.


## Detector Layer Positions

The four detector layers are placed symmetrically around the sample:

| Layer |     Position | Role                   | Detector ID |
| ----- | -----------: | ---------------------- | ----------: |
| L1    | `z = -30 mm` | upstream outer layer   |         101 |
| L2    | `z = -10 mm` | upstream inner layer   |         102 |
| L3    | `z = +10 mm` | downstream inner layer |         103 |
| L4    | `z = +30 mm` | downstream outer layer |         104 |

The distance between the two inner layers is therefore:

```text
d = 20 mm
```

This corresponds to the experimental configuration discussed in the paper.


## Si-Pixel Detector Approximation

Each Si detector layer is modeled as a thin rectangular silicon volume.

Current macro intent:

```text
active area ≈ 20 mm × 20 mm
Si thickness = 100 µm
```

In musrSim/Geant4-style `box` construction, the dimensions are normally half-lengths. Therefore:

```text
/musr/command construct box L1_Chip 20.0 20.0 0.05 ...
```

corresponds to a full size of:

```text
40 mm × 40 mm × 0.1 mm
```

If the intended full active area is 20 mm × 20 mm, the recommended command is:

```text
/musr/command construct box L1_Chip 10.0 10.0 0.05 G4_Si 0 0 -30 log_World norot musr/ScintSD 101
```

The `z` half-thickness is correct:

```text
0.05 mm = 50 µm half-thickness
full thickness = 100 µm
```


## Polyimide / Kapton Foils

Each Si layer has one thin support foil placed just downstream of the Si plane.

The paper’s simulation uses:

```text
polyimide thickness = 25 µm
```

The macro uses:

```text
hz = 0.0125 mm
```

which gives:

```text
full thickness = 0.025 mm = 25 µm
```

This is consistent with the simulation description.

The material is represented as:

```text
G4_KAPTON
```

This is a reasonable Geant4 approximation for polyimide.

Recommended consistency fix:

```text
L1_PolyimideFoil: 10.0 10.0 0.0125
L2_PolyimideFoil: 10.0 10.0 0.0125
L3_PolyimideFoil: 10.0 10.0 0.0125
L4_PolyimideFoil: 10.0 10.0 0.0125
```

if the intended full foil area is 20 mm × 20 mm.


## Sample / Target

The macro currently uses the paper’s simulation target:

```text
20 mm diameter Al sample
```

The command is:

```text
/musr/command construct tubs Target 0 10.0 0.5 0 360 G4_Al 0 0 0 log_World norot dead 10
```

This means:

| Parameter      |  Value |
| -------------- | -----: |
| inner radius   |   0 mm |
| outer radius   |  10 mm |
| full diameter  |  20 mm |
| half-thickness | 0.5 mm |
| full thickness | 1.0 mm |
| material       |     Al |

The name `Target` is useful because musrSim stores special target-related information for volumes named `Target`.

The 1 mm thickness is an assumption. The paper specifies the diameter for the simulation sample, but not a precise thickness. The thickness should be tuned if the stopping distribution is not appropriate.


## Alternative vx-µSR Sample

The first vx-µSR spectrum in the paper used a:

```text
6 mm diameter Al disk
```

To switch to this case, comment the 20 mm target and use:

```text
/musr/command construct tubs Target 0 3.0 0.5 0 360 G4_Al 0 0 0 log_World norot dead 10
```

This gives:

```text
diameter = 6 mm
```

The permanent magnets used in the real experiment are not fully specified geometrically in the paper, so they are not included as real magnetic volumes in this simplified macro.


## Magnetic Field

The present macro neglects the magnetic field.

This is appropriate for reproducing the basic scattering-resolution simulation, where the main interest is the geometric uncertainty caused by multiple scattering in the Si layers.

For reproducing the transverse-field vx-µSR spectrum, a field should be added:

```text
B ≈ 6.3 mT
```

A reasonable orientation is:

```text
B along +y
```

if:

```text
beam along +z
spin along +x
```

The exact field command depends on the musrSim build and should be checked before enabling.


## Primary Beam

The macro defines a positive surface muon beam:

```text
/gun/particle mu+
/gun/position 0 0 -100 mm
/gun/direction 0 0 1
/gun/energy 4.1 MeV
/gun/polarization 1 0 0
/gun/muonPolarizFraction 1.0
```

This corresponds to:

| Quantity         |               Value |
| ---------------- | ------------------: |
| particle         |               `mu+` |
| kinetic energy   |             4.1 MeV |
| direction        |          along `+z` |
| initial position | upstream of layer 1 |
| polarization     |          along `+x` |

For the paper-style scattering simulation, the pointlike beam is appropriate.

A finite beam spot can later be added with a vertex-smearing command, if supported by the local musrSim version.


## Physics Processes

The macro includes explicit electromagnetic processes for:

* photons;
* electrons;
* positrons;
* positive muons.

The important processes are:

| Particle | Main processes                                                            |
| -------- | ------------------------------------------------------------------------- |
| `mu+`    | multiple scattering, ionisation, bremsstrahlung, pair production          |
| `e+`     | multiple scattering, ionisation, bremsstrahlung, annihilation             |
| `e-`     | multiple scattering, ionisation, bremsstrahlung                           |
| `gamma`  | photoelectric effect, Compton scattering, conversion, Rayleigh scattering |

For vx-µSR studies with positrons, positive muon decay should also be explicitly included:

```text
/musr/command process addProcess mu+ G4Decay 0 -1 5
```

Without this, decay positrons may be absent unless decay is added elsewhere by the musrSim default physics list.


## Step Limits

The macro applies small user step limits in the thin Si layers and in the target:

```text
/musr/command SetUserLimits log_L1_Chip 0.01
/musr/command SetUserLimits log_L2_Chip 0.01
/musr/command SetUserLimits log_L3_Chip 0.01
/musr/command SetUserLimits log_L4_Chip 0.01
/musr/command SetUserLimits log_Target 0.01
```

The value:

```text
0.01 mm = 10 µm
```

is conservative and appropriate for thin 100 µm Si detectors. If the simulation becomes too slow, this value can be increased after checking that the hit positions and energy-deposition distributions remain stable.


## Output

The macro stores ROOT output in:

```text
data/
```

using:

```text
/musr/command rootOutputDirectoryName data
```

It currently keeps all events:

```text
/musr/command storeOnlyEventsWithHits false
```

This is useful for debugging and for checking stopping distributions. For large production runs, the output size can be reduced by enabling event filters for the detector IDs:

```text
101, 102, 103, 104
```


## Visualization

Visualization attributes are assigned as:

| Volume                 | Color     |
| ---------------------- | --------- |
| World                  | invisible |
| Target                 | red       |
| upstream Si layers     | yellow    |
| downstream Si layers   | cyan      |
| Kapton/polyimide foils | green     |

Visualization is disabled for production:

```text
/vis/disable
```

For geometry checking, one can instead execute a separate visualization macro:

```text
/control/execute vis.mac
```


## Run Control

The macro initializes the simulation using:

```text
/run/initialize
```

and prints progress every 10000 events:

```text
/musr/run/howOftenToPrintEvent 10000
```

The current debug/medium run is:

```text
/run/beamOn 1000000
```

For reproducing the paper-style scattering simulation, increase to:

```text
/run/beamOn 10000000
```


## Main Simplifications Compared with the Real Prototype

This macro intentionally simplifies the real instrument:

1. each Quad module is replaced by one continuous Si plane;
2. the four-chip structure of each Quad is not modeled;
3. PCB material and support mechanics are omitted;
4. Pb collimator is omitted;
5. aluminized Mylar support tape is optional and normally disabled;
6. permanent magnets are omitted;
7. no realistic magnetic-field map is included;
8. detector pixelization is not explicitly modeled;
9. timing resolution and time-over-threshold response are not modeled.

These simplifications are acceptable for a first study of geometric scattering and track extrapolation, but not for a full detector-response simulation.


## Recommended Fixes Before Final Production

Before using this macro for production, apply the following corrections:

1. If the intended Si active area is 20 mm × 20 mm, change chip half-lengths from:

```text
20.0 20.0 0.05
```

to:

```text
10.0 10.0 0.05
```

2. Make all polyimide foil dimensions consistent.

3. Keep the foil thickness documented as 25 µm, not 20 µm, unless intentionally changing the model.

4. Add positive muon decay explicitly:

```text
/musr/command process addProcess mu+ G4Decay 0 -1 5
```

5. For the vx-µSR spectrum case, switch from the 20 mm sample to the 6 mm Al disk and add a transverse magnetic field of about 6.3 mT.

---

## Intended Analysis After Simulation

The ROOT output should be used to reconstruct:

1. hit positions in layers L1 and L2;
2. incoming muon tracklet from L1-L2;
3. extrapolated muon position at `z = 0`;
4. true muon stopping position in `Target`;
5. reconstruction residual:

```text
delta_mu = |r_stop - r_extrapolated|
```

The standard deviation of `delta_mu` is the main quantity used to estimate the lateral uncertainty caused by multiple scattering.

