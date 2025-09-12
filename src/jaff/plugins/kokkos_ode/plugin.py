import os

def main(network, path_template, path_build=None):
    from jaff.preprocessor import Preprocessor

    p = Preprocessor()

    ## Generate C++ code using header-only integrators (VODE)

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
"""
    
    # Combine species indices with chemistry variables
    scommons = scommons + "\n" + chemistry_vars
    
    # Get reaction rates with C++ syntax and CSE optimization
    rates = network.get_rates(idx_offset=0, rate_variable="k", language="c++", use_cse=True)
    # Ensure we use standard <cmath> namespace, not Kokkos math wrappers
    rates = rates.replace("Kokkos::", "std::")
    
    # Generate symbolic ODE and analytical Jacobian
    sode, jacobian = network.get_symbolic_ode_and_jacobian(idx_offset=0, use_cse=True, language="c++")
    # Convert Jacobian indexing from J(i, j) (Kokkos view style) to J[i][j] (std::array style)
    # This keeps the network generator stable while adapting to header-only integrators API
    import re
    jacobian = re.sub(r"J\((\d+)\s*,\s*(\d+)\)", r"J[\1][\2]", jacobian)
    
    # Generate temperature variable definitions for C++
    # These variables are commonly used in chemistry rate expressions
    temp_vars = """// Temperature and environment variables used in chemical reactions
// T is expected to be passed as a parameter or computed from the state
const double tgas = DEFAULT_TEMPERATURE;
const double tdust = DEFAULT_TEMPERATURE;
const double av = DEFAULT_AV;  // Visual extinction
const double crate = DEFAULT_CRATE;  // Cosmic ray ionization rate
"""

    # Process template files
    num_species = str(network.get_number_of_species())
    num_reactions = str(len(network.reactions))
    
    # Generate proper C++ array declarations
    # When using CSE, we don't need the flux array
    num_reactions_decl = f"double k[{num_reactions}];"
    
    # Process all files with auto-detected comment styles
    p.preprocess(path_template,
                 ["chemistry_ode.hpp", "chemistry_ode.cpp", "CMakeLists.txt"],
                 [{"COMMONS": scommons, "RATES": rates, "ODE": sode, "JACOBIAN": jacobian,
                   "NUM_SPECIES": f"static constexpr int neqs = {num_species};",
                   "NUM_REACTIONS": num_reactions_decl, "TEMP_VARS": temp_vars},
                  {"COMMONS": scommons, "RATES": rates, "ODE": sode, "JACOBIAN": jacobian,
                   "NUM_SPECIES": f"static constexpr int neqs = {num_species};",
                   "NUM_REACTIONS": num_reactions, "TEMP_VARS": temp_vars},
                  {"NUM_SPECIES": num_species}],
                 comment="auto",
                 path_build=path_build)
