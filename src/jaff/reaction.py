import numpy as np
import sys
import sympy

class Reaction:

    def __init__(self, reactants, products, rate, tmin, tmax, original_string, errors=False):
        self.reactants = reactants
        self.products = products
        self.rate = rate
        self.tmin = tmin
        self.tmax = tmax
        self.reaction = None
        self.xsecs = None  # dictionary {"energy": [], "xsecs": []}, energy in erg, xsecs in cm^2
        self.original_string = original_string

        self.check(errors)
        self.serialized_exploded = self.serialize_exploded()
        self.serialized = self.serialize()

    def guess_type(self):
        from sympy import symbols

        rtype = "unknown"

        if type(self.rate) is str:
            if "photo" in self.rate:
                rtype = "photo"
        else:
            if self.rate.has(symbols('crate')):
                rtype = "cosmic_ray"
            elif self.rate.has(symbols('av')):
                rtype = "photo_av"
            elif self.rate.has(symbols('ntot')):
                rtype = "3_body"

        return rtype

    def is_same(self, other):
        return self.serialized == other.serialized

    def is_isomer_version(self, other):
        # compare serialized forms (ignore isomers)
        is_same_serialized = self.serialized_exploded == other.serialized_exploded

        # compare actual species names (consider isomers)
        rp1 = sorted([x.name for x in self.reactants + self.products])
        rp2 = sorted([x.name for x in other.reactants + other.products])
        has_different_species_names = rp1 != rp2

        return is_same_serialized and has_different_species_names

    # ****************
    # note that the serialized form uses the exploded form of species names
    # H2O+ will be serialzed as +/H/H/O, hence this will be identical to OH2+
    def serialize_exploded(self):
        sr = "_".join(sorted([x.serialized for x in self.reactants]))
        sp = "_".join(sorted([x.serialized for x in self.products]))
        return sr + "__" + sp

    # ****************
    # this version uses the names and not the exploded forms of the species
    def serialize(self):
        # serialize the reaction in the form R__P_P
        sr = "_".join(sorted([x.name for x in self.reactants]))
        sp = "_".join(sorted([x.name for x in self.products]))
        return sr + "__" + sp


    def check(self, errors):
        if not self.check_mass():
            print("WARNING: Mass not conserved in reaction: " + self.get_verbatim())
            if errors:
                sys.exit(1)
        if not self.check_charge():
            print("WARNING: Charge not conserved in reaction: " + self.get_verbatim())
            if errors:
                sys.exit(1)

    def check_mass(self):
        return (np.sum([x.mass for x in self.reactants]) - np.sum([x.mass for x in self.products])) < 9.1093837e-28

    def check_charge(self):
        return (np.sum([x.charge for x in self.reactants]) - np.sum([x.charge for x in self.products])) == 0

    def get_verbatim(self):
        return " + ".join([x.name for x in self.reactants]) + " -> " + \
               " + ".join([x.name for x in self.products])

    def get_latex(self):
        latex = " + ".join([x.latex for x in self.reactants]) + "\\,\\to\\," + \
               " + ".join([x.latex for x in self.products])
        return "$" + latex + "$"

    def has_any_species(self, species):
        if type(species) is str:
            species = [species]
        return any([x.name in species for x in self.reactants + self.products])

    def has_reactant(self, species):
        if type(species) is str:
            species = [species]
        return any([x.name in species for x in self.reactants])

    def has_product(self, species):
        if type(species) is str:
            species = [species]
        return any([x.name in species for x in self.products])

    def get_python(self):
        return str(self.rate)

    def get_c(self):
        return sympy.ccode(self.rate,strict=False)

    def get_f90(self):
        return sympy.fcode(self.rate,strict=False)

    def get_sympy(self):
        return sympy.sympify(self.rate)

    def plot(self, ax=None):
        import matplotlib.pyplot as plt
        import numpy as np

        tgas = np.linspace(self.tmin, self.tmax, 100)
        r = sympy.lambdify('tgas', self.rate, 'numpy')
        y = r(tgas)

        if ax is None:
            _, ax = plt.subplots()

        ax.plot(tgas, y)
        ax.set_xlabel('Temperature (K)')
        ax.set_ylabel('Rate')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_title(self.get_latex())
        ax.grid()

        if ax is None:
            plt.show()

    def plot_xsecs(self, ax=None, energy_unit='eV', energy_log=True, xsecs_log=True):
        import matplotlib.pyplot as plt
        import numpy as np

        if self.xsecs is None:
            print("No cross sections available for this reaction.")
            return

        if ax is None:
            _, ax = plt.subplots()

        clight = 2.99792458e10  # cm/s
        hplanck = 6.62607015e-27  # erg s

        if energy_unit == 'eV':
            energies = np.array(self.xsecs['energy']) / 1.60218e-12
            xlabel = 'Energy (eV)'
        elif energy_unit == 'erg':
            energies = np.array(self.xsecs['energy'])
            xlabel = 'Energy (erg)'
        elif energy_unit == 'nm':
            energies = clight * hplanck * 1e7 / np.array(self.xsecs['energy'])
            xlabel = 'Wavelength (nm)'
        elif energy_unit in ['um', 'micron']:
            energies = clight * hplanck * 1e4 / np.array(self.xsecs['energy'])
            xlabel = 'Wavelength (µm)'
        else:
            print("ERROR: Unknown energy unit '%s'" % energy_unit)
            sys.exit(1)

        xsecs = np.array(self.xsecs['xsecs'])

        ax.plot(energies, xsecs)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Cross section (cm^2)')
        if energy_log:
            ax.set_xscale('log')
        if xsecs_log:
            ax.set_yscale('log')
        ax.set_title(self.get_latex())
        ax.grid()

        if ax is None:
            plt.show()

