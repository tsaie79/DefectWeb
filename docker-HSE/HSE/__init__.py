"""
Root package for Flamyngo.
"""

__author__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__version__ = "1.2.1"

# add FLAMYNGO to path
import os
import sys
os.environ["FLAMYNGO"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
