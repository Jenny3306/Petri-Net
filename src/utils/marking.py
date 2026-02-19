"""
Marking Data Structure

Defines data structures and utilities for working with Petri net markings.
"""

from copy import deepcopy


class Marking:
    """
    Represents a marking (state) of a 1-safe Petri net.
    
    A marking is a mapping from places to binary token states (True/False or 1/0).
    For 1-safe nets, each place either has a token (1) or doesn't (0).
    hashable for use in sets and dictionaries
    """
    
    def __init__(self, marking_dict=None):
        """
        Initialize a marking.
        
        Args:
            marking_dict: Dictionary mapping place IDs to token states (bool or int 0/1)
        """
        self.marking = {}
        if marking_dict is not None:
            for place, token in marking_dict.items():
                # Normalize to boolean
                self.marking[place] = bool(token)
    
    def has_token(self, place):
        """
        Check if a place has a token.
        """
        return self.marking.get(place, False)
    
    def set_token(self, place, has_token):
        """
        Set whether a place has a token.
        """
        self.marking[place] = bool(has_token)
    
    def get_tokens(self, place):
        """
        Get the number of tokens in a place (for compatibility).
        
        For 1-safe nets, returns 1 if place has token, 0 otherwise.
        """
        return 1 if self.has_token(place) else 0
    
    def set_tokens(self, place, tokens):
        """
        Set the number of tokens in a place (for compatibility).
        
        For 1-safe nets, any non-zero value sets the token to True.
        """
        self.set_token(place, bool(tokens))
    
    def copy(self):
        """
        Create a deep copy of this marking.
        
        Returns:
            New Marking object with the same token distribution
        """
        return Marking(deepcopy(self.marking))
    
    def to_tuple(self):
        """
        Convert marking to a sorted tuple for comparison and hashing.
        
        Returns:
            Tuple of (place, tokens) pairs sorted by place ID
        """
        return tuple(sorted(self.marking.items()))
    
    def to_vector(self, places):
        """
        Convert marking to a binary vector representation given an ordered list of places.
        """
        return [1 if self.has_token(place) else 0 for place in places]
    
    def to_binary_vector(self, places):
        """
        Convert marking to binary vector (alias for to_vector for 1-safe nets).
        """
        return self.to_vector(places)
    
    @staticmethod
    def from_vector(vector, places):
        """
        Create a marking from a binary vector representation.
        """
        if len(vector) != len(places):
            raise ValueError(f"Vector length ({len(vector)}) does not match "
                           f"number of places ({len(places)})")
        
        marking_dict = {place: bool(token) for place, token in zip(places, vector)}
        return Marking(marking_dict)
    
    def get_places(self):
        """
        Get all places in this marking.
        """
        return set(self.marking.keys())
    
    def total_tokens(self):
        """
        Calculate the total number of tokens in this marking.
        """
        return sum(1 for has_token in self.marking.values() if has_token)
    
    def __eq__(self, other):
        """
        Check if two markings are equal.
        
        Two markings are equal if they have the same token distribution.
        """
        if not isinstance(other, Marking):
            return False
        return self.marking == other.marking
    
    def __hash__(self):
        """
        Compute hash of marking for use in sets and dictionaries.
        
        This is crucial for efficient reachability analysis where we need to
        track visited markings in a set.
        """
        return hash(tuple(sorted(self.marking.items())))
    
    def __lt__(self, other):
        """
        Less than comparison for sorting markings.
        
        Useful for consistent ordering in output and testing.
        """
        if not isinstance(other, Marking):
            return NotImplemented
        return self.to_tuple() < other.to_tuple()
    
    def __str__(self):
        """String representation of marking."""
        # Format as {p1: 1, p2: 0, ...} sorted by place ID
        sorted_items = sorted(self.marking.items())
        items_str = ", ".join(f"{place}: {1 if has_token else 0}" 
                             for place, has_token in sorted_items)
        return f"{{{items_str}}}"
    
    def __repr__(self):
        """Detailed string representation of marking."""
        return f"Marking({self.marking})"
    
    def to_dict(self):
        """
        Convert marking to a dictionary representation.
        """
        return {place: (1 if has_token else 0) for place, has_token in self.marking.items()}
