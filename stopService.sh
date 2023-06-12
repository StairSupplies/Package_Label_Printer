sudo systemctl stop SimpleInterfaceAPI.service

echo "Service Status"
sudo journalctl -u Put_2_Light --no-pager -n 5
echo "Use the following to check the service status:"
echo "sudo journalctl -u Put_2_Light.service --no-pager -n 50"
