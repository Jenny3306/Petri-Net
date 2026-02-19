import time
from typing import Dict, Tuple, Optional, Any

class MarkingOptimizer:
    """
    Class for Task 5: Optimization.
    Finds the marking M in Reach(M0) that maximizes c^T * M.
    Designed to work specifically with the 'dd' library used in Task 3.
    """

    def __init__(self, petri_net_structure, verbose: bool = False):
        """
        Initialize the optimizer.
        Args:
            petri_net_structure: The PetriNet object (from Task 1).
        """
        self.net = petri_net_structure

    def get_weights_from_input(self, text_input: str) -> Dict[str, int]:
        """
        Parse input string "p1=10, p2=-5" into a dictionary.
        """
        weight_map = {}
        if not text_input:
            return weight_map
            
        parts = text_input.split(',')
        for part in parts:
            if '=' in part:
                data = part.split('=')
                try:
                    name = data[0].strip()
                    value = int(data[1].strip())
                    weight_map[name] = value
                except ValueError:
                    print(f"[Warning] Cannot parse weight for '{part}'")
        return weight_map

    def find_max_score_marking(self, task3_solver, place_weights: Dict[str, int], mode: str = 'exact') -> Tuple[Optional[Dict[str, int]], Optional[int], float]:
        """
        Main function for Task 5.
        
        Args:
            task3_solver: The INSTANCE of BDDReachability class from Task 3.
                          (We need this to access .bdd_manager and .reachable_bdd)
            place_weights: Dictionary of weights (e.g. {'p1': 10, 'p2': -2})
            
        Returns:
            (best_marking, max_score, time_taken)
        """
        start_time = time.time()
        
        # Initialize tracking variables
        current_max_score = None 
        best_marking_found = None
        count = 0

        try:
            # Get the necessary tools from Task 3 object
            manager = getattr(task3_solver, "bdd_manager", None)
            reachable = getattr(task3_solver, "reachable_bdd", None)

            # Check if BDD is not initialized
            if manager is None or reachable is None:
                return None, None, time.time() - start_time

            bdd = manager

            # If reachable set is empty
            if reachable == bdd.false:
                return None, None, time.time() - start_time

            # Prepare places and weights (default weight 0)
            places = sorted(getattr(self.net, "places", []))
            weights = {p: int(place_weights.get(p, 0)) for p in places}

            # Fast path: no weights provided -> return any reachable marking with score 0
            if not place_weights:
                try:
                    assign = next(bdd.pick_iter(reachable))
                except StopIteration:
                    return None, None, time.time() - start_time
                marking = {p: (1 if bool(assign.get(p, False)) else 0) for p in places}
                return marking, 0, time.time() - start_time

            # If mode is 'greedy', use the previous greedy heuristic
            if mode == 'greedy':
                sorted_places = sorted(places, key=lambda x: (-weights.get(x, 0), x))
                current_bdd = reachable
                chosen_positives = []
                for p in sorted_places:
                    w = weights.get(p, 0)
                    if w <= 0:
                        continue
                    test_bdd = current_bdd
                    for q in chosen_positives:
                        test_bdd = test_bdd & bdd.var(q)
                        if test_bdd == bdd.false:
                            break
                    if test_bdd == bdd.false:
                        continue
                    test_bdd_p = test_bdd & bdd.var(p)
                    if test_bdd_p != bdd.false:
                        chosen_positives.append(p)
                        current_bdd = test_bdd_p
                final_bdd = reachable
                for q in chosen_positives:
                    final_bdd = final_bdd & bdd.var(q)
                if final_bdd == bdd.false:
                    final_bdd = reachable
                try:
                    assign = next(bdd.pick_iter(final_bdd))
                except StopIteration:
                    return None, None, time.time() - start_time
                marking = {p: (1 if bool(assign.get(p, False)) else 0) for p in places}
                score = sum(int(place_weights.get(p, 0)) for p, v in marking.items() if v)
                current_max_score = score
                best_marking_found = marking
            else:
                # Exact mode: branch-and-bound with BDD pruning
                # Order variables to improve pruning: descending positive weights, then name
                order = sorted(places, key=lambda x: (-max(weights.get(x, 0), 0), x))
                n = len(order)

                # initial lower bound from greedy to speed up pruning
                greedy_assign = {p: 0 for p in places}
                try:
                    ga = next(bdd.pick_iter(reachable))
                    greedy_assign = {p: (1 if bool(ga.get(p, False)) else 0) for p in places}
                    greedy_score = sum(int(place_weights.get(p, 0)) for p, v in greedy_assign.items() if v)
                except StopIteration:
                    greedy_score = float('-inf')

                if greedy_score != float('-inf'):
                    best_score = greedy_score
                    # greedy_assign is a full mapping for all places
                    best_mark = greedy_assign.copy()
                else:
                    best_score = float('-inf')
                    best_mark = None

                # Precompute prefix sums of remaining positive weights for optimistic bound
                pos_weights = [max(weights.get(p, 0), 0) for p in order]
                suffix_pos = [0] * (n + 1)
                for i in range(n - 1, -1, -1):
                    suffix_pos[i] = suffix_pos[i + 1] + pos_weights[i]

                # DFS with pruning
                def dfs(idx, node, assignment, cur_score):
                    nonlocal best_score, best_mark
                    # optimistic bound
                    optimistic = cur_score + suffix_pos[idx]
                    if optimistic <= best_score:
                        return
                    if idx == n:
                        # leaf
                        if cur_score > best_score:
                            best_score = cur_score
                            best_mark = assignment.copy()
                        return

                    p = order[idx]

                    # try p = 1
                    node1 = node & bdd.var(p)
                    if node1 != bdd.false:
                        assignment[p] = 1
                        dfs(idx + 1, node1, assignment, cur_score + weights.get(p, 0))
                        assignment[p] = 0

                    # try p = 0
                    node0 = node & ~bdd.var(p)
                    if node0 != bdd.false:
                        assignment[p] = 0
                        dfs(idx + 1, node0, assignment, cur_score)
                        assignment.pop(p, None)

                # Start dfs
                init_node = reachable
                dfs(0, init_node, {}, 0)

                if best_mark is None:
                    current_max_score = None
                    best_marking_found = None
                else:
                    # ensure marking contains all places
                    marking = {p: int(best_mark.get(p, 0)) for p in places}
                    best_marking_found = marking
                    current_max_score = int(best_score)

        except Exception:
            return None, None, time.time() - start_time

        end_time = time.time()
        run_time = end_time - start_time

        # Return found result (or None if something went wrong)
        if best_marking_found is None:
            return None, None, run_time
        return best_marking_found, current_max_score, run_time