from reaction import Reaction
from species import Species
import numpy as np
import sys
import re
from tqdm import tqdm
from sympy import parse_expr, symbols, sympify, lambdify
from parsers import parse_kida, parse_udfa, parse_prizmo, parse_krome, f90_convert

class Network:

    # ****************
    def __init__(self, fname, errors=False, label=None):
        self.mass_dict = self.load_mass_dict("data/atom_mass.dat")
        self.species = []
        self.species_dict = {}
        self.reactions_dict = {}
        self.reactions = []
        self.rlist = self.plist = None
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

        # custom variables
        variables_sympy = []

        # some of the krome shortcuts used in KROME
        krome_shortcuts = '''
        t32=tgas/3e2
        te=tgas*8.617343e-5
        invt32 = 1e0 / t32
        invte = 1e0 / te
        invtgas = 1e0 / tgas
        sqrtgas = sqrt(tgas)
        '''

        # parse krome shortcuts
        for row in krome_shortcuts.split("\n"):
            srow = row.strip()
            if srow == "" or srow.startswith("#"):
                continue
            var, val = srow.split("=")
            variables_sympy.append([var, parse_expr(val, evaluate=False)])

        # all variables found in the rate expressions (not in the custom variables)
        free_symbols_all = []

        # flag to check if we are in PRIZMO variables section
        in_variables = False

        # default krome format
        krome_format = "@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate"

        # read the file into a list of lines
        lines = open(fname).readlines()

        # remove empty lines and comments
        lines = [x.strip() for x in lines if x.strip() != ""]
        lines = [x for x in lines if not x.startswith("#")]  # general comments
        lines = [x for x in lines if not x.startswith("!")]  # kida comments

        # loop through the lines and parse them
        for srow in tqdm(lines):

            # -------------------- PRIZMO --------------------
            # check for PRIZMO variables
            if srow.startswith("VARIABLES{"):
                in_variables = True
                continue

            # end of PRIZMO variables
            if srow.startswith("}") and in_variables:
                in_variables = False
                continue

            # store variables as a single string, it will be processed later
            # format will be var1=value1;var2=value2;...
            if in_variables:
                print("PRIZMO variable detected: %s" % srow)
                srow = srow.replace(" ", "").strip().lower()
                srow = f90_convert(srow)
                var, val = srow.split("=")
                try:
                    variables_sympy.append((var, parse_expr(val, evaluate=False)))
                except Exception as e:
                    print("WARNING: could not parse variable (%s), using string instead" % e)
                    variables_sympy.append((var, val.strip()))
                continue

            # -------------------- KROME --------------------
            # check for krome format
            if srow.startswith("@format:"):
                print("KROME format detected: %s" % srow)
                krome_format = srow.strip()
                continue

            if srow.startswith("@var:"):
                print("KROME variable detected: %s" % srow)
                srow = srow.replace("@var:", "").lower().strip()
                srow = f90_convert(srow)
                var, val = srow.split("=")
                try:
                    variables_sympy.append((var, parse_expr(val, evaluate=False)))
                except Exception as e:
                    print("WARNING: could not parse variable (%s), using string instead" % e)
                    variables_sympy.append((var, val.strip()))
                continue

            # skip KROME special lines
            if srow.startswith("@"):
                continue

            # -------------------- REACTIONS --------------------
            # determine the type of reaction line and parse it
            if "->" in srow:
                rr, pp, tmin, tmax, rate = parse_prizmo(srow)
            elif ":" in srow:
                rr, pp, tmin, tmax, rate = parse_udfa(srow)
            elif srow.count(",") > 3:
                rr, pp, tmin, tmax, rate = parse_krome(srow, krome_format)
            else:
                rr, pp, tmin, tmax, rate = parse_kida(srow)

            # use lowercase for rate
            rate = rate.lower().strip()

            # parse rate with sympy
            rate = parse_expr(rate, evaluate=False)

            # use sympy to replace custom variables into the rate expression
            for vv in variables_sympy[::-1]:
                var, val = vv
                if isinstance(val, str):
                    print("WARNING: variable %s not replaced because it is a string, not a sympy expression" % var)
                else:
                    rate = rate.subs(symbols(var), val)

            # add variables to the list of all variables
            free_symbols_all += rate.free_symbols

            # convert reactants and products to Species objects
            for s in rr + pp:
                if s not in species_names:
                    species_names.append(s)
                    self.species.append(Species(s, self.mass_dict, len(species_names)-1))
                    self.species_dict[s] = self.species[-1].index

            # reactants and products are now Species objects
            rr = [self.species[species_names.index(x)] for x in rr]
            pp = [self.species[species_names.index(x)] for x in pp]

            # create a Reaction object
            rea = Reaction(rr, pp, rate, tmin, tmax, srow)
            self.reactions.append(rea)

        # unique list of variables names found in the rate expressions
        free_symbols_all = sorted([x.name for x in list(set(free_symbols_all))])

        print("Variables found:", free_symbols_all)
        print("Loaded %d reactions" % len(self.reactions))

    # ****************
    def compare_reactions(self, other, verbosity=1):
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
    def compare_species(self, other, verbosity=1):
        print("Comparing species in networks \"%s\" and \"%s\"..." % (self.label, other.label))

        net1 = [x.serialized for x in self.species]
        net2 = [x.serialized for x in other.species]

        same_species = []
        only_in_self = []
        only_in_other = []
        nmissing1 = 0
        nmissing2 = 0
        for ref in np.unique(net1 + net2):
            if ref in net1 and ref not in net2:
                sp = self.get_species_by_serialized(ref)
                nmissing2 += 1
                if verbosity > 1:
                    print("Found in \"%s\" but not in \"%s\": %s" % (self.label, other.label, sp.name))
                only_in_self.append(sp)

            elif ref in net2 and ref not in net1:
                sp = other.get_species_object(ref)
                nmissing1 += 1
                if verbosity > 1:
                    print("Found in \"%s\" but not in \"%s\": %s" % (other.label, self.label, sp.name))
                only_in_other.append(sp)
            else:
                sp = self.get_species_by_serialized(ref)
                if verbosity > 1:
                    print("Found in both networks: %s" % ref)
                same_species.append(sp)

        print("Found %d species in common:" % len(same_species), sorted([x.name for x in same_species]))
        print("Found %d species in \"%s\" but not in \"%s\":" % (len(only_in_self), self.label, other.label), sorted([x.name for x in only_in_self]))
        print("Found %d species in \"%s\" but not in \"%s\":" % (len(only_in_other), other.label, self.label), sorted([x.name for x in only_in_other]))

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
                    if rea1.tmin != rea2.tmin or rea1.tmax != rea2.tmax:
                        continue
                    if rea1.is_isomer_version(rea2):
                        continue
                    if rea1.guess_type() != rea2.guess_type():
                        continue
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

    # *****************
    def convert_d_e(self, st):
        """
        A little utility function that converts scientific notation
        of the form N.NNNd+XX to the standard N.NNNNe+XX format that
        sympy can understand

        Parameters
            st : string
                string to be converted

        Returns
            st_conv : string
                string converted to standard exponential format
        """

        st_conv = st
        idx_d = [ pos.start() for pos in re.finditer('d', st_conv) ]
        for idx in idx_d:
            if idx == 0 or idx == len(st_conv)-1:
                continue
            if (st_conv[idx-1].isnumeric() or st_conv[idx-1] == '.') and \
                (st_conv[idx+1].isnumeric() or st_conv[idx+1] == '+' or
                 st_conv[idx+1] == '-'):
                st_conv = st_conv[:idx] + 'e' + st_conv[idx+1:]
        return st_conv

    # *****************
    def get_table(self, T_min, T_max, 
                  nT = 64, err_tol = 0.01, rate_min = 1e-30):
        """
        Return a tabulation of rate coefficients as a function of 
        temperature for all reactions.

        Parameters
            T_min : float
                minimum temperature for the tabulation
            T_max : float
                maximum temperature for the tabulation
            nT : int
                initial guess for number of sampling temperatures
            err_tol : float or None
                relative error tolerance for interpolation; if set to
                None, adaptive resampling is disabled and the table size
                will be exactly nT
            rate_min : float
                adaptive error tolerance is not applied to rates below
                rate_min

        Returns
            coeff : array, shape (nreact, nTemp)
                tabulated reaction rate coefficients

        Notes
            1) Temperature is sampled logarithmically in the output,
            i.e., the temperatures at which the reaction coefficients
            are computed are the output of
            np.logspace(np.log10(T_min), np.log10(T_max), nTemp)
            where nTemp is the number of temperatures in the output
            table.
            2) For reaction rates that depend on something other than
            tgas, the results are computed at av = 0 and crate = 1;
            rates that depend on any other quantities are not tabulated,
            and the table entries for such reactions will be set to NaN.
            3) Adaptive sampling is performed by comparing the results
            of a logarithmic interpolation between each rate
            coefficient at each pair of sampled temperature with
            a calculation of the exact rate coefficient at a temperature
            halfway between the two sample points; the errors is taken
            to be abs((interp_value - exact_value) / (exact_value + rate_min)),
            and nTemp is increased until the error for all coefficients
            is below tolerance.
        """

        # First step: for each reaction, create a sympy object we can
        # use to substitute to get an expression in terms of the
        # primitive variables
        react_sympy = [ r.get_sympy() for r in self.reactions ]

        # Second step: set av = 0 and crate = 1
        react_subst = []
        for r in react_sympy:
            r = r.subs(symbols('av'), 0.0)
            r = r.subs(symbols('crate'), 1.0)
            react_subst.append(r)

        # Third step: create numpy fucntions for each reaction
        react_func = []
        for r in react_subst:
            sym = r.free_symbols
            if len(sym) == 0:
                # Reaction rates that are just constants; in this
                # case just copy that constant to the list of functions
                react_func.append(float(r))
            elif len(sym) > 2 or not symbols('tgas') in r.free_symbols:
                # For reaction rats that do not depend on temperature,
                # or that depend on variables other than temperature,
                # we cannot tabulate, so just store None
                react_func.append(None)
            else:
                # Case of reactions that depend only on temperature
                react_func.append(lambdify(symbols('tgas'), r, 'numpy'))
 
        # Fourth step: generate rate coefficient table for initial guess
        # table size
        nTemp = nT
        temp = np.logspace(np.log10(T_min), np.log10(T_max), nTemp)
        rates = np.zeros((len(react_func), nTemp))
        for i, f in enumerate(react_func):
            if type(f) is float:
                rates[i,:] = f
            elif f is None:
                rates[i,:] = np.nan
            else:
                rates[i,:] = f(temp)

        # Fifth step: do adaptive growth of table
        if err_tol is not None:

            while True:

                # Compute estimates at half-way points
                nTemp = 2 * nTemp - 1
                temp_grow = np.zeros(nTemp)
                temp_grow[::2] = temp
                temp_grow[1::2] = np.sqrt(temp[1:] * temp[:-1])
                rates_grow = np.zeros((len(react_func), nTemp))
                rates_grow[:,::2] = rates
                rates_approx = np.zeros((len(react_func), (nTemp-1)//2))
                for i, f in enumerate(react_func):
                    if type(f) is float:
                        rates_grow[i,1::2] = f
                        rates_approx[i,:] = f
                    elif f is None:
                        rates_grow[i,1::2] = np.nan
                        rates_approx[i,:] = np.nan
                    else:
                        rates_grow[i,1::2] = f(temp_grow[1::2])
                        rates_approx[i,:] = np.sqrt(rates_grow[i,:-1:2] * 
                                                    rates_grow[i,2::2])

                # Copy new estimates to current ones
                temp = temp_grow
                rates = rates_grow

                # Make error estimate
                rel_err = np.abs(
                    (rates_approx - rates[:,1::2]) / 
                    (rates[:,1::2] + rate_min ) )
                max_err = np.nanmax(rel_err)

                # Check for convergence
                if max_err < err_tol:
                    break

        # Return final table
        return rates

    # *****************
    def get_species_by_serialized(self, serialized):
        for sp in self.species:
            if sp.serialized == serialized:
                return sp
        print("ERROR: species with serialized %s not found" % serialized)
        sys.exit(1)
