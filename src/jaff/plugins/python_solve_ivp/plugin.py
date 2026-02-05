from jaff import Codegen


def main(network, path_template, path_build=None):
    from jaff.preprocessor import Preprocessor

    p = Preprocessor()
    cg = Codegen(network=network, lang="python")

    scommons = cg.get_commons()
    rates = cg.get_rates()
    sflux = cg.get_fluxes()
    sode = cg.get_ode()

    p.preprocess(
        path_template,
        ["commons.py", "rates.py", "fluxes.py", "ode.py"],
        [{"COMMONS": scommons}, {"RATES": rates}, {"FLUXES": sflux}, {"ODE": sode}],
        comment="#",
        path_build=path_build,
    )


if __name__ == "__main__":
    from jaff import Builder, Network

    net = Network("networks/test.dat")
    builder = Builder(net)
    builds_dir = builder.build(template="python_solve_ivp")
