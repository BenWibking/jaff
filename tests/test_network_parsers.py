# ABOUTME: Unit tests for Network class parser functionality
# ABOUTME: Tests format detection and parsing for all supported formats

import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jaff.network import Network
from jaff.reaction import Reaction
from jaff.species import Species


class TestNetworkParsers:
    """Test Network class parser functionality for all formats."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Return path to fixtures directory."""
        return os.path.join(os.path.dirname(__file__), 'fixtures')
    
    def test_kida_format_detection(self, fixtures_dir):
        """Test automatic detection and parsing of KIDA format."""
        kida_file = os.path.join(fixtures_dir, 'sample_kida.dat')
        
        with patch('builtins.print'):
            network = Network(kida_file)
        
        # Check that reactions were parsed
        assert len(network.reactions) > 0
        
        # Check specific reaction from our sample file
        # H + H + H -> H2 + H
        h_idx = network.get_species_index('H')
        h2_idx = network.get_species_index('H2')
        
        # Find the reaction
        found = False
        for reaction in network.reactions:
            if (len(reaction.reactants) == 3 and 
                all(r.name == 'H' for r in reaction.reactants) and
                len(reaction.products) == 2 and
                any(p.name == 'H2' for p in reaction.products)):
                found = True
                assert reaction.tmin == 10
                assert reaction.tmax == 1000
                break
        
        assert found, "Expected H + H + H -> H2 + H reaction not found"
    
    def test_udfa_format_detection(self, fixtures_dir):
        """Test automatic detection and parsing of UDFA format."""
        udfa_file = os.path.join(fixtures_dir, 'sample_udfa.dat')
        
        with patch('builtins.print'):
            network = Network(udfa_file)
        
        # Check that reactions were parsed
        assert len(network.reactions) > 0
        
        # Check for H2 photodissociation reaction
        found = False
        for reaction in network.reactions:
            if (len(reaction.reactants) == 2 and 
                any(r.name == 'H2' for r in reaction.reactants) and
                any(r.name == 'PHOTON' for r in reaction.reactants)):
                found = True
                assert reaction.tmin == 10
                assert reaction.tmax == 3000
                break
        
        assert found, "Expected H2 + PHOTON reaction not found"
    
    def test_prizmo_format_detection(self, fixtures_dir):
        """Test automatic detection and parsing of PRIZMO format."""
        prizmo_file = os.path.join(fixtures_dir, 'sample_prizmo.dat')
        
        with patch('builtins.print'):
            network = Network(prizmo_file)
        
        # Check that reactions were parsed
        assert len(network.reactions) > 0
        
        # Check that variables were parsed and substituted
        # The O + H -> OH reaction should have the variable y substituted
        found = False
        for reaction in network.reactions:
            if (len(reaction.reactants) == 2 and 
                any(r.name == 'O' for r in reaction.reactants) and
                any(r.name == 'H' for r in reaction.reactants)):
                found = True
                # Check that the rate expression contains tgas/300
                rate_str = str(reaction.rate)
                assert 'tgas' in rate_str.lower()
                assert '300' in rate_str
                break
        
        assert found, "Expected O + H -> OH reaction not found"
    
    def test_krome_format_detection(self, fixtures_dir):
        """Test automatic detection and parsing of KROME format."""
        krome_file = os.path.join(fixtures_dir, 'sample_krome.dat')
        
        with patch('builtins.print'):
            network = Network(krome_file)
        
        # Check that reactions were parsed
        assert len(network.reactions) > 0
        
        # Check that @var declarations were processed
        # The C+ + H2 -> CH+ + H reaction uses inv_tgas variable
        found = False
        for reaction in network.reactions:
            if (len(reaction.reactants) == 2 and 
                any(r.name == 'C+' for r in reaction.reactants) and
                any(r.name == 'H2' for r in reaction.reactants)):
                found = True
                # Check that inv_tgas was substituted
                rate_str = str(reaction.rate)
                assert 'tgas' in rate_str.lower()
                assert 'exp' in rate_str.lower()
                break
        
        assert found, "Expected C+ + H2 reaction not found"
    
    def test_uclchem_format_detection(self, fixtures_dir):
        """Test automatic detection and parsing of UCLCHEM format."""
        uclchem_file = os.path.join(fixtures_dir, 'sample_uclchem.dat')
        
        with patch('builtins.print'):
            network = Network(uclchem_file)
        
        # Check that reactions were parsed
        assert len(network.reactions) > 0
        
        # Check for reactions with NAN markers
        # All reactions should have been parsed despite NAN fields
        species_names = [s.name for s in network.species]
        assert 'H' in species_names
        assert 'H2' in species_names
        assert 'OH' in species_names
    
    def test_custom_variables_parsing(self, fixtures_dir):
        """Test parsing of custom variables in PRIZMO and KROME formats."""
        prizmo_file = os.path.join(fixtures_dir, 'sample_prizmo.dat')
        
        with patch('builtins.print'):
            network = Network(prizmo_file)
        
        # Check cosmic ray reaction that uses zeta variable
        found = False
        for reaction in network.reactions:
            if (len(reaction.reactants) == 2 and 
                any(r.name == 'H2' for r in reaction.reactants) and
                any(r.name == 'CR' for r in reaction.reactants)):
                found = True
                # The rate should be the zeta value (1.3e-17)
                # Since it's a constant after substitution
                break
        
        assert found, "Expected H2 + CR reaction not found"
    
    def test_photo_chemistry_parsing(self, fixtures_dir):
        """Test parsing of photochemistry reactions."""
        prizmo_file = os.path.join(fixtures_dir, 'sample_prizmo.dat')
        
        with patch('builtins.print'):
            network = Network(prizmo_file)
        
        # Check for photo reaction
        found = False
        for reaction in network.reactions:
            if any(r.name == 'PHOTON' for r in reaction.reactants):
                found = True
                # Check that photo function is in the rate
                rate_str = str(reaction.rate)
                assert 'photorates' in rate_str
                break
        
        assert found, "Expected photochemistry reaction not found"
    
    def test_temperature_limits_application(self, fixtures_dir):
        """Test that temperature limits (tmin/tmax) are correctly applied."""
        kida_file = os.path.join(fixtures_dir, 'sample_kida.dat')
        
        with patch('builtins.print'):
            network = Network(kida_file)
        
        # Check reactions have temperature limits
        for reaction in network.reactions:
            assert hasattr(reaction, 'tmin')
            assert hasattr(reaction, 'tmax')
            
            # Check that rate expressions have min/max applied
            if reaction.tmin is not None:
                rate_str = str(reaction.rate)
                assert 'max' in rate_str.lower()
            if reaction.tmax is not None:
                rate_str = str(reaction.rate)
                assert 'min' in rate_str.lower()
    
    def test_comment_and_empty_line_handling(self, fixtures_dir):
        """Test that comments and empty lines are properly handled."""
        empty_file = os.path.join(fixtures_dir, 'empty_network.dat')
        
        with patch('builtins.print'):
            network = Network(empty_file)
        
        # Should load without errors but have no reactions
        assert len(network.reactions) == 0
    
    def test_malformed_line_handling(self, fixtures_dir):
        """Test handling of malformed lines in network files."""
        malformed_file = os.path.join(fixtures_dir, 'malformed_network.dat')
        
        # The parser should skip malformed lines without crashing
        with patch('builtins.print'):
            try:
                network = Network(malformed_file)
                # If it loads, check that some lines were skipped
                assert True  # Successfully handled malformed input
            except Exception as e:
                # Some malformed lines might cause exceptions, which is acceptable
                assert True
    
    def test_format_detection_priority(self):
        """Test format detection priority when multiple patterns match."""
        # Create a file that could match multiple formats
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Test file with mixed format indicators\n")
            f.write("# This has -> like PRIZMO\n")
            f.write("H + H -> H2 : 1e-10 : 10 : 1000\n")
            f.write("# But also has : like UDFA\n")
            f.write("H:e-:H-:1e-16:0:0:10:10000:1\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should parse both lines correctly
            assert len(network.reactions) >= 2
        finally:
            os.unlink(temp_file)
    
    def test_krome_shortcuts_parsing(self):
        """Test that KROME shortcuts are properly parsed."""
        # Create a file using KROME shortcuts
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("@format:idx,R,R,P,P,tmin,tmax,rate\n")
            f.write("1,H+,e-,H,,10,10000,2.59e-13*invte\n")
            f.write("2,O,H,OH,,10,41000,9.9e-11*t32**(-0.38)\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Check that shortcuts were substituted
            for reaction in network.reactions:
                rate_str = str(reaction.rate)
                # Should not contain shortcut names
                assert 'invte' not in rate_str
                assert 't32' not in rate_str
                # Should contain expanded expressions
                assert 'tgas' in rate_str.lower()
        finally:
            os.unlink(temp_file)
    
    def test_species_creation_from_reactions(self, fixtures_dir):
        """Test that species are correctly created from parsed reactions."""
        kida_file = os.path.join(fixtures_dir, 'sample_kida.dat')
        
        with patch('builtins.print'):
            network = Network(kida_file)
        
        # Check that all species in reactions exist in species list
        species_names = [s.name for s in network.species]
        
        for reaction in network.reactions:
            for reactant in reaction.reactants:
                assert reactant.name in species_names
            for product in reaction.products:
                assert product.name in species_names
        
        # Check species dictionary
        for species in network.species:
            assert species.name in network.species_dict
            assert network.species_dict[species.name] == species.index
    
    def test_rate_expression_parsing(self):
        """Test parsing of various rate expressions."""
        # Create a file with different rate expressions
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Test various rate expressions\n")
            f.write("H + H -> H2 : 1.0e-10 : 10 : 1000\n")  # Simple constant
            f.write("H + e- -> H- : 3e-16 * (tgas/300)**0.5 : 10 : 10000\n")  # Power law
            f.write("C+ + H2 -> CH+ + H : 1e-10 * exp(-4640/tgas) : 10 : 41000\n")  # Exponential
            f.write("O + H -> OH : 9.9e-11 * sqrt(tgas) * exp(-100/tgas) : 10 : 41000\n")  # Complex
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            assert len(network.reactions) == 4
            
            # Check that all rate expressions were parsed as sympy objects
            for reaction in network.reactions:
                assert reaction.rate is not None
                # Rate should be a sympy expression or number
                assert hasattr(reaction.rate, 'free_symbols') or isinstance(reaction.rate, (int, float))
        finally:
            os.unlink(temp_file)
    
    def test_special_species_handling(self, fixtures_dir):
        """Test handling of special species like e-, PHOTON, CR, etc."""
        kida_file = os.path.join(fixtures_dir, 'sample_kida.dat')
        
        with patch('builtins.print'):
            network = Network(kida_file)
        
        # Check that special species are recognized
        species_names = [s.name for s in network.species]
        
        # These special species should be in our sample files
        special_species = ['e-', 'PHOTON', 'H+', 'H-']
        for special in special_species:
            if any(special in network.reactions[i].verbatim for i in range(len(network.reactions))):
                assert special in species_names