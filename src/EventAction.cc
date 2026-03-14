#include "EventAction.hh"

#include "G4Event.hh"
#include "G4HCofThisEvent.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"
#include "G4AnalysisManager.hh"
#include <algorithm>

#include "Hit.hh"

EventAction::EventAction() {}

void EventAction::BeginOfEventAction(const G4Event*)
{
  fHasMuonStop = false;
  fMuonTrackID = -1;
  fMuonStopPos = G4ThreeVector();
  fMuonStopTime = 0.0;
}

void EventAction::RecordMuonStop(G4int trackID, const G4ThreeVector& pos, G4double time)
{
  // Record only the first time we decide "stopped"
  if (fHasMuonStop) return;
  fHasMuonStop = true;
  fMuonTrackID = trackID;
  fMuonStopPos = pos;
  fMuonStopTime = time;
}

void EventAction::EndOfEventAction(const G4Event* evt)
{
  auto* hce = evt->GetHCofThisEvent();
  if (!hce) return;

  if (fPlaneHCID < 0) {
    fPlaneHCID = G4SDManager::GetSDMpointer()->GetCollectionID("PlaneSD/PlaneHits");
  }

  auto* hc = static_cast<HitCollection*>(hce->GetHC(fPlaneHCID));
  if (!hc) return;

  auto* am = G4AnalysisManager::Instance();
  const auto eventID = evt->GetEventID();

  // ---- Fill PlaneHits ntuple (ntupleId = 0) ----
  const auto nHits = hc->entries();
  for (G4int i = 0; i < nHits; ++i) {
    const auto* hit = (*hc)[i];

    am->FillNtupleIColumn(0, 0, eventID);
    am->FillNtupleIColumn(0, 1, hit->planeID);
    am->FillNtupleIColumn(0, 2, hit->trackID);
    am->FillNtupleIColumn(0, 3, hit->parentID);
    am->FillNtupleIColumn(0, 4, hit->pdg);

    am->FillNtupleDColumn(0, 5, hit->pos.x()/mm);
    am->FillNtupleDColumn(0, 6, hit->pos.y()/mm);
    am->FillNtupleDColumn(0, 7, hit->pos.z()/mm);
    am->FillNtupleDColumn(0, 8, hit->time/ns);
    am->FillNtupleDColumn(0, 9, hit->edep/keV);

    am->AddNtupleRow(0);
  }

  // ---- Fill MuonStop ntuple (ntupleId = 1) ----
  if (fHasMuonStop) {
    am->FillNtupleIColumn(1, 0, eventID);
    am->FillNtupleIColumn(1, 1, fMuonTrackID);

    am->FillNtupleDColumn(1, 2, fMuonStopPos.x()/mm);
    am->FillNtupleDColumn(1, 3, fMuonStopPos.y()/mm);
    am->FillNtupleDColumn(1, 4, fMuonStopPos.z()/mm);
    am->FillNtupleDColumn(1, 5, fMuonStopTime/ns);

    am->AddNtupleRow(1);
  }
}
