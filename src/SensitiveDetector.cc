#include "SensitiveDetector.hh"
#include "Hit.hh"

#include "G4HCofThisEvent.hh"
#include "G4SDManager.hh"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4Track.hh"
#include "G4VTouchable.hh"

#include <limits>

SensitiveDetector::SensitiveDetector(const G4String& name,
                                     const G4String& hitsCollectionName)
  : G4VSensitiveDetector(name)
{
  collectionName.insert(hitsCollectionName);
}

std::uint64_t SensitiveDetector::MakeKey(G4int planeID, G4int trackID)
{
  // pack two signed 32-bit ints into a 64-bit key
  const std::uint32_t a = static_cast<std::uint32_t>(planeID);
  const std::uint32_t b = static_cast<std::uint32_t>(trackID);
  return (static_cast<std::uint64_t>(a) << 32) | static_cast<std::uint64_t>(b);
}

void SensitiveDetector::Initialize(G4HCofThisEvent* hce)
{
  fHits = new HitCollection(SensitiveDetectorName, collectionName[0]);

  if (fHCID < 0) {
    fHCID = G4SDManager::GetSDMpointer()->GetCollectionID(fHits);
  }

  hce->AddHitsCollection(fHCID, fHits);

  // reset accumulator for this event
  fAccum.clear();
}

G4bool SensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*)
{
  auto* pre = step->GetPreStepPoint();
  auto* trk = step->GetTrack();

  // Identify plane
  const auto* touch = pre->GetTouchable();
  const G4int planeID = touch->GetCopyNumber();

  const G4int trackID  = trk->GetTrackID();
  const auto key = MakeKey(planeID, trackID);

  auto& a = fAccum[key]; // creates if missing

  // Fill static ids once (or overwrite with same values)
  a.planeID  = planeID;
  a.trackID  = trackID;
  a.parentID = trk->GetParentID();
  a.pdg      = trk->GetDefinition()->GetPDGEncoding();

  // Accumulate energy deposit (can be 0 for pure traversal; keep anyway)
  a.edepSum += step->GetTotalEnergyDeposit();

  // Keep earliest time and corresponding position
  const auto t = pre->GetGlobalTime();
  if (t < a.tEarliest) {
    a.tEarliest   = t;
    a.posEarliest = pre->GetPosition();
  }

  return true;
}

void SensitiveDetector::EndOfEvent(G4HCofThisEvent*)
{
  // Convert accumulators into one Hit per (plane, track)
  for (const auto& kv : fAccum) {
    const auto& a = kv.second;

    auto* hit = new ::Hit;
    hit->planeID  = a.planeID;
    hit->trackID  = a.trackID;
    hit->parentID = a.parentID;
    hit->pdg      = a.pdg;

    hit->pos  = a.posEarliest;
    hit->time = a.tEarliest;
    hit->edep = a.edepSum;

    fHits->insert(hit);
  }
}
