"""
Petri Net Data Structure

Defines the core data structures for representing a Petri net.
"""

from copy import deepcopy
from .marking import Marking


class PetriNet:
    """
    Represents a 1-safe Petri net structure.
    
    For 1-safe Petri nets:
    - Each place has at most one token (binary state: has token or no token)
    - All arc weights are implicitly 1
    
    Attributes:
        places: Set of place identifiers in the net
        transitions: Set of transition identifiers in the net
        arcs: Dictionary representing arcs (edges) in the net
              Structure: {transition_id: {'input': [place_ids], 'output': [place_ids]}}
        initial_marking: Initial marking of the net as a Marking object
        place_names: Dictionary mapping place IDs to human-readable names
        transition_names: Dictionary mapping transition IDs to human-readable names
    """
    
    def __init__(self):
        """Initialize an empty Petri net."""
        self.places = set()
        self.transitions = set()
        self.arcs = {}
        self.initial_marking = Marking()
        self.place_names = {}
        self.transition_names = {}
        self.incidence = None # To be computed as needed

    def add_place(self, place_id, has_token=False, name=None):
        """
        Add a place to the Petri net.
        """
        if place_id in self.places:
            raise ValueError(f"Place {place_id} already exists")
        
        self.places.add(place_id)
        self.initial_marking.set_token(place_id, has_token)
        
        if name:
            self.place_names[place_id] = name
    
    def add_transition(self, transition_id, name=None):
        """
        Add a transition to the Petri net.
        """
        if transition_id in self.transitions:
            raise ValueError(f"Transition {transition_id} already exists")
        
        self.transitions.add(transition_id)
        self.arcs[transition_id] = {'input': [], 'output': []}
        
        if name:
            self.transition_names[transition_id] = name
    
    def add_arc(self, source, target):
        """
        Add an arc between a place and transition or vice versa.
        """
        # Determine arc type
        if source in self.places and target in self.transitions:
            # Place to transition (input arc)
            if target not in self.arcs:
                self.arcs[target] = {'input': [], 'output': []}
            self.arcs[target]['input'].append(source)
            
        elif source in self.transitions and target in self.places:
            # Transition to place (output arc)
            if source not in self.arcs:
                self.arcs[source] = {'input': [], 'output': []}
            self.arcs[source]['output'].append(target)
            
        else:
            raise ValueError(f"Invalid arc from {source} to {target}. "
                           f"Arcs must connect places to transitions or transitions to places.")
    
    def is_enabled(self, transition, marking):
        """
        Check if a transition is enabled in a given marking.
        
        A transition is enabled if all its input places have a token.
        """
        if transition not in self.transitions:
            raise ValueError(f"Transition {transition} does not exist")
        
        # Convert dict to Marking if necessary
        if isinstance(marking, dict):
            marking = Marking(marking)
        
        # Check if all input places have a token
        for place in self.arcs[transition]['input']:
            if not marking.has_token(place):
                return False
        
        return True
    
    def fire_transition(self, transition, marking):
        """
        Fire a transition and return the new marking.
        
        Firing removes tokens from input places and adds tokens to output places.
        """
        if transition not in self.transitions:
            raise ValueError(f"Transition {transition} does not exist")
        
        # Convert dict to Marking if necessary
        if isinstance(marking, dict):
            marking = Marking(marking)
        
        if not self.is_enabled(transition, marking):
            raise ValueError(f"Transition {transition} is not enabled in the given marking")
        
        # Create new marking by deep copying
        new_marking = marking.copy()
        
        # Remove tokens from input places
        for place in self.arcs[transition]['input']:
            new_marking.set_token(place, False)
        
        # Add tokens to output places
        for place in self.arcs[transition]['output']:
            new_marking.set_token(place, True)
        
        return new_marking
    
    def get_enabled_transitions(self, marking):
        """
        Get all transitions enabled in a given marking.
        """
        if isinstance(marking, dict):
            marking = Marking(marking)
        
        return [t for t in self.transitions if self.is_enabled(t, marking)]
    
    def validate_consistency(self):
        """
        Validate the consistency of the Petri net structure.
        
        Checks for:
        - All places in arcs exist in the places set
        - All transitions have arc information
        - No missing nodes
        """
        errors = []
        
        # Check all transitions have arc entries
        for trans in self.transitions:
            if trans not in self.arcs:
                errors.append(f"Transition {trans} has no arc information")
        
        # Check all places referenced in arcs exist
        for trans, arc_info in self.arcs.items():
            if trans not in self.transitions:
                errors.append(f"Arc references non-existent transition {trans}")
            
            for place in arc_info['input']:
                if place not in self.places:
                    errors.append(f"Input arc references non-existent place {place}")
            
            for place in arc_info['output']:
                if place not in self.places:
                    errors.append(f"Output arc references non-existent place {place}")
        
        # Check initial marking covers all places
        for place in self.places:
            if place not in self.initial_marking.marking:
                self.initial_marking.set_tokens(place, 0)
        
        return len(errors) == 0, errors
    
    def get_place_name(self, place_id):
        return self.place_names.get(place_id, place_id)
    
    def get_transition_name(self, transition_id):
        return self.transition_names.get(transition_id, transition_id)

    def get_incidence(self):
        """Get the incidence matrix."""
        if self.incidence is None:
            self.incidence = {p: {t: 0 for t in self.transitions} for p in self.places}
            for t in self.transitions:
                for p in self.arcs[t]['input']:
                    self.incidence[p][t] -= 1
                for p in self.arcs[t]['output']:
                    self.incidence[p][t] += 1
        return self.incidence

    def __str__(self):
        """
        String representation for quick inspection.
        """
        return f"PetriNet(places={len(self.places)}, transitions={len(self.transitions)})"

    def __repr__(self):
        """Detailed string representation.
        Print the Petri net with dynamic column alignment:
        - All places (with names)
        - All transitions (with names)
        - Input matrix C- (|P| x |T|)
        - Output matrix C+ (|P| x |T|)
        - Incidence matrix C = C+ - C-
        """
        places = sorted(list(self.places))
        transitions = sorted(list(self.transitions))

        # 1. Calculate dynamic column widths
        # Find the longest transition string to set column width (min 3 chars)
        max_t_len = max([len(str(t)) for t in transitions] + [3])
        col_width = max_t_len + 2  # Add padding

        # Find the longest place string to set row header width
        max_p_len = max([len(str(p)) for p in places] + [0])
        row_head_width = max_p_len + 2 # Add padding

        # Build matrices data
        C_minus = {p: {t: 0 for t in transitions} for p in places}
        C_plus = {p: {t: 0 for t in transitions} for p in places}

        for t in transitions:
            for p in self.arcs[t]['input']:
                C_minus[p][t] = 1
            for p in self.arcs[t]['output']:
                C_plus[p][t] = 1

        # Places List and number of places
        place_lines = [f"Places ({len(self.places)}):"]
        for p in places:
            name = self.place_names.get(p, "")
            place_lines.append(f"  {p}" + (f" ({name})" if name else ""))

        # Transitions List
        transition_lines = [f"Transitions ({len(self.transitions)}):"]
        for t in transitions:
            name = self.transition_names.get(t, "")
            transition_lines.append(f"  {t}" + (f" ({name})" if name else ""))

        # Number of arcs
        num_arcs = sum(len(self.arcs[t]['input']) + len(self.arcs[t]['output']) for t in transitions)
        transition_lines.append(f"Number of arcs: {num_arcs}")

        # Format matrix block helper
        def format_matrix(title, M):
            header_str = " " * row_head_width + "".join(f"{str(t):>{col_width}}" for t in transitions)
            
            rows = [header_str]
            for p in places:
                # Create the row: Place ID + Values
                values = "".join(f"{M[p][t]:>{col_width}}" for t in transitions)
                row = f"{str(p):>{row_head_width}}{values}"
                rows.append(row)
            return [title] + rows

        # # Build all matrices
        # C_minus_block = format_matrix("Input Matrix C-:", C_minus)
        # C_plus_block = format_matrix("Output Matrix C+:", C_plus)

        # Compute incidence matrix C = C+ - C-
        C = {p: {t: C_plus[p][t] - C_minus[p][t] for t in transitions} for p in places}
        C_block = format_matrix("Incidence Matrix C:", C)

        # Initial marking
        initial_marking_str = "Initial Marking:\n"+str(self.initial_marking)

        # Join
        return "\n".join(
            place_lines
            + [""] 
            + transition_lines
            # + [""] 
            # + C_minus_block
            # + [""] 
            # + C_plus_block
            + [""] 
            + C_block
            + [""]
            + [initial_marking_str]
        )
