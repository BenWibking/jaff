from reaction import Reaction
from species import Species
import numpy as np
import sys
from tqdm import tqdm
from sympy import parse_expr, symbols
from parsers import parse_kida, parse_udfa, parse_prizmo, parse_krome

class Network:

    # ****************
    def __init__(self, fname, errors=False, label=None):
        self.mass_dict = self.load_mass_dict("data/atom_mass.dat")
        self.species = []
        self.species_dict = {}
        self.reactions_dict = {}
        self.reactions = []
        self.rlist = self.plist = None
        self.variables_f90 = None
        self.file_name = fname
        self.label = label if label else fname.split("/")[-1].split(".")[0]

        print("Loading network from %s" % fname)
        print("Network label = %s" % self.label)

        self.load_network(fname)

        self.check_sink_sources(errors)
        self.check_recombinations(errors)
        self.check_isomers(errors)
        self.check_unique_reactions(errors)

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

        # default krome format
        krome_format = "@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate"

        for row in tqdm(open(fname).readlines()):
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

            # check for krome format
            if srow.startswith("@format:"):
                print("KROME format detected: %s" % srow)
                krome_format = srow.strip()
                continue

            # determine the type of reaction line and parse it
            if "->" in srow:
                rr, pp, tmin, tmax, rate = parse_prizmo(srow)
            elif ":" in srow:
                rr, pp, tmin, tmax, rate = parse_udfa(srow)
            elif srow.count(",") > 3:
                rr, pp, tmin, tmax, rate = parse_krome(srow, krome_format)
            else:
                rr, pp, tmin, tmax, rate = parse_kida(srow)

            rate = rate.lower().strip()

            # parse with sympy
            rate = parse_expr(rate, evaluate=False)

            for s in rr + pp:
                if s not in species_names:
                    species_names.append(s)
                    self.species.append(Species(s, self.mass_dict, len(species_names)-1))
                    self.species_dict[s] = self.species[-1].index

            rr = [self.species[species_names.index(x)] for x in rr]
            pp = [self.species[species_names.index(x)] for x in pp]

            rea = Reaction(rr, pp, rate, tmin, tmax, srow)
            self.reactions.append(rea)

        # store rate variables for the f90 preprocessor
        self.variables_f90 = variables

        print("Loaded %d reactions" % len(self.reactions))

    # ****************
    def compare(self, other, verbosity=1):
        print("Comparing networks \"%s\" and \"%s\"..." % (self.label, other.label))

        net1 = [x.serialized for x in self.reactions]
        net2 = [x.serialized for x in other.reactions]

        nsame = 0
        nmissing1 = 0
        nmissing2 = 0
        for ref in np.unique(net1 + net2):
            if ref in net1 and ref not in net2:
                rea = self.get_reaction_by_serialized(ref)
                nmissing2 += 1
                if verbosity > 0:
                    print("Found in \"%s\" but not in \"%s\": %s" % (self.label, other.label, rea.get_verbatim()))

            elif ref in net2 and ref not in net1:
                rea = other.get_reaction_by_serialized(ref)
                nmissing1 += 1
                if verbosity > 0:
                    print("Found in \"%s\" but not in \"%s\": %s" % (other.label, self.label, rea.get_verbatim()))
            else:
                if verbosity > 1:
                    print("Found in both networks: %s" % ref)
                nsame += 1
        print("Found %d reactions in common" % nsame)
        print("%d reactions missing in \"%s\"" % (nmissing1, self.label))
        print("%d reactions missing in \"%s\"" % (nmissing2, other.label))

    # ****************
    def check_sink_sources(self, errors):
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
            print("WARNING: sink detected")
        if has_source:
            print("WARNING: source detected")

        if (has_sink or has_source) and errors:
            sys.exit()

    # ****************
    def check_recombinations(self, errors):

        has_errors = False
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
                    has_errors = True
                    print("WARNING: electron recombination not found for %s" % sp.name)
                # if not grain_recombination_found:
                #     print("WARNING: grain recombination not found for %s" % sp.name)

        if has_errors and errors:
            print("WARNING: recombination errors found")
            sys.exit(1)

    # ****************
    def check_isomers(self, errors):
        has_errors = False
        for i, sp1 in enumerate(self.species):
            for sp2 in self.species[i+1:]:
                if sp1.exploded == sp2.exploded:
                    print("WARNING: isomer detected: %s %s" % (sp1.name, sp2.name))
                    has_errors = True

        if has_errors and errors:
            print("WARNING: isomer errors found")
            sys.exit(1)

    # ****************
    def check_unique_reactions(self, errors):
        has_duplicates = False
        for i, rea1 in enumerate(self.reactions):
            for rea2 in self.reactions[i+1:]:
                if rea1.is_same(rea2):
                    print("WARNING: duplicate reaction found: %s" % rea1.get_verbatim())
                    has_duplicates = True

        if has_duplicates and errors:
            print("ERROR: duplicate reactions found")
            sys.exit(1)

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

    # *****************
    def get_reaction_by_serialized(self, serialized):
        for sp in self.reactions:
            if sp.serialized == serialized:
                return sp
        print("ERROR: reaction with serialized %s not found" % serialized)
        sys.exit(1)