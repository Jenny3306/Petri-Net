import unittest
from pathlib import Path
from explicit_reachability import ExplicitReachability
from pnml_parser import PNMLParser
from utils import PetriNet, Marking


class TestExplicitReachabilityBasic(unittest.TestCase):
    """Basic reachability analyzer tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.net = PetriNet()
        self.reachability = ExplicitReachability(self.net)
    
    def test_initialization(self):
        """Test reachability analyzer initialization."""
        self.assertIsNotNone(self.reachability)
        self.assertEqual(len(self.reachability.reachable_markings), 0)
    
    def test_initialization_with_net(self):
        """Test initialization stores reference to Petri net."""
        self.assertEqual(self.reachability.petri_net, self.net)


class TestSimpleLinearNet(unittest.TestCase):
    """Test reachability on simple linear net: p1 -> t1 -> p2 -> t2 -> p3."""
    
    def setUp(self):
        """Set up simple linear Petri net."""
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
        
        self.reachability = ExplicitReachability(self.net)
    
    def test_initial_marking_reachable(self):
        """Test initial marking is in reachable set."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        self.assertIn(self.net.initial_marking, reachable)
    
    def test_reachable_count_linear_net(self):
        """Test correct number of reachable markings in linear net."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        # Should have: {p1:1}, {p2:1}, {p3:1}
        self.assertEqual(len(reachable), 3)
    
    def test_all_intermediate_states_reachable(self):
        """Test all intermediate states are reachable."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        m1 = Marking({'p1': 1, 'p2': 0, 'p3': 0})
        m2 = Marking({'p1': 0, 'p2': 1, 'p3': 0})
        m3 = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        
        self.assertIn(m1, reachable)
        self.assertIn(m2, reachable)
        self.assertIn(m3, reachable)
    
    def test_final_state_is_deadlock(self):
        """Test final state has no enabled transitions."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        final = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        enabled = self.net.get_enabled_transitions(final)
        self.assertEqual(len(enabled), 0)
    
    def test_is_reachable_true(self):
        """Test is_reachable returns True for reachable markings."""
        self.reachability.compute_reachability(self.net.initial_marking)
        
        target = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        self.assertTrue(self.reachability.is_reachable(target))
    
    def test_is_reachable_false(self):
        """Test is_reachable returns False for unreachable markings."""
        self.reachability.compute_reachability(self.net.initial_marking)
        
        # This marking is impossible (multiple tokens)
        unreachable = Marking({'p1': 1, 'p2': 1, 'p3': 0})
        self.assertFalse(self.reachability.is_reachable(unreachable))


class TestBranchingNet(unittest.TestCase):
    """Test reachability on branching net with choice."""
    
    def setUp(self):
        """Set up net with choice: p1 -> t1 -> p2 or p1 -> t2 -> p3."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_place('p3', has_token=False)
        self.net.add_transition('t1')
        self.net.add_transition('t2')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        self.net.add_arc('p1', 't2')
        self.net.add_arc('t2', 'p3')
        
        self.reachability = ExplicitReachability(self.net)
    
    def test_both_branches_reachable(self):
        """Test both branches of choice are reachable."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        branch1 = Marking({'p1': 0, 'p2': 1, 'p3': 0})
        branch2 = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        
        self.assertIn(branch1, reachable)
        self.assertIn(branch2, reachable)
    
    def test_reachable_count_with_choice(self):
        """Test correct count with choice."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        # Should have: {p1:1}, {p2:1}, {p3:1}
        self.assertEqual(len(reachable), 3)


class TestCyclicNet(unittest.TestCase):
    """Test reachability on cyclic net."""
    
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
        
        self.reachability = ExplicitReachability(self.net)
    
    def test_cycle_reachability(self):
        """Test reachability handles cycles correctly."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        # Should have only 2 markings in cycle
        m1 = Marking({'p1': 1, 'p2': 0})
        m2 = Marking({'p1': 0, 'p2': 1})
        
        self.assertIn(m1, reachable)
        self.assertIn(m2, reachable)
        self.assertEqual(len(reachable), 2)
    
    def test_cycle_termination(self):
        """Test algorithm terminates despite cycle."""
        # Should not hang - should detect revisiting
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        self.assertIsNotNone(reachable)


class TestSynchronizationNet(unittest.TestCase):
    """Test reachability with synchronization (multiple inputs)."""
    
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
        
        self.reachability = ExplicitReachability(self.net)
    
    def test_sync_requires_both_tokens(self):
        """Test synchronization requires all inputs."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        # Should reach: {p1:1, p2:1}, {p3:1}
        initial = Marking({'p1': 1, 'p2': 1, 'p3': 0})
        final = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        
        self.assertIn(initial, reachable)
        self.assertIn(final, reachable)
    
    def test_sync_partial_tokens_unreachable(self):
        """Test states with partial tokens are not reachable."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        # Cannot reach state with only one input token and output
        impossible = Marking({'p1': 1, 'p2': 0, 'p3': 1})
        self.assertNotIn(impossible, reachable)


class TestForkNet(unittest.TestCase):
    """Test reachability with fork (multiple outputs)."""
    
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
        
        self.reachability = ExplicitReachability(self.net)
    
    def test_fork_produces_both_tokens(self):
        """Test fork produces all outputs simultaneously."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        # Should reach state with both outputs
        forked = Marking({'p1': 0, 'p2': 1, 'p3': 1})
        self.assertIn(forked, reachable)
    
    def test_fork_reachable_count(self):
        """Test fork creates expected number of states."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        # Should have: {p1:1}, {p2:1, p3:1}
        self.assertEqual(len(reachable), 2)


class TestEmptyNet(unittest.TestCase):
    """Test reachability on empty or minimal nets."""
    
    def test_empty_net(self):
        """Test reachability on completely empty net."""
        net = PetriNet()
        reachability = ExplicitReachability(net)
        
        reachable = reachability.compute_reachability(net.initial_marking)
        # Should have only empty marking
        self.assertEqual(len(reachable), 1)
    
    def test_single_place_no_transition(self):
        """Test reachability with single place, no transitions."""
        net = PetriNet()
        net.add_place('p1', has_token=True)
        reachability = ExplicitReachability(net)
        
        reachable = reachability.compute_reachability(net.initial_marking)
        # Can only reach initial marking
        self.assertEqual(len(reachable), 1)
        self.assertIn(net.initial_marking, reachable)
    
    def test_transition_no_arcs(self):
        """Test reachability with transition but no arcs."""
        net = PetriNet()
        net.add_place('p1', has_token=True)
        net.add_transition('t1')
        reachability = ExplicitReachability(net)
        
        reachable = reachability.compute_reachability(net.initial_marking)
        # Transition not connected, can't fire
        self.assertEqual(len(reachable), 1)


class TestReachabilityGraphConstruction(unittest.TestCase):
    """Test construction of reachability graph."""
    
    def setUp(self):
        """Set up simple net for graph testing."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        
        self.reachability = ExplicitReachability(self.net)
    
    def test_graph_has_edges(self):
        """Test reachability graph construction includes edges."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        
        # If graph is built, should be able to access it
        self.assertIsNotNone(reachable)
        # Graph should show m1 --t1--> m2
    
    def test_graph_initial_node(self):
        """Test initial marking is a node in graph."""
        reachable = self.reachability.compute_reachability(self.net.initial_marking)
        self.assertIn(self.net.initial_marking, reachable)


class TestReachabilityPerformance(unittest.TestCase):
    """Test reachability performance and optimization."""
    
    def test_large_linear_chain(self):
        """Test reachability on larger linear chain."""
        net = PetriNet()
        
        # Create chain of 10 places
        for i in range(10):
            has_token = (i == 0)
            net.add_place(f'p{i}', has_token=has_token)
        
        # Create 9 transitions connecting them
        for i in range(9):
            net.add_transition(f't{i}')
            net.add_arc(f'p{i}', f't{i}')
            net.add_arc(f't{i}', f'p{i+1}')
        
        reachability = ExplicitReachability(net)
        reachable = reachability.compute_reachability(net.initial_marking)
        
        self.assertEqual(len(reachable), 10)
    
    def test_visited_set_efficiency(self):
        """Test that visited set prevents revisiting."""
        net = PetriNet()
        net.add_place('p1', has_token=True)
        net.add_place('p2', has_token=False)
        net.add_transition('t1')
        net.add_transition('t2')
        net.add_arc('p1', 't1')
        net.add_arc('t1', 'p2')
        net.add_arc('p2', 't2')
        net.add_arc('t2', 'p1')
        
        reachability = ExplicitReachability(net)
        reachable = reachability.compute_reachability(net.initial_marking)
        
        # Even with cycle, should only visit each state once
        self.assertEqual(len(reachable), 2)


class TestReachabilityEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def test_self_loop_transition(self):
        """Test reachability with self-loop (p1 -> t1 -> p1)."""
        net = PetriNet()
        net.add_place('p1', has_token=True)
        net.add_transition('t1')
        net.add_arc('p1', 't1')
        net.add_arc('t1', 'p1')
        
        reachability = ExplicitReachability(net)
        reachable = reachability.compute_reachability(net.initial_marking)
        
        # Should have only 1 state (firing returns to same state)
        self.assertEqual(len(reachable), 1)
    
    def test_no_tokens_initially(self):
        """Test reachability starting with no tokens."""
        net = PetriNet()
        net.add_place('p1', has_token=False)
        net.add_place('p2', has_token=False)
        net.add_transition('t1')
        net.add_arc('p1', 't1')
        net.add_arc('t1', 'p2')
        
        reachability = ExplicitReachability(net)
        reachable = reachability.compute_reachability(net.initial_marking)
        
        # Nothing can fire, only initial state reachable
        self.assertEqual(len(reachable), 1)
    
    def test_disconnected_components(self):
        """Test reachability with disconnected components."""
        net = PetriNet()
        # Component 1
        net.add_place('p1', has_token=True)
        net.add_place('p2', has_token=False)
        net.add_transition('t1')
        net.add_arc('p1', 't1')
        net.add_arc('t1', 'p2')
        
        # Component 2 (disconnected)
        net.add_place('p3', has_token=True)
        net.add_place('p4', has_token=False)
        net.add_transition('t2')
        net.add_arc('p3', 't2')
        net.add_arc('t2', 'p4')
        
        reachability = ExplicitReachability(net)
        reachable = reachability.compute_reachability(net.initial_marking)
        
        # Should explore both components independently
        # Component 1: 2 states, Component 2: 2 states
        # Combined: 2 * 2 = 4 states
        self.assertEqual(len(reachable), 4)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
