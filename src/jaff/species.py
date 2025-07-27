import itertools
import sys


class Species:

    # ********************
    def __init__(self, name, mass_dict, index):

        if name.lower() in ["e", "eletron", "electrons", "el", "els"] or name in ["E", "E-"]:
            sys.exit("ERROR: electrons found with name: " + name + ". Use e- instead.")

        self.name = name
        self.mass = None
        self.exploded = None
        self.latex = None
        self.charge = None
        self.index = index
        self.fidx = "idx_" + name.replace("+", "j").replace("-", "k").strip()
        self.serialized = None

        self.parse(mass_dict)
        self.serialize()

    # ********************
    def serialize(self):
        self.serialized = "/".join(sorted(self.exploded))
        return self.serialized

    # ********************
    def parse(self, mass_dict):
        atoms = sorted(mass_dict.keys(), key=lambda x: len(x), reverse=True)
        ps = ["".join(x) for x in itertools.product("qzxj", repeat=4)][:len(atoms)]
        proxy = {a: p for a, p in zip(atoms, ps)}
        proxy_rev = {p: a for a, p in proxy.items()}

        pname = self.name.strip()
        for a in atoms:
            pname = pname.replace(a, "$" + proxy[a] + "$")

        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        alist = [x for x in pname.split("$") if x != ""]
        expl = []
        pold = None
        for p in alist:
            if not is_number(p):
                expl += [p]
            else:
                expl += [pold] * max(int(p)-1, 1)
            pold = p
        self.exploded = sorted([proxy_rev[x] for x in expl])
        self.mass = sum([mass_dict[x] for x in self.exploded])

        # latex name
        latex = self.name.strip()
        for i in range(0, 10):
            latex = latex.replace(str(i), "_{" + str(i) + "}")
        latex = latex.replace("+", "^{+}")
        latex = latex.replace("-", "^{-}")
        if "_ORTHO" in latex:
            latex = "o" + latex.replace("_ORTHO", "")
        if "_PARA" in latex:
            latex = "p" + latex.replace("_PARA", "")
        if "_META" in latex:
            latex = "m" + latex.replace("_META", "")
        if "_DUST" in latex:
            latex = latex.replace("_DUST", "") + "ice"

        latex = latex.replace("GRAIN", "g")

        self.latex = "{\\rm " + latex + "}"

        # charge
        if self.name == "e-":
            self.charge = -1
        else:
            self.charge = 0
            name = self.name
            # charge symbol only at the end of the name
            while name.endswith("+") or name.endswith("-"):
                if name.endswith("+"):
                    self.charge += 1
                elif name.endswith("-"):
                    self.charge -= 1
                name = name[:-1]
            #self.charge = self.name.count("+") - self.name.count("-")
