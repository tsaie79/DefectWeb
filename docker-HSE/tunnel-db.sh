#!/bin/bash
echo -n "Creating SSH tunnel to $HOST... "
ssh -4 -q -N -f -T -M -L localhost:12349:localhost:27017 tsai@$HOST
echo "Done!"

# echo -n "Closing SSH tunnel... "
# ssh -q -T -O "exit" $HOST
# echo "Done!"