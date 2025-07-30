# ABOUTME: Unit tests for Network error handling and edge cases
# ABOUTME: Tests boundary conditions and error scenarios

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


class TestNetworkEdgeCases:
    """Test Network class error handling and edge cases."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Return path to fixtures directory."""
        return os.path.join(os.path.dirname(__file__), 'fixtures')
    
    @pytest.fixture
    def sample_network(self, fixtures_dir):
        """Create a sample network for testing."""
        sample_file = os.path.join(fixtures_dir, 'sample_kida.dat')
        with patch('builtins.print'):
            return Network(sample_file)
    
    def test_missing_species_lookup(self, sample_network):
        """Test error handling for non-existent species lookup."""
        with pytest.raises(KeyError):
            sample_network.get_species_index('NONEXISTENT_SPECIES')
    
    def test_missing_species_object_lookup(self, sample_network):
        """Test error handling for non-existent species object lookup."""
        with pytest.raises(KeyError):
            sample_network.get_species_object('NONEXISTENT_SPECIES')
    
    def test_missing_reaction_lookup(self, sample_network):
        """Test error handling for non-existent reaction lookup."""
        with patch('sys.exit') as mock_exit:
            sample_network.get_reaction_by_verbatim('NONEXISTENT -> REACTION')
            mock_exit.assert_called_once_with(1)
    
    def test_missing_species_latex_lookup(self, sample_network):
        """Test error handling for non-existent species LaTeX lookup."""
        with patch('sys.exit') as mock_exit:
            sample_network.get_latex('NONEXISTENT_SPECIES')
            mock_exit.assert_called_once_with(1)
    
    def test_missing_reaction_by_serialized(self, sample_network):
        """Test error handling for non-existent serialized reaction lookup."""
        with patch('sys.exit') as mock_exit:
            sample_network.get_reaction_by_serialized('NONEXISTENT_SERIALIZED')
            mock_exit.assert_called_once_with(1)
    
    def test_missing_species_by_serialized(self, sample_network):
        """Test error handling for non-existent serialized species lookup."""
        with patch('sys.exit') as mock_exit:
            sample_network.get_species_by_serialized('NONEXISTENT_SERIALIZED')
            mock_exit.assert_called_once_with(1)
    
    def test_empty_reaction_list(self):
        """Test behavior with empty reaction lists."""
        # Create an empty network file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Empty network file\n")
            f.write("# No reactions\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Check basic properties with empty network
            assert len(network.reactions) == 0
            assert len(network.reactions_dict) == 0
            assert network.rlist is not None
            assert network.plist is not None
            assert network.rlist.shape[0] == 0  # No reactions
            assert network.get_number_of_species() >= 0  # May have default species
        finally:
            os.unlink(temp_file)
    
    def test_single_species_network(self):
        """Test network with reactions involving only one species type."""
        # Create network with only one species type
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Single species network\n")
            f.write("H + H -> H2 [10,1000] 1e-10\n")
            f.write("H2 -> H + H [10,1000] 1e-15\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should work normally
            assert len(network.reactions) == 2
            species_names = [s.name for s in network.species]
            assert 'H' in species_names
            assert 'H2' in species_names
            assert network.get_number_of_species() >= 2
        finally:
            os.unlink(temp_file)
    
    def test_very_long_species_names(self):
        """Test handling of very long species names."""
        # Use chemical-like long names instead of single letter repeated
        long_name = "C10H20O5N3S2P1"  # Long but valid chemical formula
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Network with very long species names\n")
            f.write(f"H + {long_name} -> H2 + {long_name} [10,1000] 1e-10\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle long names without crashing
            assert len(network.reactions) == 1
            species_names = [s.name for s in network.species]
            assert long_name in species_names
        finally:
            os.unlink(temp_file)
    
    def test_special_characters_in_species_names(self):
        """Test handling of special characters in species names."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Network with special characters\n")
            f.write("H+ + e- -> H [10,1000] 1e-12\n")
            f.write("C2H5OH + OH -> C2H4OH + H2O [10,1000] 1e-11\n")
            f.write("H3O+ + NH3 -> NH4+ + H2O [10,1000] 1e-9\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle special characters correctly
            assert len(network.reactions) == 3
            species_names = [s.name for s in network.species]
            assert 'H+' in species_names
            assert 'e-' in species_names
            assert 'C2H5OH' in species_names
            assert 'H3O+' in species_names
            assert 'NH4+' in species_names
        finally:
            os.unlink(temp_file)
    
    def test_invalid_mass_file_format(self):
        """Test handling of invalid mass file format."""
        # Create invalid mass file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Invalid mass file\n")
            f.write("H invalid_mass\n")  # Invalid mass value
            f.write("He\n")  # Missing mass value
            f.write("C 12.0107\n")  # Valid entry
            temp_mass_file = f.name
        
        try:
            # Should handle invalid entries gracefully
            with pytest.raises(ValueError):
                Network.load_mass_dict(temp_mass_file)
        finally:
            os.unlink(temp_mass_file)
    
    def test_missing_mass_file(self):
        """Test handling when mass file doesn't exist."""
        nonexistent_file = "/path/to/nonexistent/mass.dat"
        
        with pytest.raises(FileNotFoundError):
            Network.load_mass_dict(nonexistent_file)
    
    def test_large_number_of_reactions(self):
        """Test performance with moderately large reaction networks."""
        # Create a network with many reactions using valid chemical species
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Large network file\n")
            
            # Generate 50 reactions with simple chemistry
            for i in range(50):
                f.write(f"H + H -> H2 [10,1000] 1e-{10+i%5}\n")  # Allow duplicates for this test
            
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle large networks
            assert len(network.reactions) == 50
            assert len(network.species) >= 2  # At least H and H2
            assert network.rlist.shape[0] == 50  # 50 reactions
            assert network.plist.shape[0] == 50
        finally:
            os.unlink(temp_file)
    
    def test_circular_reaction_dependencies(self):
        """Test handling of circular reaction dependencies."""
        # Create reactions that form cycles using valid chemical species
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Circular reaction network\n")
            f.write("H -> H+ + e- [10,1000] 1e-10\n")
            f.write("H+ + e- -> H [10,1000] 1e-12\n")  # Forms a cycle
            f.write("H + H -> H2 [10,1000] 1e-15\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle circular dependencies without issues
            assert len(network.reactions) == 3
            species_names = [s.name for s in network.species]
            assert 'H' in species_names
            assert 'H+' in species_names
            assert 'e-' in species_names
        finally:
            os.unlink(temp_file)
    
    def test_extreme_rate_values(self):
        """Test handling of extreme rate coefficient values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Network with extreme rate values\n")
            f.write("H -> H+ + e- [10,1000] 1e-50\n")  # Very small rate
            f.write("He -> He+ + e- [10,1000] 1e50\n")   # Very large rate
            f.write("H2 -> H + H [10,1000] 0.0\n")    # Zero rate
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle extreme values
            assert len(network.reactions) == 3
            
            # Check that rates were parsed
            for reaction in network.reactions:
                assert reaction.rate is not None
        finally:
            os.unlink(temp_file)
    
    def test_extreme_temperature_limits(self):
        """Test handling of extreme temperature limits."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Network with extreme temperature limits\n")
            f.write("H -> H+ + e- [0.001,1e10] 1e-10\n")  # Very wide range
            f.write("He -> He+ + e- [1000,1000] 1e-10\n")   # Same tmin/tmax
            f.write("H2 -> H + H [-1,5000] 1e-10\n")     # Negative tmin
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle extreme temperature limits
            assert len(network.reactions) == 3
            
            # Check temperature limits were stored
            for reaction in network.reactions:
                assert hasattr(reaction, 'tmin')
                assert hasattr(reaction, 'tmax')
        finally:
            os.unlink(temp_file)
    
    def test_malformed_rate_expressions(self):
        """Test handling of malformed rate expressions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Network with malformed rates\n")  
            f.write("H -> H+ + e- [10,1000] invalid_function_name()\n")  # Invalid function
            f.write("He -> He+ + e- [10,1000] 1e-10 * unknown_variable\n")  # Unknown variable
            f.write("H2 -> H + H [10,1000] 1e-10\n")  # Valid reaction
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should skip malformed lines and continue
            # At least the valid reaction should be loaded
            assert len(network.reactions) >= 1
        finally:
            os.unlink(temp_file)
    
    def test_unicode_characters_in_file(self):
        """Test handling of unicode characters in network files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False, encoding='utf-8') as f:
            f.write("# Network with unicode characters\n")
            f.write("# Reaction with Greek letters: α + β → γ\n")
            f.write("H + H -> H2 [10,1000] 1e-10\n")  # Valid ASCII reaction
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle unicode in comments and process valid reactions
            assert len(network.reactions) >= 1
        finally:
            os.unlink(temp_file)
    
    def test_network_with_only_comments(self):
        """Test network file containing only comments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# This file contains only comments\n")
            f.write("# No actual reactions\n")
            f.write("! KIDA style comment\n")
            f.write("# Another comment\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should create network with no reactions
            assert len(network.reactions) == 0
            assert isinstance(network.species, list)
            assert isinstance(network.reactions_dict, dict)
        finally:
            os.unlink(temp_file)
    
    def test_invalid_reaction_stoichiometry(self):
        """Test handling of reactions with unusual stoichiometry."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Network with unusual stoichiometry\n")
            f.write("H + H + H + H + H -> H2 + H + H + H [10,1000] 1e-20\n")  # 5 reactants, 4 products
            f.write("H2 -> H + H + H + He + Ne [10,1000] 1e-10\n")  # 1 reactant, 5 products
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle high stoichiometry
            assert len(network.reactions) == 2
            
            # Check stoichiometry in matrices
            if len(network.reactions) > 0:
                assert network.rlist.shape[0] == 2
                assert network.plist.shape[0] == 2
        finally:
            os.unlink(temp_file)
    
    def test_photochemistry_without_photon_species(self):
        """Test photochemistry reactions without explicit PHOTON reactant."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Photochemistry without PHOTON\n")
            f.write("H2 -> H + H [10,1000] photo(h2_xsec, 13.6)\n")
            temp_file = f.name
        
        try:
            with patch('builtins.print'):
                network = Network(temp_file)
            
            # Should handle photo reactions
            assert len(network.reactions) >= 1
            
            # Check that rate expression contains photorates function
            photo_reactions = [r for r in network.reactions if 'photorates' in str(r.rate)]
            assert len(photo_reactions) >= 1
        finally:
            os.unlink(temp_file)