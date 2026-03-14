#pragma once

#include "G4VHit.hh"
#include "G4THitsCollection.hh"
#include "G4ThreeVector.hh"
#include "globals.hh"

class Hit : public G4VHit {
public:
  Hit() = default;
  ~Hit() override = default;

  // --- payload ---
  G4int planeID   = -1;    // copyNo of plane
  G4int trackID   = -1;
  G4int parentID  = -1;
  G4int pdg       = 0;

  G4ThreeVector pos;       // global position at step point
  G4double      time = 0;  // global time
  G4double      edep = 0;  // energy deposit in this step

  // --- required by Geant4 hit model ---
  void* operator new(size_t);
  void  operator delete(void*);
  void Draw() override {}
  void Print() override;
};

using HitCollection = G4THitsCollection<Hit>;
extern G4ThreadLocal G4Allocator<Hit>* HitAllocator;
