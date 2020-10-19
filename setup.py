from setuptools import setup
from setuptools import find_packages
#from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import gbdhidro

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

#long_description = read('README.txt', 'CHANGES.txt')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
      name='gbdhidro',
      version='gbdhidro.__version__',
      url='#',
      description='GBDHidro Package',
      license='MIT',
      author='jairo',
      author_email='jairo.rotava@gmail.com',
      install_requires=['netCDF4', 'pandas', 'numpy', 'python-dateutil', 'cfchecker', 'cfunits', 'pymongo', 'iso8601'],
      tests_requires=['pytest'],
      cmdclass={'test': PyTest},
      long_description='descricao longa',
      include_package_data=True,
      platforms='ahy',
      extras_require={
            'testing': ['pytest'],
      },
      packages=['gbdhidro', 'gbdhidro.hobo', 'gbdhidro.netcdf', 'gbdhidro.database'],
      entry_points={
          'console_scripts': [
              'gbd-get=gbdhidro.database.get:command_line',
              'gbd-insert-netcdf=gbdhidro.database.insert_netcdf:command_line',
              'gbd-hobo2netcdf=gbdhidro.netcdf.station_raw_to_netcdf.hobo_ua_003_64.hobo_ua_003_64_to_netcdf:command_line',
              'gbd-find=gbdhidro.database.find:command_line',
          ]
      },
      zip_safe=False)
