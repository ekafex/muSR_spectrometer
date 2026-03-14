#pragma once

#include "globals.hh"
#include "G4SystemOfUnits.hh"
#include <vector>

class Config {
public:
  // Singleton-ish access (simple and sufficient for this project)
  static Config& Instance();

  // --- Geometry knobs (defaults are reasonable placeholders) ---
  G4double worldSize = 1.0 * m;

  // Sample (target)
  G4double sampleXY = 10.0 * mm;
  G4double sampleZ  = 2.0  * mm;

  // Planes (Si)
  G4int    nUp   = 2;
  G4int    nDown = 2;

  G4double planeXY        = 40.0 * mm;
  G4double planeThickness = 0.10 * mm; // 100 µm
  G4double gapToSample    = 10.0 * mm;  // distance from sample face to nearest plane
  G4double planeSpacing   = 20.0 * mm;  // spacing between planes in a stack

  // Visualization toggles
  G4bool   showWorld = false; // hide world box by default
  G4bool   showAxes  = true;

private:
  Config() = default;
};
