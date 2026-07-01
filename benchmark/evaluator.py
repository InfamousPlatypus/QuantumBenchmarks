from typing import Dict, List
from qiskit import QuantumCircuit

from .analysis import analyze_circuit
from .csv_output import append_to_csv


def evaluate(
    circuit: QuantumCircuit,
    N: int,
    num_shots: int,
    model: str,
    thinking_level: str
) -> Dict:
    """Evaluate circuit against Qiskit reference implementations and record to CSV.

    Args:
        circuit: Input quantum circuit to evaluate (N-controlled Toffoli decomposition)
        N: Number of qubits targeted (controls + 1 target)
        num_shots: Number of shots for few-shot prompting (metadata only)
        model: Identifier of the model that produced the circuit
        thinking_level: Thinking level (High, medium, low, m/a)

    Returns:
        Dictionary with evaluation results for CSV output
    """
    ANALYZER = analyze_circuit(circuit, N)
    REFERENCES = generate_qiskit_references(circuit, N)

    RESULTS = {
        "model": model,
        "thinking_level": thinking_level,
        "N": N,
        "num_shots": num_shots,
        "llm_depth": ANALYZER["depth"],
        "llm_ancilla": ANALYZER["ancilla"],
    }

    FOR_CSV = {}
    for idx, REF in enumerate(REFERENCES):
        FOR_CSV.update({
            f"qiskit_method_{idx}": REF["method"],
            f"qiskit_depth_{idx}": REF["depth"],
            f"qiskit_ancilla_{idx}": REF["ancilla"],
        })

    RESULTS.update(FOR_CSV)
    append_to_csv(RESULTS, "results.csv")

    return RESULTS


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
        CIRCUIT = _create_mcx_circuit(N, ancilla_count, method_name)
        REFERENCES.append(CIRCUIT)

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
    DEPTH = _get_mcxt_gate(N, ancilla_count).depth()

    return {
        "method": method,
        "depth": DEPTH,
        "ancilla": ancilla_count,
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
        CIRCUIT = _get_mcxt_gate(N, anc)
        DEPTHS.append(CIRCUIT.depth())

    return FROM_0_TO_CURRENT[DEPTHS.index(min(DEPTHS))]


def _get_mcxt_gate(N: int, ancilla_count: int) -> QuantumCircuit:
    """Get an N-controlled Toffoli gate using Qiskit's synthesis with specified ancilla count.
    
    Args:
        N: Number of control qubits
        ancilla_count: Number of ancilla qubits to use
    
    Returns:
        QuantumCircuit containing the synthesized N-controlled Toffoli
    """
    from qiskit.synthesis import synth_mcx_n_clean
    return synth_mcx_n_clean(num_ctrl_qubits=N, num_ancilla_qubits=ancilla_count)
