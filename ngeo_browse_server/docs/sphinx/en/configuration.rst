.. _Configuration:

Configuration
=============

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

The ngEO Browse Server is configured via a number several configuration files,
as required by the various software packages used. The `eoxserver.conf`
configuration file is required by the EOxServer software package and is
documented in detail in the documentation of the package. It has to reside
within the `conf` directory of the instance. Similarily, the other major
software dependency `Django <https://www.djangoproject.com/>`_ is configured
using the two configuration files `settings.py` and `urls.py` which are
exhaustively explained on the projects documentation.

All ngEO Browse Server specific settings are stored within the `ngeo.conf`
configuration file which has also to be located within the `conf` directory of
the instance. It is divided into sections which currently support the following
configuration options:


control.ingest
--------------

In this section, browse file ingestion specific settings are stored.

optimized_files_dir
~~~~~~~~~~~~~~~~~~~

This setting configures where generated optimized files shall be stored when
they are ingested. (Required)

optimized_files_postfix
~~~~~~~~~~~~~~~~~~~~~~~

This option defines a specific postfix which is used to generate a filename
within the directory for optimized files. The postfix is used to distinguish
processed and raw raster files.
