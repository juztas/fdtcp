#!/bin/sh

# fdtcp project - FDT wrapper script
# FDT Java is run via sudo

# this target-system configuration file
. /etc/fdtcp/fdtd-system-conf.sh

# fdtd.conf defines templates for both FDT client, server commands which
# are executed via this script

inputCommand=`eval echo $@`

command="$JAVA_HOME/bin/java $inputCommand"
echo "running: '$command'"
exec $command
