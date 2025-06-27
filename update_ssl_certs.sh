#!/bin/bash
# Script to update SSL certificates after Let's Encrypt renewal

# Copy renewed certificates
sudo cp /etc/letsencrypt/live/safonov.live/fullchain.pem /home/igor/hf/cert.pem
sudo cp /etc/letsencrypt/live/safonov.live/privkey.pem /home/igor/hf/key.pem

# Fix ownership and permissions
sudo chown igor:igor /home/igor/hf/cert.pem /home/igor/hf/key.pem
chmod 644 /home/igor/hf/cert.pem
chmod 600 /home/igor/hf/key.pem

# Restart the application (optional - you may want to implement graceful restart)
# pkill -f "python app.py" && cd /home/igor/hf && python app.py &

echo "SSL certificates updated successfully"