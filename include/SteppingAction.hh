#pragma once

#include "G4UserSteppingAction.hh"
#include "globals.hh"
#include "G4SystemOfUnits.hh"

class EventAction;
class G4Step;

class SteppingAction : public G4UserSteppingAction {
public:
  explicit SteppingAction(EventAction* eventAction);
  ~SteppingAction() override = default;

  void UserSteppingAction(const G4Step* step) override;

private:
  EventAction* fEventAction = nullptr;

  // threshold for "stopped"
  G4double fStopKE = 1.0 * keV;

  // volume name to detect sample
  const G4String fSamplePVName = "SamplePV";
};
