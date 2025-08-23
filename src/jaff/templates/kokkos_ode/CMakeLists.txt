# ABOUTME: CMake build file for JAFF-generated Kokkos chemistry solver
# ABOUTME: Links against Kokkos and Kokkos-kernels for ODE solving

cmake_minimum_required(VERSION 3.16)
project(ChemistryODE LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Option to specify Kokkos location or build from source
option(USE_EXTERNAL_KOKKOS "Use an external Kokkos installation" OFF)

if(USE_EXTERNAL_KOKKOS)
    # Find external Kokkos
    find_package(Kokkos REQUIRED)
    find_package(KokkosKernels REQUIRED)
else()
    # Fetch and build Kokkos
    include(FetchContent)
    FetchContent_Declare(
        kokkos
        GIT_REPOSITORY https://github.com/kokkos/kokkos.git
        GIT_TAG 4.7.00
    )
    FetchContent_MakeAvailable(kokkos)
    
    # Fetch and build Kokkos-kernels
    FetchContent_Declare(
        kokkoskernels
        GIT_REPOSITORY https://github.com/kokkos/kokkos-kernels.git
        GIT_TAG 4.7.00
    )
    FetchContent_MakeAvailable(kokkoskernels)
endif()

# Add main executable
add_executable(chemistry_ode chemistry_ode.cpp)

# Link libraries
target_link_libraries(chemistry_ode 
    Kokkos::kokkos
    Kokkos::kokkoskernels
)
