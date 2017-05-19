#!/bin/sh

# fdtcp project - wrapper for Java AuthService, AuthClient applications
# see fdtd.conf, resp. fdtcp.conf for details (command template, arguments)

# this target-system configuration file
. /etc/fdtcp/fdtd-system-conf.sh

inputCommand=`eval echo $@`
echo env
command="$JAVA_HOME/bin/java $inputCommand"
echo "running: '$command'"
exec $command
