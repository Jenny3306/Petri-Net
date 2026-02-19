import unittest
from pathlib import Path
from pnml_parser import PNMLParser
from utils.petri_net import PetriNet


class TestPNMLParserBasic(unittest.TestCase):
    """Basic parser functionality tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = PNMLParser()
    
    def test_parser_initialization(self):
        """Test parser initialization."""
        self.assertIsNotNone(self.parser)
        self.assertEqual(len(self.parser.places), 0)
        self.assertEqual(len(self.parser.transitions), 0)
    
    def test_parse_file_not_found(self):
        """Should raise FileNotFoundError for missing files."""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file("nonexistent.pnml")


class TestSimplePNML(unittest.TestCase):
    """Comprehensive tests for .././sample_pnml/simple-01.pnml"""
    
    @classmethod
    def setUpClass(cls):
        """Parse the file once for all tests."""
        cls.parser = PNMLParser()
        cls.file_path = Path(__file__).parent.parent / ".././sample_pnml" / "simple-01.pnml"
        
        # Skip all tests if file doesn't exist
        if not cls.file_path.exists():
            raise unittest.SkipTest(f"File not found: {cls.file_path}")
        
        cls.petri_net = cls.parser.parse_file(str(cls.file_path))
    
    # ===== STRUCTURE TESTS =====
    
    def test_places_count(self):
        """Should parse exactly 3 places."""
        self.assertEqual(len(self.petri_net.places), 3)
    
    def test_places_ids(self):
        """Should have correct place IDs: p1, p2, p3."""
        expected_places = {'p1', 'p2', 'p3'}
        self.assertEqual(self.petri_net.places, expected_places)
    
    def test_transitions_count(self):
        """Should parse exactly 2 transitions."""
        self.assertEqual(len(self.petri_net.transitions), 2)
    
    def test_transitions_ids(self):
        """Should have correct transition IDs: t1, t2."""
        expected_transitions = {'t1', 't2'}
        self.assertEqual(self.petri_net.transitions, expected_transitions)
    
    def test_total_arcs_count(self):
        """Should have exactly 4 arcs total."""
        total_arcs = sum(
            len(arcs['input']) + len(arcs['output'])
            for arcs in self.petri_net.arcs.values()
        )
        self.assertEqual(total_arcs, 4)
    
    # ===== INITIAL MARKING TESTS =====
    
    def test_initial_marking_p1(self):
        """Place p1 should have 1 token initially."""
        self.assertTrue(self.petri_net.initial_marking.has_token('p1'))
    
    def test_initial_marking_p2(self):
        """Place p2 should have 0 tokens initially."""
        self.assertFalse(self.petri_net.initial_marking.has_token('p2'))
    
    def test_initial_marking_p3(self):
        """Place p3 should have 0 tokens initially."""
        self.assertFalse(self.petri_net.initial_marking.has_token('p3'))
    
    def test_initial_marking_total_tokens(self):
        """Should have exactly 1 token total in initial marking."""
        self.assertEqual(self.petri_net.initial_marking.total_tokens(), 1)
    
    # ===== ARC STRUCTURE TESTS =====
    
    def test_t1_input_arcs(self):
        """Transition t1 should have p1 as its only input."""
        self.assertEqual(self.petri_net.arcs['t1']['input'], ['p1'])
    
    def test_t1_output_arcs(self):
        """Transition t1 should have p2 as its only output."""
        self.assertEqual(self.petri_net.arcs['t1']['output'], ['p2'])
    
    def test_t2_input_arcs(self):
        """Transition t2 should have p2 as its only input."""
        self.assertEqual(self.petri_net.arcs['t2']['input'], ['p2'])
    
    def test_t2_output_arcs(self):
        """Transition t2 should have p3 as its only output."""
        self.assertEqual(self.petri_net.arcs['t2']['output'], ['p3'])
    
    def test_arc_structure_linear(self):
        """Should form a linear chain: p1 → t1 → p2 → t2 → p3."""
        # Verify the flow
        self.assertIn('p1', self.petri_net.arcs['t1']['input'])
        self.assertIn('p2', self.petri_net.arcs['t1']['output'])
        self.assertIn('p2', self.petri_net.arcs['t2']['input'])
        self.assertIn('p3', self.petri_net.arcs['t2']['output'])
    
    # ===== NAMES TESTS =====
    
    def test_place_names_parsed(self):
        """Should parse place names correctly."""
        self.assertEqual(self.petri_net.place_names.get('p1'), 'Place 1')
        self.assertEqual(self.petri_net.place_names.get('p2'), 'Place 2')
        self.assertEqual(self.petri_net.place_names.get('p3'), 'Place 3')
    
    def test_transition_names_parsed(self):
        """Should parse transition names correctly."""
        self.assertEqual(self.petri_net.transition_names.get('t1'), 'Transition 1')
        self.assertEqual(self.petri_net.transition_names.get('t2'), 'Transition 2')
    
    # ===== VALIDATION TESTS =====
    
    def test_petri_net_consistency(self):
        """The parsed net should be structurally consistent."""
        is_valid, errors = self.petri_net.validate_consistency()
        self.assertTrue(is_valid, f"Consistency errors: {errors}")
    
    def test_all_places_in_initial_marking(self):
        """All places should be present in initial marking."""
        marking_places = set(self.petri_net.initial_marking.get_places())
        self.assertEqual(marking_places, self.petri_net.places)
    
    # ===== BEHAVIOR TESTS =====
    
    def test_initial_enabled_transitions(self):
        """Initially, only t1 should be enabled (p1 has token)."""
        enabled = self.petri_net.get_enabled_transitions(
            self.petri_net.initial_marking
        )
        self.assertEqual(enabled, ['t1'])
    
    def test_t2_not_initially_enabled(self):
        """t2 should NOT be enabled initially (p2 has no token)."""
        self.assertFalse(
            self.petri_net.is_enabled('t2', self.petri_net.initial_marking)
        )
    
    def test_fire_t1_moves_token(self):
        """Firing t1 should move token from p1 to p2."""
        marking = self.petri_net.fire_transition(
            't1', 
            self.petri_net.initial_marking
        )
        
        self.assertFalse(marking.has_token('p1'))
        self.assertTrue(marking.has_token('p2'))
        self.assertFalse(marking.has_token('p3'))
    
    def test_after_t1_only_t2_enabled(self):
        """After firing t1, only t2 should be enabled."""
        marking = self.petri_net.fire_transition(
            't1', 
            self.petri_net.initial_marking
        )
        enabled = self.petri_net.get_enabled_transitions(marking)
        self.assertEqual(enabled, ['t2'])
    
    def test_fire_sequence_t1_then_t2(self):
        """Firing t1 then t2 should move token from p1 to p3."""
        marking1 = self.petri_net.fire_transition(
            't1', 
            self.petri_net.initial_marking
        )
        marking2 = self.petri_net.fire_transition('t2', marking1)
        
        self.assertFalse(marking2.has_token('p1'))
        self.assertFalse(marking2.has_token('p2'))
        self.assertTrue(marking2.has_token('p3'))
    
    def test_final_marking_is_deadlock(self):
        """Final marking (token in p3) should be a deadlock."""
        marking1 = self.petri_net.fire_transition(
            't1', 
            self.petri_net.initial_marking
        )
        marking2 = self.petri_net.fire_transition('t2', marking1)
        
        enabled = self.petri_net.get_enabled_transitions(marking2)
        self.assertEqual(enabled, [], "Final marking should have no enabled transitions")
    
    def test_total_tokens_preserved(self):
        """Total number of tokens should be preserved when firing."""
        initial_tokens = self.petri_net.initial_marking.total_tokens()
        
        marking1 = self.petri_net.fire_transition(
            't1', 
            self.petri_net.initial_marking
        )
        self.assertEqual(marking1.total_tokens(), initial_tokens)
        
        marking2 = self.petri_net.fire_transition('t2', marking1)
        self.assertEqual(marking2.total_tokens(), initial_tokens)


class TestComplexPNML(unittest.TestCase):
    """Test parsing of simple-02.pnml with multiple inputs/outputs and cycles."""
    
    @classmethod
    def setUpClass(cls):
        """Parse complex test file."""
        cls.parser = PNMLParser()
        cls.file_path = Path(__file__).parent.parent / ".././sample_pnml" / "simple-02.pnml"
        
        if not cls.file_path.exists():
            cls.petri_net = None
        else:
            cls.petri_net = cls.parser.parse_file(str(cls.file_path))
    
    def setUp(self):
        """Skip tests if file doesn't exist."""
        if self.petri_net is None:
            self.skipTest("simple-02.pnml not found - run with created test files")
    
    def test_places_count(self):
        """Should have 5 places."""
        self.assertEqual(len(self.petri_net.places), 5)
    
    def test_transitions_count(self):
        """Should have 4 transitions."""
        self.assertEqual(len(self.petri_net.transitions), 4)
    
    def test_t1_multiple_inputs(self):
        """Transition t1 should have multiple input places (synchronization)."""
        inputs = self.petri_net.arcs['t1']['input']
        self.assertGreater(len(inputs), 1, "t1 should have multiple inputs")
        self.assertIn('p1', inputs)
        self.assertIn('p2', inputs)
    
    def test_t2_multiple_outputs(self):
        """Transition t2 should have multiple output places (fork)."""
        outputs = self.petri_net.arcs['t2']['output']
        self.assertGreater(len(outputs), 1, "t2 should have multiple outputs")
        self.assertIn('p4', outputs)
        self.assertIn('p5', outputs)
    
    def test_t1_requires_both_inputs(self):
        """t1 should only be enabled when both p1 and p2 have tokens."""
        # Initial: p1=1, p2=1, so t1 should be enabled
        self.assertTrue(
            self.petri_net.is_enabled('t1', self.petri_net.initial_marking)
        )
    
    def test_cycle_structure(self):
        """Should have cycle structure (p4 → t3 → p1 and p5 → t4 → p2)."""
        # Check p4 can return to p1
        self.assertIn('p4', self.petri_net.arcs['t3']['input'])
        self.assertIn('p1', self.petri_net.arcs['t3']['output'])
        
        # Check p5 can return to p2
        self.assertIn('p5', self.petri_net.arcs['t4']['input'])
        self.assertIn('p2', self.petri_net.arcs['t4']['output'])


class TestInvalidPNML(unittest.TestCase):
    """Test parsing of invalid PNML files (should raise errors)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = PNMLParser()
    
    def test_not_1_safe_file(self):
        """Should detect or reject files that are not 1-safe."""
        file_path = Path(__file__).parent.parent / ".././sample_pnml" / "not_1_safe.pnml"
        
        if not file_path.exists():
            self.skipTest("not_1_safe.pnml not found")
        
        # Parser should raise ValueError when validating 1-safe property
        # This test assumes validate_1safe is called during parsing
        # or that parse_file validates the initial marking
        with self.assertRaises((ValueError, AssertionError)):
            petri_net = self.parser.parse_file(str(file_path))
            # If parsing succeeds, validation should fail
            is_valid = self.parser.validate_1safe()
            if not is_valid:
                raise ValueError("Net is not 1-safe")


class TestProducerConsumerPNML(unittest.TestCase):
    """Test parsing of producer_consumer.pnml (real-world example)."""
    
    @classmethod
    def setUpClass(cls):
        """Parse producer-consumer test file."""
        cls.parser = PNMLParser()
        cls.file_path = Path(__file__).parent.parent / ".././sample_pnml" / "producer_consumer.pnml"
        
        if not cls.file_path.exists():
            cls.petri_net = None
        else:
            cls.petri_net = cls.parser.parse_file(str(cls.file_path))
    
    def setUp(self):
        """Skip tests if file doesn't exist."""
        if self.petri_net is None:
            self.skipTest("producer_consumer.pnml not found")
    
    def test_initial_configuration(self):
        """Should start with producer and consumer ready, buffer empty."""
        marking = self.petri_net.initial_marking
        
        # Producer ready
        self.assertTrue(marking.has_token('ready_produce'))
        # Consumer ready
        self.assertTrue(marking.has_token('ready_consume'))
        # Buffer empty
        self.assertTrue(marking.has_token('buffer_empty'))
        # Buffer not full
        self.assertFalse(marking.has_token('buffer_full'))
    
    def test_producer_can_produce_initially(self):
        """Producer should be able to produce initially."""
        enabled = self.petri_net.get_enabled_transitions(
            self.petri_net.initial_marking
        )
        self.assertIn('produce', enabled)
    
    def test_consumer_cannot_consume_initially(self):
        """Consumer cannot consume from empty buffer initially."""
        # 'consume' requires buffer_full and ready_consume
        # Only ready_consume is available initially
        self.assertFalse(
            self.petri_net.is_enabled('consume', self.petri_net.initial_marking)
        )


class TestParserWithUtils(unittest.TestCase):
    """Integration tests verifying parser output works with utility classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = PNMLParser()
        self.file_path = Path(__file__).parent.parent / ".././sample_pnml" / "simple-01.pnml"
        
        if not self.file_path.exists():
            self.skipTest("simple-01.pnml not found")
        
        self.petri_net = self.parser.parse_file(str(self.file_path))
    
    def test_marking_to_vector_conversion(self):
        """Parsed marking should convert to vector correctly."""
        places = sorted(self.petri_net.places)
        vector = self.petri_net.initial_marking.to_vector(places)
        
        # For simple-01.pnml with places [p1, p2, p3] and marking {p1:1, p2:0, p3:0}
        self.assertEqual(len(vector), 3)
        self.assertIn(1, vector)  # Should have one token
        self.assertEqual(sum(vector), 1)  # Total of 1 token
    
    def test_marking_hashable(self):
        """Parsed markings should be hashable (for reachability sets)."""
        marking1 = self.petri_net.initial_marking
        marking2 = self.petri_net.fire_transition('t1', marking1)
        
        # Should be able to add to set
        markings_set = {marking1, marking2}
        self.assertEqual(len(markings_set), 2)
    
    def test_marking_equality(self):
        """Identical markings should be equal."""
        marking1 = self.petri_net.initial_marking
        marking1_copy = marking1.copy()
        
        self.assertEqual(marking1, marking1_copy)
        self.assertEqual(hash(marking1), hash(marking1_copy))


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
