import numpy as np
import sys
import sympy

class Reaction:

    def __init__(self, reactants, products, rate, tmin, tmax):
        self.reactants = reactants
        self.products = products
        self.rate = rate
        self.tmin = tmin
        self.tmax = tmax
        self.reaction = None
        self.check()
        self.serialize()

    def is_same(self, other):
        return self.serialized == other.serialized

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