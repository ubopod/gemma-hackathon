#!/bin/bash
# Sets up the Jetson to serve Gemma 4 at boot. Safe to re-run after changing the files here.
# Run on the Jetson from this folder's copy: sudo bash setup.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

# No desktop: frees about 1 GB for the model.
systemctl set-default multi-user.target
systemctl isolate multi-user.target

# Swap only absorbs CPU-side spikes; GPU memory can't be swapped.
if [ ! -f /swapfile ]; then
  fallocate -l 8G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# An apt upgrade of these packages has broken CUDA on the Orin Nano before.
apt-mark hold $(dpkg -l 'nvidia-l4t-*' | awk '/^ii/ {print $2}') > /dev/null

install -o mike -g mike -m 644 "$here/litert-lm-config.json" /home/mike/.litert-lm/config.json
install -m 644 "$here/litert-lm.service" /etc/systemd/system/litert-lm.service
systemctl daemon-reload
systemctl enable litert-lm
systemctl restart litert-lm

echo "Done: desktop off, swap on, NVIDIA packages held, Gemma 4 server running on port 9379."
