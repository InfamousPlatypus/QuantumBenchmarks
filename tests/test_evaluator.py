"""
Tests for the QuantumBenchmarks package.

These tests verify the functionality of the N-controlled Toffoli benchmarking framework,
ensuring that LLM-generated circuit evaluations and Qiskit reference comparisons
work correctly.
"""
import os
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit.library import MCXGate
from benchmark.analysis import analyze_circuit
from benchmark.csv_output import append_to_csv
from benchmark.evaluator import evaluate


def test_analyze_circuit_basic():
    """Test basic circuit analysis for depth and ancilla counting."""
    N = 3

    # Create a QuantumCircuit with N+1 qubits (N controls + 1 target)
    circuit = QuantumCircuit(N + 1)
    circuit.mcx(list(range(N)), N)

    result = analyze_circuit(circuit, N)

    assert "depth" in result
    assert "ancilla" in result
    assert result["ancilla"] == 0
    assert result["depth"] > 0


def test_analyze_circuit_with_ancillas():
    """Test analysis of a circuit that includes ancilla qubits."""
    N = 3

    # Create a circuit with N+1 + 2 = N+3 total qubits (N controls + 1 target + 2 ancillas)
    circuit = QuantumCircuit(N + 3)
    circuit.mcx(list(range(N)), N)

    result = analyze_circuit(circuit, N)

    assert "depth" in result
    assert "ancilla" in result
    # Ancilla count = total qubits - (N + 1) = (N+3) - (N+1) = 2
    assert result["ancilla"] == 2


def test_append_to_csv_new_file():
    """Test CSV appending to a new file (creation)."""
    test_csv = "test_new.csv"
    test_data = {"model": "test", "depth": 10}

    append_to_csv(test_data, test_csv)

    assert os.path.exists(test_csv)
    os.remove(test_csv)


def test_append_to_csv_existing():
    """Test CSV appending to an existing file."""
    test_csv = "test_existing.csv"

    if os.path.exists(test_csv):
        os.remove(test_csv)

    data1 = {"model": "test1", "depth": 10}
    data2 = {"model": "test2", "depth": 20}

    append_to_csv(data1, test_csv)
    append_to_csv(data2, test_csv)

    import pandas as pd

    df = pd.read_csv(test_csv)
    assert len(df) == 2
    assert df.iloc[0]["model"] == "test1"
    assert df.iloc[1]["model"] == "test2"

    os.remove(test_csv)


def test_evaluate_basic():
    """Test basic evaluation with a simple circuit."""
    N = 3

    # Create a proper QuantumCircuit
    circuit = QuantumCircuit(N + 1)
    circuit.mcx(list(range(N)), N)

    results = evaluate(
        circuit=circuit,
        N=N,
        num_shots=5,
        model="test_model",
        thinking_level="medium"
    )

    assert "model" in results
    assert "thinking_level" in results
    assert "N" in results
    assert "num_shots" in results
    assert "llm_depth" in results
    assert "llm_ancilla" in results

    assert results["model"] == "test_model"
    assert results["thinking_level"] == "medium"
    assert results["N"] == N
    assert results["num_shots"] == 5

    for i in range(3):
        assert f"qiskit_method_{i}" in results
        assert f"qiskit_depth_{i}" in results
        assert f"qiskit_ancilla_{i}" in results


def test_evaluate_with_complex_circuit():
    """Test evaluation with a circuit that has ancillas."""
    N = 3

    # Create a circuit with ancillas
    circuit = QuantumCircuit(N + 3)
    circuit.mcx(list(range(N)), N)

    results = evaluate(
        circuit=circuit,
        N=N,
        num_shots=10,
        model="complex_model",
        thinking_level="High"
    )

    assert results["model"] == "complex_model"
    assert results["thinking_level"] == "High"
    assert results["N"] == N
    assert results["num_shots"] == 10
    # Ancilla count = (N+3) - (N+1) = 2
    assert results["llm_ancilla"] == 2


def test_evaluate_different_thinking_levels():
    """Test evaluation with various thinking levels."""
    N = 3

    # Create a proper QuantumCircuit
    circuit = QuantumCircuit(N + 1)
    circuit.mcx(list(range(N)), N)

    thinking_levels = ["High", "medium", "low", "m/a"]

    for level in thinking_levels:
        results = evaluate(
            circuit=circuit,
            N=N,
            num_shots=1,
            model="test_model",
            thinking_level=level
        )

        assert results["thinking_level"] == level


def test_csv_integration():
    """Test that CSV integration works end-to-end."""
    test_csv = "test_integration.csv"

    if os.path.exists(test_csv):
        os.remove(test_csv)

    # Create circuits
    circuit1 = QuantumCircuit(3)
    circuit1.mcx([0, 1], 2)
    circuit2 = QuantumCircuit(4)
    circuit2.mcx([0, 1, 2], 3)

    results1 = evaluate(
        circuit=circuit1,
        N=2,
        num_shots=3,
        model="model1",
        thinking_level="medium"
    )

    results2 = evaluate(
        circuit=circuit2,
        N=3,
        num_shots=4,
        model="model2",
        thinking_level="low"
    )

    assert os.path.exists(test_csv)

    import pandas as pd

    df = pd.read_csv(test_csv)
    assert len(df) == 2
    assert df.iloc[0]["model"] == "model1"
    assert df.iloc[0]["num_shots"] == 3
    assert df.iloc[0]["N"] == 2
    assert df.iloc[1]["model"] == "model2"
    assert df.iloc[1]["num_shots"] == 4
    assert df.iloc[1]["N"] == 3

    os.remove(test_csv)
