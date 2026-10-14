# SpaceRisk Radar

**SpaceRisk Radar** is a real-time space situational awareness platform. It fetches satellite orbital data from [CelesTrak](https://celestrak.org/), propagates every orbit using the SGP4 model, screens all pairs of objects for close approaches (conjunctions), and displays everything on an interactive 3D globe in your browser.

SpaceRisk Radar runs locally. Follow the [Getting Started](getting-started.md) guide to run it on your own machine.

![SpaceRisk Radar live dashboard showing satellites on a 3D globe with HUD panels](assets/SpaceRisk-Rader1.png)
*The live dashboard showing tracked objects, HUD telemetry, and conjunction alerts.*

## Who is this for?

- **Space enthusiasts** who want to see what is orbiting overhead right now.
- **Students and educators** learning orbital mechanics and space situational awareness.
- **Developers** who want a working reference implementation of SGP4 propagation, WebSocket streaming, and risk scoring in Python.

## Sections

| Section | What you will find |
|---|---|
| [Getting Started](getting-started.md) | How to run the app on your laptop in five minutes |
| [User Guide](user-guide.md) | Task-by-task walkthroughs of every dashboard feature |
| [Concepts](concepts.md) | Plain-English definitions of TLE, SGP4, conjunction, and more |
| [How It Works](how-it-works.md) | Architecture pipeline and per-module explanations |
| [Limitations](limitations.md) | What the app can and cannot do — read before citing numbers |
| [API Reference](api-reference.md) | Every REST endpoint and WebSocket event with examples |
| [Style Guide](style-guide.md) | Writing conventions for contributors |
| [Changelog](changelog.md) | Release history |
| [Blog: What Is a Conjunction?](blog/what-is-a-conjunction.md) | A beginner-friendly explainer |

