import unittest
import time
from utils import PetriNet,Marking
from bdd_reachability import BDDReachability
from explicit_reachability import ExplicitReachability

######### pytest bdd_reachability/TestTime.py -vv #########
class TestBDDvsBFS1024(unittest.TestCase):
    """Performance comparison test: BDD vs BFS on 2^10 = 1024 states"""

    def build_independent_binary_net(self, n_bits=10):
        """
        Creates a Petri net with n independent transitions,
        each toggling a place from p_i_1 -> p_i_2.
        This yields an exponential number of reachable states: 2^n.
        """
        net = PetriNet()
        for i in range(n_bits):
            p1 = f"p{i}_1"
            p2 = f"p{i}_2"
            t = f"t{i}"

            net.add_place(p1, has_token=True)
            net.add_place(p2, has_token=False)
            net.add_transition(t)
            net.add_arc(p1, t)
            net.add_arc(t, p2)
        return net

    def test_bdd_vs_bfs_1024_states(self):
        n_bits = 10   # 2^10 = 1024
        expected_states = 2 ** n_bits

        net = self.build_independent_binary_net(n_bits)

        # ============ BFS explicit reachability ============
        bfs_solver = ExplicitReachability(net)
        start_bfs = time.time()
        bfs_reachable = bfs_solver.compute_reachability(net.initial_marking)
        bfs_time = time.time() - start_bfs

        bfs_count = len(bfs_reachable)
        self.assertEqual(bfs_count, expected_states)

        # ============ BDD symbolic reachability ============
        bdd_solver = BDDReachability(net)
        bdd_solver.initialize_bdd()

        start_bdd = time.time()
        bdd_result = bdd_solver.compute_symbolic_reachability(net.initial_marking)
        bdd_time = time.time() - start_bdd

        bdd_count = len(bdd_solver.extract_markings(bdd_result))
        self.assertEqual(bdd_count, expected_states)

        print("\n============== Performance (1024 States) ==============")
        print(f"BFS states: {bfs_count} — Time: {bfs_time:.6f} sec")
        print(f"BDD states: {bdd_count} — Time: {bdd_time:.6f} sec")
        print("=======================================================\n")

class TestBDDvsBFS2048(unittest.TestCase):
    """Performance comparison test: BDD vs BFS on 2^11 = 2048 states"""

    def build_independent_binary_net(self, n_bits=11):
        """
        Same construction as the 1024 test, just 11 bits → 2048 states.
        """
        net = PetriNet()
        for i in range(n_bits):
            p1 = f"p{i}_1"
            p2 = f"p{i}_2"
            t = f"t{i}"

            net.add_place(p1, has_token=True)
            net.add_place(p2, has_token=False)
            net.add_transition(t)
            net.add_arc(p1, t)
            net.add_arc(t, p2)
        return net

    def test_bdd_vs_bfs_2048_states(self):
        n_bits = 11   # 2^11 = 2048
        expected_states = 2 ** n_bits

        net = self.build_independent_binary_net(n_bits)

        # ============ BFS explicit reachability ============
        bfs_solver = ExplicitReachability(net)
        start_bfs = time.time()
        bfs_reachable = bfs_solver.compute_reachability(net.initial_marking)
        bfs_time = time.time() - start_bfs

        bfs_count = len(bfs_reachable)
        self.assertEqual(bfs_count, expected_states)

        # ============ BDD symbolic reachability ============
        bdd_solver = BDDReachability(net)
        bdd_solver.initialize_bdd()

        start_bdd = time.time()
        bdd_result = bdd_solver.compute_symbolic_reachability(net.initial_marking)
        bdd_time = time.time() - start_bdd

        bdd_count = len(bdd_solver.extract_markings(bdd_result))
        self.assertEqual(bdd_count, expected_states)

        print("\n============== Performance (2048 States) ==============")
        print(f"BFS states: {bfs_count} — Time: {bfs_time:.6f} sec")
        print(f"BDD states: {bdd_count} — Time: {bdd_time:.6f} sec")
        print("=======================================================\n")

class TestBDDvsBFS8192(unittest.TestCase):
    """Performance comparison test: BDD vs BFS on 2^13 = 8192 states"""

    def build_independent_binary_net(self, n_bits=13):
        """
        13 independent boolean choices → 8192 reachable markings
        """
        net = PetriNet()
        for i in range(n_bits):
            p1 = f"p{i}_1"
            p2 = f"p{i}_2"
            t = f"t{i}"

            net.add_place(p1, has_token=True)
            net.add_place(p2, has_token=False)
            net.add_transition(t)
            net.add_arc(p1, t)
            net.add_arc(t, p2)
        return net

    def test_bdd_vs_bfs_8192_states(self):
        n_bits = 13   # 2^13 = 8192
        expected_states = 2 ** n_bits

        net = self.build_independent_binary_net(n_bits)

        # ============ BFS explicit reachability ============
        bfs_solver = ExplicitReachability(net)
        start_bfs = time.time()
        bfs_reachable = bfs_solver.compute_reachability(net.initial_marking)
        bfs_time = time.time() - start_bfs

        bfs_count = len(bfs_reachable)
        self.assertEqual(bfs_count, expected_states)

        # ============ BDD symbolic reachability ============
        bdd_solver = BDDReachability(net)
        bdd_solver.initialize_bdd()

        start_bdd = time.time()
        bdd_result = bdd_solver.compute_symbolic_reachability(net.initial_marking)
        bdd_time = time.time() - start_bdd

        bdd_count = len(bdd_solver.extract_markings(bdd_result))
        self.assertEqual(bdd_count, expected_states)

        print("\n============== Performance (8192 States) ==============")
        print(f"BFS states: {bfs_count} — Time: {bfs_time:.6f} sec")
        print(f"BDD states: {bdd_count} — Time: {bdd_time:.6f} sec")
        print("=======================================================\n")
