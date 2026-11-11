"""Grafico decorativo della previsione eolica day-ahead: banda P10–P90, P50 e produzione effettiva.

Usato dal banner LinkedIn (scripts/linkedin_banner.py) e come sfondo dell'hero (Jinja: wind_chart_svg()).
I dati dell'immagine del sito (img/projects/wind-forecast.webp) non sono nel repository, quindi la
serie è sintetica e deterministica (seed fisso): stessa forma a ogni build. Nessun dato di clienti.

L'SVG non ha colori: le classes band / p50 / actual si colorano dal CSS di chi lo usa, con i token del sito.
"""

import math
import random


def power_curve(speed: float) -> float:
    """Produzione in % della capacità installata per una velocità del vento (m/s), curva tipo turbina."""
    if speed < 3 or speed > 25:
        return 0.0
    return 100 / (1 + math.exp(-(speed - 8.5) / 1.4))


def wind_series(hours: int = 72, seed: int = 11) -> dict[str, list[float]]:
    """Tre giorni orari: produzione effettiva e previsione day-ahead P10/P50/P90 (in % della capacità).

    Vento: processo AR(1) attorno a una media che cambia lentamente (fronti meteo).
    Previsione: la stessa velocità, smussata e con un errore che cresce con l'orizzonte;
    i quantili passano dalla curva di potenza, quindi la banda si stringe vicino a 0% e 100%.
    """
    rng = random.Random(seed)
    mean = [7 + 3.5 * math.sin(2 * math.pi * (t - 20) / 60) + 1.2 * math.sin(2 * math.pi * t / 24) for t in range(hours)]
    speed, dev = [], 0.0
    for t in range(hours):
        dev = 0.82 * dev + rng.gauss(0, 1.15)
        speed.append(max(0.0, mean[t] + dev))
    actual = [power_curve(v) for v in speed]

    forecast_speed, bias = [], 0.0
    for t in range(hours):
        window = speed[max(0, t - 3): t + 4]
        bias = 0.9 * bias + rng.gauss(0, 0.25)
        forecast_speed.append(sum(window) / len(window) + bias)
    p10, p50, p90 = [], [], []
    for t, v in enumerate(forecast_speed):
        sigma = 1.1 + 1.2 * t / hours  # m/s, l'incertezza cresce con l'orizzonte
        p10.append(power_curve(v - 1.28 * sigma))
        p50.append(power_curve(v))
        p90.append(power_curve(v + 1.28 * sigma))
    return {"actual": actual, "p10": p10, "p50": p50, "p90": p90}


def to_points(values: list[float], width: float, top: float, bottom: float) -> list[tuple[float, float]]:
    """Valori in % → punti nel riquadro (tutta la larghezza, 0% in basso)."""
    step = width / (len(values) - 1)
    return [(i * step, bottom - (bottom - top) * v / 100) for i, v in enumerate(values)]


def smooth(points: list[tuple[float, float]], move: bool = True) -> str:
    """Curva morbida per i punti (Catmull-Rom convertita in Bézier cubiche)."""
    path = [f"{'M' if move else 'L'}{points[0][0]:.1f},{points[0][1]:.1f}"]
    for i in range(len(points) - 1):
        p0, p1, p2 = points[max(i - 1, 0)], points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        path.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(path)


def chart_svg(series: dict[str, list[float]], width: int, height: int, top: float, bottom: float,
              css_class: str = "chart", aspect: str = "none") -> str:
    """SVG decorativo (aria-hidden). aspect è il preserveAspectRatio: "none" lo stira sul contenitore
    (banner, a dimensione fissa); "xMaxYMid slice" lo ritaglia senza deformarlo (hero, larghezza variabile:
    in uno spazio stretto si vede la parte finale della serie invece di tutta la serie compressa).
    vector-effect tiene costante lo spessore delle linee anche quando l'SVG viene scalato."""
    def line(key: str) -> str:
        return smooth(to_points(series[key], width, top, bottom))
    band = line("p90") + " " + smooth(to_points(series["p10"], width, top, bottom)[::-1], move=False) + " Z"
    return f"""<svg class="{css_class}" viewBox="0 0 {width} {height}" preserveAspectRatio="{aspect}" aria-hidden="true" focusable="false">
  <path class="band" d="{band}"/>
  <path class="p50" d="{line('p50')}" vector-effect="non-scaling-stroke"/>
  <path class="actual" d="{line('actual')}" vector-effect="non-scaling-stroke"/>
</svg>"""
