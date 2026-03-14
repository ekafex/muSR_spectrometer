#pragma once

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class G4VPhysicalVolume;

class DetectorConstruction : public G4VUserDetectorConstruction {
public:
  DetectorConstruction() = default;
  ~DetectorConstruction() override = default;

  G4VPhysicalVolume* Construct() override;
  void ConstructSDandField() override;

private:
  void DefineMaterials();

  void PlacePlaneStack(G4LogicalVolume* worldLV,
                       G4LogicalVolume* planeLV,
                       G4int nPlanes,
                       G4double zFirst,
                       G4double dz,
		       G4int copyOffset);

  const G4String fPlaneLVName = "PlaneLV";
};
