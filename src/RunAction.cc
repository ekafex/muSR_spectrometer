#include "RunAction.hh"

#include "G4AnalysisManager.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4ios.hh"

RunAction::RunAction()
{
  auto* am = G4AnalysisManager::Instance();
  am->SetVerboseLevel(1);

  // If you ever run MT, merging helps.
  am->SetNtupleMerging(true);

  // ---------- Ntuple 0: PlaneHits ----------
  am->CreateNtuple("PlaneHits", "Plane hits (one row per step)");
  am->CreateNtupleIColumn("eventID");
  am->CreateNtupleIColumn("planeID");
  am->CreateNtupleIColumn("trackID");
  am->CreateNtupleIColumn("parentID");
  am->CreateNtupleIColumn("pdg");
  am->CreateNtupleDColumn("x_mm");
  am->CreateNtupleDColumn("y_mm");
  am->CreateNtupleDColumn("z_mm");
  am->CreateNtupleDColumn("t_ns");
  am->CreateNtupleDColumn("edep_keV");
  am->FinishNtuple(0);

  // ---------- Ntuple 1: MuonStop ----------
  am->CreateNtuple("MuonStop", "Muon stop truth in sample");
  am->CreateNtupleIColumn("eventID");
  am->CreateNtupleIColumn("muTrackID");
  am->CreateNtupleDColumn("x_mm");
  am->CreateNtupleDColumn("y_mm");
  am->CreateNtupleDColumn("z_mm");
  am->CreateNtupleDColumn("t_ns");
  am->FinishNtuple(1);
}

RunAction::~RunAction()
{
  //delete G4AnalysisManager::Instance();
}

void RunAction::BeginOfRunAction(const G4Run*)
{
  auto* am = G4AnalysisManager::Instance();
  am->OpenFile(fOutFile);
  G4cout << "[RunAction] Writing ROOT output to: " << fOutFile << G4endl;
}

void RunAction::EndOfRunAction(const G4Run*)
{
  auto* am = G4AnalysisManager::Instance();
  am->Write();
  am->CloseFile();
  G4cout << "[RunAction] ROOT file written and closed." << G4endl;
}
