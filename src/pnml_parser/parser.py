"""
PNML Parser Implementation

Parses 1-safe PNML files to extract Petri net structure including:
- Places
- Transitions
- Arcs
- Initial marking
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from utils.petri_net import PetriNet
from utils.marking import Marking

class PNMLParser:
    """Parser for 1-safe PNML files."""
    
    def __init__(self):
        """Initialize the PNML parser."""
        self.places = []
        self.transitions = []
        self.arcs = []
        self.initial_marking = {}
        
        # Namespace for PNML files
        self.ns = {'pnml': 'http://www.pnml.org/version-2009/grammar/pnml'}
    
    def parse_file(self, filepath):
        """
        Parse a PNML file and extract Petri net structure.
        
        Args:
            filepath: Path to the PNML file
            
        Returns:
            PetriNet object containing places, transitions, arcs, and initial marking
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the net is not 1-safe (has places with more than 1 token)
        """
        # Check if file exists
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Parse XML
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Create PetriNet object
        petri_net = PetriNet()
        
        # Parse places
        self._parse_places(root, petri_net)
        
        # Parse transitions
        self._parse_transitions(root, petri_net)
        
        # Parse arcs
        self._parse_arcs(root, petri_net)
        
        # Validate consistency
        is_valid, errors = petri_net.validate_consistency()
        if not is_valid:
            raise ValueError(f"Petri net consistency errors: {errors}")
        
        return petri_net
    
    def _parse_places(self, root, petri_net):
        """
        Parse all places from the PNML file.
        
        Args:
            root: Root element of the XML tree
            petri_net: PetriNet object to populate
        """
        # Find all place elements (with and without namespace)
        places = root.findall('.//pnml:place', self.ns)
        if not places:
            places = root.findall('.//place')
        
        for place in places:
            place_id = place.get('id')
            
            # Get place name
            name_elem = place.find('.//pnml:name/pnml:text', self.ns)
            if name_elem is None:
                name_elem = place.find('.//name/text')
            place_name = name_elem.text if name_elem is not None else None
            
            # Get initial marking
            marking_elem = place.find('.//pnml:initialMarking/pnml:text', self.ns)
            if marking_elem is None:
                marking_elem = place.find('.//initialMarking/text')
            
            has_token = False
            if marking_elem is not None:
                try:
                    token_count = int(marking_elem.text.strip())
                    
                    # Validate 1-safe property
                    if token_count > 1:
                        raise ValueError(
                            f"Place {place_id} has {token_count} tokens. "
                            f"This net is not 1-safe (max 1 token per place)."
                        )
                    
                    has_token = (token_count == 1)
                except ValueError as e:
                    if "not 1-safe" in str(e):
                        raise
                    # If conversion fails, assume 0 tokens
                    has_token = False
            
            # Add place to Petri net
            petri_net.add_place(place_id, has_token=has_token, name=place_name)
            
            # Store for internal tracking
            self.places.append(place_id)
            self.initial_marking[place_id] = 1 if has_token else 0
    
    def _parse_transitions(self, root, petri_net):
        """
        Parse all transitions from the PNML file.
        
        Args:
            root: Root element of the XML tree
            petri_net: PetriNet object to populate
        """
        # Find all transition elements (with and without namespace)
        transitions = root.findall('.//pnml:transition', self.ns)
        if not transitions:
            transitions = root.findall('.//transition')
        
        for transition in transitions:
            transition_id = transition.get('id')
            
            # Get transition name
            name_elem = transition.find('.//pnml:name/pnml:text', self.ns)
            if name_elem is None:
                name_elem = transition.find('.//name/text')
            transition_name = name_elem.text if name_elem is not None else None
            
            # Add transition to Petri net
            petri_net.add_transition(transition_id, name=transition_name)
            
            # Store for internal tracking
            self.transitions.append(transition_id)
    
    def _parse_arcs(self, root, petri_net):
        """
        Parse all arcs from the PNML file.
        
        Args:
            root: Root element of the XML tree
            petri_net: PetriNet object to populate
        """
        # Find all arc elements (with and without namespace)
        arcs = root.findall('.//pnml:arc', self.ns)
        if not arcs:
            arcs = root.findall('.//arc')
        
        for arc in arcs:
            source = arc.get('source')
            target = arc.get('target')
            
            # Get arc weight (for validation, should be 1 for 1-safe nets)
            inscription_elem = arc.find('.//pnml:inscription/pnml:text', self.ns)
            if inscription_elem is None:
                inscription_elem = arc.find('.//inscription/text')
            
            weight = 1  # Default weight
            if inscription_elem is not None:
                try:
                    weight = int(inscription_elem.text.strip())
                except ValueError:
                    weight = 1
            
            # For 1-safe nets, arc weight should be 1
            if weight != 1:
                raise ValueError(
                    f"Arc from {source} to {target} has weight {weight}. "
                    f"For 1-safe nets, all arc weights must be 1."
                )
            
            # Add arc to Petri net
            petri_net.add_arc(source, target)
            
            # Store for internal tracking
            self.arcs.append((source, target))
    
    def validate_1safe(self):
        """
        Validate that the parsed Petri net is 1-safe.
        
        This checks if the initial marking has at most 1 token per place.
        Note: This only validates the initial marking. Full 1-safe validation
        would require checking all reachable markings.
        
        Returns:
            Boolean indicating if the initial marking is 1-safe
        """
        for place_id, tokens in self.initial_marking.items():
            if tokens > 1:
                return False
        return True
    
    def get_parsed_data(self):
        """
        Get the parsed data as a dictionary.
        
        Returns:
            Dictionary with places, transitions, arcs, and initial_marking
        """
        return {
            'places': self.places,
            'transitions': self.transitions,
            'arcs': self.arcs,
            'initial_marking': self.initial_marking
        }
