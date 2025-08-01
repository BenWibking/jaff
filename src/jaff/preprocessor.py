import os
import shutil
from glob import glob


class Preprocessor:
    def __init__(self):
        pass

    # **********************************
    # loop on the files in the fnames list and replace the pragmas from the dictionaries
    # this also copies all the files that are not in the fnames list but are in the path
    def preprocess(self, path, fnames, dictionaries, comment="!!", add_header=True):
        if type(fnames) is str:
            fnames = [fnames]

        if type(dictionaries) is not list:
            dictionaries = [dictionaries]

        # create the build path if it does not exist
        path_build = os.path.join(os.path.dirname(__file__), "builds")
        if not os.path.exists(path_build):
            os.makedirs(path_build)

        # copy files that are not in the fnames list
        for fname in glob(os.path.join(path, "*")):
            if os.path.basename(fname) in fnames:
                continue
            print(f"Copying {fname} to {path_build}")
            shutil.copyfile(fname, os.path.join(path_build, os.path.basename(fname)))

        # preprocess the files in the fnames list
        for fname, dictionary in zip(fnames, dictionaries):
            self.preprocess_file(os.path.join(path, fname), dictionary, comment=comment, add_header=add_header)

    # **********************************
    # preprocess a single file replacing the pragmas with the values from the dictionary
    # this also adds a header to the file
    # comment is the string that starts the pragma
    def preprocess_file(self, fname, dictionary, comment="!!", add_header=True):

        full_pragma = comment + " PREPROCESS_"
        in_pragma = False

        fh = open(fname)
        out = ""

        if add_header:
            out += comment + " This file was automatically generated by JAFF.\n"
            out += comment + " This file could be overwritten.\n\n"

        for row in fh:
            srow = row.strip()
            if srow.startswith(full_pragma) and srow != full_pragma + "END":
                nspace = row.split(comment)[0].count(" ")
                if srow.replace(full_pragma, "") not in dictionary:
                    out += row
                    continue
                in_pragma = True
                pragma = dictionary[srow.replace(full_pragma, "")]
                indent = " " * nspace
                this_pragma = row + "\n" + indent + pragma.replace("\n", "\n" + indent).rstrip() + "\n\n"
                # this removes the indent in the fortran pragmas (fpp)
                out += this_pragma #"\n".join([x.lstrip() if is_fpp(x) else x for x in this_pragma.split("\n")])
                continue

            if srow == full_pragma + "END":
                in_pragma = False

            if in_pragma:
                continue

            out += row
        fh.close()

        path_build = os.path.join(os.path.dirname(__file__), "builds")
        fname_build = os.path.join(path_build, os.path.basename(fname))

        print(f"Preprocessing {fname} -> {fname_build}")
        fout = open(fname_build, "w")
        fout.write(out)
        fout.close()