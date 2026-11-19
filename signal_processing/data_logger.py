"""Record raw ESP32 sensor readings as a labelled CSV experiment.

Supported Serial formats:
    one-mic mode:  mic1,vibration
    two-mic mode: mic1,mic2,vibration

Example:
    python signal_processing/data_logger.py --port COM3 --mode one-mic \
        --label normal --trial N01 --duration 60
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import serial


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "dataset" / "raw"
VALID_LABELS = ("normal", "leak", "noise")
TRIAL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def parse_sensor_line(line: str, mode: str) -> tuple[float, float | None, float]:
    """Parse one ESP32 CSV line and return mic1, mic2, vibration."""
    expected = 2 if mode == "one-mic" else 3
    parts = [part.strip() for part in line.split(",")]

    if len(parts) != expected:
        raise ValueError(f"expected {expected} values, received {len(parts)}")

    values = [float(part) for part in parts]

    if mode == "one-mic":
        return values[0], None, values[1]

    return values[0], values[1], values[2]


def record_trial(
    port: str,
    baud: int,
    mode: str,
    label: str,
    trial_id: str,
    duration: float,
    output_dir: Path = RAW_DATA_DIR,
) -> tuple[Path, Path]:
    """Read a timed experiment from Serial and save CSV plus JSON metadata."""
    if duration <= 0:
        raise ValueError("duration must be greater than zero")
    if label not in VALID_LABELS:
        raise ValueError(f"label must be one of: {', '.join(VALID_LABELS)}")
    if not TRIAL_PATTERN.fullmatch(trial_id):
        raise ValueError("trial ID may contain only letters, numbers, _ and -")

    trial_dir = output_dir / label
    trial_dir.mkdir(parents=True, exist_ok=True)

    csv_path = trial_dir / f"{trial_id}.csv"
    metadata_path = trial_dir / f"{trial_id}.json"

    if csv_path.exists() or metadata_path.exists():
        raise FileExistsError(
            f"Trial {trial_id!r} already exists in {trial_dir}. "
            "Choose another trial ID to avoid overwriting data."
        )

    started_utc = datetime.now(timezone.utc)
    valid_rows = 0
    rejected_rows = 0
    start_monotonic = time.monotonic()

    print(f"Connecting to {port} at {baud} baud...")
    with serial.Serial(port, baud, timeout=1) as device, csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        time.sleep(2)
        device.reset_input_buffer()

        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "timestamp_ms",
                "mic1",
                "mic2",
                "vibration",
                "label",
                "trial_id",
            ],
        )
        writer.writeheader()

        start_monotonic = time.monotonic()
        print(f"Recording {label}/{trial_id} for {duration:.1f} seconds...")

        while time.monotonic() - start_monotonic < duration:
            raw = device.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            try:
                mic1, mic2, vibration = parse_sensor_line(raw, mode)
            except (ValueError, TypeError):
                rejected_rows += 1
                continue

            elapsed_ms = round((time.monotonic() - start_monotonic) * 1000, 3)
            writer.writerow(
                {
                    "timestamp_ms": elapsed_ms,
                    "mic1": mic1,
                    "mic2": "" if mic2 is None else mic2,
                    "vibration": vibration,
                    "label": label,
                    "trial_id": trial_id,
                }
            )
            valid_rows += 1

    elapsed_seconds = time.monotonic() - start_monotonic
    observed_rate_hz = valid_rows / elapsed_seconds if elapsed_seconds else 0.0

    metadata = {
        "trial_id": trial_id,
        "label": label,
        "mode": mode,
        "port": port,
        "baud": baud,
        "requested_duration_seconds": duration,
        "actual_duration_seconds": round(elapsed_seconds, 3),
        "started_at_utc": started_utc.isoformat(),
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
        "observed_rate_hz": round(observed_rate_hz, 3),
        "notes": "",
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if valid_rows == 0:
        csv_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)
        raise RuntimeError(
            "No valid readings were received. Check the COM port, wiring, "
            "Serial baud rate and selected mode."
        )

    print(f"Saved {valid_rows} readings to: {csv_path}")
    print(f"Rejected lines: {rejected_rows}")
    print(f"Observed sampling rate: {observed_rate_hz:.2f} Hz")
    print(f"Metadata saved to: {metadata_path}")
    return csv_path, metadata_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VibraFlow experiment recorder")
    parser.add_argument("--port", required=True, help="ESP32 port, for example COM3")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--mode",
        choices=("one-mic", "two-mic"),
        default="two-mic",
        help="The VibraFlow MVP uses two microphones and one Piezo sensor.",
    )
    parser.add_argument("--label", choices=VALID_LABELS, required=True)
    parser.add_argument("--trial", required=True, help="Example: N01 or L01")
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        record_trial(
            port=args.port,
            baud=args.baud,
            mode=args.mode,
            label=args.label,
            trial_id=args.trial,
            duration=args.duration,
            output_dir=args.output_dir,
        )
    except KeyboardInterrupt:
        print("\nRecording cancelled.")
    except (serial.SerialException, OSError, ValueError, RuntimeError) as error:
        raise SystemExit(f"Data collection failed: {error}") from error


if __name__ == "__main__":
    main()
