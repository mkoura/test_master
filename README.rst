test_master
===========

Meant for use by CFME QE.

Generates CSV file with error counts and details out of the Artifactor report.html

Usage
-----

.. code-block::

    ./test_master.py -i /path/to/report.html -o /path/to/report.csv

or
.. code-block::

    ./test_master.py -i {artifactor_report_url} -o /path/to/report.csv --user {kerberos_user} --password {kerberos_password}

Install
-------
You can use the script directly from the cloned repository.

To install the packages required by the script to your virtualenv, run

.. code-block::

    pip install -r requirements.txt

For info about the Test Master role, see <https://mojo.redhat.com/docs/DOC-1134762>
