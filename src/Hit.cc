#include "Hit.hh"

#include "G4Allocator.hh"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"

G4ThreadLocal G4Allocator<Hit>* HitAllocator = nullptr;

void* Hit::operator new(size_t)
{
  if (!HitAllocator) HitAllocator = new G4Allocator<Hit>;
  return (void*)HitAllocator->MallocSingle();
}

void Hit::operator delete(void* hit)
{
  HitAllocator->FreeSingle((Hit*)hit);
}

void Hit::Print()
{
  G4cout
    << "Hit: planeID=" << planeID
    << " pdg=" << pdg
    << " trackID=" << trackID
    << " parentID=" << parentID
    << " pos=(" << pos.x()/mm << "," << pos.y()/mm << "," << pos.z()/mm << ") mm"
    << " t=" << time/ns << " ns"
    << " edep=" << edep/keV << " keV"
    << G4endl;
}
