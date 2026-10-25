#!/bin/bash
# Sets up the Arduino to serve Gemma 4 E2B on its NPU at boot. Safe to re-run after changing the files here.
# Needs Qualcomm's NPU libraries first: the hackathon repo's scripts/setup_npu.py puts them in npu/lib.
# Run on the Arduino from this folder's copy: sudo bash setup.sh [npu/lib folder]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
npu_libs="${1:-/home/arduino/google-litert-hackathon/npu/lib}"

# A copy, so re-running or removing the hackathon repo can't break the server.
install -d -o arduino -g arduino /home/arduino/.litert-lm/npu
cp -a "$npu_libs"/. /home/arduino/.litert-lm/npu/

install -o arduino -g arduino -m 755 "$here/litert-lm-npu" /home/arduino/.local/bin/litert-lm-npu
install -o arduino -g arduino -m 644 "$here/litert-lm-config.json" /home/arduino/.litert-lm/config.json
install -m 644 "$here/litert-lm.service" /etc/systemd/system/litert-lm.service
systemctl daemon-reload
systemctl enable litert-lm
systemctl restart litert-lm

echo "Done: Gemma 4 E2B server running on the NPU, port 9379."
