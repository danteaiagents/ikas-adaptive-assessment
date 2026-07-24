"""IRT, BKT, and Bayesian update mathematical utilities for the adaptive engine."""

import numpy as np
from typing import List, Dict, Tuple


# =============================================================================
# Item Response Theory (IRT) - 3 Parameter Logistic Model
# =============================================================================

def irt_3pl_probability(theta: float, a: float, b: float, c: float) -> float:
    """
    Compute probability of correct response under 3PL IRT model.
    
    P(θ) = c + (1 - c) / (1 + exp(-a(θ - b)))
    
    Args:
        theta: Student ability estimate (-3.0 to +3.0)
        a: Item discrimination (0.1 to 3.0) 
        b: Item difficulty (-3.0 to +3.0)
        c: Pseudo-guessing parameter (0.0 to 0.25)
    """
    exponent = -a * (theta - b)
    exponent = np.clip(exponent, -500, 500)  # Prevent overflow
    return c + (1.0 - c) / (1.0 + np.exp(exponent))


def fisher_information(theta: float, a: float, b: float, c: float) -> float:
    """
    Compute Fisher Information for an item at given ability level.
    
    I(θ) = a² * (1 - P(θ)) / P(θ) * [(P(θ) - c) / (1 - c)]²
    """
    p = irt_3pl_probability(theta, a, b, c)
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    
    if abs(1.0 - c) < 1e-10:
        return 0.0
    
    return (a ** 2) * ((1.0 - p) / p) * (((p - c) / (1.0 - c)) ** 2)


def estimate_theta_eap(
    responses: List[Dict],
    prior_mean: float = 0.0,
    prior_std: float = 1.0,
    n_quadrature: int = 30
) -> Tuple[float, float]:
    """
    Expected A Posteriori (EAP) estimation of latent ability theta
    using Gauss-Legendre quadrature.
    
    Args:
        responses: List of dicts with keys: 'a', 'b', 'c', 'correct' (1 or 0)
        prior_mean: Mean of prior distribution for theta
        prior_std: Std dev of prior distribution
        n_quadrature: Number of quadrature points (default 30)
    
    Returns:
        (theta_eap, theta_se): Estimated ability and standard error
    """
    if not responses:
        return prior_mean, prior_std
    
    # Gauss-Legendre quadrature points and weights on [-1, 1]
    nodes, weights = np.polynomial.legendre.leggauss(n_quadrature)
    
    # Scale to [-4, 4] range covering practical theta values
    quad_points = nodes * 4.0
    quad_weights = weights * 4.0
    
    # Normal prior
    prior = (1.0 / (np.sqrt(2 * np.pi) * prior_std)) * \
            np.exp(-0.5 * ((quad_points - prior_mean) / prior_std) ** 2)
    
    # Likelihood of observed responses
    likelihood = np.ones_like(quad_points)
    for resp in responses:
        p = irt_3pl_probability(quad_points, resp['a'], resp['b'], resp['c'])
        p = np.clip(p, 1e-10, 1.0 - 1e-10)
        if resp['correct'] == 1:
            likelihood *= p
        else:
            likelihood *= (1.0 - p)
    
    # Posterior = likelihood * prior
    posterior = likelihood * prior
    evidence = np.sum(posterior * quad_weights)
    
    if evidence < 1e-15:
        return prior_mean, prior_std
    
    # EAP estimate
    theta_eap = np.sum(quad_points * posterior * quad_weights) / evidence
    
    # Standard error
    variance = np.sum(((quad_points - theta_eap) ** 2) * posterior * quad_weights) / evidence
    theta_se = float(np.sqrt(max(variance, 1e-10)))
    
    return float(theta_eap), theta_se


# =============================================================================
# Bayesian Knowledge Tracing (BKT)
# =============================================================================

def bkt_update(
    p_know: float,
    correct: bool,
    p_transit: float = 0.1,
    p_guess: float = 0.2,
    p_slip: float = 0.1
) -> float:
    """
    Update BKT mastery probability after observing a response.
    
    Args:
        p_know: Prior probability of mastery P(L_t)
        correct: Whether the answer was correct
        p_transit: Probability of learning transition P(T)
        p_guess: Probability of guessing correctly P(G) 
        p_slip: Probability of slipping P(S)
    
    Returns:
        Updated mastery probability P(L_{t+1})
    """
    p_know = np.clip(p_know, 0.001, 0.999)
    
    if correct:
        # P(L_t | correct) = P(L_t) * (1 - P(S)) / [P(L_t)*(1-P(S)) + (1-P(L_t))*P(G)]
        numerator = p_know * (1.0 - p_slip)
        denominator = p_know * (1.0 - p_slip) + (1.0 - p_know) * p_guess
    else:
        # P(L_t | incorrect) = P(L_t) * P(S) / [P(L_t)*P(S) + (1-P(L_t))*(1-P(G))]
        numerator = p_know * p_slip
        denominator = p_know * p_slip + (1.0 - p_know) * (1.0 - p_guess)
    
    if denominator < 1e-15:
        p_posterior = p_know
    else:
        p_posterior = numerator / denominator
    
    # State transition: P(L_{t+1}) = P(L_t|O_t) + (1 - P(L_t|O_t)) * P(T)
    p_next = p_posterior + (1.0 - p_posterior) * p_transit
    
    return float(np.clip(p_next, 0.001, 0.999))


# =============================================================================
# Graph Belief Propagation
# =============================================================================

def propagate_beliefs(
    edges: List[Dict],
    node_states: Dict[str, float],
    damping: float = 0.5
) -> Dict[str, float]:
    """
    Propagate belief updates through prerequisite graph edges.
    
    P(Q_B=1) = P(Q_B=1|Q_A=1)*P(Q_A=1) + P(Q_B=1|Q_A=0)*(1-P(Q_A=1))
    
    Uses dampened updates (blend with current state) to prevent oscillation.
    
    Args:
        edges: List of dicts with keys: 'source', 'dest', 'p_pass_pass', 'p_pass_fail'
        node_states: Current belief states {node_id: P(pass)}
        damping: Blend factor (0.5 = equal weight to old and new)
    
    Returns:
        Updated node states
    """
    updated = node_states.copy()
    
    for edge in edges:
        src = edge['source']
        dest = edge['dest']
        
        if src not in node_states:
            continue
        
        p_src = node_states[src]
        p_pass_pass = edge.get('p_pass_pass', 0.5)
        p_pass_fail = edge.get('p_pass_fail', 0.5)
        
        # Compute propagated belief
        p_dest_new = p_pass_pass * p_src + p_pass_fail * (1.0 - p_src)
        
        # Dampened update: blend with current state
        current = updated.get(dest, 0.5)
        updated[dest] = float(damping * current + (1.0 - damping) * p_dest_new)
    
    return updated
