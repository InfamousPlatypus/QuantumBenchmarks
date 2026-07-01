from qiskit import QuantumCircuit
from qiskit.circuit.library import MCXGate


def generate_qiskit_references(circuit: QuantumCircuit, N: int) -> List[dict]:
    """Generate Qiskit-optimized reference circuits for comparison.

    Generates 3 reference circuits with different ancilla configurations:
    1. No ancilla (zero-ancilla decomposition)
    2. Matching ancilla count (same ancillas as input circuit)
    3. Optimized ancilla count (Qiskit's best depth configuration)

    Args:
        circuit: Input circuit (to extract current ancilla count)
        N: Target number of qubits (N controls + 1 target)

    Returns:
        List of dictionaries containing method, depth, and ancilla count for each reference
    """
    CURRENT_ANCILLA = circuit.num_qubits - (N + 1)

    REFERENCES = []
    
    ANCILLA_CONFIGS = [
        (0, "no_ancilla"),
        (CURRENT_ANCILLA, "match_ancilla"),
    ]

    for ancilla_count, method_name in ANCILLA_CONFIGS:
        REF = _create_mcx_circuit(N, ancilla_count, method_name)
        REFERENCES.append(REF)

    OPTIMAL_ANCILLA = _get_optimal_ancilla_config(N, CURRENT_ANCILLA)
    REF = _create_mcx_circuit(N, OPTIMAL_ANCILLA, "optimal")
    REFERENCES.append(REF)

    return REFERENCES


def _create_mcx_circuit(N: int, ancilla_count: int, method: str) -> dict:
    """Create an N-controlled Toffoli circuit with specified ancilla count.

    Args:
        N: Number of control qubits
        ancilla_count: Number of ancilla qubits to use
        method: Description of the method used

    Returns:
        Dictionary with method, depth, and ancilla count
    """
    if ancilla_count == 0:
        CIRCUIT = MCXGate(num_ctrl_qubits=N, ancilla_qubits=[])
    else:
        CIRCUIT = MCXGate(num_ctrl_qubits=N, ancilla_qubits=ancilla_count)

    DEPTH = CIRCUIT.depth()

    return {
        "method": method,
        "depth": DEPTH,
        "ancilla": ancilla_count,
        "circuit": CIRCUIT,
    }


def _get_optimal_ancilla_config(N: int, current_ancilla: int) -> int:
    """Determine optimal ancilla count for N-controlled Toffoli using Qiskit's synthesis.

    Args:
        N: Number of control qubits
        current_ancilla: Current ancilla count from input circuit

    Returns:
        Optimal ancilla count for minimizing circuit depth
    """
    FROM_0_TO_CURRENT = range(0, current_ancilla + 1)
    DEPTHS = []
    
    for anc in FROM_0_TO_CURRENT:
        CIRCUIT = MCXGate(num_ctrl_qubits=N, ancilla_qubits=anc)
        DEPTHS.append(CIRCUIT.depth())

    return FROM_0_TO_CURRENT[DEPTHS.index(min(DEPTHS))]
