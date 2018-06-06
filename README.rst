===========
Moved to https://gitlab.com/mkourim/test_master
===========

Meant for use by CFME QE.

**ostriz2csv.py**

Generates a CSV file with error counts and details out of the Artifactor report.html

**junit2tracebacks.py**

Generates a file with all tracebacks and a directory with one traceback per file out of the junit-report.xml
All tracebacks in single file are useful for quick search of all instances of particular error, whereas one traceback per file is useful for greping, sorting and listing errors for particular test cases.

Usage
=====

::

    ./ostriz2csv.py -i /path/to/report.html -o /path/to/report.csv

or

::

    ./ostriz2csv.py -i {artifactor_report_url} -o /path/to/report.csv \
    --user {kerberos_user} --password {kerberos_password}

::

    ./junit2tracebacks.py -i /path/to/junit-report.xml -f /path/to/all_tracebacks_output.txt \
    -d /path/to/dir_for_one_traceback_per_file

or

::

    ./junit2tracebacks.py -i {junit_report_url} -f /path/to/all_tracebacks_output.txt \
    -d /path/to/dir_for_one_traceback_per_file --user {kerberos_user} --password {kerberos_password}

Examples
========

::

    $ cd /path/to/dir_for_one_traceback_per_file
    # test cases names with NoSuchElementException
    $ grep -E -l 'E *NoSuchElementException:' *
    # NoSuchElementExceptions sort by their frequency
    $ grep -E -h 'E *NoSuchElementException:' * | uniq -c | sort -n -r

Install
=======
You can use the script directly from the cloned repository.

To install the packages required by the script to your virtualenv, run

.. code-block::

    pip install -r requirements.txt

For info about the Test Master role, see <https://mojo.redhat.com/docs/DOC-1134762>
