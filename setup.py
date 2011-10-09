from setuptools import setup, find_packages
import sys, os

version = '63'

try:
    import PySide
    requireds = []
except ImportError:
    requireds = ['PySide']

setup(name='python-yamusic',
      version=version,
      description="Library for acessing yandex music from python",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='yandex music js',
      author='Vladimir Yakovlev',
      author_email='nvbn.rm@gmail.com',
      url='http://github.com/nvbn/python-yamusic',
      license='LGPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=requireds,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
