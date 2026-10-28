# VibraTank — Research Summary and Comparison

**Project:** VibraTank (previously ThermaTank / VibraFlow in older materials)  
**Scope:** Detect potential water leakage from a tank using **acoustic and/or contact-vibration measurements**, without thermal imaging.  
**Prepared:** 21 October 2026  
**Companion file:** [`research_matrix.xlsx`](research_matrix.xlsx)

## 1. Research objective

Find credible research and existing products that use microphones, contact vibration sensors, or both to distinguish water leaks from normal operation. Compare sensors, signal features, algorithms, strengths and limitations. Choose a feasible, testable minimum viable product (MVP) approach for a **water tank** rather than assuming pipeline or compressed-gas results transfer directly.

**Critical distinction:** detecting *whether a leak may exist* and locating *exactly where it is* are different technical objectives. Acoustic and vibration behavior depends on fluid pressure, material, water level, leakage opening, attachment method, background noise and pump activity. A single contact sensor does not by itself provide reliable leak coordinates.

## 2. Reviewed scientific research

### [R1] AI-based acoustic leak detection in water distribution systems (2022)
- **Source:** R. Vanijjirattikhan et al., *Results in Engineering* 15, 100557. https://doi.org/10.1016/j.rineng.2022.100557
- **Detection:** An acoustic rod with an external microphone records sounds through a phone; a trained model assigns leak/non-leak labels to water-pipeline recordings. Mobile/cloud tools assist operators.
- **Sensors:** Fuji acoustic listening rod, Rode SmartLav+ omnidirectional microphone and smartphone.
- **Features:** Audio captured at 44.1 kHz; the study transforms 2048-sample frames using FFT and averages spectral magnitudes over multiple frames.
- **Processing:** SVM, DNN and CNN were compared. Reported test-set accuracy was **94.89% for DNN** (94.71% for CNN and 78.29% for SVM in the reported comparison); field trial accuracy exceeded 90%.
- **Advantages:** Demonstrates a mobile workflow, tested acoustic classification and manageable spectral features.
- **Limitations:** Evidence comes from water-distribution pipes, not storage-tank walls, and the accuracy numbers are **not expected VibraTank accuracies**. Training requires well-labeled local examples.
- **VibraTank relevance:** **Very high** for baseline collection, FFT and optional later machine learning.

### [R2] Acoustic leak detection approaches for water pipelines (2022)
- **Source:** H. Fan, S. Tariq, T. Zayed, *Automation in Construction* 138, 104226. https://doi.org/10.1016/j.autcon.2022.104226
- **Detection:** Peer-reviewed synthesis of real-time and non-real-time acoustic water leak monitoring and fault detection.
- **Sensors:** Noise loggers, accelerometers, hydrophones, wireless sensing systems and fiber-optic devices.
- **Features and processing:** Time-domain, frequency-domain, time-frequency and cross-correlation analyses, with threshold-based and classification decisions.
- **Advantages:** Useful broad reference for selecting sensors and signal-processing options.
- **Limitations:** A review, not a single proof-of-concept tank experiment. Highlights challenges with weak leaks and false alarms.
- **VibraTank relevance:** **Very high**, especially for defining and measuring failure cases.

### [R3] Numerical and experimental research on vibration signal characteristics of water pipeline leakage (2024)
- **Source:** *Measurement* study. https://www.sciencedirect.com/science/article/abs/pii/S0263224124000022
- **Detection:** Measured structure-borne leakage vibration under controlled pressure conditions.
- **Sensors:** Contact acceleration sensor mounted to a ductile-iron water pipe.
- **Signal features:** Acceleration response in changing pressure conditions. One experimental arrangement describes a 2.5 mm leak, 0.1–0.5 MPa water pressure and 50 kHz sampling, with the sensor near the leak.
- **Processing:** Numerical and experimental vibration-signal analysis.
- **Advantages:** Direct motivation to try a contact sensor on a water-carrying structure.
- **Limitations:** Pipe, material and pressure differ from an actual VibraTank prototype; no tank-specific detection performance can be inferred. Only available abstract/preview details were used for this entry.
- **VibraTank relevance:** **Very high** for selecting a contact-vibration first experiment.

### [R4] High-sensitivity gas leak detection sensor based on a compact microphone array (2021)
- **Source:** J. Li et al., *Measurement* 174, 109017. https://doi.org/10.1016/j.measurement.2021.109017
- **Detection:** A compact MEMS microphone array senses faint sound from pressurized gas leaks.
- **Sensors:** Multiple MEMS microphones.
- **Features and processing:** Airborne leak sound, directional/array response and spatial aggregation.
- **Advantages:** Establishes the usefulness of multiple synchronized microphones for suitable airborne leaks.
- **Limitations:** This is **gas**, not a water tank. Gas leak sensitivity must not be quoted as water leak sensitivity; synchronized channels add hardware and algorithmic complexity.
- **VibraTank relevance:** **Medium** for possible future directional experiments only.

## 3. Reviewed existing systems

### [R5] HWM PermaNet SU — fixed acoustic leak logger
- **Source:** Manufacturer product information. https://www.hwmglobal.com/products/permanet-su/
- **Detection:** Repeated acoustic sensing with remote alerts; network analysis can correlate recordings from multiple points.
- **Sensors:** Integrated acoustic noise logger.
- **Features and processing:** Acoustic recordings, spectrograms, machine-learning noise filtering and time-aligned correlation.
- **Advantages:** Illustrates repeat monitoring, noise filtering and human-readable alerts. Manufacturer describes suppression of pump noise.
- **Limitations:** A proprietary commercial **pipeline network** system; not a turnkey or validated tank sensor.
- **VibraTank relevance:** **High** for operating workflow and false-alarm controls.

### [R6] GUTERMANN AQUASCAN 610 — acoustic leak correlator
- **Source:** Manufacturer product information. https://en.gutermann-water.com/product/aquascan-610-leak-noise-correlator/
- **Detection:** Correlates acoustic measurements at separated positions to estimate a leak position in pipes.
- **Sensors:** Two wireless leak noise sensors; optional hydrophones or contact/ground listening accessories.
- **Features and processing:** Frequency-spectrum filtering, time-delay cross-correlation and quality checks.
- **Advantages:** Existing demonstration of the principles behind multi-point location estimation.
- **Limitations:** Relies on pipe geometry and propagation assumptions; accuracy claims are vendor-specific and cannot transfer to tank surfaces.
- **VibraTank relevance:** **Medium**, if a second phase tests two or more wall-sensor positions.

### [R7] Fluke ii900 — acoustic imaging interface inspiration
- **Source:** Manufacturer product information. https://www.fluke.com/en-au/product/industrial-imaging/sonic-industrial-imager-ii900
- **Detection:** Array of microphones maps sound intensity/direction from compressed-air/gas/vacuum leaks onto an ordinary camera image.
- **Sensors:** Spatial microphone array and visible-light camera (**not a thermal imager**).
- **Features and processing:** Acoustic frequency selection (published 2–52 kHz range), spatial acoustic processing and a SoundMap image overlay.
- **Advantages:** Strong precedent for an intuitive technician-facing visualization.
- **Limitations:** Airborne industrial leaks rather than water-induced tank-wall vibration; the ii900 is listed as discontinued/reclassified. A phone camera cannot see through a tank wall.
- **VibraTank relevance:** **Medium** for interface design, **not** an appropriate assumption about MVP sensing accuracy.

### [R8] HWM Hydrophone 2 — waterborne acoustic alternative
- **Source:** Manufacturer product information. https://www.hwmglobal.com/products/hydrophone-2/
- **Detection:** Collects low-frequency leak sounds from water pipelines and connects to acoustic monitoring/correlation systems.
- **Sensors:** Hydrophone (waterborne sound).
- **Features and processing:** Low-frequency acoustic activity, usually evaluated by another logging/correlation system.
- **Advantages:** An alternative to external wall pickup if structure-borne signals are too weak.
- **Limitations:** Integration and watertight/water-contact constraints may increase cost/complexity; product is marketed for water pipelines.
- **VibraTank relevance:** **Medium** as a possible fallback, **not required** for the first prototype.

## 4. Comparison and interpretation

| Approach | Evidence in water | Implementation for a student MVP | Can detect a leak? | Can localize a tank leak? | Overall |
|---|---|---|---|---|---|
| Single contact vibration sensor + baseline | Indirect evidence from experimental water-pipe vibration | **Most practical first test** | Testable, **not yet proven on tank** | Not from one fixed sensor alone | **Recommended starting point** |
| External contact acoustic microphone + FFT/classifier | Supported by [R1] on pipes | Practical | Testable after collecting examples | Only with scanning or additional spatial design | **Good complementary channel** |
| Two or more contact sensors + cross-correlation | Pipe correlators and review support principle | Moderate difficulty | Potentially | Needs calibration of wall propagation; unproven | Later milestone |
| Airborne MEMS microphone array | Stronger gas/air precedent than water | Greater synchronization/processing demands | Depends on audible water signal | Uncertain; must test | Future experiment, not a prerequisite |
| Hydrophone placed in water/contact point | Pipe-monitoring precedent | Integration and sealing complications | Potentially | Not without multiple locations/assumptions | Fallback option |

The rankings above are **project design judgments**, not published comparative test results for VibraTank.

## 5. Recommendation for the VibraTank MVP

**Recommended design: a contact-vibration-first prototype, with an optional external microphone for comparison.** Do not include a thermal camera, and do not require a microphone array or advanced AI to demonstrate feasibility.

1. **Test rig:** Small water-filled tank or container, with a controllable low-risk leak outlet. Keep the experiment within safe pressure limits; record material, water level and leak opening each run.
2. **Capture:** Fix one suitable contact vibration sensor (a piezo disc **with a proper signal-conditioning circuit**, or an accelerometer with adequate bandwidth) at a repeatable tank-wall position. Optionally record an external microphone channel separately. Verify the sampling bandwidth of the *whole* chain before deciding on frequency features.
3. **Data:** Collect repeated labeled recordings in normal/flowing/no-leak and multiple leak conditions, including pump noise where applicable. Use multiple sessions to avoid training and testing on near-identical samples.
4. **Signal analysis:** Plot time waveforms and FFT spectra. Calculate RMS amplitude, band energy, spectral peaks/centroid and their difference from baseline. These are **candidate features to validate**, not an established tank leak signature or one fixed magic leak frequency.
5. **Initial decision:** Start with an adjustable, documented threshold plus a minimum observation window. Only train a simple model (e.g. SVM) after sufficient labeled data exist and the threshold baseline has been evaluated.
6. **Validation:** Report confusion matrix, precision, recall, false-positive rate and performance on **held-out recording sessions**. Explicitly test false positives caused by water filling, touching the tank, pump operation and ambient vibration.
7. **UI:** Show “normal / suspected leak / insufficient evidence,” signal plot and sensor location. If using an optical photo, indicate the sampled region **without suggesting the camera itself detects the leak**. For a spatial heatmap, first test multiple sensor locations and calibrate their relation to the image.

### Why this is the best MVP choice

Contact vibration is a defensible starting hypothesis for a water tank because leak-induced vibrations can propagate through the solid wall, while airborne ultrasonic detection has clearer evidence in gas/air applications. One wall sensor is cheaper and easier to prototype and characterize than a synchronized microphone array. Supplementary microphones are worth testing **only if measurements show added information**. The goal of phase one should be reproducible leak/no-leak detection; location estimation can follow once validated.

### Stop/go criteria (suggested project decisions, not literature benchmarks)

- **Proceed:** A reproducible difference appears across repeated leak and no-leak trials and persists on held-out sessions.
- **Revise:** Differences disappear with changing fill level, pump states, tank material or re-mounting; test a different pickup, amplifier/filter, position or sensor bandwidth.
- **Do not claim localization:** Until multi-point testing produces measured localization errors against known leak positions.

## 6. Constraints and evidence quality

- The original concept proposal supplied by the team establishes the project goal, the proposed microphone-array and piezoelectric options, and the need to compare normal and leaking states. These were treated as **project assumptions**, not measured performance.
- [R1]–[R4] are research papers (with [R2] a review); [R5]–[R8] are **vendor descriptions**. Vendor benefits and claims are not independent scientific validation.
- Most mature leak solutions above were developed for **pipes or compressed gas**, not water tank walls. No included reference establishes a validated VibraTank tank-specific detection accuracy, a safe universal leak frequency or exact single-sensor localization.
- The research covers the most relevant verified accessible references for this task, **not a systematic review of all published leak-detection literature**.

## 7. Reference links

1. [R1] https://doi.org/10.1016/j.rineng.2022.100557
2. [R2] https://doi.org/10.1016/j.autcon.2022.104226
3. [R3] https://www.sciencedirect.com/science/article/abs/pii/S0263224124000022
4. [R4] https://doi.org/10.1016/j.measurement.2021.109017
5. [R5] https://www.hwmglobal.com/products/permanet-su/
6. [R6] https://en.gutermann-water.com/product/aquascan-610-leak-noise-correlator/
7. [R7] https://www.fluke.com/en-au/product/industrial-imaging/sonic-industrial-imager-ii900
8. [R8] https://www.hwmglobal.com/products/hydrophone-2/

---

**Short final recommendation:** Build VibraTank first as a controlled experiment using one conditioned contact vibration sensor (optionally compared with an external microphone), FFT/RMS features and a transparent leak/no-leak baseline. Defer exact leak localization, a synchronized microphone array and any camera-overlay location claims until repeatable tank data show that they work.
