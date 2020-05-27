from setuptools import setup
from setuptools import find_packages

pkg_location = 'src'
pkg_name     = 'mplfinance'

setup(name='gbdhidro',
    version='0.1',
    description='Testing installation of Package',
    url='#',
    author='jairo',
    author_email='jairo.rotava@gmail.com',
    license='MIT',
    package_dir={'': pkg_location},
    packages=find_packages(where=pkg_location),
    zip_safe=False)
