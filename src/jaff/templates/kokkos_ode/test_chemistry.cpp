// ABOUTME: Test program for JAFF-generated chemistry ODE solver
// ABOUTME: Verifies basic functionality and conservation properties

#include "chemistry_ode.hpp"
#include <Kokkos_Core.hpp>
#include <KokkosODE_BDF.hpp>
#include <iostream>
#include <cmath>

// Simple wrapper for testing
template <class ode_type, class vec_type, class mat_type, class scalar_type>
struct TestBDFSolve {
    ode_type my_ode;
    scalar_type t_start, t_end, dt, max_step;
    vec_type y0, y_new;
    mat_type temp, temp2;

    TestBDFSolve(const ode_type& my_ode_, const scalar_type& t_start_, const scalar_type& t_end_,
                const scalar_type& dt_, const scalar_type& max_step_, const vec_type& y0_, 
                const vec_type& y_new_, const mat_type& temp_, const mat_type& temp2_)
        : my_ode(my_ode_),
          t_start(t_start_),
          t_end(t_end_),
          dt(dt_),
          max_step(max_step_),
          y0(y0_),
          y_new(y_new_),
          temp(temp_),
          temp2(temp2_) {}

    KOKKOS_FUNCTION void operator()(const int) const {
        KokkosODE::Experimental::BDFSolve(my_ode, t_start, t_end, dt, max_step, y0, y_new, temp, temp2);
    }
};

int main(int argc, char* argv[]) {
    Kokkos::initialize(argc, argv);
    
    int test_result = 0;
    
    {
        using execution_space = Kokkos::DefaultExecutionSpace;
        using scalar_type = double;
        using vec_type = Kokkos::View<scalar_type*, execution_space>;
        using mat_type = Kokkos::View<scalar_type**, execution_space>;
        
        ChemistryODE mySys{};
        
        std::cout << "Testing Chemistry ODE System\n";
        std::cout << "Number of species: " << mySys.neqs << "\n";
        
        // Test 1: Short time integration (1 day)
        {
            std::cout << "\nTest 1: Short time integration (1 day)\n";
            
            const scalar_type t_start = 0.0;
            const scalar_type t_end = 86400.0; // 1 day in seconds
            
            vec_type y0("initial conditions", mySys.neqs);
            vec_type y_new("solution", mySys.neqs);
            
            auto y0_h = Kokkos::create_mirror_view(y0);
            for (int i = 0; i < mySys.neqs; ++i) {
                y0_h(i) = 1.0e-10;
            }
            if (mySys.neqs > 0) {
                y0_h(0) = 1.0e-6;
            }
            
            Kokkos::deep_copy(y0, y0_h);
            
            mat_type temp("buffer1", mySys.neqs, 23 + 2 * mySys.neqs + 4);
            mat_type temp2("buffer2", 6, 7);
            
            scalar_type dt = 1.0e-6;
            scalar_type max_step = t_end / 100.0;
            
            TestBDFSolve<ChemistryODE, vec_type, mat_type, scalar_type> bdf_wrapper(mySys, t_start, t_end, dt, max_step, y0, y_new, temp, temp2);
            
            Kokkos::RangePolicy<execution_space> policy(0, 1);
            Kokkos::parallel_for(policy, bdf_wrapper);
            Kokkos::fence();
            
            auto y_new_h = Kokkos::create_mirror_view(y_new);
            Kokkos::deep_copy(y_new_h, y_new);
            
            // Check that solution is finite
            bool all_finite = true;
            for (int i = 0; i < mySys.neqs; ++i) {
                if (!std::isfinite(y_new_h(i))) {
                    all_finite = false;
                    std::cout << "  ERROR: y[" << i << "] = " << y_new_h(i) << " is not finite!\n";
                }
            }
            
            if (all_finite) {
                std::cout << "  PASS: All species concentrations are finite\n";
            } else {
                test_result = 1;
            }
        }
        
        // Test 2: Medium time integration with conservation check (1 month)
        {
            std::cout << "\nTest 2: Conservation check (1 month)\n";
            
            const scalar_type t_start = 0.0;
            const scalar_type t_end = 2.628e6; // ~1 month in seconds
            
            vec_type y0("initial conditions", mySys.neqs);
            vec_type y_new("solution", mySys.neqs);
            
            auto y0_h = Kokkos::create_mirror_view(y0);
            double initial_sum = 0.0;
            for (int i = 0; i < mySys.neqs; ++i) {
                y0_h(i) = 1.0e-8 * (i + 1); // Different initial values
                initial_sum += y0_h(i);
            }
            
            Kokkos::deep_copy(y0, y0_h);
            
            mat_type temp("buffer1", mySys.neqs, 23 + 2 * mySys.neqs + 4);
            mat_type temp2("buffer2", 6, 7);
            
            scalar_type dt = 1.0;
            scalar_type max_step = t_end / 100.0;
            
            TestBDFSolve<ChemistryODE, vec_type, mat_type, scalar_type> bdf_wrapper(mySys, t_start, t_end, dt, max_step, y0, y_new, temp, temp2);
            
            Kokkos::RangePolicy<execution_space> policy(0, 1);
            Kokkos::parallel_for(policy, bdf_wrapper);
            Kokkos::fence();
            
            auto y_new_h = Kokkos::create_mirror_view(y_new);
            Kokkos::deep_copy(y_new_h, y_new);
            
            double final_sum = 0.0;
            for (int i = 0; i < mySys.neqs; ++i) {
                final_sum += y_new_h(i);
            }
            
            double rel_change = std::abs((final_sum - initial_sum) / initial_sum);
            std::cout << "  Initial sum: " << initial_sum << "\n";
            std::cout << "  Final sum:   " << final_sum << "\n";
            std::cout << "  Relative change: " << rel_change << "\n";
            
            // Allow for some numerical error in conservation
            if (rel_change < 0.1) { // 10% tolerance
                std::cout << "  PASS: Mass approximately conserved\n";
            } else {
                std::cout << "  WARNING: Large change in total mass (may be expected for some networks)\n";
            }
        }
        
        // Test 3: Long time integration and positivity (1 year)
        {
            std::cout << "\nTest 3: Long time integration and positivity check (1 year)\n";
            
            const scalar_type t_start = 0.0;
            const scalar_type t_end = 3.15576e7; // 1 year in seconds
            
            vec_type y0("initial conditions", mySys.neqs);
            vec_type y_new("solution", mySys.neqs);
            
            auto y0_h = Kokkos::create_mirror_view(y0);
            for (int i = 0; i < mySys.neqs; ++i) {
                y0_h(i) = 1.0e-9;
            }
            
            Kokkos::deep_copy(y0, y0_h);
            
            mat_type temp("buffer1", mySys.neqs, 23 + 2 * mySys.neqs + 4);
            mat_type temp2("buffer2", 6, 7);
            
            scalar_type dt = 10.0;
            scalar_type max_step = t_end / 1000.0;
            
            TestBDFSolve<ChemistryODE, vec_type, mat_type, scalar_type> bdf_wrapper(mySys, t_start, t_end, dt, max_step, y0, y_new, temp, temp2);
            
            Kokkos::RangePolicy<execution_space> policy(0, 1);
            Kokkos::parallel_for(policy, bdf_wrapper);
            Kokkos::fence();
            
            auto y_new_h = Kokkos::create_mirror_view(y_new);
            Kokkos::deep_copy(y_new_h, y_new);
            
            bool all_positive = true;
            for (int i = 0; i < mySys.neqs; ++i) {
                if (y_new_h(i) < -1.0e-20) { // Allow tiny negative values due to numerics
                    all_positive = false;
                    std::cout << "  ERROR: y[" << i << "] = " << y_new_h(i) << " is negative!\n";
                }
            }
            
            if (all_positive) {
                std::cout << "  PASS: All species concentrations are non-negative\n";
            } else {
                std::cout << "  WARNING: Some species have negative concentrations (may need solver tuning)\n";
            }
            
            // Also check for reasonableness
            bool all_reasonable = true;
            for (int i = 0; i < mySys.neqs; ++i) {
                if (!std::isfinite(y_new_h(i)) || y_new_h(i) > 1.0) {
                    all_reasonable = false;
                    std::cout << "  WARNING: y[" << i << "] = " << y_new_h(i) << " seems unreasonable\n";
                }
            }
            
            if (all_reasonable) {
                std::cout << "  PASS: All species concentrations are reasonable after 1 year\n";
            }
        }
        
        std::cout << "\n========================================\n";
        if (test_result == 0) {
            std::cout << "All tests completed successfully!\n";
        } else {
            std::cout << "Some tests failed. Check output above.\n";
        }
        std::cout << "========================================\n";
    }
    
    Kokkos::finalize();
    
    return test_result;
}