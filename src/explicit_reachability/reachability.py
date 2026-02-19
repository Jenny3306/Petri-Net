from collections import deque
from utils import Marking, PetriNet


class ExplicitReachability:
    """
    Explicit reachability (BFS) for 1-safe Petri nets.

    Notes / decisions made to match the test-suite:
    - compute_reachability accepts an optional initial_marking argument
      (Marking or dict). If omitted, uses petri_net.initial_marking.
    - Uses BFS (collections.deque with popleft) to be stable and predictable.
    - compute_reachability resets internal reachable_markings and transition_graph
      on each call.
    """

    def __init__(self, petri_net: PetriNet):
        self.petri_net = petri_net
        self.reachable_markings = set()
        self.transition_graph = {}

    def compute_reachability(self, initial_marking):
        """
        Compute all reachable markings from the initial_marking (or net.initial_marking)
        using BFS and return the set of reachable Marking objects.
        """
        # Normalize input initial marking
        if initial_marking is None:
            initial = self.petri_net.initial_marking
        else:
            if isinstance(initial_marking, dict):
                initial = Marking(initial_marking)
            elif isinstance(initial_marking, Marking):
                initial = initial_marking.copy()
            else:
                # try to accept other types that behave like Marking
                initial = initial_marking

        # Reset state for this run
        self.reachable_markings = set()
        self.transition_graph = {}

        queue = deque([initial])
        self.reachable_markings.add(initial)
        self.transition_graph[initial] = {}

        while queue:
            current = queue.popleft()

            enabled = self.petri_net.get_enabled_transitions(current)

            if enabled:
                # Explore enabled transitions
                for t in enabled:
                    new_marking = self.petri_net.fire_transition(t, current)

                    # Register edge in transition graph
                    self.transition_graph.setdefault(current, {})
                    self.transition_graph[current][t] = new_marking

                    # If unseen, add and enqueue
                    if new_marking not in self.reachable_markings:
                        self.reachable_markings.add(new_marking)
                        queue.append(new_marking)
                        # ensure node exists in graph
                        self.transition_graph.setdefault(new_marking, {})
                        
        return self.reachable_markings

    def is_reachable(self, target_marking):
        """
        Check if a marking is reachable (after compute_reachability has been run).
        Accepts a dict or Marking.
        """
        if isinstance(target_marking, dict):
            target = Marking(target_marking)
        elif isinstance(target_marking, Marking):
            target = target_marking
        else:
            target = target_marking

        return target in self.reachable_markings

    def get_transition_graph(self):
        """
        Return the transition graph mapping:
            {Marking: {transition_id: new_marking, ...}, ...}
        """
        return self.transition_graph
