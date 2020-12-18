# MCP_Qradar
Conversion Scripts to ingest McAfee Cloud Proxy logs into IBM Qradar. This requires pulling the websaas CSV files from the McAfee CSR Server to be converted into an ingestible format

This is an initial push of this, it is confirmed working but you need to know what you're looking for. There's comments in line in the scripts below.

# The Overview

There's two scripts, a python script and a shell script. The shell script is used as a cron / scheduled task (say, create a cron to run it every 15 minutes). 
It look for new files that came in, dispatch them to conversion jobs and output a file for each into an output directory for retrieval by Qradar.

The python script is a threaded conversion script that pulls in the WebSaas CSV files from McAfee CSR server which report all of the connection log data from McAfee Cloud Proxy.
The conversion makes them a valid log stream that, on the Qradar Side, can be ingested by a log source configured with the McAfee Web Gateway DSM Type upsing a File protocol, such as SFTP.


# Details

## Architecture

The scripts, as-is, assume you have a linux host with a local user, mcafee who lives in `/home/mcafee`.
This linux host and user act as a middle man between McAfee CSR and Qradar. That user's home directory should contain 4 additional subdirectories,
`in`, `out` and `tmp`.

- Incoming files go into `in`
- Outgoing files go into `out`
- Files being converted go into `tmp`
- Our scripts go into a directory named `bin`


The Windows CSR Server will need to push the CSV logs into this Linux Server, targetting our `in` directory ( eg. `/home/mcafee/in` ) listed above.
You can use `Posh-SSH` for this, See: https://www.powershellgallery.com/packages/Posh-SSH/2.1

A cron on the linux server for every 15 minutes should be configured to run the shell script contained here from the user's `bin` directory (eg. `/home/mcafee/bin/` )

All files that are being converted will temporarily be put into the `tmp` directory while the conversion is happening, and the finalized converted file will be moved to the `out` directory.


On the Qradar Side, setup a log source using the McAfee Web Gateway DSM, with SFTP File Protocol and point it to your `/home/mcafee/out` directory looking for `*\.log`

# Testing

I suggest reading the heavily commented scripts to understand their mechanics and test them. You can run the python script directly (python 2.7 for now)

Make hwatever edits you want to suit it to your environment. 
