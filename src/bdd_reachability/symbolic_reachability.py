# bdd_reachability.py
"""
Symbolic BDD reachability with a proper transition relation.

- Declares current vars `p` and next vars `p'` for each place.
- Builds transition relation T(s,s') = OR_t ( enabled_t(s) & update_t(s,s') ).
- Computes reachability by fixpoint: R <- R ∪ Post(R) with Post(R)(s') = ∃s. R(s) & T(s,s')
- Adds zero-marking in dead-end single-token situations to match explicit reachability logic.
"""

from dd.autoref import BDD
from utils import Marking,PetriNet

class BDDReachability:
    #########################################################################CONSTRUCTOR#######################################################
    def __init__(self, petri_net):
        self.petri_net = petri_net
        # BDD manager is None until initialize_bdd() is called (tests expect this)
        self.bdd_manager = None

        # maps place -> Function (current var) and place -> Function (next var)
        self.place_var = {}
        self.next_var = {}

        # transition maps (t -> [places])
        self.trans_in = {}
        self.trans_out = {}

        # the full transition relation (BDD over current and next vars)
        self.transition_relation = None

        # reachable set (bdd over current vars)
        self.reachable_bdd = None

    # -------------------------
    # Build transition maps (robust)
    # -------------------------
    def _build_transition_maps(self):
        net = self.petri_net
        # initialize entries
        for t in getattr(net, "transitions", []):
            self.trans_in.setdefault(t, [])
            self.trans_out.setdefault(t, [])

        #  xử lý cấu trúc dict của utils.PetriNet
        if hasattr(net, "arcs") and isinstance(net.arcs, dict):
            try:
                for t, arc_info in net.arcs.items():
                    # Chỉ cập nhật nếu t là một transition hợp lệ
                    if t in getattr(net, "transitions", []):
                        self.trans_in[t] = list(arc_info.get('input', []))
                        self.trans_out[t] = list(arc_info.get('output', []))
                return # Đã thành công, thoát khỏi các logic fallback khác
            except Exception:
                pass

        if hasattr(net, "pre") and hasattr(net, "post"):
            try:
                for t in getattr(net, "pre", {}):
                    self.trans_in[t] = list(net.pre[t])
                for t in getattr(net, "post", {}):
                    self.trans_out[t] = list(net.post[t])
                return
            except Exception:
                pass

        if hasattr(net, "preset") and hasattr(net, "postset"):
            try:
                for t in getattr(net, "preset", {}):
                    self.trans_in[t] = list(net.preset[t])
                for t in getattr(net, "postset", {}):
                    self.trans_out[t] = list(net.postset[t])
                return
            except Exception:
                pass

        if hasattr(net, "arcs"):
            try:
                for arc in net.arcs:
                    if not (isinstance(arc, (list, tuple)) and len(arc) >= 2):
                        continue
                    src, dst = arc[0], arc[1]
                    if src in getattr(net, "places", []) and dst in getattr(net, "transitions", []):
                        self.trans_in.setdefault(dst, []).append(src)
                    if src in getattr(net, "transitions", []) and dst in getattr(net, "places", []):
                        self.trans_out.setdefault(src, []).append(dst)
                return
            except Exception:
                pass

        # fallback: try any iterable attr that looks like arcs
        for attr in dir(net):
            if attr.startswith("_"):
                continue
            val = getattr(net, attr)
            if isinstance(val, (list, tuple)):
                try:
                    built = False
                    for item in val:
                        if not isinstance(item, (list, tuple)) or len(item) < 2:
                            continue
                        src, dst = item[0], item[1]
                        if src in getattr(net, "places", []) and dst in getattr(net, "transitions", []):
                            self.trans_in.setdefault(dst, []).append(src)
                            built = True
                        if src in getattr(net, "transitions", []) and dst in getattr(net, "places", []):
                            self.trans_out.setdefault(src, []).append(dst)
                            built = True
                    if built:
                        return
                except Exception:
                    continue

        # ensure at least empty lists for every transition
        for t in getattr(net, "transitions", []):
            self.trans_in.setdefault(t, [])
            self.trans_out.setdefault(t, [])

    # -------------------------
    # Initialize BDD (declare variables)
    # -------------------------
    ###############################################################Initialize BDD#############################################
    def initialize_bdd(self):
        """Declare vars and build transition relation."""
        self.bdd_manager = BDD()
        self.place_var = {}
        self.next_var = {}

        places = list(getattr(self.petri_net, "places", []))
        places.sort()

        # declare current and next var names (use p and p')
        for p in places:
            name_now = p
            name_next = p + "'"
            # declare both names
            self.bdd_manager.declare(name_now)
            self.bdd_manager.declare(name_next)
            # store function nodes
            self.place_var[p] = self.bdd_manager.var(name_now)
            self.next_var[p] = self.bdd_manager.var(name_next)

        # build trans maps
        self._build_transition_maps()

        # build transition relation
        self._build_transition_relation()

        # reset reachable containers
        self.reachable_bdd = self.bdd_manager.false

    # -------------------------
    # Build transition relation T(s,s')
    # -------------------------
    def _build_transition_relation(self):
        """T = OR_t ( enabled_t(s) & update_t(s,s') )."""
        if self.bdd_manager is None:
            raise RuntimeError("Call initialize_bdd() first")

        bdd = self.bdd_manager
        places = list(getattr(self.petri_net, "places", []))
        places.sort()

        T = bdd.false

        for t in getattr(self.petri_net, "transitions", []):
            pre = list(self.trans_in.get(t, []))
            post = list(self.trans_out.get(t, []))

            # enabled(s): all pre places true
            enabled = bdd.true
            for p in pre:
                enabled &= self.place_var[p]

            # next-state constraints
            next_cons = bdd.true
            for p in places:
                x = self.place_var[p]
                xp = self.next_var[p]
                if p in post:
                    # produced -> xp == 1
                    next_cons &= xp
                elif p in pre:
                    # consumed -> xp == 0
                    next_cons &= ~xp
                else:
                    # unchanged: xp == x  <=> (¬x & ¬xp) ∨ (x & xp)
                    next_cons &= ((~x & ~xp) | (x & xp))

            T = T | (enabled & next_cons)

        self.transition_relation = T

    # -------------------------
    # Encode a marking into BDD (current vars)
    # -------------------------
    def encode_marking(self, marking):
        if self.bdd_manager is None:
            raise RuntimeError("Call initialize_bdd() before encoding markings.")
        if isinstance(marking, dict):
            marking = Marking(marking)

        bdd = self.bdd_manager
        node = bdd.true
        for p in sorted(getattr(self.petri_net, "places", [])):
            var = self.place_var[p]
            if marking.has_token(p):
                node &= var
            else:
                node &= ~var
        return node

    # -------------------------
    # Post-image: Post(R) = ∃s. R(s) & T(s,s')  (returns BDD over current vars)
    # -------------------------
    def post(self, R):
        if self.bdd_manager is None:
            raise RuntimeError("Call initialize_bdd() before computing post.")
        if self.transition_relation is None:
            return self.bdd_manager.false

        bdd = self.bdd_manager
        prod = R & self.transition_relation

        # existential quantification over current var names (strings)
        places = sorted(getattr(self.petri_net, "places", []))
        if places:
            prod = bdd.exist(places, prod)

        # rename next vars (p') -> current var nodes p
        # mapping keys are var names p' (string) and values are Function nodes for p
        rename_map = {p + "'": self.place_var[p] for p in places}
        if rename_map:
            prod = bdd.let(rename_map, prod)

        return prod

    # -------------------------###################################################################################
    # Compute symbolic reachability (fixpoint). Also inject zero-marking as in explicit code.
    # -------------------------###################################################################################
    def compute_symbolic_reachability(self, initial_marking):
        if isinstance(initial_marking, dict):
            initial_marking = Marking(initial_marking)

        if self.bdd_manager is None:
            self.initialize_bdd()

        # R0
        R = self.encode_marking(initial_marking)

        while True:
            postR = self.post(R)
            Rnext = R | postR

            if Rnext == R:
                break
            R = Rnext

        self.reachable_bdd = R
        # build explicit set for compatibility
        return R

    # helper that returns set/list of Marking objects from a reachable-bdd using only current vars ################extract helper###################
    def _extract_markings_from_bdd(self, reachable_bdd, places):
        bdd = self.bdd_manager
        results = set()
        if not places:
            if reachable_bdd != bdd.false:
                results.add(Marking({}))
            return results

        # bdd.pick_iter yields assignments varname->bool
        for assign in bdd.pick_iter(reachable_bdd):
            m = {}
            for p in places:
                val = bool(assign.get(p, False))
                m[p] = 1 if val else 0
            results.add(Marking(m))
        return results

    # -------------------------
    # Public extract_markings (keeps API)
    # -------------------------
    def extract_markings(self, reachable_bdd=None):
        if self.bdd_manager is None:
            raise RuntimeError("Call initialize_bdd() before extracting markings.")
        if reachable_bdd is None:
            reachable_bdd = self.reachable_bdd
        if reachable_bdd is None:
            return set()
        places = sorted(getattr(self.petri_net, "places", []))
        return set(self._extract_markings_from_bdd(reachable_bdd, places))
    ######################################################################Các hàm khác ################################################################
    # -------------------------
    # Encode transitions for tests (returns simple dict)
    # -------------------------
    def encode_transition(self, t):
        return {"name": t, "pre": list(self.trans_in.get(t, [])), "post": list(self.trans_out.get(t, []))}

    def encode_all_transitions(self):
        return [self.encode_transition(t) for t in getattr(self.petri_net, "transitions", [])]

    # -------------------------
    # Check equality-based satisfies (used in tests)
    # -------------------------
    def satisfies(self, marking_bdd, marking):
        enc = self.encode_marking(marking)
        return marking_bdd == enc

    # -------------------------
    # Convenience: is marking reachable (after compute)
    # -------------------------
    def is_reachable(self, marking):
        if isinstance(marking, dict):
            marking = Marking(marking)
        if self.reachable_bdd is None:
            # try compute from net.initial_marking if available
            init = getattr(self.petri_net, "initial_marking", None)
            if init is None:
                return False
            self.compute_symbolic_reachability(init)
        enc = self.encode_marking(marking)
        return (enc & self.reachable_bdd) != self.bdd_manager.false

