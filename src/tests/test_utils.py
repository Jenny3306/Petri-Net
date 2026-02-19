import unittest
from utils import PetriNet, Marking


class TestPetriNet(unittest.TestCase):
    """Test cases for Petri net data structure."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.net = PetriNet()
    
    def test_petri_net_initialization(self):
        """Test Petri net initialization."""
        self.assertIsNotNone(self.net)
        self.assertEqual(len(self.net.places), 0)
        self.assertEqual(len(self.net.transitions), 0)
    
    def test_add_place(self):
        """Test adding a place."""
        self.net.add_place('p1', has_token=True)
        self.assertIn('p1', self.net.places)
        self.assertTrue(self.net.initial_marking.has_token('p1'))
        # Also verify get_tokens() returns 1 
        self.assertEqual(self.net.initial_marking.get_tokens('p1'), 1)
    
    def test_add_transition(self):
        """Test adding a transition."""
        self.net.add_transition('t1')
        self.assertIn('t1', self.net.transitions)
        self.assertIn('t1', self.net.arcs)


class TestMarking(unittest.TestCase):
    """Test cases for marking data structure."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.marking = Marking({'p1': 1, 'p2': 0})
    
    def test_marking_initialization(self):
        """Test marking initialization."""
        self.assertIsNotNone(self.marking)
        self.assertEqual(self.marking.get_tokens('p1'), 1)
        self.assertTrue(self.marking.has_token('p1'))
    
    def test_get_tokens(self):
        """Test getting token count."""
        self.assertEqual(self.marking.get_tokens('p1'), 1)
        self.assertEqual(self.marking.get_tokens('p2'), 0)
        self.assertEqual(self.marking.get_tokens('p3'), 0)
    
    def test_has_token(self):
        """Test checking if place has token."""
        self.assertTrue(self.marking.has_token('p1'))
        self.assertFalse(self.marking.has_token('p2'))
        self.assertFalse(self.marking.has_token('p3'))
    
    def test_set_tokens(self):
        """Test setting token count (1-safe: only 0 or 1)."""
        # Test setting to 0 (no token)
        self.marking.set_token('p1', False)
        self.assertFalse(self.marking.has_token('p1'))
        self.assertEqual(self.marking.get_tokens('p1'), 0)
        
        # Test setting to 1 (has token)
        self.marking.set_token('p1', True)
        self.assertTrue(self.marking.has_token('p1'))
        self.assertEqual(self.marking.get_tokens('p1'), 1)
        
        # Test compatibility method set_tokens
        self.marking.set_tokens('p1', 0)
        self.assertFalse(self.marking.has_token('p1'))
        
        self.marking.set_tokens('p1', 1)
        self.assertTrue(self.marking.has_token('p1'))
    
    def test_marking_equality(self):
        """Test marking equality."""
        m1 = Marking({'p1': 1, 'p2': 0})
        m2 = Marking({'p1': 1, 'p2': 0})
        m3 = Marking({'p1': 0, 'p2': 1}) 
        self.assertEqual(m1, m2)
        self.assertNotEqual(m1, m3)
    
    def test_marking_to_vector(self):
        """Test conversion to binary vector."""
        places = ['p1', 'p2']
        vector = self.marking.to_vector(places)
        self.assertEqual(vector, [1, 0])
    
    def test_marking_from_vector(self):
        """Test creation from binary vector."""
        places = ['p1', 'p2', 'p3']
        vector = [1, 0, 1]
        marking = Marking.from_vector(vector, places)
        self.assertTrue(marking.has_token('p1'))
        self.assertFalse(marking.has_token('p2'))
        self.assertTrue(marking.has_token('p3'))


if __name__ == '__main__':
    unittest.main()
