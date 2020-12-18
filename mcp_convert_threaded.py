#!/usr/bin/env python
from __future__ import print_function

import re
import csv
import sys
import socket
from multiprocessing import Pool, cpu_count
import time
import datetime
"""

This script takes a single argument, the CSV file for conversion.

It takes this CSV file in, and spits out a LEEF formatted stream to STDOUT.
There is an accompanying Shell script that should handle calling this file. 
If you call it directly, you'll want to redirect STDOUT to a file. 

Status messages, errors and counter data is printed to STDERR.

The gist here is this script will allow you to convert data coming in from McAfee Cloud Proxy and put it in a file 
which can be collected by an IBM Qradar Event Processor or Event Collector.

For this, you have two options: Either stream it line by line over syslog to a listener, or put it in a directory where
FTP/SFTP/SCP can grab it. I personally prefer the SFTP, as it allows Qradar to recursively search directories, fetch multiple files,
allows for key based auth, and overall is lighter / easier to maintain than having to spit a stream to the collector itself.

This script is confirmed working, but I suggest reading the comments below. Feel free to reach out or open a bug if you have questions or concerns.

--- 

Written by Mike Piekarski, Enterprise Security Architect at Array Solutions

To be compliant with Qradar's Python Interpreter, this script is written with Python 2.7.

csv.DictReader would need to be updated in order to work on Python 3. I haven't evaluated the rest, but 
I don't think it's a high level of effort to port over, if need be.

"""

# Get our File Name - Simply the first argument handed to our script.
# Yea yea yea -- I know I should handle this with argparse.
test_file = sys.argv[1]

# Column Names just in case
column_names = 'user_id,username,source_ip,http_action,server_to_client_bytes,client_to_server_bytes,requested_host,requested_path,result,virus,request_timestamp_epoch,request_timestamp,uri_scheme,category,media_type,application_type,reputation,last_rule,http_status_code,client_ip,location,block_reason,user_agent_product,user_agent_version,user_agent_comment'

def eprint(*args, **kwargs):
    """ Function to print to stderr """
    print(*args, file=sys.stderr, **kwargs)


def call_processing_rows_pickably(row):
    process_row(row)


def process_row(row):
    """
    Method which handles actual record processing
    """
    try:
        # Only select lines with a valid Username
        if not row['username'] == "":
            # Only select lines with a valid epoch timestamp
            if re.match('^[\d]+$', row['request_timestamp_epoch']):
                # Set and format timestamp
                timestamp = datetime.datetime.fromtimestamp(int(row['request_timestamp_epoch'])).strftime('%b %d %X')
                # Fail to 169.254.1.1 if DNS Resolution fails for the hostname
                if row['requested_host']:
                    dest_ip = socket.gethostbyname(row['requested_host'])
                else:
                    dest_ip = '169.254.1.1'
                # Output the formatted syslog payload in compliance with McAfee and Qradar's formatting and DSM 
                print("<30>{} MCP mgw: LEEF:1.0|McAfee|Web Gateway|7.0|0|devTime={}|src={}|usrName={}|dst={}|httpStatus={}|blockReason={}|url={}://{}{}".format(
                    timestamp,
                    row['request_timestamp_epoch'],
                    row['client_ip'],
                    row['username'],
                    dest_ip,
                    row['http_status_code'],
                    row['block_reason'],
                    row['uri_scheme'],
                    row['requested_host'],
                    row['requested_path']))
    except socket.gaierror:
        pass

class process_csv():


    def __init__(self, file_name):
        self.file_name = file_name

    def get_row_count(self):
        """
        Return total number of rows in target file
        """
        with open(self.file_name) as f:
            for i, l in enumerate(f):
                pass
        self.row_count = i

    def select_chunk_size(self):
        """
        Dynamically assign chunk sizes for reading blocks of CSV data into the worker queue
        """
        if(self.row_count>10000000):
            self.chunk_size = 1000000
            return
        if(self.row_count>5000000):
            self.chunk_size = 500000
            return
        self.chunk_size = 250000
        return

    def process_rows(self):
        """
        Perform the actual reading of the target CSV and populate a list of CSV rows
        Rows are pulled as Dicts to make columns fetchable by name

        Note Worker Pool p is set below, outside of this method.

        """
        list_de_rows = []
        count = 0
        chunk_remainder = self.row_count % self.chunk_size
        max_chunked = self.row_count - chunk_remainder
        # Run Through the CSV in our Chunks defined above.
        with open(self.file_name, 'rb') as file:
            reader = csv.DictReader(file)
            for row in reader:
                count += 1
                if count % 10000 == 0:
                    # Print to StdErr every 10k rows being read in with a timestamp
                    now = datetime.datetime.now()
                    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
                    eprint("{}: Count {}".format(date_time, count))
                # Append each row to the list_de_rows list
                list_de_rows.append(row)
                if(len(list_de_rows) == self.chunk_size):
                    # When we hit our Chunk Size, Map our worker pool to start processing 
                    p.map(call_processing_rows_pickably, list_de_rows)
                    del list_de_rows[:]
                elif( count >= max_chunked ):
                    # Detect when we are on the last Chunk
                    if(len(list_de_rows) == (self.row_count % self.chunk_size) - 2):
                        # Perfom the final pass of processing when we are at the last chunk which is smaller than our chunk_size
                        p.map(call_processing_rows_pickably, list_de_rows)
                        del list_de_rows[:]


    def start_process(self):
        # Invoke our processing methods
        self.get_row_count()
        self.select_chunk_size()
        self.process_rows()

# Set the processing start time
initial = datetime.datetime.now()

# Set our number of workers for use in process_rows
# You can change this to your liking, up or down OR see the dynamic scaling options below
p = Pool(40)

# Below is a commented out demonstration of using dynamic scaling
#p = Pool(cpu_count()+1)
ob = process_csv(test_file)
ob.start_process()
# Set the processing stop time
final = datetime.datetime.now()
# Print the total run time to stderr
eprint(final-initial)


