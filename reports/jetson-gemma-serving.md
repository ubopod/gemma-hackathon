# Jetson Gemma serving for Ubo Pod

As of 2026-10-24, Gemma 4 E4B is running on the Jetson Orin Nano Super and answering over the local network. MedGemma is set aside for now.

## What's running

| | |
|---|---|
| Endpoint | `http://192.168.1.45:9379/v1`, an OpenAI-compatible API. Model ID: `gemma-4-e4b` |
| Runtime | LiteRT-LM 0.18.1 `serve`, on the GPU (set in `~/.litert-lm/config.json`) |
| Model | `gemma-4-E4B-it.litertlm`. Its SHA-256 checksum matches Hugging Face. |
| Service | `litert-lm.service` starts at boot, restarts 5 s after any crash, and sends one warm-up request when it starts |
| System | Desktop off, 8 GB swap file, 66 `nvidia-l4t-*` packages held, power mode 25W |

## Benchmark

Streamed requests sent from the Mac over the network on 2026-10-24, while the Jetson's GPU, memory, temperature and power were sampled every second.

| | |
|---|---|
| Short question (17–21 tokens in) | First word in 2.0 s (median of 3), then 15.6 tokens/s |
| ~500-token prompt | First word in 3.8 s, then 15.4 tokens/s |
| Jetson under load | GPU at 99%, memory 5.7 of 7.5 GB, 63 °C, 15.3 W average (16.3 W peak) |
| Crash recovery | After a `kill -9`, the server was back and warmed up within 29 s, with no help |

At about 15 tokens/s, a 100-token answer finishes in about 9 s, and a 400-token answer takes about 28 s.

To cap answer length, a request must send `max_completion_tokens`. `serve` ignores the older `max_tokens` field: in the benchmark, two answers capped at 150 tokens with `max_tokens` came back with 409 and 776 tokens.

## Full test

Run from the Mac on 2026-10-24 over 3.8 minutes. No request failed, and the server never restarted except when killed on purpose.

| | |
|---|---|
| 10 short questions back to back | All answered (17 + 25 came back as "42"). First word in 1.96–2.25 s, then 15–16 tokens/s throughout |
| ~1,500-token prompt | 9.9 s total for a 72-token summary |
| ~500-token answer | 33.6 s, at a steady 15.6 tokens/s to the end |
| Two requests at once | Both answered correctly, one after the other: the second waited for the first (first word in 7.9 s) |
| Client hangs up mid-answer | The server stops generating. The next question's first word came in 2.4 s. The log records one harmless `BrokenPipeError` |
| Crash restart (`kill -9`) | Back and warmed up in 25 s. The first answer was a little slower (13.1 tokens/s, first word in 3.6 s), then speed was normal |
| Jetson | Memory peaked at 5.7 of 7.5 GB and swap at 64 MB. 62 °C, 13.4 W average (16.8 W peak). No out-of-memory kills or throttling |

## Open issues

1. **The first answer after a restart can be slow.** Once it generated at 1.8 tokens/s (55 s total). In the full test it ran at 13.1 tokens/s. Either way, the second answer is back to normal speed. The cause is unknown. It isn't the warm-up being too short: `serve` ignores the warm-up's `max_tokens`, so the warm-up already generates a full short answer.
2. **Reboot not tested yet.** It needs `sudo reboot`, which also ends the current SSH session.
3. **No authentication.** Anyone on the local network can use the endpoint, so don't port-forward 9379.

## Next: connect the Ubo Pod

In the Pod's assistant settings, choose **Add Generic LLM** and enter:

- Base URL: `http://192.168.1.45:9379/v1`
- Model: `gemma-4-e4b`
- API key: leave blank

Also check which length field ubo_app sends. If it sends `max_tokens` rather than `max_completion_tokens`, answers won't be capped. In that case, ask for short answers in the system prompt instead.

## MedGemma, set aside

- MedGemma 1.5 4B, released in January 2026, is the newest version.
- The file on the Jetson matches Hugging Face's checksum, but its 4-bit format fails to load on LiteRT-LM's GPU backend.
- On the CPU it ran at 5.2–5.6 tokens/s, with the first word in 1.8 s once loaded. Switching between it and Gemma 4 took 19–24 s, because `serve` keeps only one model in memory.
- It has been removed from LiteRT-LM's model list. The file is still at `~/.litert-lm/models/litert/MedGemma-1.5-4B-IT/`.

## Day-to-day commands

- Logs: `journalctl -u litert-lm -f`
- Restart the server: `sudo systemctl restart litert-lm`
- Bring the desktop back: `sudo systemctl isolate graphical.target`
- Upgrade NVIDIA packages on purpose: run `sudo apt-mark unhold` on them first

## Left as found

`~/.litert-lm/models/` also holds about 55 GB that the session from 192.168.1.248 moved or copied there: the old `~/models/litert` folder and about 10 GB of Gemma 3 1B copies. LiteRT-LM uses only Gemma 4 E4B; the rest sits unused.
