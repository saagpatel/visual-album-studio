import json
import sys

from vas_audio_worker import analyze_audio


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        path = req.get("audio_path", "")
        res = analyze_audio(path)
        print(json.dumps(res), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
