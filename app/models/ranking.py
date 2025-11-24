import numpy as np
from scipy.stats import norm, kendalltau
import math
import itertools
from typing import List, Tuple, Dict, Optional, Any

class RankingEngine:
    def __init__(self, items: List[str], initial_mu: float = 25.0, initial_sigma: float = 8.333, target_sigma: float = None):
        """
        Initialize the ranking engine.
        items: list of item IDs
        initial_mu: Initial mean skill
        initial_sigma: Initial standard deviation (uncertainty)
        target_sigma: Target standard deviation for convergence. 
                      Defaults to initial_sigma / 2.0 (approx 4.16), which offers a good balance 
                      between accuracy and number of comparisons (approx N*3 comparisons).
        """
        self.items = items
        self.initial_mu = initial_mu
        self.initial_sigma = initial_sigma
        self.target_sigma = target_sigma if target_sigma is not None else initial_sigma / 2.0
        self.mu: Dict[str, float] = {item: initial_mu for item in items}
        self.sigma: Dict[str, float] = {item: initial_sigma for item in items}
        self.comparisons: List[Tuple[str, str]] = [] # List of (winner, loser) tuples
        self.beta = initial_sigma / 2.0 # Distance that guarantees about 76% chance of winning
        self.tau = initial_sigma / 100.0 # Dynamic factor

    def update(self, winner: str, loser: str):
        """
        Update the ratings based on a comparison result using a simplified Bayesian update (TrueSkill-like).
        """
        self.comparisons.append((winner, loser))
        
        mu_w = self.mu[winner]
        sigma_w = self.sigma[winner]
        mu_l = self.mu[loser]
        sigma_l = self.sigma[loser]
        
        c = math.sqrt(2 * self.beta**2 + sigma_w**2 + sigma_l**2)
        diff = mu_w - mu_l
        t = diff / c
        
        # V and W functions for Gaussian truncation
        # Explicitly cast to float to avoid numpy array type issues if inputs were numpy types
        v = float(norm.pdf(t) / norm.cdf(t))
        w = v * (v + t)
        
        # Update means
        self.mu[winner] = mu_w + (sigma_w**2 / c) * v
        self.mu[loser] = mu_l - (sigma_l**2 / c) * v
        
        # Update variances
        self.sigma[winner] = math.sqrt(sigma_w**2 * (1 - (sigma_w**2 / c**2) * w))
        self.sigma[loser] = math.sqrt(sigma_l**2 * (1 - (sigma_l**2 / c**2) * w))

    def get_next_pair(self) -> Optional[Tuple[str, str]]:
        """
        Select the next pair to compare using uncertainty sampling.
        We want to compare items with high uncertainty or items that are close in rank (hard to distinguish).
        A simple heuristic is to pick the pair with the highest probability of a draw (closest means) 
        weighted by their uncertainty.
        """
        # If we are converged, we don't need more comparisons
        if self.is_converged():
            return None

        best_pair = None
        max_score = -1.0
        
        # Generate all unique pairs
        pairs = list(itertools.combinations(self.items, 2))
        
        # Filter out pairs that have already been compared directly
        existing_pairs = set()
        for w, l in self.comparisons:
            existing_pairs.add(tuple(sorted((w, l))))
            
        available_pairs = [p for p in pairs if tuple(sorted(p)) not in existing_pairs]
        
        if not available_pairs:
            return None

        # Scoring function: maximize uncertainty (sigma) and minimize distance (mu diff)
        # This is equivalent to finding the pair with the highest "match quality"
        for p1, p2 in available_pairs:
            mu1, sigma1 = self.mu[p1], self.sigma[p1]
            mu2, sigma2 = self.mu[p2], self.sigma[p2]
            
            # Match quality (probability of draw)
            c = math.sqrt(2 * self.beta**2 + sigma1**2 + sigma2**2)
            delta_mu = abs(mu1 - mu2)
            quality = math.exp(-(delta_mu**2) / (2 * c**2))
            
            # We can also factor in total uncertainty to encourage exploring high-variance items
            uncertainty_bonus = (sigma1 + sigma2) / (2 * 8.333) 
            
            score = quality * (1 + uncertainty_bonus)
            
            if score > max_score:
                max_score = score
                best_pair = (p1, p2)
                
        return best_pair

    def get_ranking(self) -> List[str]:
        """
        Return the current ranking sorted by mean skill.
        """
        ranking = sorted(self.items, key=lambda x: self.mu[x], reverse=True)
        return ranking

    def get_kendall_tau(self) -> float:
        """
        Calculate Kendall Tau correlation between current ranking and a simulated "true" ranking 
        (or just stability metric). 
        For this requirement, we might need to compare against the previous iteration or a sample.
        R11 says: "between the current ranking and the Bayesian posterior sample ranking"
        """
        current_ranking = self.get_ranking()
        
        # Sample from the posterior to get a "possible" true ranking
        sampled_scores = {item: np.random.normal(self.mu[item], self.sigma[item]) for item in self.items}
        sampled_ranking = sorted(self.items, key=lambda x: sampled_scores[x], reverse=True)
        
        # Calculate Kendall Tau
        # We need to map items to their ranks for the calculation
        rank_map_current = {item: i for i, item in enumerate(current_ranking)}
        rank_map_sampled = {item: i for i, item in enumerate(sampled_ranking)}
        
        x = [rank_map_current[item] for item in self.items]
        y = [rank_map_sampled[item] for item in self.items]
        
        tau_result = kendalltau(x, y)
        # kendalltau returns a SignificanceResult object or tuple depending on scipy version
        # Accessing by index 0 is safer for older versions too
        # Explicitly cast to float to satisfy type checker
        val = tau_result[0]
        if isinstance(val, (float, int)):
             return float(val)
        return 0.0

    def total_comparisons(self) -> int:
        n = len(self.items)
        return max(0, int(n * (n - 1) / 2))

    def is_converged(self) -> bool:
        """
        Check if the ranking has converged based on the average uncertainty (sigma).
        """
        if not self.items:
            return True
        avg_sigma = sum(self.sigma.values()) / len(self.items)
        return avg_sigma <= self.target_sigma

    def is_complete(self) -> bool:
        """
        Check if the ranking is complete.
        It is complete if it has converged OR if all possible pairs have been compared.
        """
        if self.is_converged():
            return True
            
        total = self.total_comparisons()
        if total == 0:
            return True
        return len(self.comparisons) >= total

    def get_progress(self) -> float:
        """
        Get the progress of the ranking process.
        Progress is defined by the reduction in uncertainty (sigma) towards the target sigma.
        """
        if self.is_complete():
            return 100.0
            
        # Calculate progress based on sigma reduction
        current_avg_sigma = sum(self.sigma.values()) / len(self.items)
        
        # Avoid division by zero
        if self.initial_sigma <= self.target_sigma:
            return 100.0
            
        sigma_progress = (self.initial_sigma - current_avg_sigma) / (self.initial_sigma - self.target_sigma)
        
        # Clamp between 0 and 100 (just in case sigma increases, which shouldn't happen often in this model)
        return max(0.0, min(100.0, sigma_progress * 100.0))

    def get_inconsistency_level(self) -> float:
        """
        Detect cycles or inconsistencies.
        Simple check: if A > B and B > C, but C > A in comparisons.
        This is computationally expensive for all cycles, but we can check for direct conflicts 
        if we allowed re-voting (which we don't usually).
        
        For a DAG check or "problematic edges", we can count how many edges violate the current sorted order.
        """
        current_ranking = self.get_ranking()
        rank_map = {item: i for i, item in enumerate(current_ranking)}
        
        violations = 0
        for w, l in self.comparisons:
            # If winner is ranked lower (higher index) than loser in the current estimated ranking
            if rank_map[w] > rank_map[l]:
                violations += 1
                
        if not self.comparisons:
            return 0.0
            
        return (violations / len(self.comparisons)) * 100
