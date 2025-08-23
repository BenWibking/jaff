import os

def main(network, path_template, path_build=None):
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
    sflux = network.get_fluxes(idx_offset=0, rate_variable="k", species_variable="y", brackets="[]", idx_prefix="")
    sode = network.get_ode(idx_offset=0, flux_variable="flux", brackets="[]", species_variable="f", idx_prefix="", derivative_prefix="")
    
    # Fix spacing in ODE expressions
    import re
    # Replace patterns like "- flux" or "+ flux" with proper spacing
    sode = re.sub(r'([+-])\s*flux', r'\1 flux', sode)
    # Also ensure space before operators that aren't at the start of the expression
    sode = re.sub(r'(\S)([+-])', r'\1 \2', sode)
    
    # Get jacobian if possible (we'll need to implement this in the template)
    # For now, we'll pass empty jacobian and let the template handle numerical jacobian
    jacobian = ""  # Placeholder for analytical jacobian
    
    # Generate temperature variable definitions for C++
    temp_vars = """// Temperature variables used in chemical reactions
const double Tgas = T;  // Gas temperature (matches KROME convention)
const double Te = T * 8.617343e-5;  // Temperature in eV (matches KROME convention)
const double invTe = 1.0 / Te;  // Inverse temperature in eV (matches KROME convention)
const double invT = 1.0 / T;  // Inverse temperature in K (matches KROME convention)
const double T32 = T / 32.0;  // Temperature divided by 32 (matches KROME convention)
const double invT32 = 32.0 / T;  // 32 divided by temperature (matches KROME convention)
const double sqrTgas = Kokkos::sqrt(T);  // Square root of temperature (matches KROME convention)
const double lnTe = Kokkos::log(Te);  // Log of temperature in eV (matches KROME convention)

// Essential lowercase aliases that are actually used in expressions
const double tgas = Tgas;  // Lowercase alias for temperature

// Function parameter for accessing species densities
const auto& n = y;  // Access to species array

// Additional chemistry variables (these would typically come from the simulation)
const double av = 1.0;  // Visual extinction
const double crate = 1.3e-17;  // Cosmic ray ionization rate
const double user_av = av;  // User-defined extinction (lowercase)
const double user_Av = av;  // User-defined extinction (KROME case)
const double user_tdust = T;  // Dust temperature (lowercase)
const double user_Tdust = T;  // Dust temperature (KROME case)

// Additional variables that may be referenced in KROME expressions
const double user_H2self = 1.0;  // H2 self-shielding factor (placeholder)
const double HnOj = 1.0;  // H_n O+ rate factor (placeholder)
const double Hnuclei = 1.0;  // Total hydrogen nuclei density (placeholder)
const double fA = 1.0;  // Dust formation efficiency factor (placeholder)
const double ntot = 1.0;  // Total number density (placeholder)
const double invTgas = 1.0/T;  // Inverse gas temperature alias
const double logT = 10.0;  // log10(Tgas) placeholder
const double invsqrT = 1.0/Kokkos::sqrt(T);  // 1/sqrt(Tgas) alias

// Placeholder functions for KROME expressions
// These should be properly implemented in a real chemistry solver
auto get_hnuclei = [](const auto& /*y*/) -> double { 
    return 1.0;  // Total hydrogen nuclei density placeholder
};"""
    
    # Process template files
    num_species = str(network.get_number_of_species())
    num_reactions = str(len(network.reactions))
    
    # Generate proper C++ array declarations
    num_reactions_decl = f"double k[{num_reactions}];\ndouble flux[{num_reactions}];"
    
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
                 comment="auto",
                 path_build=path_build)
