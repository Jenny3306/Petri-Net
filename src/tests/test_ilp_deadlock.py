import unittest
from pathlib import Path

from ilp_deadlock import DeadlockDetector
from pnml_parser import PNMLParser
from utils import PetriNet, Marking
from bdd_reachability import BDDReachability

def is_valid_deadlock(detector, marking):
    """Return True if the marking is a real reachable deadlock, else False."""
    if marking is None:
        return False

    m_dict = marking.to_dict()
    # 1. check no enabled transitions
    for t in detector.net.transitions:
        preset = detector.net.arcs[t]["input"]
        if preset and all(m_dict.get(p, 0) == 1 for p in preset):
            return False

    # 2. check BDD reachability
    if not detector._is_reachable(m_dict):
        return False

    return True

# ----------------------------------------------------------------------
# Utility helper to initialize DeadlockDetector with BDD reachability
# ----------------------------------------------------------------------
def make_detector_with_bdd(net):
    """Build BDD reachable set and return DeadlockDetector ready to run."""
    R = BDDReachability(net)
    R.compute_symbolic_reachability(net.initial_marking)

    return DeadlockDetector(
        net,
        reachable_bdd=R.reachable_bdd,
        bdd_manager=R.bdd_manager
    )



# ======================================================================
# BASIC TESTS
# ======================================================================

class TestDeadlockDetectorBasic(unittest.TestCase):

    def setUp(self):
        self.net = PetriNet()
        # Must supply reachable_bdd explicitly
        R = BDDReachability(self.net)
        R.compute_symbolic_reachability(self.net.initial_marking)
        self.detector = DeadlockDetector(self.net, R.reachable_bdd, R.bdd_manager)

    def test_initialization(self):
        self.assertIsNotNone(self.detector)
        self.assertEqual(self.detector.deadlocks, [])

    def test_initialization_with_net(self):
        self.assertEqual(self.detector.net, self.net)


# ======================================================================
# SIMPLE LINEAR NET p1 → p2 → p3
# ======================================================================

class TestDeadlockLinearNet(unittest.TestCase):

    def setUp(self):
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

        self.detector = make_detector_with_bdd(self.net)

    def test_detect_deadlock(self):
        deadlock = self.detector.detect_deadlock()
        self.assertTrue(is_valid_deadlock(self.detector, deadlock))

    def test_correct_deadlock_marking(self):
        deadlock = self.detector.detect_deadlock()
        expected = Marking({'p1': 0, 'p2': 0, 'p3': 1})
        self.assertEqual(deadlock, expected)


# ======================================================================
# CYCLIC NET – NO DEADLOCK
# ======================================================================

class TestNoDeadlock(unittest.TestCase):

    def setUp(self):
        self.net = PetriNet()
        self.net.add_place('p1', has_token=True)
        self.net.add_place('p2', has_token=False)

        self.net.add_transition('t1')
        self.net.add_transition('t2')
        self.net.add_arc('p1', 't1')
        self.net.add_arc('t1', 'p2')
        self.net.add_arc('p2', 't2')
        self.net.add_arc('t2', 'p1')

        self.detector = make_detector_with_bdd(self.net)

    def test_no_deadlock(self):
        self.assertIsNone(self.detector.detect_deadlock())


# ======================================================================
# MULTIPLE DEADLOCKS – ILP RETURNS ONE
# ======================================================================

class TestMultipleDeadlocks(unittest.TestCase):

    def setUp(self):
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

        self.detector = make_detector_with_bdd(self.net)

    def test_detect_one_deadlock(self):
        deadlock = self.detector.detect_deadlock()
        self.assertIsNotNone(deadlock)
        self.assertTrue(is_valid_deadlock(self.detector, deadlock))
        self.assertIn(deadlock, [
            Marking({'p1': 0, 'p2': 1, 'p3': 0}),
            Marking({'p1': 0, 'p2': 0, 'p3': 1}),
        ])


# ======================================================================
# BDD-BASED DEADLOCK DETECTION
# ======================================================================

class TestDeadlockBDD(unittest.TestCase):

    def setUp(self):
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

        self.detector = make_detector_with_bdd(self.net)

    def test_deadlock_with_bdd(self):
        deadlock = self.detector.detect_deadlock()
        self.assertTrue(is_valid_deadlock(self.detector, deadlock))
        self.assertEqual(deadlock, Marking({'p1': 0, 'p2': 0, 'p3': 1}))

# EDGE CASES

class TestEdgeCases(unittest.TestCase):

    def test_empty_net(self):
        net = PetriNet()
        detector = make_detector_with_bdd(net)
        # Empty net = trivial deadlock
        self.assertIsNotNone(detector.detect_deadlock())

    def test_no_transitions(self):
        net = PetriNet()
        net.add_place('p1', has_token=True)
        detector = make_detector_with_bdd(net)
        self.assertIsNotNone(detector.detect_deadlock())


if __name__ == "__main__":
    unittest.main(verbosity=2)
