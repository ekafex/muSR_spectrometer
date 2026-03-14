#include "SteppingAction.hh"
#include "EventAction.hh"

#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4Track.hh"
#include "G4VPhysicalVolume.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"

SteppingAction::SteppingAction(EventAction* eventAction)
  : fEventAction(eventAction)
{}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  auto* trk = step->GetTrack();

  // Only mu+
  if (trk->GetDefinition()->GetParticleName() != "mu+") return;

  // Must be inside SamplePV
  auto* prePV = step->GetPreStepPoint()->GetPhysicalVolume();
  if (!prePV) return;
  if (prePV->GetName() != fSamplePVName) return;

  // Decide "stopped": very low KE (simple & robust for now)
  const auto ke = trk->GetKineticEnergy();
  if (ke > fStopKE) return;

  // Record truth stop position/time
  const auto pos  = step->GetPreStepPoint()->GetPosition();
  const auto time = step->GetPreStepPoint()->GetGlobalTime();

  fEventAction->RecordMuonStop(trk->GetTrackID(), pos, time);
}
