"""
Petri Net Analysis Application

Main entry point for the Petri net analysis tool.
"""

import sys
import argparse
import time
from pathlib import Path

# Import all modules
from pnml_parser import PNMLParser
from explicit_reachability import ExplicitReachability
from bdd_reachability import BDDReachability
from ilp_deadlock import DeadlockDetector
from optimization import MarkingOptimizer
from utils import PetriNet, Marking

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
SAMPLE_PNML_DIR = PROJECT_ROOT / "sample_pnml"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Petri Net Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse a PNML file
  python main.py parse simple-01.pnml
  
  # Compute explicit reachability
  python main.py explicit simple-01.pnml
  
  # Compute BDD-based reachability
  python main.py bdd simple-01.pnml
  
  # Detect deadlocks
  python main.py deadlock simple-01.pnml
  
  # Optimize objective over reachable markings
  python main.py optimize simple-01.pnml
  
  # Run all analysis commands
  python main.py full simple-01.pnml
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        default=None,
        choices=['parse', 'explicit', 'bdd', 'deadlock', 'optimize', 'full', 'compare'],
    )

    parser.add_argument(
        'pnml_file',
        nargs='?',
        default=None,
        help='PNML filename or leave empty to select from menu'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def run_parse(pnml_file, verbose=False):
    """Parse a PNML file."""
    print(f"Parsing PNML file: {pnml_file}")
    parser = PNMLParser()
    
    try:
        result = parser.parse_file(pnml_file)
        print("✓ PNML file parsed successfully")
        if verbose:
            print(repr(result))
    except NotImplementedError:
        print("✗ PNML parsing not yet implemented")
    except Exception as e:
        print(f"✗ Error parsing PNML file: {e}")


def run_explicit_reachability(pnml_file, verbose=False):
    """Run explicit BFS reachability analysis."""
    print(f"Computing explicit reachability for: {pnml_file}")
    
    parser = PNMLParser()
    try:
        petri_net = parser.parse_file(pnml_file)
    except Exception as e:
        print(f"✗ Error parsing PNML file: {e}")
        return
    
    try:
        reachability = ExplicitReachability(petri_net)

        t0 = time.perf_counter()
        reachable = reachability.compute_reachability(petri_net.initial_marking)
        t1 = time.perf_counter()

        print(f"✓ Found {len(reachable)} reachable markings")
        print(f"  Running time: {t1 - t0:.4f}s")

        if verbose:
            for marking in list(reachable)[:10]:
                print(f"  {marking}")

    except Exception as e:
        print(f"✗ Error computing reachability: {e}")



def run_bdd_reachability(pnml_file, verbose=False):
    """Run BDD-based symbolic reachability analysis."""
    print(f"Computing BDD-based reachability for: {pnml_file}")

    parser = PNMLParser()
    try:
        petri_net = parser.parse_file(pnml_file)
    except Exception as e:
        print(f"✗ Error parsing PNML file: {e}")
        return

    try:
        bdd_reachability = BDDReachability(petri_net)

        t0 = time.perf_counter()
        bdd_reachability.initialize_bdd()
        bdd_reachability.compute_symbolic_reachability(petri_net.initial_marking)
        t1 = time.perf_counter()

        print("✓ BDD-based reachability computed")
        print(f"  Running time: {t1 - t0:.4f}s")

        if verbose:
            for marking in list(bdd_reachability.extract_markings())[:10]:
                print(f"  {marking}")

    except Exception as e:
        print(f"✗ Error computing BDD reachability: {e}")

def run_deadlock_detection(pnml_file, verbose=False):
    """Run ILP + BDD deadlock detection."""
    print(f"Detecting deadlocks in: {pnml_file}")
    parser = PNMLParser()
    try:
        petri_net = parser.parse_file(pnml_file)
    except Exception as e:
        print(f"✗ Error parsing PNML file: {e}")
        return
    try:
        bdd_reachability = BDDReachability(petri_net)
        bdd_reachability.initialize_bdd()
        bdd_reachability.compute_symbolic_reachability(petri_net.initial_marking)
    except Exception as e:
        print(f"✗ Error computing BDD reachability: {e}")
        return
    try:
        detector = DeadlockDetector(
            petri_net,
            bdd_reachability.reachable_bdd,
            bdd_reachability.bdd_manager,
            verbose=verbose
        )

        t0 = time.perf_counter()
        deadlock = detector.detect_deadlock()
        t1 = time.perf_counter()
        runtime = t1 - t0

        if not deadlock:
            print("✓ No deadlocks found")
        else:
            print("✓ Deadlock detected")
            if verbose:
                print(f"  Deadlock marking: {deadlock}")
        print(f"  Running time: {runtime:.4f}s")

    except Exception as e:
        print(f"✗ Error detecting deadlocks: {e}")


def run_optimization(pnml_file, verbose=False):
    """Run linear objective optimization over reachable states with user-provided weights (one per place)."""
    print(f"Optimizing objective for: {pnml_file}")
    
    # 1. Parse PNML file
    parser = PNMLParser()
    try:
        petri_net = parser.parse_file(pnml_file)
    except NotImplementedError:
        print("✗ PNML parsing not yet implemented")
        return
    except Exception as e:
        print(f"✗ Error parsing PNML file: {e}")
        return
    
    # 2. Compute BDD Reachability
    try:
        bdd_solver = BDDReachability(petri_net)
        bdd_solver.initialize_bdd()
        bdd_solver.compute_symbolic_reachability(petri_net.initial_marking)
    except Exception as e:
        print(f"✗ Error initializing BDD solver: {e}")
        return

    # 3. Weight Selection Strategy
    try:
        optimizer = MarkingOptimizer(petri_net, verbose=verbose)
        sorted_places = sorted(petri_net.places)

        print("\nSelect weight strategy:")
        print("  1. Strategy A: Alternating incremental (+1, -2, +3, -4, ...)")
        print("  2. Strategy B: Uniform weights (all = 1)")
        print("  3. Strategy C: Manual input")
        
        choice = input("Enter your choice: ").strip()
        weights = {}

        # --- Strategy A: Alternating Incremental ---
        if choice == "1":
            print("  → Using Strategy A (alternating incremental)")
            for idx, place in enumerate(sorted_places, 1):
                weights[place] = idx * (-1 if idx % 2 == 0 else 1)

        # --- Strategy B: Uniform weights ---
        elif choice == "2":
            print("  → Using Strategy B (uniform weights = 1)")
            for place in sorted_places:
                weights[place] = 1

        # --- Strategy C: Manual Input ---
        elif choice == "3":
            print("  → Using Strategy C (manual input)")
            for place in sorted_places:
                while True:
                    user_input = input(f"Weight for {place} (ENTER = 1): ").strip()
                    if user_input == "":
                        weights[place] = 1
                        break
                    try:
                        weights[place] = float(user_input)
                        break
                    except ValueError:
                        print("  Invalid number, try again.")

        else:
            print("✗ Invalid choice — aborting.")
            return

        print(f"\n  Chosen weights: {weights}")

        # 4. Run Optimization
        best_marking, optimal_value, runtime = optimizer.find_max_score_marking(
            bdd_solver, weights
        )
        
        if best_marking is None:
            print("✗ No reachable states found or optimization failed.")
        else:
            print("-" * 30)
            print(f"✓ Optimal value: {optimal_value}")
            print(f"  Calculation time: {runtime:.4f}s")
            print(f"  Optimal marking: {best_marking}")
            print("-" * 30)

    except Exception as e:
        print(f"✗ Error optimizing: {e}")



def run_full_analysis(pnml_file, verbose=False):
    """Run all available analysis commands."""
    print("=" * 60)
    print("RUNNING FULL PETRI NET ANALYSIS")
    print("=" * 60)
    print()
    
    # Run all commands in sequence
    run_parse(pnml_file, verbose)
    print()
    
    run_explicit_reachability(pnml_file, verbose)
    print()
    
    run_bdd_reachability(pnml_file, verbose)
    print()
    
    run_deadlock_detection(pnml_file, verbose)
    print()
    
    run_optimization(pnml_file, verbose)
    print()
    
    print("=" * 60)
    print("FULL ANALYSIS COMPLETED")
    print("=" * 60)

def run_compare(pnml_file, verbose=False):
    """Compare explicit vs BDD in time and structural complexity."""
    print(f"Comparing explicit vs BDD for: {pnml_file}")

    parser = PNMLParser()
    try:
        petri_net = parser.parse_file(pnml_file)
    except Exception as e:
        print(f"✗ Error parsing PNML file: {e}")
        return

    # ---- Explicit ----
    try:
        reach = ExplicitReachability(petri_net)

        t0 = time.perf_counter()
        reachable = reach.compute_reachability(petri_net.initial_marking)
        t1 = time.perf_counter()
        explicit_time = t1 - t0

        print("EXPLICIT")
        print(f"  Reachable states: {len(reachable)}")
        print(f"  Time: {explicit_time:.4f}s")

    except Exception as e:
        print(f"Explicit method failed: {e}")

    # ---- BDD ----
    try:
        bdd = BDDReachability(petri_net)

        t0 = time.perf_counter()
        bdd.initialize_bdd()
        bdd.compute_symbolic_reachability(petri_net.initial_marking)
        t1 = time.perf_counter()
        bdd_time = t1 - t0

        # Structural size (Memory proxy)
        node_count = len(bdd.reachable_bdd)
        
        try:
            logical_state_count = bdd.reachable_bdd.count()
        except:
            logical_state_count = "Unknown"

        print("\nBDD")
        print(f"  BDD Nodes: {node_count}")
        print(f"  Logical States Covered: {logical_state_count}")
        print(f"  Time: {bdd_time:.4f}s")
        
        # Calculate compression
        if node_count > 0 and isinstance(logical_state_count, (int, float)):
             print(f"  Compression: 1 BDD Node ≈ {logical_state_count / node_count:.1f} States")

    except Exception as e:
        print(f"BDD method failed: {e}")
        return

def resolve_pnml_path(arg_value: str) -> str:
    """
    Priority:
      1. absolute path (if exists)
      2. relative to current working dir
      3. sample_pnml/<filename>
    """
    if arg_value is None:
        return None

    p = Path(arg_value)

    if p.is_absolute() and p.exists():
        return str(p.resolve())

    cwd_path = Path.cwd() / arg_value
    if cwd_path.exists():
        return str(cwd_path.resolve())

    sample_path = SAMPLE_PNML_DIR / arg_value
    if sample_path.exists():
        return str(sample_path.resolve())

    return str(sample_path)

def choose_pnml_file():
    folder = SAMPLE_PNML_DIR
    files = sorted([f for f in folder.iterdir() if f.suffix.lower() == ".pnml"])

    if not files:
        print("✗ No PNML files found in sample_pnml/")
        sys.exit(1)

    print("\nAvailable PNML files:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")

    while True:
        choice = input("\nSelect file by number: ").strip()

        if not choice.isdigit():
            print("Invalid input, enter a number.")
            continue

        choice = int(choice)
        if 1 <= choice <= len(files):
            print(f"✓ Selected: {files[choice - 1].name}")
            return str(files[choice - 1])

        print("Out of range, try again.")

def choose_command():
    options = [
        'parse',
        'explicit',
        'bdd',
        'deadlock',
        'optimize',
        'full',
        'compare'
    ]

    print("\nAvailable Commands:")
    for i, c in enumerate(options, 1):
        print(f"  {i}. {c}")

    while True:
        choice = input("\nSelect command by number: ").strip()

        if not choice.isdigit():
            print("Invalid input, enter a number.")
            continue

        choice = int(choice)
        if 1 <= choice <= len(options):
            print(f"✓ Selected command: {options[choice - 1]}")
            return options[choice - 1]

        print("Out of range, try again.")



def main():
    args = parse_arguments()

    # choose command if missing
    if args.command is None:
        command = choose_command()
    else:
        command = args.command

    # choose file if missing
    if args.pnml_file is None:
        pnml_file = choose_pnml_file()
    else:
        pnml_file =pnml_file = resolve_pnml_path(args.pnml_file)

    if not Path(pnml_file).exists():
        print(f"✗ File not found: {pnml_file}. Put the file in sample_pnml or provide a valid path.")
        sys.exit(1)
    
    commands = {
        'parse': run_parse,
        'explicit': run_explicit_reachability,
        'bdd': run_bdd_reachability,
        'deadlock': run_deadlock_detection,
        'optimize': run_optimization,
        'full': run_full_analysis,
        'compare': run_compare
    }
    
    commands[command](pnml_file, args.verbose)



if __name__ == '__main__':
    main()