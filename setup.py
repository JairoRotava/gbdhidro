from setuptools import setup
from setuptools import find_packages
#from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import

setup(name='gbdhidro',
      version='0.0.1',
      description='GBDHidro Package',
      url='#',
      author='jairo',
      author_email='jairo.rotava@gmail.com',
      license='MIT',
      packages=['gbdhidro', 'gbdhidro.test'],
      install_requires=['netCDF4'],
      zip_safe=False)
