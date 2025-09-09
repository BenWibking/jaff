import os
import shutil


def main(network, path_template, path_build=None):
    """Generate Python (solve_ivp) sources using the plugin API.

    New API: accept `path_build` as the output destination.
    Preprocesses templates into JAFF's internal build directory,
    then copies results to `path_build` if provided.
    """
    # Import the preprocessor module to get its internal build path
    from jaff import preprocessor as preprocessor_module

    p = preprocessor_module.Preprocessor()

    # Internal build directory used by the preprocessor
    internal_build_dir = os.path.join(os.path.dirname(preprocessor_module.__file__), "builds")

    # Ensure a clean internal build directory
    if os.path.isdir(internal_build_dir):
        for fname in os.listdir(internal_build_dir):
            try:
                os.remove(os.path.join(internal_build_dir, fname))
            except IsADirectoryError:
                shutil.rmtree(os.path.join(internal_build_dir, fname))
    else:
        os.makedirs(internal_build_dir, exist_ok=True)

    scommons = network.get_commons()
    rates = network.get_rates()
    sflux = network.get_fluxes()
    sode = network.get_ode()

    p.preprocess(
        path_template,
        ["commons.py", "rates.py", "fluxes.py", "ode.py"],
        [
            {"COMMONS": scommons},
            {"RATES": rates},
            {"FLUXES": sflux},
            {"ODE": sode},
        ],
        comment="#",
    )

    # Copy generated files to the requested build directory
    if path_build is not None:
        os.makedirs(path_build, exist_ok=True)
        for fname in os.listdir(internal_build_dir):
            src = os.path.join(internal_build_dir, fname)
            dst = os.path.join(path_build, fname)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copyfile(src, dst)
