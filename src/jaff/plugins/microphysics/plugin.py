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
    charge_cons = "0.0"

    sode, jac = network.get_symbolic_ode_and_jacobian(
        idx_offset=1, use_cse=True, language="c++"
    )
    sode = re.sub(r"f\[\s*(\d+)\s*\]", r"ydot(\1)", sode).replace(
        "const double", "static const amrex::Real"
    )
    sode = re.sub(r"nden\[\s*(\d+)\s*\]", r"nden(\1)", sode)
    jac = re.sub(r"J\(\s*(\d+)\s*,\s*(\d+)\s*\)", r"jac(\1, \2)", jac).replace(
        "const double", "static const amrex::Real"
    )
    jac = re.sub(r"nden\[\s*(\d+)\s*\]", r"nden(\1)", jac)

    for i, specie in enumerate(network.species):
        if not int(specie.charge):
            continue

        if specie.name == "e-":
            charge_cons = f"state.xn[{i}] = {charge_cons}"
            continue

        if abs(float(specie.charge)) > 1:
            charge_cons += f" + ({float(specie.charge)}) * state.xn[{i}]"
            continue

        charge_cons += f" + state.xn[{i}]"

    charge_cons += ";"

    pp_sub = [
        {},
        {"CHARGE": charge_cons},
        {
            "ODE": sode,
            "JACOBIAN": jac,
        },
    ]

    pp.preprocess(path_template, filenames, pp_sub, comment="//", path_build=path_build)


if __name__ == "__main__":
    from jaff.builder import Builder

    network = Network("../../../../networks/test.dat")
    builder = Builder(network)
    builds_dir = builder.build(template="microphysics")
