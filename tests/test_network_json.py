# ABOUTME: Unit tests for Network JSON serialization
# ABOUTME: Ensures Network.to_jaff_file/from_jaff_file round-trip preserves reactions

import os
import sys
import tempfile
from unittest.mock import patch

import pytest
import sympy

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jaff.network import Network


def test_network_json_roundtrip_sample_kida_valid():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    path = os.path.join(fixtures_dir, "sample_kida_valid.dat")

    with patch("builtins.print"):
        net = Network(path)

    with pytest.raises(ValueError):
        net.to_jaff_file("not_a_network.json")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jaff", delete=False) as f:
        json_path = f.name

    try:
        net.to_jaff_file(json_path)
        net2 = Network.from_jaff_file(json_path)

        assert net2.label == net.label
        assert len(net2.species) == len(net.species)
        assert len(net2.reactions) == len(net.reactions)

        for r1, r2 in zip(net.reactions, net2.reactions):
            assert r2.get_verbatim() == r1.get_verbatim()
            assert r2.tmin == r1.tmin
            assert r2.tmax == r1.tmax

            if isinstance(r1.rate, str):
                assert r2.rate == r1.rate
            else:
                assert isinstance(r2.rate, sympy.Basic)
                assert r2.rate == r1.rate

            assert r2.dE == r1.dE
    finally:
        os.unlink(json_path)
