# LLM servers for Ubo Pod

Serves Gemma 4 from two boards on the local network, so the Ubo Pod can send them complex queries. Both serve the same OpenAI-compatible API on port 9379.

| Board | Endpoint | Model ID | Runs on |
|---|---|---|---|
| Jetson Orin Nano Super | `http://192.168.1.45:9379/v1` | `gemma-4-e4b` | GPU |
| Arduino (`vq01`, Qualcomm QCS8275) | `http://192.168.1.225:9379/v1` | `gemma-4-e2b` | NPU |

```
jetson/    setup script, systemd unit and LiteRT-LM config for the Jetson
arduino/   the same for the Arduino, plus litert-lm-npu, which makes LiteRT-LM's NPU backend work on Linux
scripts/   benchmark.py: times either board from any machine on the LAN
reports/   setup notes and test results for each board
```

## Set up the Jetson

1. On the Jetson, install LiteRT-LM and import the model:

   ```bash
   uv tool install litert-lm==0.18.1
   litert-lm import /path/to/gemma-4-E4B-it.litertlm gemma-4-e4b
   ```

2. From this repo, copy the `jetson` folder over and run the setup script. You'll be asked for the sudo password.

   ```bash
   scp -r jetson mike@192.168.1.45:/tmp/
   ssh -t mike@192.168.1.45 'sudo bash /tmp/jetson/setup.sh'
   ```

## Set up the Arduino

1. On the Arduino, install LiteRT-LM and import the NPU build of the model. Then get Qualcomm's NPU libraries by running the hackathon repo's `scripts/setup_npu.py`, which puts them in its `npu/lib` folder.

   ```bash
   uv tool install litert-lm==0.18.1
   litert-lm import /path/to/gemma-4-E2B-it_Qualcomm_QCS8275.litertlm gemma-4-e2b
   ```

2. From this repo, copy the `arduino` folder over and run the setup script. You'll be asked for the sudo password. If the NPU libraries aren't in `~/google-litert-hackathon/npu/lib`, pass their folder to the script.

   ```bash
   scp -r arduino arduino@vq01.local:/tmp/
   ssh -t arduino@vq01.local 'sudo bash /tmp/arduino/setup.sh'
   ```

## Benchmark

```bash
python3 scripts/benchmark.py jetson
```

```bash
python3 scripts/benchmark.py arduino
```

The details and latest results are in [reports/jetson-gemma-serving.md](reports/jetson-gemma-serving.md) and [reports/arduino-gemma-serving.md](reports/arduino-gemma-serving.md).
