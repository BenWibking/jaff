import sys



# ****************
def parse_prizmo(line):

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
def parse_udfa(line):

    arow = line.split(":")
    rtype = arow[1]
    rr = arow[2:4]
    pp = arow[4:8]
    ka, kb, kc = [float(x) for x in arow[9:12]]
    tmin, tmax = [float(x) for x in arow[12:14]]

    rate = None
    if rtype == "CR":
        rate = "%.2e * crate" % kc
    elif rtype == "PH":
        rate = "%.2e * exp(-%.2f * av)" % (ka, kc)
    else:
        rate = "%.2e" % ka
        if kb != 0e0:
            rate += " * (tgas / 3e2)**(%.2f)" % kb
        if kc != 0e0:
            rate += " * exp(-%.2f / tgas)" % kc

    rr = [x.strip() for x in rr if x.strip() != ""]
    pp = [x.strip() for x in pp if x.strip() != ""]

    return rr, pp, tmin, tmax, rate

# ****************
def parse_kida(line):

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
def parse_krome(line, fmt):

    line = line.replace(" ", "")
    line = line.replace(",e,", ",e-,").replace(",E,", ",e-,")

    afmt = [x.strip() for x in fmt.lower().strip().split(":")[1].split(",")]

    arow = [x.strip() for x in line.strip().split(",")]

    tmin = 3e0
    tmax = 1e6

    rr = []
    pp = []
    for i, x in enumerate(afmt):
        if x == "r":
            rr.append(arow[i])
        elif x == "p":
            pp.append(arow[i])
        elif x == "tmin":
            if arow[i].strip().lower() != "none":
                tmin = float(arow[i])
        elif x == "tmax":
            if arow[i].strip().lower() != "none":
                tmax = float(arow[i])
        elif x == "rate":
            rate = arow[i].strip()
        elif x == "idx":
            pass
        else:
            print("ERROR: unknown KROME format %s in line '%s'" % (x, line))
            sys.exit(1)

    rr = [x.strip() for x in rr if x.strip() != ""]
    pp = [x.strip() for x in pp if x.strip() != ""]

    return rr, pp, tmin, tmax, rate

