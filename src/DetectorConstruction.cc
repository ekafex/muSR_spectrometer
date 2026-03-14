#include "DetectorConstruction.hh"
#include "Config.hh"

#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"

#include "SensitiveDetector.hh"
#include "G4SDManager.hh"
#include "G4LogicalVolumeStore.hh"


G4VPhysicalVolume* DetectorConstruction::Construct()
{
  DefineMaterials();

  auto& cfg = Config::Instance();
  auto* nist = G4NistManager::Instance();

  // --- Materials ---
  G4Material* worldMat  = nist->FindOrBuildMaterial("G4_AIR");
  G4Material* sampleMat = nist->FindOrBuildMaterial("G4_Cu");   // placeholder; change later
  G4Material* planeMat  = nist->FindOrBuildMaterial("G4_Si");

  // --- World ---
  auto* worldSolid = new G4Box("WorldSolid",
                               cfg.worldSize/2, cfg.worldSize/2, cfg.worldSize/2);

  auto* worldLV = new G4LogicalVolume(worldSolid, worldMat, "WorldLV");

  auto* worldPV = new G4PVPlacement(nullptr, {}, worldLV, "WorldPV",
                                    nullptr, false, 0, true);

  // --- Sample (centered at origin) ---
  auto* sampleSolid = new G4Box("SampleSolid",
                                cfg.sampleXY/2, cfg.sampleXY/2, cfg.sampleZ/2);

  auto* sampleLV = new G4LogicalVolume(sampleSolid, sampleMat, "SampleLV");

  new G4PVPlacement(nullptr, {0,0,0}, sampleLV, "SamplePV",
                    worldLV, false, 0, true);

  // --- Plane logical volume (reused for all planes) ---
  auto* planeSolid = new G4Box("PlaneSolid",
                               cfg.planeXY/2, cfg.planeXY/2, cfg.planeThickness/2);

  auto* planeLV = new G4LogicalVolume(planeSolid, planeMat, "PlaneLV");

  // z positions:
  // Sample spans [-sampleZ/2, +sampleZ/2]
  // Upstream planes: negative z side (beam coming from -z -> +z is typical)
  // First upstream plane is at z = -(sampleZ/2 + gapToSample + planeThickness/2)
  // Then further upstream by planeSpacing each
  const G4double zUpFirst =
      -(cfg.sampleZ/2 + cfg.gapToSample + cfg.planeThickness/2);

  // Downstream planes: positive z side
  const G4double zDownFirst =
      +(cfg.sampleZ/2 + cfg.gapToSample + cfg.planeThickness/2);

  PlacePlaneStack(worldLV, planeLV, cfg.nUp,   zUpFirst,   -cfg.planeSpacing, 0);
  PlacePlaneStack(worldLV, planeLV, cfg.nDown, zDownFirst, +cfg.planeSpacing, 100);
  

  // --- Visualization attributes (so you see something immediately) ---
  if (!cfg.showWorld) {
    worldLV->SetVisAttributes(G4VisAttributes::GetInvisible());
  } else {
    auto* worldVis = new G4VisAttributes(G4Colour(0.8, 0.8, 0.8));
    worldVis->SetForceWireframe(true);
    worldLV->SetVisAttributes(worldVis);
  }

  auto* sampleVis = new G4VisAttributes(G4Colour(0.2, 0.6, 1.0));
  sampleVis->SetForceSolid(true);
  sampleLV->SetVisAttributes(sampleVis);

  auto* planeVis = new G4VisAttributes(G4Colour(1.0, 0.6, 0.2));
  planeVis->SetForceSolid(true);
  planeLV->SetVisAttributes(planeVis);

  return worldPV;
}

void DetectorConstruction::DefineMaterials()
{
  // NIST manager builds what we need; keep this for future custom materials.
  G4NistManager::Instance();
}

void DetectorConstruction::PlacePlaneStack(G4LogicalVolume* worldLV,
                                           G4LogicalVolume* planeLV,
                                           G4int nPlanes,
                                           G4double zFirst,
                                           G4double dz,
                                           G4int copyOffset)
{
  for (G4int i = 0; i < nPlanes; ++i) {
    const G4double z = zFirst + i * dz;
    const G4int copyNo = copyOffset + i;

    new G4PVPlacement(nullptr, {0, 0, z},
                      planeLV,
                      "PlanePV",
                      worldLV,
                      false,
                      copyNo,
                      true);
  }
}


void DetectorConstruction::ConstructSDandField()
{
  // Find the plane logical volume by name
  auto* lv = G4LogicalVolumeStore::GetInstance()->GetVolume(fPlaneLVName, false);
  if (!lv) {
    G4Exception("DetectorConstruction::ConstructSDandField", "SD001", FatalException,
                "PlaneLV not found. Check the logical volume name.");
  }

  // Create + register SD
  auto* sdManager = G4SDManager::GetSDMpointer();

  // SD name and hits collection name
  auto* sd = new SensitiveDetector("PlaneSD", "PlaneHits");
  sdManager->AddNewDetector(sd);

  // Attach SD to plane logical volume
  SetSensitiveDetector(lv, sd);
}

