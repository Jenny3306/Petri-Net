"""
ILP + BDD Deadlock Detection Module

This module combines Integer Linear Programming (ILP) and Binary Decision Diagrams (BDDs)
to efficiently detect deadlocks in Petri nets.
"""

from .deadlock_detector import DeadlockDetector

__all__ = ['DeadlockDetector']
