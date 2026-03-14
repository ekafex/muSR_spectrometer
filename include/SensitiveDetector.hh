#pragma once

#include "globals.hh"
#include "G4VSensitiveDetector.hh"

#include "Hit.hh"

#include <unordered_map>
#include <cstdint>

class G4Step;
class G4HCofThisEvent;

class SensitiveDetector : public G4VSensitiveDetector {
public:
  explicit SensitiveDetector(const G4String& name,
                             const G4String& hitsCollectionName);

  ~SensitiveDetector() override = default;

  void Initialize(G4HCofThisEvent* hce) override;
  G4bool ProcessHits(G4Step* step, G4TouchableHistory*) override;
  void EndOfEvent(G4HCofThisEvent*) override;

private:
  struct Accum {
    G4int planeID   = -1;
    G4int trackID   = -1;
    G4int parentID  = -1;
    G4int pdg       = 0;

    G4ThreeVector posEarliest;
    G4double      tEarliest = DBL_MAX;
    G4double      edepSum   = 0.0;
  };

  // Key: (planeID, trackID) packed into uint64
  static std::uint64_t MakeKey(G4int planeID, G4int trackID);

  HitCollection* fHits = nullptr;
  G4int fHCID = -1;

  std::unordered_map<std::uint64_t, Accum> fAccum;
};
