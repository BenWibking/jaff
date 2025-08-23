import os

def main(network, path_template):
    from jaff.preprocessor import Preprocessor

    p = Preprocessor()

    # Generate C++ code for Kokkos
    # Get species indices and counts with C++ formatting
    scommons = network.get_commons(idx_offset=0, idx_prefix="idx_", definition_prefix="static constexpr int ")
    
    # Get reaction rates with C++ syntax
    rates = network.get_rates(idx_offset=0, rate_variable="k", language="c++")
    
    # Get ODE fluxes and derivatives with C++ array access
    sflux = network.get_fluxes(idx_offset=0, rate_variable="k", species_variable="y", brackets="()", idx_prefix="")
    sode = network.get_ode(idx_offset=0, flux_variable="flux", brackets="()", species_variable="dydt", idx_prefix="")
    
    # Get jacobian if possible (we'll need to implement this in the template)
    # For now, we'll pass empty jacobian and let the template handle numerical jacobian
    jacobian = ""  # Placeholder for analytical jacobian
    
    # Process template files
    num_species = str(network.get_number_of_species())
    num_reactions = str(len(network.reactions))
    
    # Process C++ files with C++ comments
    p.preprocess(path_template,
                 ["chemistry_ode.hpp", "chemistry_ode.cpp"],
                 [{"COMMONS": scommons, "RATES": rates, "FLUXES": sflux, "ODE": sode, "JACOBIAN": jacobian,
                   "NUM_SPECIES": f"static constexpr int neqs = {num_species};",
                   "NUM_REACTIONS": num_reactions},
                  {"COMMONS": scommons, "RATES": rates, "FLUXES": sflux, "ODE": sode, "JACOBIAN": jacobian,
                   "NUM_SPECIES": f"static constexpr int neqs = {num_species};",
                   "NUM_REACTIONS": num_reactions},
                  {"NUM_SPECIES": num_species}],
                 comment="//")
    
    # Process CMake file with CMake comments
    p.preprocess(path_template,
                 ["CMakeLists.txt"],
                 [{"NUM_SPECIES": num_species}],
                 comment="#")
