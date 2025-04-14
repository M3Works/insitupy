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
I want to read in a file that looks like this:

::

    # Location,East River
    # Date/Local Standard Time,2020-04-27T08:45
    # Latitude,38.92524
    # Longitude,-106.97112
    # Flags,random flag
    # Top (cm),Bottom (cm),Density (kg/m3)
    95.0,85.0,401.0
    85.0,75.0,449.0
    75.0,65.0,472.0

The metadata and data parsers are configured with a lot of defaults
for working with SnowEx data, so the simple approach is

.. code-block:: python

    from insitupy.campaigns.snowex import SnowExProfileData
    my_data = SnowExProfileDataCollection.from_csv(
        "./fake_data.csv", allow_map_failure=True
    )
    print(my_data.profiles[0].df)
    print(my_data.profiles[0].metadata)

If you want to try your hand at defining variables yourself, you can do
as follows:

I can define a `metadata` file that looks like this:

::

    LATITUDE:
      auto_remap: true
      code: latitude
      description: Latitude
      map_from:
      - lat
      - latitude
      match_on_code: true
    LONGITUDE:
      auto_remap: true
      code: longitude
      description: Longitude
      map_from:
      - long
      - lon
      - longitude
    DATETIME:
      auto_remap: true
      code: datetime
      description: Combined date and time
      map_from:
      - Date/Local Standard Time
      - date/local_standard_time
      - datetime
      - "date&time"
      - date/time
      - date/local_time
      match_on_code: true
    SITE_NAME:
      auto_remap: true
      code: site_name
      description: Name of campaign site
      map_from:
          - location
      match_on_code: true

and a primary variable file like:

::

    BOTTOM_DEPTH:
      auto_remap: true
      code: bottom_depth
      description: Lower edge of measurement
      map_from:
      - bottom
      - bottom_depth
      match_on_code: true
    DENSITY:
      auto_remap: true
      code: density
      description: measured snow density
      map_from:
      - density
      - density_mean
      match_on_code: true
    DEPTH:
      auto_remap: true
      code: depth
      description: top or center depth of measurement
      map_from:
      - depth
      - top
      match_on_code: true
    LAYER_THICKNESS:
      auto_remap: true
      code: layer_thickness
      description: thickness of layer
      map_from: null
      match_on_code: true


.. important::

    LAYER_THICKNESS, DEPTH, and BOTTOM_DEPTH are required variables
    for reading in **profile** data

Then read in the file like this:

.. code-block:: python

    from insitupy.campaigns.snowex import SnowExProfileData
    my_data = SnowExProfileDataCollection.from_csv(
        "./fake_data.csv", allow_map_failure=True,
        # Use the files YOU defined here
        primary_variable_files=["../primaryvariables.yaml"],
        metadata_variable_files=["../metadatavariables.yaml"],
    )
    print(my_data.profiles[0].df)
    print(my_data.profiles[0].metadata)


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
