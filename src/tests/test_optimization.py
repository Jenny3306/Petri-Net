import unittest
import sys
import os

# --- SETUP PATHS ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- IMPORT CLASSES ---
try:
    from optimization.optimizer import MarkingOptimizer
    from utils import PetriNet, Marking
    from bdd_reachability.symbolic_reachability import BDDReachability
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import modules. Details: {e}")
    sys.exit(1)

class TestMarkingOptimizerIntegration(unittest.TestCase):
    
    def setUp(self):
        pass

    def _build_net_and_solve(self, places, transitions, arcs):
        """Helper: Builds real PetriNet and runs BDD Reachability."""
        # 1. Build Net (Task 1)
        net = PetriNet()
        for p, token in places: net.add_place(p, has_token=token)
        for t in transitions: net.add_transition(t)
        for s, t in arcs: net.add_arc(s, t)
            
        # 2. Compute Reachability (Task 3)
        solver = BDDReachability(net)
        solver.initialize_bdd() 
        solver.compute_symbolic_reachability(net.initial_marking)
        return solver, net

    # ----------------------------------------------------------------
    # Test Cases
    # ----------------------------------------------------------------

    def test_01_parse_weights(self):
        """Test 1: Weight string parsing."""
        optimizer = MarkingOptimizer(PetriNet())
        weights = optimizer.get_weights_from_input("p1=10, p2=-5, p3=0")
        self.assertEqual(weights['p1'], 10)
        self.assertEqual(weights['p2'], -5)

    def test_02_maximize_linear_chain(self):
        """Test 2: Linear Chain (p1 -> p2 -> p3)."""
        # Linear chain: p1 -> p2 -> p3
        places = [('p1', True), ('p2', False), ('p3', False)]
        trans, arcs = ['t1', 't2'], [('p1', 't1'), ('t1', 'p2'), ('p2', 't2'), ('t2', 'p3')]
        solver, net = self._build_net_and_solve(places, trans, arcs)
        optimizer = MarkingOptimizer(net)
        
        # Case A: Uniform weights
        best_m, val, _ = optimizer.find_max_score_marking(solver, {'p1': 1, 'p2': 1, 'p3': 1})
        self.assertIsNotNone(best_m)
        self.assertEqual(val, 1)
        
        # Case B: Prefer p3 (Weight 10)
        best_m, val, _ = optimizer.find_max_score_marking(solver, {'p1': 1, 'p2': 2, 'p3': 10})
        self.assertIsNotNone(best_m)
        assert best_m is not None
        self.assertEqual(val, 10)
        # best_m should include p3==1
        self.assertEqual(best_m.get('p3', 0), 1)

    def test_03_optimization_choice(self):
        """Test 3: Conflict/Choice (p1 -> p2 OR p3)."""
        # Conflict / choice: p1 -> p2 OR p3
        places = [('p1', True), ('p2', False), ('p3', False)]
        trans = ['t1', 't2']
        arcs = [('p1', 't1'), ('t1', 'p2'), ('p1', 't2'), ('t2', 'p3')]
        solver, net = self._build_net_and_solve(places, trans, arcs)
        
        # p3 (5) > p2 (3) -> Must pick p3
        weights = {'p1': 1, 'p2': 3, 'p3': 5}
        best_m, val, _ = MarkingOptimizer(net).find_max_score_marking(solver, weights)
        
        self.assertIsNotNone(best_m)
        assert best_m is not None
        self.assertEqual(val, 5)
        self.assertEqual(best_m.get('p3', 0), 1)

    def test_04_optimization_fork(self):
        """Test 4: Parallel Fork (p1 -> {p2, p3})."""
        # Parallel fork: p1 -> {p2, p3}
        places = [('p1', True), ('p2', False), ('p3', False)]
        trans, arcs = ['t1'], [('p1', 't1'), ('t1', 'p2'), ('t1', 'p3')]
        solver, net = self._build_net_and_solve(places, trans, arcs)
        
        # Score = p2 + p3 = 3 + 4 = 7
        weights = {'p1': 1, 'p2': 3, 'p3': 4}
        best_m, val, _ = MarkingOptimizer(net).find_max_score_marking(solver, weights)
        
        self.assertIsNotNone(best_m)
        assert best_m is not None
        self.assertEqual(val, 7)
        self.assertEqual(best_m.get('p2', 0), 1)
        self.assertEqual(best_m.get('p3', 0), 1)

    def test_05_negative_weights(self):
        """Test 5: Negative Weights (Minimization)."""
        # Negative weights: optimizer prefers positive-marked places
        places = [('p1', True), ('p2', False)]
        trans, arcs = ['t1'], [('p1', 't1'), ('t1', 'p2')]
        solver, net = self._build_net_and_solve(places, trans, arcs)
        
        # Avoid p1 (-10), select p2 (5)
        weights = {'p1': -10, 'p2': 5}
        best_m, val, _ = MarkingOptimizer(net).find_max_score_marking(solver, weights)
        
        self.assertIsNotNone(best_m)
        assert best_m is not None
        self.assertEqual(val, 5)
        self.assertEqual(best_m.get('p2', 0), 1)

    def test_06_empty_weights(self):
        """Test 6: No weights provided."""
        # No weights provided -> score should be 0
        solver, net = self._build_net_and_solve([('p1', True)], [], [])
        
        # Default score is 0
        best_m, val, _ = MarkingOptimizer(net).find_max_score_marking(solver, {})
        
        self.assertIsNotNone(best_m)
        self.assertEqual(val, 0)

    # ----------------------------------------------------------------
    # Edge-case tests (previously in separate file)
    # ----------------------------------------------------------------

    def test_07_uninitialized_solver_returns_none(self):
        """Test 7: Uninitialized solver returns (None, None, float)."""
        # Uninitialized solver should return (None, None, float)
        net = PetriNet()
        opt = MarkingOptimizer(net)

        solver = BDDReachability(net)  # do not initialize
        best_m, val, run_time = opt.find_max_score_marking(solver, {'p': 1})

        self.assertIsNone(best_m)
        self.assertIsNone(val)
        self.assertIsInstance(run_time, float)

    def test_08_no_reachable_markings(self):
        """Test 8: No reachable markings (reachable_bdd is false)."""
        # reachable_bdd == false -> no reachable markings
        net = PetriNet()
        net.add_place('p1', has_token=False)

        solver = BDDReachability(net)
        solver.initialize_bdd()
        mgr = getattr(solver, 'bdd_manager', None)
        if mgr is not None:
            solver.reachable_bdd = mgr.false
        else:
            solver.reachable_bdd = None

        opt = MarkingOptimizer(net)
        best_m, val, run_time = opt.find_max_score_marking(solver, {'p1': 10})

        self.assertIsNone(best_m)
        self.assertIsNone(val)
        self.assertIsInstance(run_time, float)

    def test_09_tie_handling_returns_one_of_maxima(self):
        """Test 9: Tie handling — returns one valid maximal marking."""
        # Tie handling: choose any maximal marking
        net = PetriNet()
        net.add_place('p1', has_token=True)
        net.add_place('p2', has_token=False)
        net.add_place('p3', has_token=False)
        net.add_transition('t1')
        net.add_transition('t2')
        net.add_arc('p1', 't1')
        net.add_arc('t1', 'p2')
        net.add_arc('p1', 't2')
        net.add_arc('t2', 'p3')

        solver = BDDReachability(net)
        solver.compute_symbolic_reachability(net.initial_marking)

        opt = MarkingOptimizer(net)
        weights = {'p1': 0, 'p2': 5, 'p3': 5}
        best_m, val, run_time = opt.find_max_score_marking(solver, weights)

        self.assertEqual(val, 5)
        self.assertIsNotNone(best_m)
        possible = [
            {'p1': 0, 'p2': 1, 'p3': 0},
            {'p1': 0, 'p2': 0, 'p3': 1}
        ]
        self.assertIn(best_m, possible)

    def test_10_malformed_weight_input(self):
        """Test 10: Malformed weight string is partially parsed."""
        # Malformed weight input: valid entries parsed, invalid skipped
        opt = MarkingOptimizer(PetriNet())
        parsed = opt.get_weights_from_input("p1=5, p2=bad, =7, p3=2, , p4=3a")

        self.assertIn('p1', parsed)
        self.assertEqual(parsed['p1'], 5)
        self.assertIn('p3', parsed)
        self.assertEqual(parsed['p3'], 2)
        self.assertNotIn('p2', parsed)
        self.assertNotIn('p4', parsed)
        # parsed content assertions above

    def test_11_missing_weights_treated_as_zero_and_return_types(self):
        """Test 11: Missing weights treated as zero; return types correct."""
        # Missing weights should be treated as zero; return types validated
        net = PetriNet()
        net.add_place('p1', has_token=True)
        net.add_place('p2', has_token=False)
        net.add_transition('t1')
        net.add_arc('p1', 't1')
        net.add_arc('t1', 'p2')

        solver = BDDReachability(net)
        solver.compute_symbolic_reachability(net.initial_marking)

        opt = MarkingOptimizer(net)
        weights = {'p2': 10}
        best_m, val, run_time = opt.find_max_score_marking(solver, weights)

        self.assertIsInstance(run_time, float)
        self.assertIsInstance(best_m, dict)
        self.assertEqual(val, 10)

if __name__ == '__main__':
    unittest.main()