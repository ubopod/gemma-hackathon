# Basic benchmark of a board's Gemma 4 endpoint, run from any machine on the LAN.
# Times 3 short questions and 1 ~500-token prompt; on the Jetson it also samples GPU, RAM,
# temperature and power. Takes about a minute: python3 scripts/benchmark.py [jetson|arduino]
import json, re, statistics, subprocess, sys, threading, time, urllib.request

BOARDS = {"jetson": ("192.168.1.45", "mike", "gemma-4-e4b"),
          "arduino": ("192.168.1.225", "arduino", "gemma-4-e2b")}
HOST, USER, MODEL = BOARDS[sys.argv[1] if len(sys.argv) > 1 else "jetson"]
URL = f"http://{HOST}:9379/v1/chat/completions"
# The boards have no SSH key set up, so stats come through an already-open control connection.
# Without one, or without tegrastats (only the Jetson has it), only the request timings are printed.
SSH = ["ssh", "-o", "ControlPath=~/.ssh/cm-%C", "-o", "BatchMode=yes", f"{USER}@{HOST}"]
samples = []

def sample_jetson(proc):
    for line in proc.stdout:
        gpu, ram = re.search(r"GR3D_FREQ (\d+)%", line), re.search(r"RAM (\d+)/", line)
        temp, power = re.search(r"tj@([\d.]+)C", line), re.search(r"VDD_IN (\d+)mW", line)
        if gpu and ram:
            samples.append((int(gpu.group(1)), int(ram.group(1)),
                            float(temp.group(1)) if temp else 0, int(power.group(1)) if power else 0))

def chat(prompt):
    # serve ignores the older max_tokens field; only max_completion_tokens caps the answer.
    body = json.dumps({"model": MODEL, "stream": True, "max_completion_tokens": 150,
                       "stream_options": {"include_usage": True},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    start, first, chunks, usage = time.time(), None, 0, None
    with urllib.request.urlopen(req, timeout=60) as resp:
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            event = json.loads(line[5:])
            usage = event.get("usage") or usage
            if any(c.get("delta", {}).get("content") for c in event.get("choices", [])):
                first = first or time.time()
                chunks += 1
    end = time.time()
    out = usage["completion_tokens"] if usage else chunks
    r = {"in": usage["prompt_tokens"] if usage else "?", "out": out,
         "ttft": first - start, "tps": (out - 1) / (end - first), "total": end - start}
    print(f"  in {r['in']:>4} tok | first word {r['ttft']:.2f}s | {r['tps']:.1f} tok/s | out {out} tok | total {r['total']:.1f}s")
    return r

tegra = subprocess.Popen(SSH + ["timeout 120 tegrastats --interval 1000"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
threading.Thread(target=sample_jetson, args=(tegra,), daemon=True).start()

print("Short questions:")
short = [chat(q) for q in ["Explain in about 100 words how vaccines work.",
                           "Give me three tips to sleep better.",
                           "What is the difference between weather and climate?"]]
print("~500-token prompt:")
notes = "The town council met to discuss the new library, bus routes, the festival budget and noise complaints. " * 25
chat(notes + "\nSummarize these notes in about 80 words.")

tegra.terminate()
print(f"\nShort question median: first word {statistics.median(r['ttft'] for r in short):.2f}s, "
      f"{statistics.median(r['tps'] for r in short):.1f} tok/s")
if samples:
    print(f"Jetson: GPU max {max(s[0] for s in samples)}%, RAM max {max(s[1] for s in samples)} MB, "
          f"temp max {max(s[2] for s in samples):.0f} C, power avg {statistics.mean(s[3] for s in samples) / 1000:.1f} W "
          f"max {max(s[3] for s in samples) / 1000:.1f} W")
