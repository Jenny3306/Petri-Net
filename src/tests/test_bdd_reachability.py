import unittest
from pathlib import Path
from bdd_reachability import BDDReachability
from pnml_parser import PNMLParser
from utils import PetriNet, Marking


class TestBDDReachabilityBasic(unittest.TestCase):
    """Basic BDD reachability analyzer tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.net = PetriNet()
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_initialization(self):
        """Test BDD reachability analyzer initialization."""
        self.assertIsNotNone(self.bdd_reachability)
        self.assertIsNone(self.bdd_reachability.bdd_manager)
    
    def test_initialization_with_net(self):
        """Test initialization stores reference to Petri net."""
        self.assertEqual(self.bdd_reachability.petri_net, self.net)


class TestBDDInitialization(unittest.TestCase):
    """Test BDD manager initialization."""
    
    def setUp(self):
        """Set up simple Petri net."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_initialize_bdd(self):
        """Test BDD manager initialization."""
        self.bdd_reachability.initialize_bdd()
        self.assertIsNotNone(self.bdd_reachability.bdd_manager)
    
    def test_bdd_variables_created(self):
        """Test BDD variables created for each place."""
        self.bdd_reachability.initialize_bdd()
        # Should have variables for p1 and p2
        # Exact structure depends on BDD library used
        self.assertIsNotNone(self.bdd_reachability.bdd_manager)


class TestSimpleLinearNetBDD(unittest.TestCase):
    """Test BDD reachability on simple linear net."""
    
    def setUp(self):
        """Set up simple linear Petri net: p1 -> t1 -> p2 -> t2 -> p3."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_place('p3', has_token=False)
        self.net.add_transition('t1')
        self.net.add_transition('t2')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        self.net.add_arc('p2', 't2')
        self.net.add_arc('t2', 'p3')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_compute_symbolic_reachability(self):
        """Test symbolic reachability computation."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        self.assertIsNotNone(reachable_bdd)
    
    def test_extract_markings_from_bdd(self):
        """Test extracting explicit markings from BDD."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        markings = self.bdd_reachability.extract_markings(reachable_bdd)
        
        # Should have 4 reachable markings
        self.assertEqual(len(markings), 3)
    
    def test_bdd_contains_initial_marking(self):
        """Test BDD contains initial marking."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        markings = self.bdd_reachability.extract_markings(reachable_bdd)
        self.assertIn(self.net.initial_marking, markings)
    
    def test_bdd_contains_final_marking(self):
        """Test BDD contains final marking."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        markings = self.bdd_reachability.extract_markings(reachable_bdd)
        final = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        self.assertIn(final, markings)


class TestBDDTransitionEncoding(unittest.TestCase):
    """Test encoding of transitions as BDD formulas."""
    
    def setUp(self):
        """Set up test net."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_encode_transition(self):
        """Test encoding a single transition."""
        self.bdd_reachability.initialize_bdd()
        transition_bdd = self.bdd_reachability.encode_transition('t1')
        
        self.assertIsNotNone(transition_bdd)
    
    def test_encode_all_transitions(self):
        """Test encoding all transitions."""
        self.bdd_reachability.initialize_bdd()
        all_transitions_bdd = self.bdd_reachability.encode_all_transitions()
        
        self.assertIsNotNone(all_transitions_bdd)


class TestBDDFixedPointIteration(unittest.TestCase):
    """Test fixed-point iteration for reachability."""
    
    def setUp(self):
        """Set up cyclic net: p1 -> t1 -> p2 -> t2 -> p1."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_transition('t1')
        self.net.add_transition('t2')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        self.net.add_arc('p2', 't2')
        self.net.add_arc('t2', 'p1')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_fixed_point_convergence(self):
        """Test fixed-point iteration converges."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        # Should converge despite cycle
        self.assertIsNotNone(reachable_bdd)
    
    def test_cyclic_net_reachability(self):
        """Test correct reachable set for cyclic net."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        markings = self.bdd_reachability.extract_markings(reachable_bdd)
        
        # Should have 2 markings in cycle
        self.assertEqual(len(markings), 2)


class TestBDDWithSynchronization(unittest.TestCase):
    """Test BDD encoding with synchronization."""
    
    def setUp(self):
        """Set up net with sync: p1, p2 -> t1 -> p3."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=True)
        self.net.add_place('p3', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('p2', 't1')
        self.net.add_arc('t1', 'p3')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_synchronization_encoding(self):
        """Test BDD correctly encodes synchronization."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        markings = self.bdd_reachability.extract_markings(reachable_bdd)
        
        # Should require both inputs
        final = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        self.assertIn(final, markings)


class TestBDDWithFork(unittest.TestCase):
    """Test BDD encoding with fork (multiple outputs)."""
    
    def setUp(self):
        """Set up net with fork: p1 -> t1 -> p2, p3."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_place('p3', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        self.net.add_arc('t1', 'p3')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_fork_encoding(self):
        """Test BDD correctly encodes fork."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        markings = self.bdd_reachability.extract_markings(reachable_bdd)
        
        # Should produce both outputs
        forked = Marking({'p1': 0, 'p2': 1, 'p3': 1})
        self.assertIn(forked, markings)


class TestBDDMarkingEncoding(unittest.TestCase):
    """Test encoding markings as BDD formulas."""
    
    def setUp(self):
        """Set up test net."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_place('p3', has_token=True)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_encode_marking(self):
        """Test encoding a marking as BDD."""
        self.bdd_reachability.initialize_bdd()
        marking = Marking({'p1': 1, 'p2': 0, 'p3': 1})
        marking_bdd = self.bdd_reachability.encode_marking(marking)
        
        self.assertIsNotNone(marking_bdd)
    
    def test_marking_satisfies_bdd(self):
        """Test encoded marking satisfies its BDD."""
        self.bdd_reachability.initialize_bdd()
        marking = self.net.initial_marking
        marking_bdd = self.bdd_reachability.encode_marking(marking)
        
        self.assertTrue(self.bdd_reachability.satisfies(marking_bdd, marking))


class TestBDDComparisonWithExplicit(unittest.TestCase):
    """Test BDD results match explicit reachability."""
    
    def setUp(self):
        """Set up test net."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_place('p3', has_token=False)
        self.net.add_transition('t1')
        self.net.add_transition('t2')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        self.net.add_arc('p2', 't2')
        self.net.add_arc('t2', 'p3')
        
        self.bdd_reachability = BDDReachability(self.net)
    
    def test_bdd_matches_explicit_count(self):
        """Test BDD finds same number of markings as explicit."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        bdd_markings = self.bdd_reachability.extract_markings(reachable_bdd)
        
        # Compare with explicit reachability (if implemented)
        from explicit_reachability import ExplicitReachability
        explicit_reachability = ExplicitReachability(self.net)
        explicit_markings = explicit_reachability.compute_reachability(
            self.net.initial_marking
        )
        
        self.assertEqual(len(bdd_markings), len(explicit_markings))
    
    def test_bdd_matches_explicit_markings(self):
        """Test BDD finds same markings as explicit."""
        self.bdd_reachability.initialize_bdd()
        reachable_bdd = self.bdd_reachability.compute_symbolic_reachability(
            self.net.initial_marking
        )
        
        bdd_markings = set(self.bdd_reachability.extract_markings(reachable_bdd))
        
        # Compare with explicit reachability
        from explicit_reachability import ExplicitReachability
        explicit_reachability = ExplicitReachability(self.net)
        explicit_markings = explicit_reachability.compute_reachability(
            self.net.initial_marking
        )
        
        self.assertEqual(bdd_markings, explicit_markings)


class TestBDDPerformance(unittest.TestCase):
    """Test BDD performance characteristics."""
    
    def test_large_state_space(self):
        """Test BDD can handle larger state spaces."""
        # Create net with many places
        net = PetriNet()
        
        for i in range(5):
            p1 = f'p{i}_1'
            p2 = f'p{i}_2'
            t = f't{i}'
            
            net.add_place(p1, has_token=True)
            net.add_place(p2, has_token=False)
            net.add_transition(t)
            net.add_arc(p1, t)
            net.add_arc(t, p2)
        
        bdd_reachability = BDDReachability(net)
        bdd_reachability.initialize_bdd()
        
        reachable_bdd = bdd_reachability.compute_symbolic_reachability(
            net.initial_marking
        )
        
        # Should handle 2^5 = 32 states
        markings = bdd_reachability.extract_markings(reachable_bdd)
        self.assertEqual(len(markings), 32)


class TestBDDEdgeCases(unittest.TestCase):
    """Test BDD edge cases."""
    
    def test_empty_net(self):
        """Test BDD on empty net."""
        net = PetriNet()
        bdd_reachability = BDDReachability(net)
        
        bdd_reachability.initialize_bdd()
        reachable_bdd = bdd_reachability.compute_symbolic_reachability(
            net.initial_marking
        )
        
        markings = bdd_reachability.extract_markings(reachable_bdd)
        # Should have only empty marking
        self.assertEqual(len(markings), 1)
    
    def test_no_transitions(self):
        """Test BDD with places but no transitions."""
        net = PetriNet()
        net.add_place('p1', has_token=True)
        net.add_place('p2', has_token=False)
        
        bdd_reachability = BDDReachability(net)
        bdd_reachability.initialize_bdd()
        
        reachable_bdd = bdd_reachability.compute_symbolic_reachability(
            net.initial_marking
        )
        
        markings = bdd_reachability.extract_markings(reachable_bdd)
        # Can only reach initial marking
        self.assertEqual(len(markings), 1)
    
    def test_self_loop(self):
        """Test BDD with self-loop."""
        net = PetriNet()
        net.add_place('p1', has_token=True)
        net.add_transition('t1')
        net.add_arc('p1', 't1')
        net.add_arc('t1', 'p1')
        
        bdd_reachability = BDDReachability(net)
        bdd_reachability.initialize_bdd()
        
        reachable_bdd = bdd_reachability.compute_symbolic_reachability(
            net.initial_marking
        )
        
        markings = bdd_reachability.extract_markings(reachable_bdd)
        # Should have only 1 state
        self.assertEqual(len(markings), 1)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
