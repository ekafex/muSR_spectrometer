cmake_minimum_required(VERSION 3.16...3.27)

project(g4_vr_musr LANGUAGES C CXX)

# ------------------------------------------------------------
# Options
# ------------------------------------------------------------
option(BUILD_WITH_GEANT4_UIVIS "Build with Geant4 UI and visualization drivers" ON)

# ------------------------------------------------------------
# Geant4 package
# ------------------------------------------------------------
if(BUILD_WITH_GEANT4_UIVIS)
  find_package(Geant4 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 REQUIRED)
endif()

include(${Geant4_USE_FILE})

# ------------------------------------------------------------
# C++ standard
# ------------------------------------------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ------------------------------------------------------------
# Sources
# ------------------------------------------------------------
set(APP_SOURCES
  app/main.cc
  src/Config.cc
  src/DetectorConstruction.cc
  src/PrimaryGeneratorAction.cc
  src/ActionInitialization.cc
  src/RunAction.cc
  src/EventAction.cc
  src/Hit.cc
  src/SensitiveDetector.cc
  src/SteppingAction.cc
)

# You will add these once you create them:
# file(GLOB PROJECT_HEADERS ${PROJECT_SOURCE_DIR}/include/*.hh)
# file(GLOB PROJECT_SOURCES ${PROJECT_SOURCE_DIR}/src/*.cc)

include_directories(${PROJECT_SOURCE_DIR}/include)

add_executable(g4_vr_musr
  ${APP_SOURCES}
  ${PROJECT_SOURCES}
)

target_link_libraries(g4_vr_musr PRIVATE ${Geant4_LIBRARIES})
target_include_directories(g4_vr_musr PRIVATE ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(g4_vr_musr PRIVATE ${Geant4_LIBRARIES})

# ------------------------------------------------------------
# Copy macros to build dir for convenience
# ------------------------------------------------------------
file(GLOB MACRO_FILES "${PROJECT_SOURCE_DIR}/macros/*.mac")
foreach(_macro ${MACRO_FILES})
  configure_file(${_macro} ${PROJECT_BINARY_DIR} COPYONLY)
endforeach()

# ------------------------------------------------------------
# Install
# ------------------------------------------------------------
install(TARGETS g4_vr_musr DESTINATION bin)
