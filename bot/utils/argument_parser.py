"""
Argument parsing utilities for command line options.
"""

import argparse
import logging
from typing import Optional


class ArgumentParser:
    """Handle command line argument parsing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with available options."""
        parser = argparse.ArgumentParser(
            description="Discord Governance Bot for Hemi Network",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            '--network',
            choices=['hemi', 'ethereum'],
            default='hemi',
            help='Network to connect to (default: hemi)'
        )
        
        parser.add_argument(
            '--read-only',
            action='store_true',
            help='Run in read-only mode (no voting or modifications)'
        )
        
        parser.add_argument(
            '--solo-mode',
            action='store_true',
            help='Run in solo mode (no automatic voting)'
        )
        
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Set logging level (default: INFO)'
        )
        
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run in test mode'
        )
        
        return parser
    
    def parse_args(self, args=None) -> argparse.Namespace:
        """Parse command line arguments."""
        try:
            return self.parser.parse_args(args)
        except SystemExit as e:
            # Handle argument parsing errors gracefully
            self.logger.error(f"Argument parsing failed: {e}")
            raise
    
    def get_network_from_args(self, args: argparse.Namespace) -> str:
        """Get network name from parsed arguments."""
        return getattr(args, 'network', 'hemi')
    
    def get_log_level_from_args(self, args: argparse.Namespace) -> str:
        """Get log level from parsed arguments."""
        return getattr(args, 'log_level', 'INFO')
    
    def is_read_only_mode(self, args: argparse.Namespace) -> bool:
        """Check if read-only mode is enabled."""
        return getattr(args, 'read_only', False)
    
    def is_solo_mode(self, args: argparse.Namespace) -> bool:
        """Check if solo mode is enabled."""
        return getattr(args, 'solo_mode', False)
    
    def is_test_mode(self, args: argparse.Namespace) -> bool:
        """Check if test mode is enabled."""
        return getattr(args, 'test', False)
    
    def get_config_file(self, args: argparse.Namespace) -> Optional[str]:
        """Get configuration file path from arguments."""
        return getattr(args, 'config', None)