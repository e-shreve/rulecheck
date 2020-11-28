"""
    verbose Module

    Contains the Verbose "static" class which provides printing to the console only if global
    verbose mode has been enabled.
"""
from builtins import staticmethod


class Verbose:
    """Helper class with static methods for verbose printing."""

    _verbose = False

    @staticmethod
    def set_verbose(verbose:bool):
        """Enable/disable verbosity."""
        Verbose._verbose = verbose

    @staticmethod
    def print(message:str):
        "Prints message if verbosity is true."
        if Verbose._verbose:
            print(message)
            