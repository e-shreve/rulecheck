'''
Created on Nov 27, 2020

@author: Erik
'''
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
            