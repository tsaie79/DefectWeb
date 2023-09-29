#!/bin/bash
export HOST="129.10.50.43"
echo -n "Creating SSH tunnel to $HOST... "
ssh -4 -q -N -f -T -M -L 3306:127.0.0.1:3306 tsai@$HOST
echo "Done!"

# echo -n "Closing SSH tunnel... "
# ssh -q -T -O "exit" $HOST
# echo "Done!"