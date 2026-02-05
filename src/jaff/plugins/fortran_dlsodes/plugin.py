from jaff import Codegen, Preprocessor


def main(network, path_template, path_build=None):
    p = Preprocessor()
    cg = Codegen(network=network, lang="fortran")

    scommons = cg.get_commons(idx_offset=1, definition_prefix="integer,parameter::")
    rates = cg.get_rates()
    sflux = cg.get_fluxes()
    sode = cg.get_ode(derivative_var="dn")

    p.preprocess(
        path_template,
        ["commons.f90", "ode.f90", "fluxes.f90", "reactions.f90"],
        [{"COMMONS": scommons}, {"ODE": sode}, {"FLUXES": sflux}, {"REACTIONS": rates}],
        comment="!!",
        path_build=path_build,
    )
