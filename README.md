# # D118-Evaluwise-PS-Sync

Script to synchronize basic staff info from PowerSchool to Evaluwise.

## Overview

This script is a fairly simple one that grabs basic demographic information and exports it to a file which is uploaded to Evaluwise. It starts off by getting a list of school IDs and names from the schools table and puts them into a dictionary for reference later. Then it goes through all active staff members and gets their information, getting their IEIN or substituting their teacher number if they do not have one, and similarly for legal or general first and last names. The information is exported to a .csv file, which is then uploaded via SFTP to the Evaluwise server.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- EVALUWISE_SFTP_USERNAME
- EVALUWISE_SFTP_PASSWORD
- EVALUWISE_SFTP_ADDRESS

These are fairly self explanatory, and just relate to the usernames, passwords, and host IP/URLs for PowerSchool and the Evaluwise SFTP server. If you wish to directly edit the script and include these credentials or to use other environment variable names, you can.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

**As part of the pysftp connection to the output SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

You will need to change the table where the legal first and last name and IEIN number is stored if you are not in Illinois and don't use the `s_il_usr_x` table.
Additionally, you will need to have a table(s) and fields where the staff hire date and EEO5 classification information is stored. We use a custom table named `u_humanresources` and fields named `curhiredate` and `eeo5class` for this, but you will need to edit the SQL query to match your table/fields.

## Customization

Besides changing the custom tables and fields as described above that the data is coming from, this script is pretty simple and should "just work" assuming all the requirements are made.

- If you want to add any other optional fields to the output, you will need to add them to the header, change the SQL query to retrieve them, process them, and them add them to the output line in the same field order as the header row.
