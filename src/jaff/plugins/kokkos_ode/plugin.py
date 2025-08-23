import os

def main(network, path_template):
    from jaff.preprocessor import Preprocessor

    p = Preprocessor()

    # Generate C++ code for Kokkos
    # Get species indices and counts with C++ formatting
    scommons = network.get_commons(idx_offset=0, idx_prefix="", definition_prefix="static constexpr int ")
    # Add semicolons for C++ syntax
    scommons = '\n'.join([line + ';' if line.strip() and not line.strip().endswith(';') else line for line in scommons.split('\n')])
    
    # Get reaction rates with C++ syntax
    rates = network.get_rates(idx_offset=0, rate_variable="k", language="c++")
    
    # Get ODE fluxes and derivatives with C++ array access
    sflux = network.get_fluxes(idx_offset=0, rate_variable="k", species_variable="y", brackets="()", idx_prefix="")
    sode = network.get_ode(idx_offset=0, flux_variable="flux", brackets="()", species_variable="dydt", idx_prefix="")
    
    # Get jacobian if possible (we'll need to implement this in the template)
    # For now, we'll pass empty jacobian and let the template handle numerical jacobian
    jacobian = ""  # Placeholder for analytical jacobian
    
    # Generate temperature variable definitions for C++
    temp_vars = """// Temperature variables used in chemical reactions
        const double tgas = T;  // Gas temperature
        const double te = T * 8.617343e-5;  // Temperature in eV
        const double invte = 1.0 / te;  // Inverse temperature in eV
        const double invt = 1.0 / T;  // Inverse temperature in K
        const double t32 = T / 32.0;  // Temperature divided by 32
        const double invt32 = 32.0 / T;  // 32 divided by temperature
        const double sqrtgas = Kokkos::sqrt(T);  // Square root of temperature
        const double lnte = Kokkos::log(te);  // Log of temperature in eV
        
        // Additional chemistry variables (these would typically come from the simulation)
        const double av = 1.0;  // Visual extinction
        const double crate = 1.3e-17;  // Cosmic ray ionization rate
        const double user_av = av;  // User-defined extinction
        const double user_tdust = T;  // Dust temperature
        
        // Placeholder functions and variables for complex expressions
        // These should be properly implemented in a real chemistry solver
        // const double ntot = ...;  // Total number density"""
    
    # Process template files
    num_species = str(network.get_number_of_species())
    num_reactions = str(len(network.reactions))
    
    # Generate proper C++ array declarations
    num_reactions_decl = f"double k[{num_reactions}];\n        double flux[{num_reactions}];"
    
    # Process all files with auto-detected comment styles
    p.preprocess(path_template,
                 ["chemistry_ode.hpp", "chemistry_ode.cpp", "CMakeLists.txt"],
                 [{"COMMONS": scommons, "RATES": rates, "FLUXES": sflux, "ODE": sode, "JACOBIAN": jacobian,
                   "NUM_SPECIES": f"static constexpr int neqs = {num_species};",
                   "NUM_REACTIONS": num_reactions_decl, "TEMP_VARS": temp_vars},
                  {"COMMONS": scommons, "RATES": rates, "FLUXES": sflux, "ODE": sode, "JACOBIAN": jacobian,
                   "NUM_SPECIES": f"static constexpr int neqs = {num_species};",
                   "NUM_REACTIONS": num_reactions, "TEMP_VARS": temp_vars},
                  {"NUM_SPECIES": num_species}],
                 comment="auto")
