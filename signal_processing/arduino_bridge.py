"""Calculate live features from ESP32 Serial data.

Expected line format: mic1,mic2,vibration
Use data_logger.py when collecting labelled experiments.
"""

from __future__ import annotations

import argparse

import numpy as np
import serial

try:
    from .features import extract_features
except ImportError:
    from features import extract_features


def run(port: str, baud: int, window_size: int, sample_rate: float) -> None:
    buffers = {"mic1": [], "mic2": [], "vibration": []}

    print(f"Connecting to {port} at {baud} baud...")
    with serial.Serial(port, baud, timeout=1) as device:
        print("Listening for mic1,mic2,vibration...")

        try:
            while True:
                raw = device.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue

                try:
                    mic1, mic2, vibration = (
                        float(value.strip()) for value in raw.split(",")
                    )
                except (ValueError, TypeError):
                    continue

                buffers["mic1"].append(mic1)
                buffers["mic2"].append(mic2)
                buffers["vibration"].append(vibration)

                if len(buffers["mic1"]) < window_size:
                    continue

                results = extract_features(
                    mic1=np.asarray(buffers["mic1"]),
                    mic2=np.asarray(buffers["mic2"]),
                    vibration=np.asarray(buffers["vibration"]),
                    fs=sample_rate,
                    include_spectrum=False,
                )

                print(
                    f"Mic1 RMS: {results['mic1']['rms']:.2f} | "
                    f"Mic2 RMS: {results['mic2']['rms']:.2f} | "
                    f"Vibration Peak: {results['vibration']['max_peak']:.2f}"
                )

                for buffer in buffers.values():
                    buffer.clear()

        except KeyboardInterrupt:
            print("\nStopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="VibraFlow live feature reader")
    parser.add_argument("--port", required=True, help="Example: COM3")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--window-size", type=int, default=1000)
    parser.add_argument("--sample-rate", type=float, required=True)
    args = parser.parse_args()

    try:
        run(args.port, args.baud, args.window_size, args.sample_rate)
    except serial.SerialException as error:
        raise SystemExit(f"Serial connection failed: {error}") from error


if __name__ == "__main__":
    main()
