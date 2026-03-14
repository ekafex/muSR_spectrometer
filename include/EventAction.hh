#pragma once

#include "globals.hh"
#include "G4UserEventAction.hh"
#include "G4ThreeVector.hh"

class G4Event;

class EventAction : public G4UserEventAction {
public:
  EventAction();
  ~EventAction() override = default;

  void BeginOfEventAction(const G4Event*) override;
  void EndOfEventAction(const G4Event*) override;

  // Called by SteppingAction when muon stops in sample
  void RecordMuonStop(G4int trackID, const G4ThreeVector& pos, G4double time);

private:
  // Hits
  G4int fPlaneHCID = -1;

  // Truth: muon stop
  G4bool        fHasMuonStop = false;
  G4int         fMuonTrackID = -1;
  G4ThreeVector fMuonStopPos;
  G4double      fMuonStopTime = 0.0;
};
