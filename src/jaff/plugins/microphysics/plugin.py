import os
import re

from jaff.network import Network
from jaff.preprocessor import Preprocessor


def main(
    network: Network,
    path_template: os.PathLike,
    path_build: os.PathLike | None = None,
) -> None:
    filenames = ["actual_network.H", "actual_network_data.cpp", "actual_rhs.H"]
    pp = Preprocessor()

    scommons: str = network.get_commons(
        idx_offset=0, idx_prefix="", definition_prefix="static const int "
    ).replace("\n", ";\n")

    rates: str = (
        network.get_rates(
            idx_offset=1, rate_variable="ydot", language="c++", use_cse=True
        )
        .replace("Kokkos::", "std::")
        .replace("const double", "const amrex::Real")
    )

    rates = re.sub(r"ydot\[(\d+)\]", r"ydot(\1)", rates)
    # print("\n===================================================\n")
    # print(f"Rates:\n\n{rates}")
    # print("\n===================================================\n")

    sode, jac = network.get_symbolic_ode_and_jacobian(
        idx_offset=1, use_cse=True, language="c++"
    )

    sode = re.sub(r"f\[\s*(\d+)\s*\]", r"ydot(\1)", sode).replace(
        "const double", "static const amrex::Real"
    )

    jac = re.sub(r"J\(\s*(\d+)\s*,\s*(\d+)\s*\)", r"jac(\1, \2)", jac).replace(
        "const double", "static const amrex::Real"
    )

    num_spec: int = network.get_number_of_species()
    num_react: int = len(network.reactions)

    num_reaction_cxx_decl: str = f"std::vector<double> nreact({num_react})"

    pp_sub = [
        {"COMMONS": scommons, "RATES": rates, "ODE": sode, "JACOBIAN": jac},
        {"NUM_SPECIES": num_spec},
        {
            "COMMONS": scommons,
            "RATES": rates,
            "ODE": sode,
            "JACOBIAN": jac,
            "NUM_SPECIES": f"static constexpr int nspec = {num_spec};",
            "NUM_REACTIONS": num_react,
        },
    ]

    pp.preprocess(path_template, filenames, pp_sub, comment="//", path_build=path_build)


if __name__ == "__main__":
    from jaff.builder import Builder

    # network = Network("../../../../tests/fixtures/sample_krome.dat")
    network = Network("../../../../networks/GOW.dat")
    print("\n===================================================\n")
    print("Reactions: \n")
    print([rea.rate for rea in network.reactions])
    print("\n===================================================\n")

    print("\n===================================================\n")
    print(f"Network loaded: {network.label}")
    print(f"Number of species: {network.get_number_of_species()}")
    print(f"Number of reactions: {len(network.reactions)}")
    print("\n===================================================\n")

    # Create builder and generate Kokkos C++ code
    builder = Builder(network)
    builds_dir = builder.build(template="microphysics")

    print("\n===================================================\n")
    print("\nC++ Microphysics generated successfully!")
    print(f"Generated files are located at {builds_dir}")
    print("\n===================================================\n")
