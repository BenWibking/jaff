---
title: 'JAFF: An astrochemical network parser and code generator'
tags:
  - Python
  - astrochemistry
  - chemical networks
  - code generation
  - KIDA
  - UDFA
  - KROME
  - PRIZMO
authors:
  - name: Your Name
    orcid: 0000-0000-0000-0000
    corresponding: true
    affiliation: 1
affiliations:
  - name: Your Affiliation, Your Department
    index: 1
date: 2025-09-13
bibliography: paper.bib
---

# Summary

JAFF is a lightweight, extensible astrochemical network parser and code generator for modeling gas–phase and photo–chemical processes in astrophysical environments. It reads multiple widely used network formats (KIDA, UDFA, PRIZMO, KROME, UCLCHEM), validates mass/charge conservation, evaluates temperature–dependent rate coefficients, and generates efficient ODE solver code in Python, Fortran, and C++.

The library provides high–level Python APIs and a convenient CLI for inspecting networks, listing species and reactions, exporting adaptive rate tables (TXT/HDF5), and generating solvers with optional analytic Jacobians and common–subexpression elimination. Photochemical cross–sections and auxiliary external functions are supported for realistic setups. Source, documentation, and examples are available at https://github.com/tgrassi/jaff.

# Statement of need

Researchers working with astrochemical kinetics often juggle heterogeneous file formats (e.g., KIDA, UDFA) and bespoke scripts to translate reaction networks into performant solvers. This fragmented workflow increases the risk of subtle inconsistencies (units, charge/mass balance, rate expressions) and duplicates effort across projects.

JAFF addresses these issues by: (i) unifying ingestion of common network formats; (ii) providing programmatic validation, analysis, and inspection tools; and (iii) generating solver code for multiple targets (Python via SciPy, Fortran with DLSODES, and modern C++ headers). This enables rapid iteration—from exploratory analysis to production solvers—while keeping the network as the single source of truth. JAFF complements existing tools such as KROME by focusing on interoperable parsing, validation, and template–driven code generation.

# Mathematics

Given species concentrations x_i and reaction set R, the network defines a system of ordinary differential equations

$$\frac{\mathrm{d} x_i}{\mathrm{d} t} = \sum_{r\in R} s_{ir} \, k_r(T,\ldots) \prod_j x_j^{\nu_{jr}},$$

where s_{ir} is the stoichiometric coefficient of species i in reaction r, k_r is the temperature–dependent rate coefficient, and \nu_{jr} are reactant orders. JAFF can symbolically derive analytic Jacobians \(\partial f/\partial x\) to accelerate stiff integration.

# Citations

We rely on established community data sources and software, including the KIDA and UDFA databases for reaction networks [@wakelam2012kida; @kida2024], KROME for reproducible astrochemistry pipelines [@grassi2014krome], and PRIZMO–style network definitions used in recent studies [@grassi2020prizmo]. Core scientific Python dependencies include NumPy [@harris2020array], SciPy [@virtanen2020scipy], and SymPy [@meurer2017sympy].

# Figures

![High‑level JAFF workflow.](figures/architecture.png){#fig:architecture}

# Acknowledgements

We thank the maintainers of the KIDA and UDFA databases and the authors of KROME, as well as the broader scientific Python community.

# References

