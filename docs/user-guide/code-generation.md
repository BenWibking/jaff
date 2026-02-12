# Code Generation

Comprehensive guide to generating code from chemical reaction networks using JAFF.

## Overview

JAFF can generate optimized code for chemical reaction networks in multiple programming languages. The `Codegen` class provides methods to generate:

- Rate coefficient calculations
- Reaction fluxes
- ODE systems (right-hand side)
- Jacobian matrices
- Common constants and indices

```python
from jaff import Network, Codegen

# Load network
net = Network("networks/react_COthin")

# Create code generator
cg = Codegen(network=net, lang="c++")

# Generate code
rates = cg.get_rates(use_cse=True)
odes = cg.get_ode(use_cse=True)
jacobian = cg.get_jacobian(use_cse=True)
```

## Quick Start

### Basic Code Generation

```python
from jaff import Network, Codegen

# 1. Load network
net = Network("networks/react_COthin")

# 2. Create code generator for C++
cg = Codegen(network=net, lang="c++")

# 3. Generate rate calculations
rates = cg.get_rates(
    idx_offset=0,
    rate_variable="k",
    use_cse=True
)

# 4. Save to file
with open("rates.cpp", "w") as f:
    f.write(rates)

print("Generated rates.cpp!")
```

### Complete Chemistry Module

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="c++")

# Generate all components
commons = cg.get_commons(
    idx_offset=0,
    idx_prefix="idx_",
    definition_prefix="const int "
)

rates = cg.get_rates(idx_offset=0, use_cse=True)
odes = cg.get_ode(idx_offset=0, use_cse=True)
jac = cg.get_jacobian(idx_offset=0, use_cse=True)

# Combine into complete file
code = f"""
#include <cmath>

namespace chemistry {{

// Species indices and counts
{commons}

// Rate coefficient calculations
void compute_rates(double* k, double tgas) {{
{rates}
}}

// ODE right-hand side
void compute_odes(double* dydt, const double* y, const double* k) {{
{odes}
}}

// Jacobian matrix
void compute_jacobian(double** jac, const double* y, const double* k) {{
{jac}
}}

}} // namespace chemistry
"""

with open("chemistry.cpp", "w") as f:
    f.write(code)
```

## Supported Languages

### C++

```python
cg = Codegen(network=net, lang="c++")
# or
cg = Codegen(network=net, lang="cxx")
# or
cg = Codegen(network=net, lang="cpp")
```

**Features:**
- 0-based indexing
- Semicolons (`;`)
- Square brackets (`[]`)
- Comments: `//`

**Example output:**
```cpp
k[0] = 1.2e-10 * pow(tgas/300, 0.5);
k[1] = 3.4e-11 * exp(-500/tgas);
```

### C

```python
cg = Codegen(network=net, lang="c")
```

**Features:**
- 0-based indexing
- Semicolons (`;`)
- Square brackets (`[]`)
- Comments: `//`
- C-style function calls

**Example output:**
```c
k[0] = 1.2e-10 * pow(tgas/300.0, 0.5);
k[1] = 3.4e-11 * exp(-500.0/tgas);
```

### Fortran 90

```python
cg = Codegen(network=net, lang="fortran")
# or
cg = Codegen(network=net, lang="f90")
```

**Features:**
- 1-based indexing
- No semicolons
- Parentheses (`()`)
- Comments: `!!`

**Example output:**
```fortran
k(1) = 1.2d-10 * (tgas/300.d0)**0.5d0
k(2) = 3.4d-11 * dexp(-500.d0/tgas)
```

### Python

```python
cg = Codegen(network=net, lang="python")
# or
cg = Codegen(network=net, lang="py")
```

**Features:**
- 0-based indexing
- No semicolons
- Square brackets (`[]`)
- Comments: `#`

**Example output:**
```python
k[0] = 1.2e-10 * (tgas/300)**0.5
k[1] = 3.4e-11 * exp(-500/tgas)
```

## Code Generation Methods

### Common Constants

Generate species indices and counts:

```python
commons = cg.get_commons(
    idx_offset=0,
    idx_prefix="idx_",
    definition_prefix="const int "
)
```

**Output:**
```cpp
const int idx_h = 0;
const int idx_h2 = 1;
const int idx_o = 2;
const int idx_oh = 3;
const int idx_co = 4;
const int nspecs = 35;
const int nreactions = 127;
```

### Rate Calculations

Generate rate coefficient calculations:

```python
rates = cg.get_rates(
    idx_offset=0,
    rate_variable="k",
    use_cse=True,
    cse_var="x"
)
```

**Output (with CSE):**
```cpp
//Common subexpressions
const double x0 = sqrt(tgas);
const double x1 = pow(tgas/300, 0.5);
const double x2 = exp(-500/tgas);

//Rate calculations using common subexpressions
k[0] = 1.2e-10 * x1;
k[1] = 3.4e-11 * x2;
k[2] = 5.6e-12 * x0 * x1;
```

### Flux Calculations

Generate reaction flux expressions:

```python
fluxes = cg.get_flux_expressions(
    rate_var="k",
    species_var="y",
    idx_prefix="idx_",
    flux_var="flux"
)
```

**Output:**
```cpp
flux[0] = k[0] * y[idx_h] * y[idx_o];
flux[1] = k[1] * y[idx_h2] * y[idx_o];
flux[2] = k[2] * y[idx_c] * y[idx_o2];
```

### ODE Expressions

Generate ODE right-hand side from fluxes:

```python
odes = cg.get_ode_expressions(
    flux_var="flux",
    species_var="y",
    idx_prefix="idx_",
    derivative_prefix="d"
)
```

**Output:**
```cpp
dy[idx_h] = 0.0 - flux[0] + flux[1];
dy[idx_o] = 0.0 - flux[0] - flux[1] + flux[2];
dy[idx_oh] = 0.0 + flux[0] + flux[1];
```

### Complete ODE System

Generate optimized ODE system with CSE:

```python
odes = cg.get_ode(
    idx_offset=0,
    use_cse=True,
    ode_var="dydt"
)
```

**Output:**
```cpp
const double cse0 = k[0] * y[0];
const double cse1 = k[1] * y[1];
const double cse2 = cse0 * y[2];

dydt[0] = -cse2 + cse1;
dydt[1] = -cse1 + cse0;
dydt[2] = cse2 - cse0;
```

### Jacobian Matrix

Generate analytical Jacobian (∂f/∂y):

```python
jac = cg.get_jacobian(
    idx_offset=0,
    use_cse=True,
    jac_var="J"
)
```

**Output:**
```cpp
const double cse0 = k[0] * y[1];
const double cse1 = k[1] * y[0];

J[0][0] = -cse1;
J[0][1] = -cse0;
J[1][0] = cse1;
J[1][1] = cse0;
```

## Common Subexpression Elimination (CSE)

CSE is an optimization that identifies and extracts repeated subexpressions.

### Without CSE

```python
rates = cg.get_rates(use_cse=False)
```

**Output:**
```cpp
k[0] = 1.2e-10 * sqrt(tgas) * pow(tgas/300, 0.5);
k[1] = 3.4e-11 * sqrt(tgas) * exp(-500/tgas);
k[2] = 5.6e-12 * sqrt(tgas) * pow(tgas/300, 0.5);
```

`sqrt(tgas)` and `pow(tgas/300, 0.5)` are computed multiple times.

### With CSE

```python
rates = cg.get_rates(use_cse=True)
```

**Output:**
```cpp
const double x0 = sqrt(tgas);
const double x1 = pow(tgas/300, 0.5);
const double x2 = exp(-500/tgas);

k[0] = 1.2e-10 * x0 * x1;
k[1] = 3.4e-11 * x0 * x2;
k[2] = 5.6e-12 * x0 * x1;
```

Shared expressions computed once and reused.

### CSE Benefits

- **Performance**: Reduces redundant calculations (20-50% speedup)
- **Code size**: Shorter generated code
- **Accuracy**: Consistent evaluation of shared terms

**Always use CSE for production code:**

```python
rates = cg.get_rates(use_cse=True)
odes = cg.get_ode(use_cse=True)
jac = cg.get_jacobian(use_cse=True)
```

## Customization

### Array Indexing

Control array indexing offset:

```python
# 0-based (C/C++/Python)
code = cg.get_rates(idx_offset=0)
# Output: k[0], k[1], k[2], ...

# 1-based (Fortran)
code = cg.get_rates(idx_offset=1)
# Output: k(1), k(2), k(3), ...

# Custom offset
code = cg.get_rates(idx_offset=5)
# Output: k[5], k[6], k[7], ...
```

### Bracket Styles

Override default bracket styles:

```python
# C++ with parentheses
cg = Codegen(network=net, lang="c++", brac_format="()")
# Output: k(0), k(1), ...

# Python with parentheses
cg = Codegen(network=net, lang="py", brac_format="()")
# Output: k(0), k(1), ...
```

### Matrix Formats

Customize 2D array indexing:

```python
# C++ with comma separation
cg = Codegen(network=net, lang="c++", matrix_format="[,]")
jac = cg.get_jacobian(jac_var="J")
# Output: J[0,0], J[0,1], ...

# Fortran style
cg = Codegen(network=net, lang="c++", matrix_format="(,)")
# Output: J(0,0), J(0,1), ...
```

### Variable Names

Customize variable names:

```python
# Custom rate variable
rates = cg.get_rates(rate_variable="rate_coef")
# Output: rate_coef[0] = ...

# Custom ODE variable
odes = cg.get_ode(ode_var="rhs")
# Output: rhs[0] = ...

# Custom Jacobian variable
jac = cg.get_jacobian(jac_var="jac_matrix")
# Output: jac_matrix[0][0] = ...
```

## Language-Specific Examples

### Complete C++ Module

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="c++")

code = f"""
#ifndef CHEMISTRY_H
#define CHEMISTRY_H

#include <cmath>

namespace chemistry {{

{cg.get_commons(idx_prefix="idx_", definition_prefix="constexpr int ")}

void compute_rates(double* k, double tgas) {{
{cg.get_rates(rate_variable="k", use_cse=True)}
}}

void compute_odes(double* dydt, const double* y, const double* k) {{
{cg.get_ode(ode_var="dydt", use_cse=True)}
}}

void compute_jacobian(double** J, const double* y, const double* k) {{
{cg.get_jacobian(jac_var="J", use_cse=True)}
}}

}} // namespace chemistry

#endif // CHEMISTRY_H
"""

with open("chemistry.h", "w") as f:
    f.write(code)
```

### Complete Fortran Module

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="f90")

code = f"""
module chemistry
  implicit none
  
{cg.get_commons(idx_prefix="idx_", definition_prefix="  integer, parameter :: ")}
  
contains

  subroutine compute_rates(k, tgas)
    real(8), intent(out) :: k(nreactions)
    real(8), intent(in) :: tgas
    
{cg.get_rates(rate_variable="k", use_cse=True)}
  end subroutine compute_rates

  subroutine compute_odes(dydt, y, k)
    real(8), intent(out) :: dydt(nspecs)
    real(8), intent(in) :: y(nspecs)
    real(8), intent(in) :: k(nreactions)
    
{cg.get_ode(ode_var="dydt", use_cse=True)}
  end subroutine compute_odes

  subroutine compute_jacobian(jac, y, k)
    real(8), intent(out) :: jac(nspecs, nspecs)
    real(8), intent(in) :: y(nspecs)
    real(8), intent(in) :: k(nreactions)
    
{cg.get_jacobian(jac_var="jac", use_cse=True)}
  end subroutine compute_jacobian

end module chemistry
"""

with open("chemistry.f90", "w") as f:
    f.write(code)
```

### Complete Python Module

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="python")

code = f"""
import numpy as np
from math import sqrt, exp, log, pow

# Species indices and counts
{cg.get_commons(idx_prefix="idx_", definition_prefix="")}

def compute_rates(tgas):
    k = np.zeros(nreactions)
{cg.get_rates(rate_variable="k", use_cse=True)}
    return k

def compute_odes(y, k):
    dydt = np.zeros(nspecs)
{cg.get_ode(ode_var="dydt", use_cse=True)}
    return dydt

def compute_jacobian(y, k):
    jac = np.zeros((nspecs, nspecs))
{cg.get_jacobian(jac_var="jac", use_cse=True, matrix_format="[,]")}
    return jac
"""

with open("chemistry.py", "w") as f:
    f.write(code)
```

## Integration Examples

### With CVODE/SUNDIALS

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="c")

code = f"""
#include <cvode/cvode.h>
#include <nvector/nvector_serial.h>

{cg.get_commons(definition_prefix="#define ")}

static int rhs(realtype t, N_Vector y, N_Vector ydot, void* user_data) {{
    realtype* ydata = N_VGetArrayPointer(y);
    realtype* ydotdata = N_VGetArrayPointer(ydot);
    realtype tgas = *(realtype*)user_data;
    
    // Compute rates
    realtype k[nreactions];
{cg.get_rates(rate_variable="k", use_cse=True)}
    
    // Compute ODE
{cg.get_ode(ode_var="ydotdata", use_cse=True)}
    
    return 0;
}}
"""
```

### With SciPy (Python)

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="python")

code = f"""
from scipy.integrate import solve_ivp
import numpy as np

{cg.get_commons()}

def chemistry_rhs(t, y, tgas):
    k = np.zeros(nreactions)
{cg.get_rates(rate_variable="k", use_cse=True)}
    
    dydt = np.zeros(nspecs)
{cg.get_ode(ode_var="dydt", use_cse=True)}
    
    return dydt

# Solve ODE
y0 = np.zeros(nspecs)
y0[idx_h2] = 1.0e4
tgas = 100.0

sol = solve_ivp(
    lambda t, y: chemistry_rhs(t, y, tgas),
    [0, 1e10],
    y0,
    method='BDF'
)
"""
```

## Best Practices

### 1. Always Use CSE

```python
# Good - optimized
rates = cg.get_rates(use_cse=True)
odes = cg.get_ode(use_cse=True)

# Bad - slower, larger code
rates = cg.get_rates(use_cse=False)
```

### 2. Match Language Conventions

```python
# C++: 0-based, semicolons
cg_cpp = Codegen(network=net, lang="c++")
code = cg_cpp.get_rates(idx_offset=0)

# Fortran: 1-based, no semicolons
cg_f90 = Codegen(network=net, lang="f90")
code = cg_f90.get_rates(idx_offset=1)
```

### 3. Review Generated Code

```python
# Generate and inspect
code = cg.get_rates(use_cse=True)
print(code)  # Check output

# Save and review
with open("rates.cpp", "w") as f:
    f.write(code)
# Open in editor, check syntax
```

### 4. Use Consistent Variable Names

```python
# Consistent naming across components
commons = cg.get_commons(idx_prefix="idx_")
rates = cg.get_rates(rate_variable="k")
fluxes = cg.get_flux_expressions(rate_var="k", species_var="y")
odes = cg.get_ode_expressions(flux_var="flux", species_var="y")
```

### 5. Test Generated Code

```python
# Generate code
code = cg.get_rates(use_cse=True)

# Save to file
with open("rates.cpp", "w") as f:
    f.write(code)

# Test compilation
import subprocess
result = subprocess.run(
    ["g++", "-c", "rates.cpp"],
    capture_output=True
)
if result.returncode != 0:
    print("Compilation failed:", result.stderr)
```

## Performance Tips

### CSE Impact

```python
import time

# Without CSE
start = time.time()
code_no_cse = cg.get_rates(use_cse=False)
time_no_cse = time.time() - start

# With CSE
start = time.time()
code_cse = cg.get_rates(use_cse=True)
time_cse = time.time() - start

print(f"Without CSE: {len(code_no_cse)} chars, {time_no_cse:.3f}s")
print(f"With CSE: {len(code_cse)} chars, {time_cse:.3f}s")
```

### Large Networks

For networks with >1000 reactions:

1. Use CSE (essential)
2. Generate code in chunks if needed
3. Consider compiler optimizations
4. Test compilation time

## Troubleshooting

### Issue: Undefined Variables

```cpp
// Error: 'tgas' was not declared
k[0] = 1.2e-10 * tgas;
```

**Solution:** Ensure variables are passed as function parameters.

### Issue: Array Index Out of Bounds

```cpp
// Wrong offset for 1-based arrays
k[0] = ...  // Should be k[1] for Fortran
```

**Solution:** Match `idx_offset` to language convention.

### Issue: Compilation Errors

**Solution:** Check generated code syntax, add necessary headers/imports.

## See Also

- [Codegen API](../api/codegen.md) - Complete API reference
- [Template Syntax](template-syntax.md) - Template-based generation
- [CLI](../api/cli.md) - Command-line code generation
- [Tutorial: Code Generation](../tutorials/code-generation.md) - Hands-on tutorial

---

**Next:** Learn about [Template Syntax](template-syntax.md) for advanced code generation.
