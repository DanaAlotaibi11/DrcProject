"""Record one labelled VibraFlow experiment from four microphones and Piezo.

Expected ESP32 Serial line:
    mic1,mic2,mic3,mic4,vibration

Example:
    python signal_processing/data_logger.py --port COM3 \
        --label normal --trial N01 --duration 60

Important:
    EXPECTED_SAMPLE_RATE_HZ describes the intended INMP441 acquisition rate.
    The ESP32 I2S configuration must also use 16000 Hz. This logger reports the
    observed Serial row rate so the team can verify that acquisition and
    transfer are keeping up.
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
EXPECTED_SAMPLE_RATE_HZ = 16000
MICROPHONE_COUNT = 4


def parse_sensor_line(line: str) -> tuple[float, float, float, float, float]:
    """Parse mic1,mic2,mic3,mic4,vibration from one ESP32 CSV line."""
    parts = [part.strip() for part in line.split(",")]
    expected_values = MICROPHONE_COUNT + 1

    if len(parts) != expected_values:
        raise ValueError(
            f"expected {expected_values} values, received {len(parts)}"
        )

    mic1, mic2, mic3, mic4, vibration = (
        float(part) for part in parts
    )
    return mic1, mic2, mic3, mic4, vibration


def record_trial(
    port: str,
    baud: int,
    label: str,
    trial_id: str,
    duration: float,
    output_dir: Path = RAW_DATA_DIR,
) -> tuple[Path, Path]:
    """Record one timed experiment and save CSV plus JSON metadata."""
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

    print(f"Connecting to {port} at {baud} baud...")
    with serial.Serial(port, baud, timeout=1) as device, csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        time.sleep(2)
        device.reset_input_buffer()

        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "sample_index",
                "timestamp_ms",
                "mic1",
                "mic2",
                "mic3",
                "mic4",
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
                mic1, mic2, mic3, mic4, vibration = parse_sensor_line(raw)
            except (ValueError, TypeError):
                rejected_rows += 1
                continue

            elapsed_ms = (time.monotonic() - start_monotonic) * 1000.0
            writer.writerow(
                {
                    "sample_index": valid_rows,
                    "timestamp_ms": round(elapsed_ms, 4),
                    "mic1": mic1,
                    "mic2": mic2,
                    "mic3": mic3,
                    "mic4": mic4,
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
        "microphone_count": MICROPHONE_COUNT,
        "expected_sample_rate_hz": EXPECTED_SAMPLE_RATE_HZ,
        "port": port,
        "baud": baud,
        "requested_duration_seconds": duration,
        "actual_duration_seconds": round(elapsed_seconds, 3),
        "started_at_utc": started_utc.isoformat(),
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
        "observed_serial_row_rate_hz": round(observed_rate_hz, 3),
        "expected_samples_per_microphone": round(
            EXPECTED_SAMPLE_RATE_HZ * duration
        ),
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
            "No valid five-channel readings were received. Check the COM "
            "port, wiring, baud rate and ESP32 output format."
        )

    print(f"Saved {valid_rows} readings to: {csv_path}")
    print(f"Rejected lines: {rejected_rows}")
    print(f"Observed Serial row rate: {observed_rate_hz:.2f} Hz")
    print(f"Expected INMP441 sample rate: {EXPECTED_SAMPLE_RATE_HZ} Hz")

    if observed_rate_hz < EXPECTED_SAMPLE_RATE_HZ * 0.95:
        print(
            "WARNING: the Serial row rate is below 16 kHz. Text CSV over "
            "Serial may not be fast enough for four raw INMP441 channels. "
            "Do not treat this file as full-rate audio until verified."
        )

    print(f"Metadata saved to: {metadata_path}")
    return csv_path, metadata_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VibraFlow experiment recorder")
    parser.add_argument("--port", required=True, help="ESP32 port, for example COM3")
    parser.add_argument("--baud", type=int, default=115200)
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
            label=args.label,
            trial_id=args.trial,
            duration=args.duration,
            output_dir=args.output_dir,
        )
    except KeyboardInterrupt:
        print("\nRecording cancelled.")
    except (
        serial.SerialException,
        OSError,
        ValueError,
        RuntimeError,
    ) as error:
        raise SystemExit(f"Data collection failed: {error}") from error


if __name__ == "__main__":
    main()
