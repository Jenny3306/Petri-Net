import time 
from typing import Dict, List, Optional
import pulp
from dd import autoref as _bdd
from utils import Marking

class DeadlockDetector:
    """
    Deadlock detector using the Hybrid ILP + BDD approach (Generate and Test).
    Now enhanced with Lexicographic Distance Minimization to guide ILP toward
    reachable dead markings.
    """

    def __init__(self, petri_net, reachable_bdd=None, bdd_manager: _bdd.BDD = None, verbose: bool = False):
        self.net = petri_net
        self.reachable_bdd = reachable_bdd
        self.manager = bdd_manager
        self.deadlocks: List[Marking] = []
        self.verbose = verbose

        if self.reachable_bdd is None or self.manager is None:
            raise ValueError("reachable_bdd and bdd_manager must be provided")

        # store initial marking as dict {place:0/1}
        self.initial_marking = petri_net.initial_marking.to_dict()

    def detect_deadlock(self) -> Optional[Dict[str, int]]:
        # trivial enabledness check
        for t in self.net.transitions:
            if len(list(self.net.arcs[t]["input"])) == 0:
                return None

        # ============================================================
        # 1. ILP Model (MINIMIZE distance to initial marking)
        # ============================================================
        prob = pulp.LpProblem("Deadlock_Detection", pulp.LpMinimize)

        # marking variables
        x = pulp.LpVariable.dicts("x", list(self.net.places), cat='Binary')

        self.net.get_incidence()  # ensure incidence matrix is computed

        # transition firing count variables n[t] ≥ 0, integer
        n = pulp.LpVariable.dicts("n", list(self.net.transitions),
                                lowBound=0, cat='Integer')

        # ============================================================
        # 2. Constraints
        # ============================================================

        # State equation constraints: M = M0 + C * n
        for p in self.net.places:
            prob += (
                x[p]
                == self.initial_marking[p]
                + pulp.lpSum(self.net.incidence[p][t] * n[t] for t in self.net.transitions)
            )

        prob += pulp.lpSum([n[t] for t in self.net.transitions])  # MINIMIZE total firings

        # Deadlock constraints: For each transition, at least one place in its preset must be enabled
        for t in self.net.transitions:
            preset = list(self.net.arcs[t]["input"])
            if len(preset) > 0:
                # sum of all tokens in preset <= |preset|-1  (disable)
                prob += pulp.lpSum([x[p] for p in preset]) <= len(preset) - 1

        iteration = 0
        t_ilp_start = time.time()

        # ============================================================
        # ITERATIVE CUTTING LOOP
        # ============================================================
        while True:
            iteration += 1

            # --- Measure ILP Time ---
            status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
            t_ilp_end = time.time()
                

            if status != pulp.LpStatusOptimal:
                return None

            # extract candidate
            candidate_marking = {
                p: int(x[p].varValue if x[p].varValue is not None else 0)
                for p in self.net.places
            }

            # --- Measure BDD Check Time ---
            t_bdd_start = time.time()
            reachable = self._is_reachable(candidate_marking)
            t_bdd_end = time.time()

            if reachable:
                if self.verbose:
                    print(f"[+] Deadlock found after {iteration} ILP iterations.")
                    print(f"   [Time] ILP Solve: {t_ilp_end - t_ilp_start:.6f}s")
                    print(f"   [Time] BDD Check: {t_bdd_end - t_bdd_start:.6f}s")
                deadlock = Marking(candidate_marking)
                self.deadlocks.append(deadlock)
                return deadlock

            # ========================================================
            # Add canonical cut to eliminate this candidate
            # ========================================================
            cut_terms = []
            for p, val in candidate_marking.items():
                if val == 1:
                    cut_terms.append(1 - x[p])
                else:
                    cut_terms.append(x[p])

            prob += pulp.lpSum(cut_terms) >= 1

    # ------------------------------------------------------------
    def _is_reachable(self, marking: Dict[str, int]) -> bool:
        bdd_marking = {p: bool(v) for p, v in marking.items()}
        u = self.manager.let(bdd_marking, self.reachable_bdd)
        return u == self.manager.true

    # ------------------------------------------------------------
    def is_deadlock_free(self) -> bool:
        return self.detect_deadlock() is None