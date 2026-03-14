#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4UIExecutive.hh"
#include "G4VisExecutive.hh"

#include "Randomize.hh"

// Your classes (create later)
#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"
//#include "PhysicsList.hh"
#include "G4PhysListFactory.hh"
#include "G4VModularPhysicsList.hh"

#include <memory>
#include <string>

int main(int argc, char** argv)
{
  // ------------------------------------------------------------
  // UI session: if no macro provided, start interactive UI (GUI)
  // ------------------------------------------------------------
  G4UIExecutive* ui = nullptr;
  if (argc == 1) {
    ui = new G4UIExecutive(argc, argv); // will choose Qt if available
  }

  // ------------------------------------------------------------
  // Run manager
  // ------------------------------------------------------------
  //auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Default);
  auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

  // ------------------------------------------------------------
  // Random engine/seed
  // ------------------------------------------------------------
  G4Random::setTheEngine(new CLHEP::RanecuEngine);
  // For reproducibility you can set a fixed seed:
  // G4Random::setTheSeed(123456);
  // Or keep it time-based:
  G4Random::setTheSeed(static_cast<long>(time(nullptr)));

  // ------------------------------------------------------------
  // Mandatory initialization classes (plug in later)
  // ------------------------------------------------------------
  runManager->SetUserInitialization(new DetectorConstruction());
  //runManager->SetUserInitialization(new PhysicsList());
  
  G4PhysListFactory factory;
  auto* phys = factory.GetReferencePhysList("FTFP_BERT");
  if (!phys) {
     G4Exception("main", "PL001", FatalException, "Failed to create FTFP_BERT");
   }
   runManager->SetUserInitialization(phys);

  runManager->SetUserInitialization(new ActionInitialization());


  // TEMPORARY: you can still compile and run, but it will do nothing useful
  // until you provide the classes above.

  // ------------------------------------------------------------
  // Initialize visualization
  // ------------------------------------------------------------
  auto visManager = std::make_unique<G4VisExecutive>();
  visManager->Initialize();

  // ------------------------------------------------------------
  // Macro handling
  // ------------------------------------------------------------
  auto* UImanager = G4UImanager::GetUIpointer();

  if (ui) {
    // Interactive mode: execute a default visualization macro
    // Put run_vis.mac in macros/ (copied to build dir by CMake)
    UImanager->ApplyCommand("/control/execute init_vis.mac");
    ui->SessionStart();
    delete ui;
  } else {
    // Batch mode: user supplies a macro file as first argument
    // Example: ./g4_vr_musr run_batch.mac
    G4String command = "/control/execute ";
    G4String fileName = argv[1];
    UImanager->ApplyCommand(command + fileName);
  }

  // Cleanup
  delete runManager;
  return 0;
}
