import os

def main(network, path_template, path_build=None):
    from jaff.preprocessor import Preprocessor

    p = Preprocessor()

    # Generate C++ code for Kokkos
    # Get species indices and counts with C++ formatting
    scommons = network.get_commons(idx_offset=0, idx_prefix="", definition_prefix="static constexpr int ")
    # Add semicolons for C++ syntax
    scommons = '\n'.join([line + ';' if line.strip() and not line.strip().endswith(';') else line for line in scommons.split('\n')])
    
    # Add common chemistry variables that are used in rate expressions
    # These are typically parameters that should be passed in or computed
    chemistry_vars = """// Common chemistry variables used in rate expressions
// These should typically be passed as parameters or computed from the state
static constexpr double DEFAULT_TEMPERATURE = 300.0;  // Default gas temperature in K
static constexpr double DEFAULT_AV = 1.0;             // Default visual extinction
static constexpr double DEFAULT_CRATE = 1.3e-17;      // Default cosmic ray ionization rate

// Placeholder function for photorates (should be replaced with actual implementation)
template<typename T>
KOKKOS_INLINE_FUNCTION
static double photorates(int /*index*/, T /*energy*/, T /*max_energy*/) {
    // Placeholder: return 0 for photochemistry rates
    // In a real implementation, this would compute photo-dissociation/ionization rates
    return 0.0;
}"""
    
    # Combine species indices with chemistry variables
    scommons = scommons + "\n" + chemistry_vars
    
    # Get reaction rates with C++ syntax and CSE optimization
    rates = network.get_rates(idx_offset=0, rate_variable="k", language="c++", use_cse=True)
    
    # Get ODE fluxes and derivatives with C++ array access
    sflux = network.get_fluxes(idx_offset=0, rate_variable="k", species_variable="y", brackets="[]", idx_prefix="")
    
    # Generate symbolic ODE and analytical Jacobian
    sode_symbolic, jacobian = network.get_symbolic_ode_and_jacobian(idx_offset=0, use_cse=True, language="c++")
    
    # For backward compatibility, also generate the traditional ODE (without CSE)
    # This can be used if the symbolic version has issues
    sode_traditional = network.get_ode(idx_offset=0, flux_variable="flux", brackets="[]", species_variable="f", idx_prefix="", derivative_prefix="")
    
    # Fix spacing in traditional ODE expressions
    import re
    # Replace patterns like "- flux" or "+ flux" with proper spacing
    sode_traditional = re.sub(r'([+-])\s*flux', r'\1 flux', sode_traditional)
    # Also ensure space before operators that aren't at the start of the expression
    sode_traditional = re.sub(r'(\S)([+-])', r'\1 \2', sode_traditional)
    
    # Use the symbolic ODE by default
    sode = sode_symbolic
    
    # Generate temperature variable definitions for C++
    # These variables are commonly used in chemistry rate expressions
    temp_vars = """// Temperature and environment variables used in chemical reactions
// T is expected to be passed as a parameter or computed from the state
const double Tgas = DEFAULT_TEMPERATURE;  // Gas temperature (matches network conventions)
const double tgas = Tgas;  // Lowercase alias for compatibility

// Environmental parameters (should be passed in or use defaults)
const double av = DEFAULT_AV;  // Visual extinction
const double crate = DEFAULT_CRATE;  // Cosmic ray ionization rate

// Access to species densities (for compatibility with different conventions)
const auto& n = y;  // Species array alias"""
    
    # Process template files
    num_species = str(network.get_number_of_species())
    num_reactions = str(len(network.reactions))
    
    # Generate proper C++ array declarations
    # When using CSE, we don't need the flux array
    num_reactions_decl = f"double k[{num_reactions}];"
    
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
