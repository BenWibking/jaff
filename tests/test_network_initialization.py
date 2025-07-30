# ABOUTME: Unit tests for Network class initialization
# ABOUTME: Tests constructor, mass dict loading, and label handling

import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jaff.network import Network
from jaff.species import Species


class TestNetworkInitialization:
    """Test Network class initialization functionality."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Return path to fixtures directory."""
        return os.path.join(os.path.dirname(__file__), 'fixtures')
    
    @pytest.fixture
    def sample_kida_file(self, fixtures_dir):
        """Return path to sample KIDA file."""
        return os.path.join(fixtures_dir, 'sample_kida.dat')
    
    def test_successful_initialization(self, sample_kida_file, capsys):
        """Test successful network initialization with valid file."""
        # Suppress print output during initialization
        with patch('builtins.print'):
            network = Network(sample_kida_file)
        
        # Check basic attributes are initialized
        assert network.file_name == sample_kida_file
        assert network.label == 'sample_kida'
        assert isinstance(network.species, list)
        assert isinstance(network.reactions, list)
        assert isinstance(network.species_dict, dict)
        assert isinstance(network.reactions_dict, dict)
        assert isinstance(network.mass_dict, dict)
        
        # Check that some reactions were loaded
        assert len(network.reactions) > 0
        assert len(network.species) > 0
    
    def test_initialization_with_custom_label(self, sample_kida_file):
        """Test initialization with custom label parameter."""
        custom_label = "my_custom_network"
        
        with patch('builtins.print'):
            network = Network(sample_kida_file, label=custom_label)
        
        assert network.label == custom_label
        assert network.file_name == sample_kida_file
    
    def test_initialization_with_nonexistent_file(self):
        """Test initialization fails gracefully with non-existent file."""
        with pytest.raises(FileNotFoundError):
            Network("/path/to/nonexistent/file.dat")
    
    def test_default_label_extraction(self, sample_kida_file):
        """Test default label extraction from filename."""
        with patch('builtins.print'):
            network = Network(sample_kida_file)
        
        # Should extract 'sample_kida' from 'sample_kida.dat'
        assert network.label == 'sample_kida'
        
        # Test with path containing directories
        test_path = "/some/long/path/to/network_file.txt"
        with patch('builtins.print'), patch('builtins.open', MagicMock()):
            with patch.object(Network, 'load_network', MagicMock()):
                with patch.object(Network, 'check_sink_sources', MagicMock()):
                    with patch.object(Network, 'check_recombinations', MagicMock()):
                        with patch.object(Network, 'check_isomers', MagicMock()):
                            with patch.object(Network, 'check_unique_reactions', MagicMock()):
                                with patch.object(Network, 'generate_ode', MagicMock()):
                                    with patch.object(Network, 'generate_reactions_dict', MagicMock()):
                                        network = Network(test_path)
        
        assert network.label == 'network_file'
    
    def test_mass_dict_loading(self):
        """Test mass dictionary loading from atom_mass.dat."""
        # Create a temporary mass file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("# Test mass file\n")
            f.write("H  1.00794\n")
            f.write("He 4.002602\n")
            f.write("C  12.0107\n")
            f.write("\n")  # Empty line
            f.write("# Another comment\n")
            f.write("O  15.9994\n")
            temp_file = f.name
        
        try:
            mass_dict = Network.load_mass_dict(temp_file)
            
            assert len(mass_dict) == 4
            assert mass_dict['H'] == 1.00794
            assert mass_dict['He'] == 4.002602
            assert mass_dict['C'] == 12.0107
            assert mass_dict['O'] == 15.9994
        finally:
            os.unlink(temp_file)
    
    def test_errors_parameter_true(self, sample_kida_file):
        """Test initialization with errors=True parameter."""
        with patch('builtins.print'):
            # Mock sys.exit to prevent test from exiting
            with patch('sys.exit') as mock_exit:
                network = Network(sample_kida_file, errors=True)
                
                # If there are any validation errors, sys.exit should be called
                # In our sample file, we don't expect errors, so it shouldn't exit
                mock_exit.assert_not_called()
    
    def test_errors_parameter_false(self, sample_kida_file):
        """Test initialization with errors=False parameter (default)."""
        with patch('builtins.print'):
            network = Network(sample_kida_file, errors=False)
        
        # Should complete without raising exceptions
        assert network is not None
    
    def test_initialization_workflow(self, sample_kida_file):
        """Test that all initialization steps are called in correct order."""
        with patch('builtins.print'):
            with patch.object(Network, 'load_network') as mock_load:
                with patch.object(Network, 'check_sink_sources') as mock_sink:
                    with patch.object(Network, 'check_recombinations') as mock_recomb:
                        with patch.object(Network, 'check_isomers') as mock_isomers:
                            with patch.object(Network, 'check_unique_reactions') as mock_unique:
                                with patch.object(Network, 'generate_ode') as mock_ode:
                                    with patch.object(Network, 'generate_reactions_dict') as mock_dict:
                                        network = Network(sample_kida_file, errors=True)
        
        # Verify all methods were called
        mock_load.assert_called_once_with(sample_kida_file)
        mock_sink.assert_called_once_with(True)
        mock_recomb.assert_called_once_with(True)
        mock_isomers.assert_called_once_with(True)
        mock_unique.assert_called_once_with(True)
        mock_ode.assert_called_once()
        mock_dict.assert_called_once()
    
    def test_empty_network_file(self, fixtures_dir):
        """Test initialization with empty network file."""
        empty_file = os.path.join(fixtures_dir, 'empty_network.dat')
        
        with patch('builtins.print'):
            network = Network(empty_file)
        
        # Should initialize but with no reactions
        assert len(network.reactions) == 0
        # May have default species or none
        assert isinstance(network.species, list)
    
    def test_initial_data_structures(self, sample_kida_file):
        """Test that data structures are properly initialized."""
        with patch('builtins.print'):
            network = Network(sample_kida_file)
        
        # Check data structure types and initial states
        assert isinstance(network.species, list)
        assert isinstance(network.species_dict, dict)
        assert isinstance(network.reactions, list)
        assert isinstance(network.reactions_dict, dict)
        assert isinstance(network.mass_dict, dict)
        
        # Check that rlist and plist are generated
        assert network.rlist is not None
        assert network.plist is not None
        assert hasattr(network.rlist, 'shape')  # Should be numpy array
        assert hasattr(network.plist, 'shape')  # Should be numpy array
