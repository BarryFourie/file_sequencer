==============
File Sequencer
==============

A tool to sequence and rename files based on their revision history.

Overview
========

`File Sequencer` is a Python tool designed to process and rename files. It extracts revision data from Python files, builds an ordered chain of revisions, and renames the files in sequence.

Features
========

- Extracts `revision_id` and `revises_id` from Python files.
- Processes all Python files in a specified directory.
- Builds an ordered chain of files based on their revision history.
- Renames files in sequence to reflect their order in the revision chain.
- Handles errors and provides logging for debugging purposes.

Installation
============

To install `file_sequencer`, simply use pip:

.. code-block:: sh

    pip install file_sequencer

To install the latest version from TestPyPI, use:

.. code-block:: sh

    pip install -i https://test.pypi.org/simple/ file-sequencer

Usage
=====

To use `file_sequencer`, run the following command:

.. code-block:: sh

    file_sequencer <directory>

If no directory is provided, it defaults to `revision_files`.

Example
=======

.. code-block:: sh

    file_sequencer path/to/directory

This will process all Python files in `path/to/directory`, build the revision chain, and rename the files in sequence.

