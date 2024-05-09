"""Script to send teacher infor to Evaluwise from PowerSchool.

https://github.com/Philip-Greyson/D118-Evaluwise-PS-Sync

Does a big query for all staff in PowerSchool, filters to just teachers, and exports the relevant fields to a csv file for upload.

See the following for PS table information:
https://ps.powerschool-docs.com/pssis-data-dictionary/latest/teachers-ver7-8-0
https://ps.powerschool-docs.com/pssis-data-dictionary/latest/userscorefields-ver7-7-1
"""

# importing module
import os  # needed for environement variable reading
from datetime import *

import oracledb  # needed for connection to PowerSchool server (ordcle database)
import pysftp  # needed for sftp file upload

# set up database connection info
DB_UN = os.environ.get('POWERSCHOOL_READ_USER')  # username for read-only database user
DB_PW = os.environ.get('POWERSCHOOL_DB_PASSWORD')  # the password for the database account
DB_CS = os.environ.get('POWERSCHOOL_PROD_DB')  # the IP address, port, and database name to connect to

# sftp connection info , stored as environment variables on system
SFTP_UN = os.environ.get('EVALUWISE_SFTP_USERNAME')
SFTP_PW = os.environ.get('EVALUWISE_SFTP_PASSWORD')
SFTP_HOST = os.environ.get('EVALUWISE_SFTP_ADDRESS')
CNOPTS = pysftp.CnOpts(knownhosts='known_hosts')  # connection options to use the known_hosts file for key validation

# SFTP_OUTPUT_DIRECTORY = ''
OUTPUT_FILENAME = 'teacherupload.csv'

print(f"Username: {DB_UN} | Password: {DB_PW} | Server: {DB_CS}")  # debug so we can see where oracle is trying to connect to/with
# print(f"SFTP Username: {SFTP_UN} | SFTP Password: {SFTP_PW} | SFTP Server: {SFTP_HOST}")  # debug so we can see where pysftp is trying to connect to/with
badnames = ['use', 'training1','trianing2','trianing3','trianing4','planning','admin','nurse','user', 'use ', 'test', 'testtt', 'human', 'teacher', 'do not', 'substitute', 'sub', 'plugin', 'lunch', 'mba', 'tech', 'technology', 'administrator']

if __name__ == '__main__':  # main file execution
    with open('Evaluwise_log.txt', 'w') as log:
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with open(OUTPUT_FILENAME, 'w', encoding="utf-8") as output:
            # print out header rows into files, column names with comma delimiters
            print('Teacher ID,First Name,Last Name,Email,Schools,Positions,Date of Hire,Date of Birth', file=output)
            try:
                with oracledb.connect(user=DB_UN, password=DB_PW, dsn=DB_CS) as con:  # create the connecton to the database
                    with con.cursor() as cur:  # start an entry cursor
                        print("Connection established - version: " + con.version)
                        print("Connection established - version: " + con.version, file=log)

                        schoolMappings = {}  # create empty dict to hold the school number to name mappings
                        cur.execute('SELECT school_number, name FROM schools')
                        schools = cur.fetchall()  # fetchall() is used to fetch all records from result set
                        for school in schools:
                            schoolMappings.update({school[0]: school[1]})  # add the school number : school name entry to the schoolMappings dict
                        print(f'DBUG: {schoolMappings}')  # debug
                        print(f'DBUG: {schoolMappings}', file=log)  # debug

                        # do the main SQL query for all staff members. Exclude staff who are not active in their homeschool, or staff who do not have emails
                        cur.execute('SELECT u.email_addr, u.dcid, u.first_name, u.last_name, u.teachernumber, core.dob, il.legal_first_name, il.legal_last_name, il.iein, u.homeschoolid, hr.curhiredate, hr.eeo5class, hr.staff_categorystatus FROM users u \
                            LEFT JOIN s_il_usr_x il ON u.dcid = il.usersdcid \
                            LEFT JOIN userscorefields core ON u.dcid = core.usersdcid \
                            LEFT JOIN u_humanresources hr ON u.dcid = hr.usersdcid \
                            LEFT JOIN schoolstaff s ON (u.dcid = s.users_dcid AND u.homeschoolid = s.schoolid) \
                            WHERE u.email_addr IS NOT NULL AND  s.status = 1')
                        staffMembers = cur.fetchall()  # fetchall() is used to fetch all records from result set
                        for staff in staffMembers:
                            try:
                                if not staff[2].lower() in badnames and not staff[3].lower() in badnames:  # filter out the accounts that have first or last names with words in our badnames list
                                    # print(staff)
                                    idNum = staff[8] if (staff[8] and staff[8] !='0')else staff[4]  # use the IEIN field if it exists and isnt just 0, otherwise use the teachernumber field
                                    firstName = staff[6] if staff[6] else staff[2]  # use the legal first name if it exists, otherwise the normal first name
                                    lastName = staff[7] if staff[7] else staff[3]  # use the legal last name if it exists, otherwise the normal last name
                                    birthdate = staff[5] if staff[5] else ""  # use the date of birth field if it exists, otherwise set it to a blank string. Strangely enough the usercorefields DOB is not a timestamp format, just a string
                                    email = staff[0]
                                    building = schoolMappings.get(staff[9]).title()  # convert the homeschool id number into the string name of the school using the mappings dictionary
                                    hiredate = staff[10].strftime('%m/%d/%Y') if staff[10] else ""
                                    position = staff[11] + '[A]' if staff[11] else ""
                                    # subgroup = staff[12] if staff[12] else ""  # not going to be used at this moment
                                    print(f'DBUG: {email} - {firstName} {lastName} - {idNum}, {birthdate}')
                                    print(f'{idNum},{firstName},{lastName},{email},{building},"{position}",{hiredate},{birthdate}', file=output)  # output the relevant fields to the .csv file
                            except Exception as er:
                                print(f'ERROR while processing {staff[0]} - DCID {staff[1]}: {er}')
                                print(f'ERROR while processing {staff[0]} - DCID {staff[1]}: {er}', file=log)
            except Exception as er:
                    print(f'ERROR while connecting to PS Database or running initial query: {er}')
                    print(f'ERROR while connecting to PS Database or running initial query: {er}', file=log)

        try:
            # connect to the Clever SFTP server using the login details stored as environement variables
            with pysftp.Connection(SFTP_HOST, username=SFTP_UN, password=SFTP_PW, cnopts=CNOPTS) as sftp:
                print(f'INFO: SFTP connection to Evaluwise at {SFTP_HOST} successfully established')
                print(f'INFO: SFTP connection to Evaluwise at {SFTP_HOST} successfully established', file=log)
                # print(sftp.pwd) # debug, show what folder we connected to
                # print(sftp.listdir())  # debug, show what other files/folders are in the current directory
                sftp.put(OUTPUT_FILENAME)  # upload the file onto the sftp server
                print("INFO: Staff file successfully placed on remote server")
                print("INFO: Staff file successfully placed on remote server", file=log)
        except Exception as er:
            print(f'ERROR while connecting or uploading to Clever SFTP server: {er}')
            print(f'ERROR while connecting or uploading to Clever SFTP server: {er}', file=log)

        endTime = datetime.now()
        endTime = endTime.strftime('%H:%M:%S')
        print(f'INFO: Execution ended at {endTime}')
        print(f'INFO: Execution ended at {endTime}', file=log)
