========
insitupy
========


.. image:: https://img.shields.io/pypi/v/insitupy.svg
        :target: https://pypi.python.org/pypi/insitupy

.. image:: https://img.shields.io/travis/m3works/insitupy.svg
        :target: https://travis-ci.com/m3works/insitupy

.. image:: https://readthedocs.org/projects/insitupy/badge/?version=latest
        :target: https://insitupy.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status



Manage reading and analyzing raw files of insitu data. The goal is to get
raw insitu data files into manageable classes with helpful functions and provide
access to the data as GeoPandas Arrays.

The first application of this will be for SnowEx pit data.

THIS IS A WORK IN PROGRESS (use at your own risk as outlined in the MIT license). We
fully welcome any contribution and ideas. Snow science works better together!


* Free software: MIT license
* Documentation: https://loomsitu.readthedocs.io.


Features
--------

* Parsing of raw insitu data files with a variable number of header lines
* Reading csv data files into a pandas DataFrame, and parsing metadata into usable format
* Flexible user-defined variables
* Reading both pit and point data
* Parsing of date and location data


Example
-------
See the file....
# TODO


Variables
---------

Types of variables
~~~~~~~~~~~~~~~~~~
There are two types of variable definitions:

1. `primary variables` - These are the data that expect to be found in the data columns
2. `metadata variables` - These are the data that are expected to be found in the header lines

Variables definitions
~~~~~~~~~~~~~~~~~~~~~
The variables are defined the same way, in separate yaml files. A standard
definition looks like this

.. code-block:: yaml

    TOTAL_DEPTH:
      code: total_depth
      description: Total depth of measurement
      map_from:
      - total_snow_depth
      - hs
      match_on_code: true
      auto_remap: true

* code: The string that will be used to reference this variable
* description: A description of the variable
* map_from: A list of strings that will be used to match the variable in the data
* match_on_code: If true, the variable will be matched if the `code` values is found
    in the data, not just the `map_from` values
* auto_remap: If true, the variable will be remapped to the `code` value

Overriding variables
~~~~~~~~~~~~~~~~~~~~
We can provide a list of variable files that will override as you go down the list.
For instance, if we created our variables like this

.. code-block:: python

    from insitupy.variables import ExtendableVariables
    variable_paths = ['variables/primary_variables1.yaml', 'variables/primary_variables2.yaml']
    my_vars = ExtendableVariables(variable_paths)

Any variable with the same key in `primary_variables2.yaml` will override
the same variable in `primary_variables1.yaml`

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
