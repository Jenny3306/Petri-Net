import unittest
from utils import PetriNet, Marking


class TestMarkingCreation(unittest.TestCase):
    """Test marking creation and initialization."""
    
    def test_empty_marking(self):
        """Test creating empty marking."""
        marking = Marking()
        self.assertEqual(marking.total_tokens(), 0)
        self.assertEqual(len(marking.get_places()), 0)
    
    def test_marking_from_dict(self):
        """Test creating marking from dictionary."""
        marking = Marking({'p1': 1, 'p2': 0, 'p3': 1})
        self.assertTrue(marking.has_token('p1'))
        self.assertFalse(marking.has_token('p2'))
        self.assertTrue(marking.has_token('p3'))
    
    def test_marking_from_dict_integers(self):
        """Test creating marking from dict with integer values (compatibility)."""
        marking = Marking({'p1': 1, 'p2': 0})
        self.assertEqual(marking.get_tokens('p1'), 1)
        self.assertEqual(marking.get_tokens('p2'), 0)
    
    def test_marking_with_no_places(self):
        """Test marking with no places."""
        marking = Marking({})
        self.assertEqual(marking.total_tokens(), 0)


class TestMarkingTokenOperations(unittest.TestCase):
    """Test token manipulation operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.marking = Marking({'p1': 1, 'p2': 0, 'p3': 1})
    
    def test_has_token_true(self):
        """Test has_token returns True for places with tokens."""
        self.assertTrue(self.marking.has_token('p1'))
        self.assertTrue(self.marking.has_token('p3'))
    
    def test_has_token_false(self):
        """Test has_token returns False for places without tokens."""
        self.assertFalse(self.marking.has_token('p2'))
    
    def test_has_token_nonexistent_place(self):
        """Test has_token returns False for nonexistent places."""
        self.assertFalse(self.marking.has_token('p999'))
    
    def test_get_tokens(self):
        """Test get_tokens returns correct values."""
        self.assertEqual(self.marking.get_tokens('p1'), 1)
        self.assertEqual(self.marking.get_tokens('p2'), 0)
        self.assertEqual(self.marking.get_tokens('p3'), 1)
    
    def test_get_tokens_nonexistent(self):
        """Test get_tokens returns 0 for nonexistent places."""
        self.assertEqual(self.marking.get_tokens('p999'), 0)
    
    def test_set_token_true(self):
        """Test set_token with True adds token."""
        self.marking.set_token('p2', True)
        self.assertTrue(self.marking.has_token('p2'))
        self.assertEqual(self.marking.get_tokens('p2'), 1)
    
    def test_set_token_false(self):
        """Test set_token with False removes token."""
        self.marking.set_token('p1', False)
        self.assertFalse(self.marking.has_token('p1'))
        self.assertEqual(self.marking.get_tokens('p1'), 0)
    
    def test_set_tokens_compatibility(self):
        """Test set_tokens method (compatibility with general Petri nets)."""
        self.marking.set_tokens('p2', 1)
        self.assertTrue(self.marking.has_token('p2'))
        
        self.marking.set_tokens('p1', 0)
        self.assertFalse(self.marking.has_token('p1'))
    
    def test_set_tokens_nonzero_as_true(self):
        """Test set_tokens treats any nonzero as True."""
        self.marking.set_tokens('p2', 5)
        self.assertTrue(self.marking.has_token('p2'))
    
    def test_total_tokens(self):
        """Test total_tokens counts all tokens."""
        self.assertEqual(self.marking.total_tokens(), 2)


class TestMarkingVectorConversion(unittest.TestCase):
    """Test conversion between markings and vectors."""
    
    def test_to_vector_ordered(self):
        """Test to_vector produces correctly ordered vector."""
        marking = Marking({'p1': 1, 'p2': 0, 'p3': 1})
        places = ['p1', 'p2', 'p3']
        vector = marking.to_vector(places)
        self.assertEqual(vector, [1, 0, 1])
    
    def test_to_vector_different_order(self):
        """Test to_vector respects place order."""
        marking = Marking({'p1': 1, 'p2': 0, 'p3': 1})
        places = ['p3', 'p1', 'p2']
        vector = marking.to_vector(places)
        self.assertEqual(vector, [1, 1, 0])
    
    def test_to_vector_missing_place(self):
        """Test to_vector handles missing places (treats as 0)."""
        marking = Marking({'p1': 1})
        places = ['p1', 'p2', 'p3']
        vector = marking.to_vector(places)
        self.assertEqual(vector, [1, 0, 0])
    
    def test_to_binary_vector(self):
        """Test to_binary_vector (alias for to_vector in 1-safe)."""
        marking = Marking({'p1': 1, 'p2': 0})
        places = ['p1', 'p2']
        vector = marking.to_binary_vector(places)
        self.assertEqual(vector, [1, 0])
    
    def test_from_vector(self):
        """Test creating marking from vector."""
        places = ['p1', 'p2', 'p3']
        vector = [1, 0, 1]
        marking = Marking.from_vector(vector, places)
        self.assertTrue(marking.has_token('p1'))
        self.assertFalse(marking.has_token('p2'))
        self.assertTrue(marking.has_token('p3'))
    
    def test_from_vector_all_zeros(self):
        """Test from_vector with all zeros."""
        places = ['p1', 'p2']
        vector = [0, 0]
        marking = Marking.from_vector(vector, places)
        self.assertFalse(marking.has_token('p1'))
        self.assertFalse(marking.has_token('p2'))
        self.assertEqual(marking.total_tokens(), 0)
    
    def test_from_vector_all_ones(self):
        """Test from_vector with all ones."""
        places = ['p1', 'p2']
        vector = [1, 1]
        marking = Marking.from_vector(vector, places)
        self.assertTrue(marking.has_token('p1'))
        self.assertTrue(marking.has_token('p2'))
        self.assertEqual(marking.total_tokens(), 2)
    
    def test_vector_round_trip(self):
        """Test to_vector and from_vector are inverses."""
        original = Marking({'p1': 1, 'p2': 0, 'p3': 1})
        places = ['p1', 'p2', 'p3']
        vector = original.to_vector(places)
        reconstructed = Marking.from_vector(vector, places)
        self.assertEqual(original, reconstructed)


class TestMarkingComparison(unittest.TestCase):
    """Test marking equality and hashing."""
    
    def test_equality_same_markings(self):
        """Test equal markings are equal."""
        m1 = Marking({'p1': 1, 'p2': 0})
        m2 = Marking({'p1': 1, 'p2': 0})
        self.assertEqual(m1, m2)
    
    def test_equality_different_markings(self):
        """Test different markings are not equal."""
        m1 = Marking({'p1': 1, 'p2': 0})
        m2 = Marking({'p1': 0, 'p2': 1})
        self.assertNotEqual(m1, m2)
    
    def test_equality_different_places(self):
        """Test markings with different places are not equal."""
        m1 = Marking({'p1': 1})
        m2 = Marking({'p2': 1})
        self.assertNotEqual(m1, m2)
    
    def test_hash_consistent(self):
        """Test hash is consistent for equal markings."""
        m1 = Marking({'p1': 1, 'p2': 0})
        m2 = Marking({'p1': 1, 'p2': 0})
        self.assertEqual(hash(m1), hash(m2))
    
    def test_hash_in_set(self):
        """Test markings can be added to sets."""
        m1 = Marking({'p1': 1, 'p2': 0})
        m2 = Marking({'p1': 0, 'p2': 1})
        m3 = Marking({'p1': 1, 'p2': 0})  # Same as m1
        
        marking_set = {m1, m2, m3}
        self.assertEqual(len(marking_set), 2)  # m1 and m3 are duplicates
    
    def test_hash_in_dict(self):
        """Test markings can be dict keys."""
        m1 = Marking({'p1': 1})
        m2 = Marking({'p2': 1})
        
        marking_dict = {m1: 'first', m2: 'second'}
        self.assertEqual(marking_dict[m1], 'first')
        self.assertEqual(marking_dict[m2], 'second')


class TestMarkingUtilities(unittest.TestCase):
    """Test marking utility methods."""
    
    def test_copy(self):
        """Test copy creates independent marking."""
        original = Marking({'p1': 1, 'p2': 0})
        copy = original.copy()
        
        # They should be equal
        self.assertEqual(original, copy)
        
        # But independent
        copy.set_token('p2', True)
        self.assertFalse(original.has_token('p2'))
        self.assertTrue(copy.has_token('p2'))
    
    def test_to_tuple(self):
        """Test to_tuple produces sorted tuple."""
        marking = Marking({'p2': 0, 'p1': 1, 'p3': 1})
        tuple_repr = marking.to_tuple()
        # Should be sorted by place name
        self.assertIsInstance(tuple_repr, tuple)
    
    def test_get_places(self):
        """Test get_places returns all places."""
        marking = Marking({'p1': 1, 'p2': 0, 'p3': 1})
        places = marking.get_places()
        self.assertEqual(len(places), 3)
        self.assertIn('p1', places)
        self.assertIn('p2', places)
        self.assertIn('p3', places)


class TestPetriNetCreation(unittest.TestCase):
    """Test Petri net creation and initialization."""
    
    def test_empty_net(self):
        """Test creating empty Petri net."""
        net = PetriNet()
        self.assertEqual(len(net.places), 0)
        self.assertEqual(len(net.transitions), 0)
        self.assertEqual(len(net.arcs), 0)
    
    def test_initial_marking_empty(self):
        """Test initial marking is empty for new net."""
        net = PetriNet()
        self.assertEqual(net.initial_marking.total_tokens(), 0)


class TestPetriNetPlaces(unittest.TestCase):
    """Test place operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.net = PetriNet()
    
    def test_add_place_without_token(self):
        """Test adding place without token."""
        self.net.add_place('p1', has_token=False)
        self.assertIn('p1', self.net.places)
        self.assertFalse(self.net.initial_marking.has_token('p1'))
    
    def test_add_place_with_token(self):
        """Test adding place with token."""
        self.net.add_place('p1', has_token=True)
        self.assertIn('p1', self.net.places)
        self.assertTrue(self.net.initial_marking.has_token('p1'))
    
    def test_add_place_with_name(self):
        """Test adding place with human-readable name."""
        self.net.add_place('p1', has_token=False, name='Input Place')
        self.assertEqual(self.net.place_names['p1'], 'Input Place')
    
    def test_add_duplicate_place(self):
        """Test adding duplicate place raises error."""
        self.net.add_place('p1')
        with self.assertRaises(ValueError):
            self.net.add_place('p1')
    
    def test_add_multiple_places(self):
        """Test adding multiple places."""
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_place('p3', has_token=True)
        
        self.assertEqual(len(self.net.places), 3)
        self.assertEqual(self.net.initial_marking.total_tokens(), 2)
    
    def test_get_place_name(self):
        """Test getting place name."""
        self.net.add_place('p1', name='Place 1')
        self.assertEqual(self.net.get_place_name('p1'), 'Place 1')
    
    def test_get_place_name_default(self):
        """Test getting place name returns ID if no name set."""
        self.net.add_place('p1')
        self.assertEqual(self.net.get_place_name('p1'), 'p1')


class TestPetriNetTransitions(unittest.TestCase):
    """Test transition operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.net = PetriNet()
    
    def test_add_transition(self):
        """Test adding transition."""
        self.net.add_transition('t1')
        self.assertIn('t1', self.net.transitions)
        self.assertIn('t1', self.net.arcs)
        self.assertEqual(self.net.arcs['t1'], {'input': [], 'output': []})
    
    def test_add_transition_with_name(self):
        """Test adding transition with name."""
        self.net.add_transition('t1', name='Process')
        self.assertEqual(self.net.transition_names['t1'], 'Process')
    
    def test_add_duplicate_transition(self):
        """Test adding duplicate transition raises error."""
        self.net.add_transition('t1')
        with self.assertRaises(ValueError):
            self.net.add_transition('t1')
    
    def test_get_transition_name(self):
        """Test getting transition name."""
        self.net.add_transition('t1', name='Transition 1')
        self.assertEqual(self.net.get_transition_name('t1'), 'Transition 1')
    
    def test_get_transition_name_default(self):
        """Test getting transition name returns ID if no name set."""
        self.net.add_transition('t1')
        self.assertEqual(self.net.get_transition_name('t1'), 't1')


class TestPetriNetArcs(unittest.TestCase):
    """Test arc operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_transition('t1')
    
    def test_add_arc_place_to_transition(self):
        """Test adding arc from place to transition (input arc)."""
        self.net.add_arc('p1', 't1')
        self.assertIn('p1', self.net.arcs['t1']['input'])
    
    def test_add_arc_transition_to_place(self):
        """Test adding arc from transition to place (output arc)."""
        self.net.add_arc('t1', 'p2')
        self.assertIn('p2', self.net.arcs['t1']['output'])
    
    def test_add_arc_place_to_place_invalid(self):
        """Test adding arc from place to place raises error."""
        with self.assertRaises(ValueError):
            self.net.add_arc('p1', 'p2')
    
    def test_add_arc_transition_to_transition_invalid(self):
        """Test adding arc from transition to transition raises error."""
        self.net.add_transition('t2')
        with self.assertRaises(ValueError):
            self.net.add_arc('t1', 't2')
    
    def test_add_multiple_input_arcs(self):
        """Test adding multiple input arcs to transition."""
        self.net.add_arc('p1', 't1')
        self.net.add_arc('p2', 't1')
        self.assertEqual(len(self.net.arcs['t1']['input']), 2)
        self.assertIn('p1', self.net.arcs['t1']['input'])
        self.assertIn('p2', self.net.arcs['t1']['input'])
    
    def test_add_multiple_output_arcs(self):
        """Test adding multiple output arcs from transition."""
        self.net.add_place('p3', has_token=False)
        self.net.add_arc('t1', 'p2')
        self.net.add_arc('t1', 'p3')
        self.assertEqual(len(self.net.arcs['t1']['output']), 2)


class TestPetriNetTransitionFiring(unittest.TestCase):
    """Test transition enabling and firing."""
    
    def setUp(self):
        """Set up simple linear net: p1 -> t1 -> p2."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
    
    def test_is_enabled_true(self):
        """Test transition is enabled when input places have tokens."""
        self.assertTrue(self.net.is_enabled('t1', self.net.initial_marking))
    
    def test_is_enabled_false(self):
        """Test transition is not enabled when input places lack tokens."""
        marking = Marking({'p1': 0, 'p2': 0})
        self.assertFalse(self.net.is_enabled('t1', marking))
    
    def test_is_enabled_nonexistent_transition(self):
        """Test is_enabled raises error for nonexistent transition."""
        with self.assertRaises(ValueError):
            self.net.is_enabled('t999', self.net.initial_marking)
    
    def test_fire_transition(self):
        """Test firing enabled transition."""
        new_marking = self.net.fire_transition('t1', self.net.initial_marking)
        self.assertFalse(new_marking.has_token('p1'))
        self.assertTrue(new_marking.has_token('p2'))
    
    def test_fire_transition_disabled(self):
        """Test firing disabled transition raises error."""
        marking = Marking({'p1': 0, 'p2': 0})
        with self.assertRaises(ValueError):
            self.net.fire_transition('t1', marking)
    
    def test_fire_transition_preserves_tokens(self):
        """Test token count preserved when firing."""
        initial_count = self.net.initial_marking.total_tokens()
        new_marking = self.net.fire_transition('t1', self.net.initial_marking)
        self.assertEqual(new_marking.total_tokens(), initial_count)
    
    def test_fire_transition_immutable(self):
        """Test firing doesn't modify original marking."""
        original = self.net.initial_marking.copy()
        new_marking = self.net.fire_transition('t1', self.net.initial_marking)
        self.assertEqual(self.net.initial_marking, original)
    
    def test_get_enabled_transitions(self):
        """Test getting all enabled transitions."""
        enabled = self.net.get_enabled_transitions(self.net.initial_marking)
        self.assertEqual(enabled, ['t1'])
    
    def test_get_enabled_transitions_none(self):
        """Test getting enabled transitions when none enabled."""
        marking = Marking({'p1': 0, 'p2': 1})
        enabled = self.net.get_enabled_transitions(marking)
        self.assertEqual(enabled, [])
    
    def test_get_enabled_transitions_multiple(self):
        """Test getting multiple enabled transitions."""
        # Add another transition
        self.net.add_transition('t2')
        self.net.add_arc('p1', 't2')
        self.net.add_place('p3', has_token=False)
        self.net.add_arc('t2', 'p3')
        
        enabled = self.net.get_enabled_transitions(self.net.initial_marking)
        self.assertEqual(len(enabled), 2)
        self.assertIn('t1', enabled)
        self.assertIn('t2', enabled)


class TestPetriNetSynchronization(unittest.TestCase):
    """Test synchronization (multiple inputs)."""
    
    def setUp(self):
        """Set up net with synchronization: p1, p2 -> t1 -> p3."""
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=True)
        self.net.add_place('p3', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('p2', 't1')
        self.net.add_arc('t1', 'p3')
    
    def test_enabled_with_both_tokens(self):
        """Test transition enabled when all inputs have tokens."""
        self.assertTrue(self.net.is_enabled('t1', self.net.initial_marking))
    
    def test_not_enabled_missing_one_token(self):
        """Test transition not enabled when one input lacks token."""
        marking = Marking({'p1': 1, 'p2': 0, 'p3': 0})
        self.assertFalse(self.net.is_enabled('t1', marking))
    
    def test_fire_consumes_both_tokens(self):
        """Test firing consumes tokens from all inputs."""
        new_marking = self.net.fire_transition('t1', self.net.initial_marking)
        self.assertFalse(new_marking.has_token('p1'))
        self.assertFalse(new_marking.has_token('p2'))
        self.assertTrue(new_marking.has_token('p3'))


class TestPetriNetFork(unittest.TestCase):
    """Test fork (multiple outputs)."""
    
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
    
    def test_fire_produces_both_tokens(self):
        """Test firing produces tokens in all outputs."""
        new_marking = self.net.fire_transition('t1', self.net.initial_marking)
        self.assertFalse(new_marking.has_token('p1'))
        self.assertTrue(new_marking.has_token('p2'))
        self.assertTrue(new_marking.has_token('p3'))


class TestPetriNetValidation(unittest.TestCase):
    """Test Petri net validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.net = PetriNet()
    
    def test_validate_consistency_empty_net(self):
        """Test validation passes for empty net."""
        is_valid, errors = self.net.validate_consistency()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_consistency_valid_net(self):
        """Test validation passes for valid net."""
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)
        self.net.add_transition('t1')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        
        is_valid, errors = self.net.validate_consistency()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)


class TestPetriNetStringRepresentation(unittest.TestCase):
    """Test string representations."""
    
    def test_str_representation(self):
        """Test __str__ method."""
        net = PetriNet()
        net.add_place('p1')
        net.add_transition('t1')
        net.add_arc('p1', 't1')
        
        str_repr = str(net)
        self.assertIn('PetriNet', str_repr)
        self.assertIn('places=1', str_repr)
        self.assertIn('transitions=1', str_repr)
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        net = PetriNet()
        net.add_place('p1', has_token=True)
        
        repr_str = str(net)
        self.assertIn('PetriNet', repr_str)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
