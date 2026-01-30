#ifndef actual_rhs_H
#define actual_rhs_H

#include <AMReX_Array.H>
#include <AMReX_REAL.H>
#include <cmath>

#include <actual_network.H>
#include <burn_type.H>
#include <extern_parameters.H>
#include <jacobian_utilities.H>

using namespace ArrayUtil;
using namespace network_rp;

AMREX_GPU_HOST_DEVICE AMREX_INLINE amrex::Real photorates() { return 0.0; }

AMREX_GPU_HOST_DEVICE AMREX_INLINE void
rhs_specie(const burn_t &state, amrex::Array1D<amrex::Real, 1, neqs> &ydot) {

  using namespace Rates;

  amrex::Real tgas = state.T;
  amrex::Real crate = 0; // placeholder
  amrex::Real av = 0;    // placeholder
  amrex::Real nden = 0;  // placeholder

  // PREPROCESS_ODE
  // PREPROCESS_END
}

AMREX_GPU_HOST_DEVICE AMREX_INLINE Real rhs_eint(const burn_t &state) {

  using namespace Rates;

  amrex::Real tgas = state.T;
}

AMREX_GPU_HOST_DEVICE AMREX_INLINE void
actual_rhs(burn_t &state, amrex::Array1D<amrex::Real, 1, neqs> &ydot) {
  amrex::Real z = redshift;

  Array1D<amrex::Real, 0, NumSpec - 1> X;
  for (int i = 0; i < NumSpec; ++i) {
    X(i) = state.xn[i];
  }
  // YDOTS

  rhs_specie(state, ydot);

  // Edot

  amrex::Real edot = rhs_eint(state);

  // Append the energy equation (this is erg/g/s)

  ydot(net_ienuc) = edot;
}

template <class MatrixType>
AMREX_GPU_HOST_DEVICE AMREX_INLINE void jac_nuc(const burn_t &state,
                                                MatrixType &jac) {

  amrex::Real tgas = state.T;

  // PREPROCESS_JACOBIAN
  // PREPROCESS_END
}

template <class MatrixType>
AMREX_GPU_HOST_DEVICE AMREX_INLINE void actual_jac(const burn_t &state,
                                                   MatrixType &jac) {
  // amrex::Real z = redshift;

  // amrex::Array1D<amrex::Real, 0, NumSpec - 1> X;
  // for (int i = 0; i < NumSpec; ++i) {
  //   X(i) = state.xn[i];
  // }
  // Species Jacobian elements with respect to other species

  jac_nuc(state, jac);
}

AMREX_INLINE
void actual_rhs_init() {}

#endif
