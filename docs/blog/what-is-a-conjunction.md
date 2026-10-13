# What Is a Conjunction?

*A plain-English explanation for anyone curious about how satellites avoid collisions in space.*

---

Right now, as you read this, thousands of objects are orbiting Earth at speeds of around 7–8 km per second — roughly 25,000 km/h. Most of them never come anywhere near each other. But occasionally, two objects' paths in space bring them uncomfortably close. That close approach is what space operators call a **conjunction**.

The word sounds technical, but the concept is straightforward: a conjunction is simply a moment when two space objects are near each other. "Near" is relative, of course — in everyday life, two cars 100 metres apart are very close. In space, 100 km is considered extremely close.

## The motorway analogy

Imagine a multi-lane motorway with thousands of cars, except the cars are invisible and there are no lines on the road. Each car is travelling in a slightly different direction at a slightly different height (think of a motorway interchange stacked 10 levels high). You can see each car's position and speed, but only approximately — your GPS is a day old.

Now imagine two cars appear to be converging on the same spot in a few minutes. They might be on the same level, heading straight for each other. Or they might be on different levels and just look close from a bird's-eye view. You cannot tell for certain — the GPS uncertainty is too large. Do you radio one driver to swerve, burning fuel and disrupting their route? Or do you wait and see?

This is exactly the dilemma space operators face every day.

## What SpaceRisk Radar looks for

SpaceRisk Radar fetches a catalog of satellite orbital elements from CelesTrak every couple of hours. Each set of elements — called a **TLE** (Two-Line Element set) — encodes where a satellite was at a specific moment and how its orbit is shaped. Using a mathematical model called **SGP4**, the app extrapolates where every tracked object is right now.

Then it checks every possible pair. With 2,000 objects tracked in the live view, that is roughly 2,000 × 1,999 ÷ 2 ≈ 2 million pairs per cycle. For each pair, the app computes the 3D straight-line distance between the two objects. Any pair closer than the *screening threshold* (500 km by default, but you can change it) is flagged as a conjunction.

## A conjunction is not a collision

The most important thing to understand is this: **a conjunction is a warning to look closer, not a prediction of impact.**

Even at 1 km separation, two objects might be travelling in exactly parallel paths at the same speed — never getting any closer. Or one might be moving away already. The distance at a single snapshot in time is a starting point for analysis, not a verdict.

Operational space agencies such as NASA and ESA compute a quantity called *probability of collision* (Pc) that takes into account the uncertainty in each object's position (its "error ellipsoid"), the relative velocity, and the physical size of each object. SpaceRisk Radar uses a simplified heuristic score instead — because the full covariance data needed for a rigorous Pc calculation is not publicly available for most objects.

The score in SpaceRisk Radar is useful for **ranking conjunctions by severity** and for educational exploration. It is not a substitute for operational collision avoidance analysis.

## Why it matters

The 2009 collision between Iridium 33 (an active US communications satellite) and Cosmos 2251 (a defunct Russian satellite) produced more than 1,800 trackable debris fragments. That event — and the 2021 Russian ASAT test, which destroyed Cosmos 1408 and created another large debris cloud — demonstrated that a single collision can make an entire orbital band more dangerous for decades.

This is the spectre of **Kessler syndrome**: a cascade where each collision generates debris that causes more collisions, which generate more debris. The concern is not imminent — the orbital environment is large — but the trend of increasing object density makes tools for conjunction monitoring more important over time.

![Conjunction threat detection panel showing two objects within the screening threshold](../assets/SpaceRisk-Rader4.png)
*SpaceRisk Radar's conjunction panel. Each row shows two objects, their 3D distance, and a risk level derived from a heuristic probability score.*

## What you can do

If you want to learn more, the [NASA Conjunction Assessment](https://www.nasa.gov/conjunction-assessment-risk-analysis/) programme publishes detailed information about how operational conjunction assessment works. The [CelesTrak](https://celestrak.org/) website, the source of the data SpaceRisk Radar uses, also has extensive tutorials on reading TLEs and understanding orbital mechanics.

And of course, you can open [SpaceRisk Radar](https://spacerisk-radar.onrender.com/) right now, lower the screening threshold to 100 km, and watch which pairs appear. The orbit replay slider lets you wind the clock forward or back and see how the picture changes — a reminder that space situational awareness is always a race against time.

---

*Further reading: Kessler, D.J., Cour-Palais, B.G. (1978). "Collision frequency of artificial satellites: The creation of a debris belt." Journal of Geophysical Research, 83(A6), 2637–2646.*
