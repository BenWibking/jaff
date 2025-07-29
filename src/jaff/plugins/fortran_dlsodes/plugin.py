import os

def main(network, path_template):
    from jaff.preprocessor import Preprocessor

    p = Preprocessor()

    scommons = network.get_commons(idx_offset=1, definition_prefix="integer,parameter::")
    rates = network.get_rates()
    sflux = network.get_fluxes()
    sode = network.get_ode(idx_offset=1, brackets="()")

    p.preprocess(path_template,
                 ["commons.f90", "ode.f90"],
                 [{"COMMONS": scommons}, {"ODE": sode}],
                 comment="!!")

