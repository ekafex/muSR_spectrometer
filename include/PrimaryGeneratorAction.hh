#pragma once

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

class G4ParticleGun;
class G4Event;

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction {
public:
  PrimaryGeneratorAction();
  ~PrimaryGeneratorAction() override;

  void GeneratePrimaries(G4Event* event) override;

private:
  G4ParticleGun* fGun = nullptr;

  // Beam parameters (minimal knobs; later move to Config + UI commands)
  G4double fMeanX = 0.0;
  G4double fMeanY = 0.0;
  G4double fSigmaX = 2.0; // mm
  G4double fSigmaY = 2.0; // mm

  G4double fZ0 = -60.0;   // mm (start upstream of planes/sample)
  G4double fP = 28.0;     // MeV/c (placeholder; tune to your case)

  // Small Gaussian helper
  G4double Gauss(G4double mean, G4double sigma) const;
};
