"""Symbolic checks for the approved voluntary-buffer baseline.

Run: python model/verify_foc.py
Dependency: SymPy. This script verifies algebra, not equilibrium existence
or the analytical conditions needed to differentiate an optimum.
"""

import sympy as sp


def equal(label, actual, expected):
    residual = sp.simplify(actual - expected)
    if residual != 0:
        raise AssertionError(f"{label}: nonzero residual {residual}")
    print(f"PASS: {label}")


def require(label, condition):
    if condition is not True:
        raise AssertionError(f"{label}: sign not established ({condition})")
    print(f"PASS: {label}")


def main():
    a = sp.Symbol("a", positive=True)
    e, z, u, beta, A, chi, rho = sp.symbols(
        "e z u beta A chi rho", real=True
    )
    z_u = beta * A + u + chi * rho

    # Valid only when -a < z < a. The negative part is then integrated
    # from the lower support endpoint to the zero-liquidity threshold.
    integral = sp.integrate((-z - e) / (2 * a), (e, -a, -z))
    L = (a - z) ** 2 / (4 * a)
    pi = (a - z) / (2 * a)
    equal("interior uniform expected-deficit integral", integral, L)
    L_u = L.subs(z, z_u)
    pi_u = pi.subs(z, z_u)
    equal("interior dL/du = -pi", sp.diff(L_u, u), -pi_u)
    equal("interior d2L/du2 = 1/(2a)", sp.diff(L_u, u, 2), 1 / (2 * a))
    equal("interior dpi/du = -1/(2a)", sp.diff(pi_u, u), -1 / (2 * a))

    # Outside the interior, L=-z (certain deficit) or L=0 (no deficit).
    equal("certain-deficit derivative", sp.diff(-z_u, u), -1)
    equal("no-deficit derivative", sp.diff(sp.Integer(0), u), 0)
    equal("lower-support value joins", L.subs(z, -a), a)
    equal("upper-support value joins", L.subs(z, a), 0)
    equal("lower-support slope joins", sp.diff(L, z).subs(z, -a), -1)
    equal("upper-support slope joins", sp.diff(L, z).subs(z, a), 0)

    kappa, h = sp.symbols("kappa h", positive=True)
    V = kappa * u + h * L_u
    equal("single-state marginal cost", sp.diff(V, u), kappa - h * pi_u)
    curvature = sp.diff(V, u, 2)
    equal("single-state convexity expression", curvature, h / (2 * a))
    require("positive curvature when h>0 and threshold is inside support",
            curvature.is_positive)

    # Two-state curvature, conditional on both thresholds inside support.
    a0, a1, h0, h1 = sp.symbols("a0 a1 h0 h1", positive=True)
    z0, z1, p = sp.symbols("z0 z1 p", real=True)
    two_state_V = kappa * u + (1-p)*h0*(a0-z0-u)**2/(4*a0) \
        + p*h1*(a1-z1-u)**2/(4*a1)
    equal("two-state weighted curvature", sp.diff(two_state_V, u, 2),
          (1-p)*h0/(2*a0) + p*h1/(2*a1))

    psi, phi = sp.symbols("psi phi", real=True)
    qI, qF, ell = sp.symbols("q_I q_F ell", nonnegative=True)
    composite = psi*qI + (1-psi)*(phi*qF + (1-phi)*ell)
    equal("exclusive funding weights sum to one",
          psi + (1-psi)*phi + (1-psi)*(1-phi), 1)
    equal("deficit-composite rewrite", composite,
          psi*qI + (1-psi)*(ell-phi*(ell-qF)))

    RD, corpus = sp.symbols("R_D corpus", nonnegative=True)
    Delta = sp.Symbol("Delta", positive=True)
    rationed_phi = (corpus + RD) / Delta
    rationed_h = composite.subs(phi, rationed_phi)
    h_RD = sp.diff(rationed_h, RD)
    equal("rationed coverage derivative", sp.diff(rationed_phi, RD), 1/Delta)
    equal("rationed private-cost derivative", h_RD,
          -(1-psi)*(ell-qF)/Delta)
    equal("fully covered private-cost derivative",
          sp.diff(composite.subs(phi, 1), RD), 0)
    equal("capacity derivative in NU", sp.diff(corpus+RD, RD), 1)
    equal("capacity derivative in U", sp.diff(RD, RD), 1)

    # Differentiating M(u,R_D)=kappa gives M_u du/dR_D + M_R_D=0.
    # Here M_u=-D and M_R_D=pi*h_RD in a single rationed state.
    D, pi_prob = sp.symbols("D pi_prob", positive=True)
    du_RD = pi_prob*h_RD / D
    equal("implicit-function differentiated FOC", (-D)*du_RD + pi_prob*h_RD,
          0)
    equal("conditional buffer derivative", du_RD,
          -pi_prob*(1-psi)*(ell-qF)/(Delta*D))

    # Strict conditions: positive gap, residual fraction, deficit probability,
    # Delta, and curvature. These parameterizations encode ell>qF, psi<1.
    gap, residual = sp.symbols("gap residual", positive=True)
    strict_derivative = sp.simplify(
        du_RD.subs({ell: qF+gap, psi: 1-residual})
    )
    require("strictly negative conditional backing derivative",
            strict_derivative.is_negative)
    equal("zero derivative if public and uncovered costs coincide",
          du_RD.subs(ell, qF), 0)
    equal("zero derivative if all deficits are interbank-funded",
          du_RD.subs(psi, 1), 0)

    # In the multistate result each state contributes a nonnegative term.
    t0, t1 = sp.symbols("t0 t1", nonnegative=True)
    aggregate_derivative = -gap*(t0+t1)/D
    require("weakly negative multistate derivative",
            aggregate_derivative.is_nonpositive)
    t_strict = sp.Symbol("t_strict", positive=True)
    require("strict sign with at least one positive state contribution",
            aggregate_derivative.subs(t0, t_strict).is_negative)

    print("All symbolic checks passed.")
    print("Scope: interior-support algebra and conditional best-response effects.")
    print("Not verified: equilibrium feedbacks, calibration, or contract accounting.")


if __name__ == "__main__":
    main()
