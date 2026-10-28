# VibraTank — Short MVP Recommendation

**Recommendation:** Start with one properly conditioned **contact vibration sensor** on the wall of a small water tank. If available, record an external microphone simultaneously as a separate comparison channel. Use repeated no-leak and controlled-leak measurements, evaluate RMS and FFT spectral features, and begin with a simple, documented classification threshold.

This is the most feasible starting point because vibrations from water leaks can propagate through solid structures. A basic sensor and repeatable experiment can establish feasibility before the team invests in a synchronized microphone array, complex machine learning, or spatial overlays. Research on water pipelines is relevant but **does not prove performance on the VibraTank tank**.

**Implementation priorities:** (1) verify contact, amplification and sample bandwidth; (2) record labeled normal-flow and leak trials at different water levels and pump states; (3) evaluate false alarms with held-out sessions; (4) only add an AI classifier if it demonstrably improves the measured baseline.

**Localization is a stretch goal:** One fixed sensor should not be claimed to identify exact leak coordinates. Consider multiple calibrated sensor positions and correlation only after reliable leak detection is demonstrated. The regular phone camera may document a suspected area, but cannot see hidden leakage through the wall. No thermal hardware is part of this proposal.

**Supporting evidence:** [Water-pipe audio classification](https://doi.org/10.1016/j.rineng.2022.100557), [acoustic-methods review](https://doi.org/10.1016/j.autcon.2022.104226), [water-pipe vibration experiment](https://www.sciencedirect.com/science/article/abs/pii/S0263224124000022).

Full analysis: `research_summary.md` · Comparison table: `research_matrix.xlsx`.
