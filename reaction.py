import numpy as np
import sys
import sympy

class Reaction:

    def __init__(self, reactants, products, rate, tmin, tmax, original_string):
        self.reactants = reactants
        self.products = products
        self.rate = rate
        self.tmin = tmin
        self.tmax = tmax
        self.reaction = None
        self.original_string = original_string

        self.check()
        self.serialize()

    def guess_type(self):
        from sympy import symbols

        rtype = "unknown"
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
        is_same_serialized = self.serialized == other.serialized

        # compare actual species names (consider isomers)
        rp1 = sorted([x.name for x in self.reactants + self.products])
        rp2 = sorted([x.name for x in other.reactants + other.products])
        has_different_species_names = rp1 != rp2

        return is_same_serialized and has_different_species_names

    def serialize(self):
        sr = "_".join(sorted([x.serialized for x in self.reactants]))
        sp = "_".join(sorted([x.serialized for x in self.products]))
        self.serialized = sr + "__" + sp
        return self.serialized

    def check(self):
        if not self.check_mass():
            print("Mass not conserved in reaction: " + self.get_verbatim())
            sys.exit(1)
        if not self.check_charge():
            print("Charge not conserved in reaction: " + self.get_verbatim())
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
        return sympy.ccode(self.rate)

    def get_f90(self):
        return sympy.fcode(self.rate)

    def plot(self, ax=None):
        import matplotlib.pyplot as plt
        import numpy as np

        t = np.linspace(self.tmin, self.tmax, 100)
        r = sympy.lambdify('t', self.rate, 'numpy')
        y = r(t)

        if ax is None:
            _, ax = plt.subplots()

        ax.plot(t, y)
        ax.set_xlabel('Temperature (K)')
        ax.set_ylabel('Rate')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_title(self.get_verbatim())
        ax.grid()

        if ax is None:
            plt.show()