#include "PhysicsList.hh"

#include "G4PhysListFactory.hh"
#include "G4VModularPhysicsList.hh"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"

PhysicsList::PhysicsList()
{
  // Use a proven reference list
  G4PhysListFactory factory;
  auto* base = factory.GetReferencePhysList("FTFP_BERT");

  if (!base) {
    G4Exception("PhysicsList::PhysicsList", "PL001", FatalException,
                "Failed to create reference physics list FTFP_BERT");
  }

  // Copy modules from the reference list into *this*
  for (G4int i = 0; ; ++i) {
    auto* physics = base->GetPhysics(i);
    if (!physics) break;
    RegisterPhysics(physics);
  }

  // Cuts: keep small-ish; tune later
  SetDefaultCutValue(0.1 * mm);

  G4cout << "[PhysicsList] Using reference list: FTFP_BERT" << G4endl;
}
