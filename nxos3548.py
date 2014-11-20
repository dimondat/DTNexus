# The script examples provided by Cisco for your use are provided for reference only as a customer courtesay.  
# They are intended to facilitate development of your own scripts and software that interoperate with Cisco switches 
# and software.  Although Cisco has made efforts to create script examples that will be effective as aids to script 
# or software development,  Cisco assumes no liability for or support obligations related to the use of the script 
# examples or any results obtained using or referring to the script examples.

from cisco import *
from socket import *
import time
import struct

server_host = '172.31.2.12'     # server name, or IP like in this case
server_port =  50007             # non-reserved port used by the server
bufferInfo=bytearray()

# MGMT IP Info to identify the source
mgmtIPInfo=cli('show interface mgmt 0 brief | grep mgmt0')
mgmtIP=mgmtIPInfo[1].split()[3].split(".")

while [ 1 ]:
  # Clear the data first - else we will have a large amount of data
	cli('clear hardware profile buffer monitor', False)
	# Sleep for a second - to collect 1 second worth of data
	time.sleep(1)
	# Capture data for that second
	bufferCLIOutput=CLI('show hardware profile buffer monitor detail | grep "/"', False)

	bufferBlock1Output=CLI('show hardware profile buffer monitor buffer-block 1 detail | grep / | grep -v CLI', False)
	bufferBlock2Output=CLI('show hardware profile buffer monitor buffer-block 2 detail | grep / | grep -v CLI', False)
	bufferBlock3Output=CLI('show hardware profile buffer monitor buffer-block 3 detail | grep / | grep -v CLI', False)

	# Add signature
	bufferInfo[:] = b'Cisco Nexus 3548 ABM'

	# Add IP info to the packet - to identify
	counter = 0
	while ( counter < len(mgmtIP) ):
		bufferInfo.append(int(mgmtIP[counter]))
		counter = counter + 1

	TSDone=0	# To add time stamp only once

	# Parse output
	for line in bufferCLIOutput.get_output():
		# Line containing word "Active" contains port number
		if "Active" in line:
			port=line.split()[5].split("/")[1]
			continue
		# Skip lines that don't have info that we need
		elif "Detail CLI" in line:
			continue
		else:
			# Skip lines that don't have info that we need
			if not ":" in line:
				continue

			# Add timestamp - epoch - 4 bytes
			# 1 byte for hour, 1 byte for min and 1 byte for second
			if TSDone == 0:
				# Month and Day
				tsDate=bufferCLIOutput.get_output()[2].split()[0]
				tsTime=bufferCLIOutput.get_output()[2].split()[1]
				tsPattern = '%m/%d/%Y %H:%M:%S'
				tsEpochTime=int(time.mktime(time.strptime(tsDate + ' ' + tsTime, tsPattern)))
				bufferInfo = bufferInfo + struct.pack('<I', tsEpochTime)
				TSDone=1

			# Add the port number
			bufferInfo.append(int(port))

			# port buffer usage - 
			# 1 byte per value : 16 values = 16 bytes
			for bUsage in bufferCLIOutput.get_output()[2].split()[2::]:
				bufferInfo.append(int(bUsage))


        # Add the buffer-block number - 1
        bufferInfo.append(1)

        # buffer-block 1 buffer usage -
        # 1 byte per value : 16 values = 16 bytes
        for bb1Usage in bufferBlock1Output.get_output()[0].split()[2::]:
                bufferInfo.append(int(bb1Usage))

        # Add the buffer-block number - 2
        bufferInfo.append(2)

        # buffer-block 2 buffer usage -
        # 1 byte per value : 16 values = 16 bytes
        for bb2Usage in bufferBlock2Output.get_output()[0].split()[2::]:
                bufferInfo.append(int(bb2Usage))

        # Add the buffer-block number - 3
        bufferInfo.append(3)

        # buffer-block 3 buffer usage -
        # 1 byte per value : 16 values = 16 bytes
        for bb3Usage in bufferBlock3Output.get_output()[0].split()[2::]:
                bufferInfo.append(int(bb3Usage))

	# Try connecting and sending the data
	sock_obj = socket(AF_INET, SOCK_DGRAM)
	sock_obj.sendto(bufferInfo, (server_host,server_port))

	# Clear bytearray
	del bufferInfo[0::]

# Close socket - 
sock_obj.close()