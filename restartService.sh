sudo systemctl stop Put_2_Light.service
sudo systemctl start Put_2_Light.service

echo "Service Status"
sudo journalctl -u Put_2_Light --no-pager -n 5
echo "Use the following to check the service status:"
echo "sudo journalctl -u Put_2_Light --no-pager -n 50"
