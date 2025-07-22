from reaction import Reaction
from species import Species
import numpy as np
import sys
from sympy import parse_expr, symbols


class Network:

    # ****************
    def __init__(self, fname):
        self.mass_dict = self.load_mass_dict("data/atom_mass.dat")
        self.species = []
        self.species_dict = {}
        self.reactions_dict = {}
        self.reactions = []
        self.rlist = self.plist = None
        self.variables_f90 = None

        self.load_network(fname)

        self.check_sink_sources()
        self.check_recombinations()
        self.check_isomers()

        self.generate_ode()
        self.generate_reactions_dict()

        print("All done!")

    # ****************
    @staticmethod
    def load_mass_dict(fname):
        mass_dict = {}
        for row in open(fname):
            srow = row.strip()
            if srow == "":
                continue
            if srow[0] == "#":
                continue
            rr = srow.split()
            mass_dict[rr[0]] = float(rr[1])
        return mass_dict

    # ****************
    def load_network(self, fname):

        default_species = [] # ["dummy", "CR", "CRP", "Photon"]
        self.species = [Species(s, self.mass_dict, i) for i, s in enumerate(default_species)]
        self.species_dict = {s.name: s.index for s in self.species}
        species_names = [x for x in default_species]

        variables = ""

        in_variables = False

        for row in open(fname):
            srow = row.strip()
            if srow == "":
                continue
            if srow[0] == "#":
                continue

            # check for variables
            if srow.startswith("VARIABLES{"):
                in_variables = True
                continue
            if srow.startswith("}") and in_variables:
                in_variables = False
                continue

            # store variables as a single string, it will be processed later
            if in_variables:
                variables += srow + ";"
                continue

            # determine the type of reaction line and parse it
            if "->" in srow:
                rr, pp, tmin, tmax, rate = self.line_prizmo(srow)
            elif ":" in srow:
                rr, pp, tmin, tmax, rate = self.line_udfa(srow)
            else:
                rr, pp, tmin, tmax, rate = self.line_kida(srow)

            # parse with sympy
            rate = parse_expr(rate, evaluate=False)

            for s in rr + pp:
                if s not in species_names:
                    species_names.append(s)
                    self.species.append(Species(s, self.mass_dict, len(species_names)-1))
                    self.species_dict[s] = self.species[-1].index

            rr = [self.species[species_names.index(x)] for x in rr]
            pp = [self.species[species_names.index(x)] for x in pp]

            rea = Reaction(rr, pp, rate, tmin, tmax)
            self.reactions.append(rea)

        # store rate variables for the f90 preprocessor
        self.variables_f90 = variables

        print("Loaded %d reactions" % len(self.reactions))

    # ****************
    def line_prizmo(self, line):

        srow = line.strip()

        # temperature ranges
        arow = srow.replace("[", "]").split("]")
        reaction, tlims, rate = [x.strip() for x in arow]

        if tlims.replace(" ", "") == "":
            tmin = None
            tmax = None
        else:
            tmin = float(tlims.split(",")[0])
            tmax = float(tlims.split(",")[1])

        reaction = reaction.replace("HE", "He")
        reaction = reaction.replace(" E", " e-")
        reaction = reaction.replace("E ", "e- ")
        reaction = reaction.replace("GRAIN0", "GRAIN")

        rate = rate.replace("user_crflux", "crate")
        rate = rate.replace("user_av", "av")
        if "user_" in rate:
            print(srow)
            print("ERROR: user_* variable still in rate! It should be replaced by a local variable")
            sys.exit(1)
        if tmin is not None:
            rate = rate.lower().replace("tgas", "max(tgas, %f)" % tmin)
        if tmax is not None:
            rate = rate.lower().replace("tgas", "min(tgas, %f)" % tmax)

        rr, pp = reaction.split("->")
        rr = [x.strip() for x in rr.split(" + ")]
        pp = [x.strip() for x in pp.split(" + ")]

        return rr, pp, tmin, tmax, rate

    # ****************
    def line_udfa(self, line):

        arow = line.split(":")
        rtype = arow[1]
        rr = arow[2:4]
        pp = arow[4:8]
        ka, kb, kc = [float(x) for x in arow[9:12]]
        tmin, tmax = [float(x) for x in arow[12:14]]

        rate = None
        if rtype == "CR":
            rate = "%.2e * user_crate" % kc
        elif rtype == "PH":
            rate = "%.2e * exp(-%.2f * user_av)" % (ka, kc)
        else:
            rate = "%.2e" % ka
            if kb != 0e0:
                rate += " * (Tgas / 3e2)**(%.2f)" % kb
            if kc != 0e0:
                rate += " * exp(-%.2f / Tgas)" % kc

        rr = [x.strip() for x in rr if x.strip() != ""]
        pp = [x.strip() for x in pp if x.strip() != ""]

        return rr, pp, tmin, tmax, rate

    # ****************
    def line_kida(self, line):

        ignore = ["CR", "CRP", "Photon"]

        products_pos = 34
        a_pos = 91

        srow = line

        rr = srow[:products_pos].split()
        pp = srow[products_pos:a_pos].split()
        arow = srow[a_pos:].split()
        ka, kb, kc = [float(x) for x in arow[:3]]
        formula = int(arow[9])
        tmin = float(arow[7])
        tmax = float(arow[8])

        rate = ""

        if formula == 1:
            rate += "%e * crate" % ka
        elif formula == 2:
            rate += "%.2e * np.exp(-%e*av)" % (ka, kc)
        elif formula == 3:
            rate += "%.2e" % ka
            if kb != 0e0:
                rate += " * (max(min(tgas, %f), %f) / 3e2)**(% .2f)" % (tmax, tmin, kb)
            if kc != 0e0:
                rate += " * np.exp(-% .2f / max(min(tgas, %f), %f))" % (kc, tmax, tmin)
        elif formula == 4:
            rate += "%.2e" % (ka * kb)
            if kc != 0e0:
                rate += " * (0.62 + 0.4767 * %.2e * np.sqrt(3e2 / max(min(tgas, %f), %f)))" % (kc, tmax, tmin)
        elif formula == 5:
            rate += "%.2e" % (ka * kb)
            if kc != 0e0:
                rate += " * (1e0 + 0.0967 * %.2e * np.sqrt(3e2 / max(min(tgas, %f), %f)) + %e * 3e2 / 10.526 / max(min(tgas, %f), %f))" % (kc, tmax, tmin, kc ** 2, tmax, tmin)
        else:
            print("ERROR: KIDA formula %d not implemented" % formula)
            sys.exit(1)

        rr = [x.strip() for x in rr if x.strip() not in ignore]
        pp = [x.strip() for x in pp if x.strip() not in ignore]

        return rr, pp, tmin, tmax, rate

    # ****************
    def check_sink_sources(self):
        pps = []
        rrs = []
        for rea in self.reactions:
            for p in rea.products:
                pps.append(p.name)
            for r in rea.reactants:
                rrs.append(r.name)

        has_sink = has_source = False
        for s in self.species:
            if s.name == "dummy":
                continue
            if s.name not in pps:
                print("Sink: ", s.name)
                has_sink = True
            if s.name not in rrs:
                print("Source: ", s.name)
                has_source = True

        if has_sink:
            print("ERROR: sink detected")
        if has_source:
            print("ERROR: source detected")

        if has_sink or has_source:
            sys.exit()

    # ****************
    def check_recombinations(self):
        for sp in self.species:
            if sp.charge == 0:
                continue
            if sp.charge > 0:
                electron_recombination_found = False
                # grain_recombination_found = False
                for rea in self.reactions:
                    if sp in rea.reactants and "e-" in [x.name for x in rea.reactants]:
                        electron_recombination_found = True
                    # if sp in rea.reactants and "GRAIN-" in [x.name for x in rea.reactants]:
                    #     grain_recombination_found = True

                    if electron_recombination_found: # and grain_recombination_found:
                        break

                if not electron_recombination_found:
                    print("WARNING: electron recombination not found for %s" % sp.name)
                # if not grain_recombination_found:
                #     print("WARNING: grain recombination not found for %s" % sp.name)

    # ****************
    def check_isomers(self):
        for i, sp1 in enumerate(self.species):
            for sp2 in self.species[i+1:]:
                if sp1.exploded == sp2.exploded:
                    print("WARNING: isomer detected: %s %s" % (sp1.name, sp2.name))


    # ****************
    def generate_reactions_dict(self):
        self.reactions_dict = {rea.get_verbatim(): i for i, rea in enumerate(self.reactions)}

    # ****************
    def get_reaction_verbatim(self, idx):
        return self.reactions[idx].get_verbatim()

    # ****************
    def generate_ode(self):
        print("generating ode...")
        rmax = pmax = 0
        for rea in self.reactions:
            rmax = max(rmax, len(rea.reactants))
            pmax = max(pmax, len(rea.products))
        rlist = np.zeros((len(self.reactions), rmax), dtype=int)
        plist = np.zeros((len(self.reactions), pmax), dtype=int)

        for i, rea in enumerate(self.reactions):
            ridx = [x.index for x in rea.reactants]
            rlist[i, :len(ridx)] = ridx
            pidx = [x.index for x in rea.products]
            plist[i, :len(pidx)] = pidx

        self.rlist = rlist
        self.plist = plist

    # *****************
    def get_number_of_species(self):
        return len(self.species)

    # *****************
    def get_kall(self, tgas, av, crate):
        kall = np.zeros(len(self.reactions))
        for i, rea in enumerate(self.reactions):
            try:
                kall[i] = rea.reaction(tgas, av, crate)
            except FloatingPointError:
                print(i, rea.lambda_verbatim)
                exit("ERORR: FloatingPointError in reaction rate!")
        return kall

    # *****************
    def prepare_variables_f90(self):

        # if there are no variables, return empty string
        if self.variables_f90 is None or self.variables_f90 == "":
            return ""

        # use the semi-colon to split the variables
        vv = self.variables_f90.replace("\n", "").split(";")
        vv = [x.strip() for x in vv if x.strip() != ""]

        # get the variable names
        names = [x.split("=")[0].strip() for x in vv]

        # check that the variable names does not contain "tgas" since it will be replaced with min(max(tgas, tmin), tmax)
        for x in names:
            if "tgas" in x.lower():
                print("ERROR: the variable '%s' contains the string 'tgas'" % x)
                print("This is not allowed since tgas is a reserved variable!")
                sys.exit(1)

        # definitions are just all real*8
        defs = ["real*8::" + x for x in names]

        # top of the string is the definitions (e.g. real*8:: tgas32)
        sv = "\n".join(defs) + "\n\n"

        # these are the assignments (e.g. tgas32 = tgas / 3d2)
        sv += "\n".join(vv) + "\n"

        return sv

    # *****************
    def get_species_index(self, name):
        return self.species_dict[name]

    # *****************
    def get_species_object(self, name):
        return self.species[self.species_dict[name]]

    # *****************
    def get_reaction_index(self, name):
        return self.reactions_dict[name]

    # *****************
    def get_latex(self, name, dollars=True):
        for sp in self.species:
            if sp.name == name:
                if dollars:
                    return "$" + sp.latex + "$"
                else:
                    return sp.latex

        print("ERROR: species %s latex not found" % name)
        sys.exit(1)
