launchctl stop ai.openclaw.gateway && sleep 3 && launchctl start ai.openclaw.gateway && sleep 3 && ps aux | grep openclaw-gateway | grep -v grep
