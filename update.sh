#!/bin/bash

APPFILE=/home/pi/SimpleInterfaceAPI/flaskRun.sh
SERVICEFILE=/home/pi/SimpleInterfaceAPI/service.txt
SERVICELOCATION=/etc/systemd/system/SimpleInterfaceAPI.service
# Uncomment the following if you want to have git pulls also
# git reset --hard
# git pull

sudo chown pi $APPFILE
sudo chmod +x $APPFILE


echo "ReCreating: Service" 
sudo mv $SERVICEFILE $SERVICELOCATION
echo "Done"
echo "Starting Service"
sudo systemctl stop SimpleInterfaceAPI.service
sudo systemctl start SimpleInterfaceAPI.service
sudo systemctl enable SimpleInterfaceAPI.service
echo "Service Status"
sudo journalctl -u SimpleInterfaceAPI.service --no-pager -n 50
echo "Use the following to check the service status:"
echo "sudo journalctl -u SimpleInterfaceAPI.service --no-pager -n 50"
