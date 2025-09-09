import os
import shutil


def main(network, path_template, path_build=None):
    """Generate Fortran (DLSODES) sources using the plugin API.

    New API: accept `path_build` as destination for generated files.
    This function preprocesses templates into JAFF's internal build
    directory, then copies results into `path_build` when provided.
    """
    # Import the preprocessor module to discover its internal build path
    from jaff import preprocessor as preprocessor_module

    p = preprocessor_module.Preprocessor()

    # Compute preprocessor's internal build directory
    internal_build_dir = os.path.join(os.path.dirname(preprocessor_module.__file__), "builds")

    # Ensure the internal build directory is clean
    if os.path.isdir(internal_build_dir):
        for fname in os.listdir(internal_build_dir):
            try:
                os.remove(os.path.join(internal_build_dir, fname))
            except IsADirectoryError:
                shutil.rmtree(os.path.join(internal_build_dir, fname))
    else:
        os.makedirs(internal_build_dir, exist_ok=True)

    scommons = network.get_commons(idx_offset=1, definition_prefix="integer,parameter::")
    rates = network.get_rates(language="f90")
    sflux = network.get_fluxes(language="f90")
    sode = network.get_ode(derivative_variable="dn", language="f90")

    p.preprocess(
        path_template,
        ["commons.f90", "ode.f90", "fluxes.f90", "reactions.f90"],
        [
            {"COMMONS": scommons},
            {"ODE": sode},
            {"FLUXES": sflux},
            {"REACTIONS": rates},
        ],
        comment="!!",
    )

    # If a destination build directory is provided, copy outputs there
    if path_build is not None:
        os.makedirs(path_build, exist_ok=True)
        for fname in os.listdir(internal_build_dir):
            src = os.path.join(internal_build_dir, fname)
            dst = os.path.join(path_build, fname)
            if os.path.isdir(src):
                # Mirror any subdirectories if they exist
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copyfile(src, dst)
