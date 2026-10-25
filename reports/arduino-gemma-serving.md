# Arduino Gemma serving for Ubo Pod

As of 2026-10-25, Gemma 4 E2B is running on the Arduino's NPU and answering over the local network. The Arduino is `vq01`, a Qualcomm QCS8275 board with 15 GB of memory.

## What's running

| | |
|---|---|
| Endpoint | `http://192.168.1.225:9379/v1`, an OpenAI-compatible API. Model ID: `gemma-4-e2b` |
| Runtime | LiteRT-LM 0.18.1 `serve` on the Hexagon NPU, started through `arduino/litert-lm-npu`. Stock `litert-lm` only allows an NPU on Windows. |
| Model | `gemma-4-E2B-it_Qualcomm_QCS8275.litertlm`, the NPU build for this chip. Its SHA-256 checksum matches Hugging Face. No E4B build exists for this NPU. |
| NPU libraries | Qualcomm's QAIRT 2.50 libraries and LiteRT's Qualcomm dispatch library, from the hackathon repo's `setup_npu.py`, copied to `~/.litert-lm/npu`. The dispatch library is a third-party build (the flutter_edge_ai project), pinned by SHA-256 in `setup_npu.py`. |
| Service | `litert-lm.service` starts at boot, restarts 5 s after any crash, and sends one warm-up request when it starts |
| Network | Wi-Fi on the extender's 5 GHz band (`TP-Link_Extender_5GHz`), with the 2.4 GHz band kept as a fallback. On 2.4 GHz the Arduino topped out at about 0.35 MB/s; on 5 GHz it reached 2.4 MB/s. |

## Full test

Run from the Mac on 2026-10-25 over 3.5 minutes. It was the same test as the Jetson's. No request failed, and the server never restarted except when killed on purpose. The Jetson column is from its own full test, for comparison.

| | Arduino: Gemma 4 E2B on the NPU | Jetson: Gemma 4 E4B on the GPU |
|---|---|---|
| 10 short questions back to back | All answered (17 + 25 came back as "42"). First word in 1.29–1.81 s, then 11–14 tokens/s | First word in 1.96–2.25 s, then 15–16 tokens/s |
| ~500-token prompt | 6.0 s total, first word in 1.5 s | 8.7 s total, first word in 4.1 s |
| ~1,500-token prompt | 6.6 s total, first word in 1.9 s | 9.9 s total |
| ~500-token answer | 462 tokens in 35.1 s, 13.6 tokens/s | 33.6 s, 15.6 tokens/s |
| Two requests at once | Both answered correctly, one after the other: the second's first word came at 13.0 s | The same, at 7.9 s |
| Client hangs up mid-answer | The server stops generating. The next question's first word came in 1.6 s | 2.4 s |
| Crash restart (`kill -9`) | Back and warmed up in 13 s. The first answers ran at full speed | 25 s, and the first answer was slower |
| Board | Memory: 4.3 of 15 GB in use, about 1.5 GB of it the server. The hottest sensor stayed at 37 °C. There is no power sensor | 5.7 of 7.5 GB, 62 °C, 13.4 W |

The NPU reads prompts much faster than the Jetson's GPU, so long conversations get their first word sooner. The Jetson generates slightly faster once it starts, and it runs the larger model.

## Don't use the hackathon's faster library

The hackathon repo also ships its own build of LiteRT-LM's core library (`npu/litertlm/libLiteRtLm.so`). It reportedly puts the NPU in high-performance mode, making it about 3× faster. With it, the first request hung and the whole board froze about 8 s later, with nothing in the logs. The board needed a power cycle. The server uses the stock library from PyPI.

## Open issues

1. **Reboot not tested yet.** The service was installed after the last power cycle, so starting at boot hasn't been seen yet.
2. **No authentication.** Anyone on the local network can use the endpoint, so don't port-forward 9379.
3. **`litert-lm-npu` patches a LiteRT-LM internal.** Keep `litert-lm` pinned at 0.18.1, and re-test before upgrading.

## Day-to-day commands

- Logs: `journalctl -u litert-lm -f`. The NPU libraries log harmless `fastrpc ... Error` lines at every start and stop.
- Restart the server: `sudo systemctl restart litert-lm`

## Left as found

- The hackathon checkout in `~/google-litert-hackathon`, including its unfinished model download (1.28 GB in `models/.cache`).
- An unfinished 277 MB download in `~/iq8-gemma/`.
- The SanDisk USB drive plugged in at 01:27.
- `adbd.service`, which fails and restarts every few seconds. That was happening before this setup.
