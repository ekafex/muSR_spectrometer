#include "PrimaryGeneratorAction.hh"

#include "G4Event.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction()
{
  // One primary per event
  fGun = new G4ParticleGun(1);

  // Particle: mu+
  auto* particle = G4ParticleTable::GetParticleTable()->FindParticle("mu+");
  fGun->SetParticleDefinition(particle);

  // Direction: +z (beam from -z -> +z)
  fGun->SetParticleMomentumDirection(G4ThreeVector(0, 0, 1));

  // Momentum magnitude (use momentum, not kinetic energy, to keep it simple)
  fGun->SetParticleMomentum(fP * MeV);

  // Default starting position; actual position randomized per event
  fGun->SetParticlePosition(G4ThreeVector(0, 0, fZ0 * mm));
}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fGun;
}

G4double PrimaryGeneratorAction::Gauss(G4double mean, G4double sigma) const
{
  // CLHEP/Geant4 helper
  return mean + sigma * G4RandGauss::shoot();
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event)
{
  // Randomize transverse beam spot (Gaussian)
  const G4double x = Gauss(fMeanX, fSigmaX) * mm;
  const G4double y = Gauss(fMeanY, fSigmaY) * mm;

  fGun->SetParticlePosition(G4ThreeVector(x, y, fZ0 * mm));

  fGun->GeneratePrimaryVertex(event);
}
