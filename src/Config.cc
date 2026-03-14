#include "Config.hh"

Config& Config::Instance() {
  static Config cfg;
  return cfg;
}
