from .reaction import Reaction
from .species import Species
import numpy as np
import sys
import re
import os
from tqdm import tqdm
import sympy
from sympy import parse_expr, symbols, sympify, lambdify, srepr, Function
import h5py
from .parsers import parse_kida, parse_udfa, parse_prizmo, parse_krome, parse_uclchem, f90_convert
from .fastlog import fast_log2, inverse_fast_log2
from .photochemistry import Photochemistry

class Network:

    # ****************
    def __init__(self, fname, errors=False, label=None):

        self.motd()

        # Get the path to the data file relative to this module
        data_path = os.path.join(os.path.dirname(__file__), "data", "atom_mass.dat")
        self.mass_dict = self.load_mass_dict(data_path)
        self.species = []
        self.species_dict = {}
        self.reactions_dict = {}
        self.reactions = []
        self.rlist = self.plist = None
        self.file_name = fname
        self.label = label if label else os.path.basename(fname).split(".")[0]

        print("Loading network from %s" % fname)
        print("Network label = %s" % self.label)

        self.photochemistry = Photochemistry()

        self.load_network(fname)

        self.check_sink_sources(errors)
        self.check_recombinations(errors)
        self.check_isomers(errors)
        self.check_unique_reactions(errors)

        self.generate_reactions_dict()
        self.generate_reaction_matrices()

        print("All done!")

    # ****************
    @staticmethod
    def motd():
        try:
            with open("assets/words.dat", "r") as f:
                words = f.readlines()
            words = [x.strip() for x in words if x.lower().startswith("f") and x.strip().isalpha()]
            fword = np.random.choice(words)
        except:
            fword = "Fancy"
        print("Welcome to JAFF: Just Another %s Format!" % fword.title())

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
        lines = [x for x in lines if (not x.startswith("#")) or (",NAN," in x)]  # general comments
        lines = [x for x in lines if not x.startswith("!")]  # kida comments

        # number of photo-reactions
        n_photo = 0

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

            # check for KROME variables
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
            try:
                if "->" in srow:
                    rr, pp, tmin, tmax, rate = parse_prizmo(srow)
                elif ":" in srow:
                    rr, pp, tmin, tmax, rate = parse_udfa(srow)
                elif srow.count(",") > 3 and not ",NAN," in srow:
                    rr, pp, tmin, tmax, rate = parse_krome(srow, krome_format)
                elif ",NAN," in srow:
                    rr, pp, tmin, tmax, rate = parse_uclchem(srow)
                else:
                    rr, pp, tmin, tmax, rate = parse_kida(srow)
            except (ValueError, IndexError) as e:
                print(f"WARNING: Skipping invalid line: {srow[:50]}... ({e})")
                continue

            # use lowercase for rate
            rate = rate.lower().strip()
            
            # parse rate with sympy
            # photo-chemistry
            if("photo" in rate.lower()):
                # Extract arguments from photo(arg1, arg2) format
                import re
                match = re.match(r'(?i)photo\((.*)\)', rate)
                if match:
                    args_str = match.group(1)
                    photo_args = [arg.strip() for arg in args_str.split(',')]
                    if len(photo_args) < 2:
                        photo_args.append('1e99')
                    f = Function("photorates")
                    rate = f(n_photo, photo_args[0], photo_args[1])
                    n_photo += 1
                else:
                    # Fallback to old parsing if regex fails
                    photo_args = rate.split(',')
                    if len(photo_args) < 3:
                        photo_args.append(1e99)
                    f = Function("photorates")
                    rate = f(n_photo, photo_args[1], photo_args[2])
                    n_photo += 1
            else:
                # parse non-photo-chemistry rates
                rate = parse_expr(rate, evaluate=False)
                # If rate is just a single variable name that got parsed as a function,
                # convert it to a symbol
                if hasattr(rate, '__name__') and rate.__name__ in [v[0] for v in variables_sympy]:
                    rate = symbols(rate.__name__)
            print(rate)

            # use sympy to replace custom variables into the rate expression
            # note: reverse order to allow for nested variable replacement
            for vv in variables_sympy[::-1]:
                var, val = vv
                if type(val) is str:
                    print("WARNING: variable %s not replaced because it is a string, not a sympy expression" % var)
                else:
                    if type(rate) is not str:
                        rate = rate.subs(symbols(var), val)

            if tmin is not None and tmin > 0:
                rate = rate.subs(symbols("tgas"), "max(tgas, %f)" % tmin)
            if tmax is not None and tmax > 0:
                rate = rate.subs(symbols("tgas"), "min(tgas, %f)" % tmax)

            if type(rate) is not str:
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

            if rea.guess_type() == "photo":
                rea.xsecs = self.photochemistry.get_xsec(rea)

            self.reactions.append(rea)

        # unique list of variables names found in the rate expressions
        free_symbols_all = sorted([x.name for x in list(set(free_symbols_all))])

        print("Variables found:", free_symbols_all)
        print("Loaded %d reactions" % len(self.reactions))
        print("Lodaded %d photo-chemistry reactions" % n_photo)

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
    def generate_reaction_matrices(self):
        """Generate reaction matrices (rlist and plist) for tracking reactants and products."""
        n_reactions = len(self.reactions)
        n_species = len(self.species)
        
        # Initialize matrices
        self.rlist = np.zeros((n_reactions, n_species), dtype=int)
        self.plist = np.zeros((n_reactions, n_species), dtype=int)
        
        # Fill matrices based on reactions
        for i, reaction in enumerate(self.reactions):
            # Count reactants
            for reactant in reaction.reactants:
                species_idx = reactant.index
                self.rlist[i, species_idx] += 1
            
            # Count products  
            for product in reaction.products:
                species_idx = product.index
                self.plist[i, species_idx] += 1

    # ****************
    def get_reaction_verbatim(self, idx):
        return self.reactions[idx].get_verbatim()

    # ****************
    def get_commons(self, idx_offset=0, idx_prefix="", definition_prefix=""):

        scommons = ""
        for i, sp in enumerate(self.species):
            scommons += f"{definition_prefix}{idx_prefix}{sp.fidx} = {idx_offset + i}\n"

        scommons += f"{definition_prefix}nspecs = {len(self.species)}\n"
        scommons += f"{definition_prefix}nreactions = {len(self.reactions)}\n"

        return scommons

    # ****************
    def get_rates(self, idx_offset=0, rate_variable="k", language="python", use_cse=True):

        if language in ["fortran", "f90"]:
            brackets = "()"
        elif language in ["c++", "cpp", "cxx"]:
            brackets = "[]"
        else:
            brackets = "[]"

        lb, rb = brackets[0], brackets[1]

        rates = ""
        
        # For C++ with CSE enabled, collect all rate expressions and apply CSE
        if language in ["c++", "cpp", "cxx"] and use_cse:
            from sympy import cse, cxxcode, Function
            
            # Collect all rate expressions as SymPy objects
            rate_exprs = []
            photo_indices = []
            for i, rea in enumerate(self.reactions):
                if type(rea.rate) is str:
                    # String rates are kept as-is (will be handled separately)
                    rate_exprs.append(None)
                elif hasattr(rea.rate, 'func') and isinstance(rea.rate.func, type(Function('f'))):
                    if rea.rate.func.__name__ == 'photorates':
                        # Photorates are handled specially
                        rate_exprs.append(None)
                        photo_indices.append(i)
                    else:
                        rate_exprs.append(rea.rate)
                else:
                    rate_exprs.append(rea.rate)
            
            # Filter out None values for CSE
            valid_exprs = [(i, expr) for i, expr in enumerate(rate_exprs) if expr is not None]
            
            if valid_exprs:
                # Apply CSE to all valid expressions
                indices, exprs = zip(*valid_exprs)
                replacements, reduced_exprs = cse(exprs, optimizations='basic')
                
                # Generate code for common subexpressions
                if replacements:
                    rates += "// Common subexpressions\n"
                for i, (var, expr) in enumerate(replacements):
                    cpp_expr = cxxcode(expr, strict=False).replace("std::", "Kokkos::")
                    rates += f"const double {var} = {cpp_expr};\n"
                
                if replacements:
                    rates += "\n// Rate calculations using common subexpressions\n"
                
                # Generate code for reduced rate expressions
                expr_dict = dict(zip(indices, reduced_exprs))
                
                # Generate all rate assignments
                for i, rea in enumerate(self.reactions):
                    if i in expr_dict:
                        # Use CSE-optimized expression
                        cpp_code = cxxcode(expr_dict[i], strict=False).replace("std::", "Kokkos::")
                        rates += f"{rate_variable}{lb}{idx_offset+i}{rb} = {cpp_code};\n"
                    elif type(rea.rate) is str:
                        # String rate
                        rate = rea.rate
                        if rea.guess_type() == "photo":
                            rate = rate.replace("#IDX#", str(idx_offset + i))
                        rates += f"{rate_variable}{lb}{idx_offset+i}{rb} = {rate};\n"
                    elif i in photo_indices:
                        # Photorates
                        rate = f"photorates(#IDX#, {', '.join(str(arg) for arg in rea.rate.args[1:])})"
                        rate = rate.replace("#IDX#", str(idx_offset + i))
                        rates += f"{rate_variable}{lb}{idx_offset+i}{rb} = {rate};\n"
                    else:
                        # Fallback to regular code generation
                        rate = rea.get_cpp()
                        if rea.guess_type() == "photo":
                            rate = rate.replace("#IDX#", str(idx_offset + i))
                        rates += f"{rate_variable}{lb}{idx_offset+i}{rb} = {rate};\n"
            else:
                # No valid expressions for CSE, use regular generation
                for i, rea in enumerate(self.reactions):
                    rate = rea.get_cpp()
                    if rea.guess_type() == "photo":
                        rate = rate.replace("#IDX#", str(idx_offset + i))
                    rates += f"{rate_variable}{lb}{idx_offset+i}{rb} = {rate};\n"
        else:
            # Original behavior for non-C++ or CSE disabled
            for i, rea in enumerate(self.reactions):
                if language in ["python", "py"]:
                    rate = rea.get_python()
                elif language in ["c++", "cpp", "cxx"]:
                    rate = rea.get_cpp()
                else:
                    rate = rea.get_python()
                if rea.guess_type() == "photo":
                    rate = rate.replace("#IDX#", str(idx_offset + i))
                if language in ["c++", "cpp", "cxx"]:
                    rates += f"{rate_variable}{lb}{idx_offset+i}{rb} = {rate};\n"
                else:
                    rates += f"{rate_variable}{lb}{idx_offset+i}{rb} = {rate}\n"

        return rates

    # ****************
    def get_fluxes(self, idx_offset=0, rate_variable="k", species_variable="y", brackets="[]", idx_prefix=""):
        lb, rb = brackets[0], brackets[1]

        fluxes = ""
        for i, rea in enumerate(self.reactions):
            flux = rea.get_flux(idx=idx_offset+i, rate_variable=rate_variable, species_variable=species_variable, brackets=brackets, idx_prefix=idx_prefix)
            fluxes += f"flux{lb}{idx_offset+i}{rb} = {flux};\n"

        return fluxes

    # ****************
    def get_ode(self, idx_offset=0, flux_variable="flux", brackets="[]", species_variable="y", idx_prefix="", derivative_prefix="d"):

        lb, rb = brackets[0], brackets[1]

        ode = {}
        for i, rea in enumerate(self.reactions):
            for rr in rea.reactants:
                rrfidx = idx_prefix + rr.fidx
                if rrfidx not in ode:
                    ode[rrfidx] = ""
                ode[rrfidx] += f"- {flux_variable}{lb}{idx_offset+i}{rb}"
            for pp in rea.products:
                ppfidx = idx_prefix + pp.fidx
                if ppfidx not in ode:
                    ode[ppfidx] = ""
                ode[ppfidx] += f"+ {flux_variable}{lb}{idx_offset+i}{rb}"

        sode = ""
        for name, expr in ode.items():
            sode += f"{derivative_prefix}{species_variable}{lb}{name}{rb} = {expr};\n"

        return sode

    # *****************
    def get_symbolic_ode_and_jacobian(self, idx_offset=0, use_cse=True, language="c++"):
        """
        Generate symbolic ODE expressions and compute the analytical Jacobian.
        
        Returns:
            tuple: (ode_expressions, jacobian_expressions)
                - ode_expressions: string containing the ODE expressions
                - jacobian_expressions: string containing the Jacobian matrix elements
        """
        import sympy as sp
        from sympy import symbols, Matrix, diff, cse, numbered_symbols
        
        # Create symbolic variables for species concentrations
        n_species = len(self.species)
        y_symbols = [symbols(f'y[{i}]') for i in range(n_species)]
        
        # Create symbolic variables for reaction rates
        n_reactions = len(self.reactions)
        k_symbols = [symbols(f'k[{i}]') for i in range(n_reactions)]
        
        # Build symbolic flux expressions
        flux_symbols = []
        for i, rea in enumerate(self.reactions):
            flux_expr = k_symbols[i]
            for rr in rea.reactants:
                # Handle both integer indices and string identifiers like "idx_Hj"
                if isinstance(rr.fidx, str):
                    if rr.fidx.startswith("idx_"):
                        # The fidx format replaces + with j and - with k
                        # So we need to look up the species by its actual name
                        idx = rr.index  # Use the species index directly
                    else:
                        idx = int(rr.fidx)
                else:
                    idx = int(rr.fidx)
                flux_expr *= y_symbols[idx]
            flux_symbols.append(flux_expr)
        
        # Build symbolic ODE expressions (RHS)
        ode_symbols = [sp.Integer(0) for _ in range(n_species)]
        for i, rea in enumerate(self.reactions):
            # Subtract flux from reactants
            for rr in rea.reactants:
                # Handle both integer indices and string identifiers like "idx_Hj"
                if isinstance(rr.fidx, str):
                    if rr.fidx.startswith("idx_"):
                        # The fidx format replaces + with j and - with k
                        # So we need to look up the species by its actual name
                        idx = rr.index  # Use the species index directly
                    else:
                        idx = int(rr.fidx)
                else:
                    idx = int(rr.fidx)
                ode_symbols[idx] -= flux_symbols[i]
            # Add flux to products
            for pp in rea.products:
                # Handle both integer indices and string identifiers like "idx_Hj"
                if isinstance(pp.fidx, str):
                    if pp.fidx.startswith("idx_"):
                        # The fidx format replaces + with j and - with k
                        # So we need to look up the species by its actual name
                        idx = pp.index  # Use the species index directly
                    else:
                        idx = int(pp.fidx)
                else:
                    idx = int(pp.fidx)
                ode_symbols[idx] += flux_symbols[i]
        
        # Compute the Jacobian matrix
        jacobian_matrix = Matrix(ode_symbols).jacobian(y_symbols)
        
        # Generate code strings
        if language in ["c++", "cpp", "cxx"]:
            brackets = "[]"
            assignment_op = "="
            line_end = ";"
        else:  # Default to Python/Fortran style
            brackets = "[]" if language == "python" else "()"
            assignment_op = "="
            line_end = ""
        
        lb, rb = brackets[0], brackets[1]
        
        # Apply common subexpression elimination if requested
        if use_cse:
            # Collect all expressions for CSE
            all_exprs = list(ode_symbols) + list(jacobian_matrix)
            replacements, reduced_exprs = cse(all_exprs, symbols=numbered_symbols("cse"))
            
            # Generate CSE assignments
            cse_code = ""
            for i, (var, expr) in enumerate(replacements):
                expr_str = sp.cxxcode(expr) if language in ["c++", "cpp", "cxx"] else str(expr)
                # Replace array brackets in the expression
                expr_str = expr_str.replace('[', lb).replace(']', rb)
                cse_code += f"const double {var} {assignment_op} {expr_str}{line_end}\n"
            
            # Split reduced expressions back
            ode_reduced = reduced_exprs[:n_species]
            jac_reduced = reduced_exprs[n_species:]
            
            # Generate ODE code with CSE
            ode_code = cse_code
            for i, expr in enumerate(ode_reduced):
                expr_str = sp.cxxcode(expr) if language in ["c++", "cpp", "cxx"] else str(expr)
                expr_str = expr_str.replace('[', lb).replace(']', rb)
                ode_code += f"f{lb}{i}{rb} {assignment_op} {expr_str}{line_end}\n"
            
            # Generate Jacobian code with CSE (include CSE variable definitions)
            jac_code = cse_code  # Include the CSE variable definitions
            for i in range(n_species):
                for j in range(n_species):
                    idx = i * n_species + j
                    expr = jac_reduced[idx]
                    if expr != 0:
                        expr_str = sp.cxxcode(expr) if language in ["c++", "cpp", "cxx"] else str(expr)
                        expr_str = expr_str.replace('[', lb).replace(']', rb)
                        # Use parentheses for Jacobian matrix access in C++ (Kokkos views)
                        if language in ["c++", "cpp", "cxx"]:
                            jac_code += f"J({i}, {j}) {assignment_op} {expr_str}{line_end}\n"
                        else:
                            jac_code += f"J{lb}{i}{rb}{lb}{j}{rb} {assignment_op} {expr_str}{line_end}\n"
        else:
            # Generate ODE code without CSE
            ode_code = ""
            for i, expr in enumerate(ode_symbols):
                expr_str = sp.cxxcode(expr) if language in ["c++", "cpp", "cxx"] else str(expr)
                expr_str = expr_str.replace('[', lb).replace(']', rb)
                ode_code += f"f{lb}{i}{rb} {assignment_op} {expr_str}{line_end}\n"
            
            # Generate Jacobian code without CSE
            jac_code = ""
            for i in range(n_species):
                for j in range(n_species):
                    expr = jacobian_matrix[i, j]
                    if expr != 0:
                        expr_str = sp.cxxcode(expr) if language in ["c++", "cpp", "cxx"] else str(expr)
                        expr_str = expr_str.replace('[', lb).replace(']', rb)
                        # Use parentheses for Jacobian matrix access in C++ (Kokkos views)
                        if language in ["c++", "cpp", "cxx"]:
                            jac_code += f"J({i}, {j}) {assignment_op} {expr_str}{line_end}\n"
                        else:
                            jac_code += f"J{lb}{i}{rb}{lb}{j}{rb} {assignment_op} {expr_str}{line_end}\n"
        
        return ode_code, jac_code

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
    def get_species_by_serialized(self, serialized):
        for sp in self.species:
            if sp.serialized == serialized:
                return sp
        print("ERROR: species with serialized %s not found" % serialized)
        sys.exit(1)

    # *****************
    def get_reaction_by_serialized(self, serialized):
        for sp in self.reactions:
            if sp.serialized == serialized:
                return sp
        print("ERROR: reaction with serialized %s not found" % serialized)
        sys.exit(1)

    # *****************
    def get_reaction_by_verbatim(self, verbatim, rtype=None):

        for rea in self.reactions:
            if rea.get_verbatim() == verbatim:
                if rtype is None or rea.guess_type() == rtype:
                    return rea
        print("ERROR: reaction with verbatim '%s' not found" % verbatim)
        sys.exit(1)

    # *****************
    def get_table(self, T_min = None, T_max = None,
                  nT = 64, err_tol = 0.01,
                  rate_min = 1e-30, rate_max = 1e100,
                  fast_log = False, verbose = False):
        """
        Return a tabulation of rate coefficients as a function of
        temperature for all reactions.

        Parameters
        ----------
            T_min : float or None
                minimum temperature for the tabulation; if left as None,
                will be set to the minimum temperature over reactions in
                the network
            T_max : float or None
                maximum temperature for the tabulation; if left as None,
                will be set to the maximum temperature over reactions in
                the network
            nT : int
                initial guess for number of sampling temperatures
            err_tol : float or None
                relative error tolerance for interpolation; if set to
                None, adaptive resampling is disabled and the table size
                will be exactly nT
            rate_min : float
                adaptive error tolerance is not applied to rates below
                rate_min
            rate_max : float
                rataes above rate_max are clipped to rate_max to prevent
                overflow
            fast_log : bool
                if True, sample points are equally spaced in fast_log2(T)
                rather than log(T)
            verbose : bool
                if True, produce verbose output while adaptively refining

        Returns
        -------
            temp : array, shape (nTemp)
                gas temperatures at which rates are sampled
            coeff : array, shape (nreact, nTemp)
                tabulated reaction rate coefficients at temperatures temp

        Notes
        -----
            1) By default temperature is sampled logarithmically in the
            output, i.e., temp =
            np.logspace(np.log10(T_min), np.log10(T_max), nTemp)
            where nTemp is the number of temperatures in the output
            table. If fast_log is set to True, then the outputs are
            instead uniformly spaced in fast_log2 rather than the
            true logarithm.
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

        # Get min and max temperature if not provided
        if T_min is None:
            T_min = np.nanmin([r.tmin if r.tmin is not None else np.nan 
                               for r in self.reactions])
        if T_max is None:
            T_max = np.nanmax([r.tmax if r.tmax is not None else np.nan 
                               for r in self.reactions])
        if T_min is None or T_max is None:
            raise ValueError("could not determine T_min or T_max from "
                             "reaction list; set T_min and T_max manually")

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
        for i, r in enumerate(react_subst):
            if len(r.free_symbols) == 0:
                # Reaction rates that are just constants; in this
                # case just copy that constant to the list of functions
                react_func.append(np.log(float(r)))
            elif (len(r.free_symbols) > 1) or \
                (symbols('tgas') not in r.free_symbols) or \
                ('Function' in srepr(r)):
                # For reaction rates that do not depend on temperature,
                # that depend on variables other than temperature,
                # or that contain arbitrary functions, we cannot
                # tabulate, so just store None
                react_func.append(None)
            else:
                # Case of reactions that depend only on temperature; to
                # avoid overflows we will take the log of the rate function
                # and expand it before converting to numpy, and then we will
                # exponentiate at the very end
                logr = sympy.expand_log(sympy.log(r))
                react_func.append(lambdify(symbols('tgas'), logr, 'numpy'))

        # Fourth step: generate rate coefficient table for initial guess
        # table size
        nTemp = nT
        if not fast_log:
            temp = np.logspace(np.log10(T_min), np.log10(T_max), nTemp)
        else:
            # Generate sample points that are uniformly sampled in fast_log2
            log_temp_min = fast_log2(T_min)
            log_temp_max = fast_log2(T_max)
            log_temp = np.linspace(log_temp_min, log_temp_max, nTemp)
            temp = inverse_fast_log2(log_temp)
        log_rates = np.zeros((len(react_func), nTemp))
        for i, f in enumerate(react_func):
            if isinstance(f, float):
                log_rates[i,:] = f
            elif f is None:
                log_rates[i,:] = np.nan
            else:
                # Note: it would be much faster to do this via an array operation
                # rather than a list comprehension, but sympy (as of v1.13) does
                # not consistently generate numpy expressions that work properly
                # with vector inputs, so restricting the input to scalars is safer.
                f_eval = np.array([f(t) for t in temp])
                log_rates[i,:] = np.clip(f_eval,
                                         a_min = None, a_max = rate_max)

        # Fifth step: do adaptive growth of table
        if err_tol is not None:

            while True:

                # Compute estimates at half-way points
                nTemp = 2 * nTemp - 1
                temp_grow = np.zeros(nTemp)
                temp_grow[::2] = temp
                if not fast_log:
                    temp_grow[1::2] = np.sqrt(temp[1:] * temp[:-1])
                else:
                    log_temp_lo = fast_log2(temp[:-1])
                    log_temp_hi = fast_log2(temp[1:])
                    temp_grow[1::2] = inverse_fast_log2(0.5 * (log_temp_lo + log_temp_hi))
                log_rates_grow = np.zeros((len(react_func), nTemp))
                log_rates_grow[:,::2] = log_rates
                log_rates_approx = np.zeros((len(react_func), (nTemp-1)//2))
                for i, f in enumerate(react_func):
                    if isinstance(f, float):
                        log_rates_grow[i,1::2] = np.log(f)
                        log_rates_approx[i,:] = np.log(f)
                    elif f is None:
                        log_rates_grow[i,1::2] = np.nan
                        log_rates_approx[i,:] = np.nan
                    else:
                        # See comment above about why we're using a list comprehension
                        # here instead of a straight array operation
                        f_eval = np.array([f(t) for t in temp_grow[1::2]])
                        log_rates_grow[i,1::2] = np.clip(f_eval,
                                                         a_min = None,
                                                         a_max = rate_max)
                        log_rates_approx[i,:] = 0.5 * \
                            (log_rates_grow[i,:-1:2] +  
                             log_rates_grow[i,2::2])

                # Copy new estimates to current ones
                temp = temp_grow
                log_rates = log_rates_grow

                # Make error estimate
                rel_err = np.abs(
                    (np.exp(log_rates_approx) - np.exp(log_rates[:,1::2])) /
                    (np.exp(log_rates[:,1::2]) + rate_min ) )
                max_err = np.nanmax(rel_err)

                # Print output if verbose
                if verbose:
                    idx_max = np.unravel_index(np.nanargmax(rel_err),
                                               rel_err.shape)
                    print("nTemp = {:d}, max_err = {:f} in reaction {:s} at T = {:e}".
                          format(nTemp, max_err,
                                 self.reactions[idx_max[0]].get_verbatim(),
                                 temp[idx_max[1]]))

                # Check for convergence
                if max_err < err_tol:
                    break

        # Return final table
        return temp, np.exp(log_rates)

    # *****************
    def write_table(self, fname, T_min = None, T_max = None,
                    nT = 64, err_tol = 0.01,
                    rate_min = 1e-30, rate_max = 1e100,
                    fast_log = False, format = 'auto',
                    include_all = False, verbose = False):
        """
        Write a tabulation of rate coefficients as a function of
        temperature for all reactions.

        Parameters
        ----------
            fname : string
                name of output file
            T_min : float or None
                minimum temperature for the tabulation; if left as None,
                will be set to the minimum temperature over reactions in
                the network
            T_max : float or None
                maximum temperature for the tabulation; if left as None,
                will be set to the maximum temperature over reactions in
                the network
            nT : int
                initial guess for number of sampling temperatures
            err_tol : float or None
                relative error tolerance for interpolation; if set to
                None, adaptive resampling is disabled and the table size
                will be exactly nT
            rate_min : float
                adaptive error tolerance is not applied to rates below
                rate_min
            rate_max : float
                rataes above rate_max are clipped to rate_max to prevent
                overflow
            fast_log : bool
                if True, sample points are equally spaced in fast_log2(T)
                rather than log(T)
            format : 'auto' | 'txt' | 'hdf5'
                output format; if set to 'auto', format will be guessed from
                extension of fname, otherwise output will be set to either
                text for hdf5 format
            include_all : bool
                if True, the output table will contain all reactions, with
                entries for rate coefficients that cannot be tabulated
                just as a function of temperature set to NaN; if False,
                the output table only includes coefficients that can be
                tabulated and are non-constant
            verbose : bool
                if True, produce verbose output while adaptively refining

        Returns
        -------
            Nothing

        Raises
        ------
            ValueError
                if format is set to 'auto' and the extension is of fname
                is not 'txt', 'hdf', or 'hdf5'
            IOError
                if the output fille cannot be opened

        Notes
        -----
            See notes to get_table for details on how temperature sampling
            and error tolerance is handled.
        """

        # Deduce output format
        if format == 'txt':
            out_type = 'txt'
        elif format == 'hdf5':
            out_type = 'hdf5'
        elif format == 'auto':
            if os.path.splitext(fname)[1] == ".txt":
                out_type = 'txt'
            elif os.path.splitext(fname)[1] == '.hdf5' \
                or os.path.splitext(fname)[1] == '.hdf':
                out_type = 'hdf5'
            else:
                raise ValueError("cannot deduce output type from "
                                 "extension {:s}".format(
                                     os.path.splitext(fname)
                                 ))
        else:
            raise ValueError("unknown output format {:s}".
                             format(str(format)))
        
        # Get rate coefficients
        temp, coef = self.get_table(T_min = T_min, T_max = T_max, 
                                    nT = nT, err_tol = err_tol, 
                                    rate_min = rate_min,
                                    rate_max = rate_max,
                                    fast_log = fast_log,
                                    verbose = verbose)
        
        # Remove from table reaction rates that are either constant
        # or NaN
        if include_all:
            react_list = list(range(len(coef)))
        else:
            react_list = []
            for i, c in enumerate(coef):
                if np.sum(np.isnan(c)) > 0 or \
                    np.amax(c) - np.amin(c) == 0.0:
                    continue
                react_list.append(i)
        coef = coef[react_list]

        # For the reactions that we are including, grab the reaction
        # type and lists of reactants and products
        rtype = []
        reactants = []
        products = []
        for i in react_list:
            if self.reactions[i].guess_type() == 'unknown':
                rtype.append('2_body')
            else:
                rtype.append(self.reactions[i].guess_type())
            reactants_ = {}
            for r in self.reactions[i].reactants:
                if r.name in reactants_.keys():
                    reactants_[r.name] += 1
                else:
                    reactants_[r.name] = 1
            reactants.append(reactants_)
            products_ = {}
            for p in self.reactions[i].products:
                if p.name in products_.keys():
                    products_[p.name] += 1
                else:
                    products_[p.name] = 1
            products.append(products_)

        # Write output in appropriate format
        if out_type == 'txt':

            # Text output
            fp = open(fname, 'w')

            # Write header
            fp.write("# JAFF auto-generated rate coefficient table\n")
            fp.write("# Network name: {:s}\n".format(self.label))
            fp.write("# Reactions included\n")
            fp.write("#   (reactants) (products) (reaction type)\n")
            for rt, r, p in zip(rtype, reactants, products):
                fp.write("#   {:s} {:s} {:s}\n".format(
                    repr(r), repr(p), rt))

            # Write data in quokka table format
            fp.write("1\n")                       # Table is 1d
            fp.write("{:d}\n".format(len(coef)))  # N outputs per table entry
            if fast_log:
                fp.write("3\n")                   # Table is uniform in fast_log
            else:
                fp.write("2\n")                   # Table is uniform in log
            fp.write("{:d}\n".format(len(temp)))  # Number of temperature entries
            fp.write("{:e} {:e}\n".
                     format(temp[0], temp[-1]))   # Min/max temperature

            # Now write the data
            for c in coef:
                for c_ in c:
                    fp.write("{:e} ".format(c_))
                fp.write("\n")

            # Close
            fp.close()

        elif out_type == 'hdf5':

            # HDF5 output
            fp = h5py.File(fname, mode='w')

            # Create a group to contain the data
            grp = fp.create_group('reaction_coeff')

            # Store metadata in the attributes
            grp.attrs['input_names'] = ['temperature']
            grp.attrs['input_units'] = ['K']
            grp.attrs['xlo'] = np.array([temp[0]])
            grp.attrs['xhi'] = np.array([temp[-1]])
            if fast_log:     # Spacing type
                grp.attrs['spacing'] = ['fast_log']
            else:
                grp.attrs['spacing'] = ['log']

            # Store information on which reactions / rate coefficients
            # are included; note that we store these as data sets
            # instead of attributes to avoid problems in the case where
            # the number of reactions is very large, and thus resulting
            # size of the output reaction list exceeds the HDF5 limit
            # on the sizes of attributes
            output_names = []
            output_units = []
            for i, rt, r, p in zip(range(len(rtype)), rtype, 
                                   reactants, products):
                output_names.append(
                    '{:s} rate coefficient: {:s} --> {:s}'.
                    format(str(rt), str(r), str(p))
                )
                output_units.append('cm^3 s^-1')
            grp.create_dataset('output_names', data=output_names, dtype=h5py.string_dtype())
            grp.create_dataset('output_units', data=output_units, dtype=h5py.string_dtype())

            # Create data set holding the coefficient table
            dset = grp.create_dataset('data', data=coef)

            # Close file
            fp.close()
