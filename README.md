# Minimal Geant4 μSR Vertex Spectrometer Simulation

This repository contains a **minimal Geant4 simulation of a μSR vertex-resolved spectrometer** inspired by recent proposals to perform μSR using **silicon pixel detectors with vertex reconstruction**.

The goal of this project is to build a **controlled, modular Geant4 prototype** that allows rapid exploration of:

-   detector geometry
-   vertex reconstruction algorithms
-   muon–positron association
-   pile-up handling

before porting the work to **muSRsim**, the simulation framework used in μSR experiments at PSI.

This code intentionally avoids unnecessary complexity so that detector assumptions and reconstruction methods can be **tested quickly and modified easily**.



# Project Overview

The simulation models a **simplified μSR spectrometer** consisting of:

-   a **target sample** where muons stop and decay
-   two stacks of **silicon tracking planes**
-   a **μ⁺ beam source**
-   minimal **digitization and hit merging**

The simulation produces **ROOT file output** containing both detector hits and ground-truth information required for reconstruction studies.



# Repository Structure

The project follows a **classic Geant4 layout** separating headers, implementation, and application entry points.

```
muSR_spectrometer/
├─ CMakeLists.txt
├─ README.md
├─ macros/
├─ include/
├─ src/
├─ app/
├─ analysis/
└─ build/
```

### Important directories

**include/**
Geant4 class headers.

**src/**
Implementation of detector, physics, and actions.

**app/**
Program entry point (`main.cc`).

**macros/**
Geant4 control macros for batch and visualization runs.

**analysis/**
Python scripts used for reconstruction and plotting.



# Detector Model

### Geometry

The simulated detector consists of:

-   a **world volume** filled with air
-   a **target sample** located at the origin
-   two stacks of **silicon tracking planes**

```
   upstream planes
        ||
        ||
        \/ 
   ---- detector ----
        sample
   ---- detector ----
        /\
        ||
        ||
   downstream planes
```

Tracking planes are modeled as **thin silicon slabs**.

### Plane Identification

Plane copy numbers are unique:

```
upstream planes:   0 .. N
downstream planes: 100 .. 100+N
```

This prevents ambiguity during hit reconstruction.



# Beam Model

The μ⁺ beam is generated using `PrimaryGeneratorAction`.

Properties:

-   particle: **μ⁺**
-   propagation direction: **−z → +z**
-   transverse profile: **Gaussian**
-   beam momentum tuned so that **muons stop in the sample**

Beam parameters can be adjusted directly in the generator.



# Sensitive Detector Model

Each silicon plane acts as a **Geant4 SensitiveDetector**.

To suppress Geant4 stepping noise, hits are **merged per (planeID, trackID)**.

For each `(planeID, trackID)` pair:

```
energy deposit  → summed
hit time        → earliest step
hit position    → position of earliest step
```

This produces **one detector hit per particle per plane**, approximating a pixel detector response.



# Recorded Hit Information

Each hit contains:

```
planeID
trackID
parentID
pdg
x,y,z
time
edep
```

Values are converted to analysis-friendly units before writing to ROOT.



# Ground-Truth Information

Muon stopping positions are recorded using `SteppingAction`.

When a μ⁺ reaches very low kinetic energy inside the sample, the following information is stored:

```
muTrackID
x,y,z stop position
stop time
```

This information serves as **ground truth** for reconstruction validation.



# ROOT Output

Simulation output is written to a ROOT file.

Two ntuples are generated.

### PlaneHits

One row per detector hit.

```
eventID
planeID
trackID
parentID
pdg
x_mm
y_mm
z_mm
t_ns
edep_keV
```

### MuonStop

One row per event.

```
eventID
muTrackID
x_mm
y_mm
z_mm
t_ns
```



# Reconstruction Workflow

The Geant4 simulation produces **detector hits + ground truth**.

Reconstruction is implemented externally in Python.

Planned analysis steps:

1.  **Track reconstruction**
    -   separate μ⁺ and e⁺ hits
    -   fit tracks through plane hits
2.  **Vertex reconstruction**
    -   compute closest approach between μ and e⁺ tracks
3.  **Muon–positron association**
    -   match decay positrons with parent muons
4.  **Performance studies**
    -   vertex resolution
    -   pairing efficiency
    -   detector spacing optimization
    -   multiple scattering effects
    -   pile-up tolerance



# Development Goals

This minimal simulation is intended to support:

-   rapid detector geometry studies
-   algorithm development
-   validation of vertex-resolved μSR concepts

The long-term goal is to **transfer validated detector configurations and reconstruction methods to μSRSim** for realistic beamline simulations.



# Future Extensions

Planned improvements include:

-   magnetic field support
-   pile-up simulation (multiple muons per time window)
-   improved detector digitization
-   pixel pitch and clustering simulation
-   helix track fitting in magnetic fields
-   realistic timing resolution



# Motivation

Traditional μSR experiments are limited by **single-muon rate constraints**.

Vertex-resolved μSR using silicon tracking detectors may allow:

-   higher beam rates
-   improved statistics
-   spatially resolved μSR measurements

This simulation provides a **controlled environment to study these ideas**.

