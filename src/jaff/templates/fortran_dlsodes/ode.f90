module ode
    use commons
    contains

    subroutine fex(t, y, ydot)
        implicit none
        real*8::t
        real*8::y(nspecs+1)
        real*8::ydot(nspecs+1)

        !! PREPROCESS_ODE

        !! PREPROCESS_END

    end subroutine fex

end module
