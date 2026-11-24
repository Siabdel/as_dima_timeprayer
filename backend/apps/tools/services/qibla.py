"""
Calcul du cap vers La Mecque (Qibla) par la formule du grand cercle.

Formule :
  θ = atan2( sin Δλ · cos φ2,
             cos φ1 · sin φ2 − sin φ1 · cos φ2 · cos Δλ )

où (φ1, λ1) = position de l'utilisateur, (φ2, λ2) = Kaaba
(21.4225° N, 39.8262° E). Le résultat est un azimut en degrés
(0° = nord, 90° = est), normalisé dans [0, 360[.
"""
import math

# Coordonnées de la Kaaba (grande mosquée de La Mecque).
KAABA_LATITUDE = 21.4225
KAABA_LONGITUDE = 39.8262


def qibla_direction(latitude: float, longitude: float) -> float:
    """
    Cap (azimut) en degrés vers la Kaaba depuis (latitude, longitude).
    Retourne une valeur dans [0, 360[.
    """
    phi1 = math.radians(latitude)
    phi2 = math.radians(KAABA_LATITUDE)
    delta_lambda = math.radians(KAABA_LONGITUDE - longitude)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.degrees(math.atan2(y, x))
    return bearing % 360


def kaaba_distance_km(latitude: float, longitude: float) -> float:
    """
    Distance orthodromique (grand cercle) vers la Kaaba, en kilomètres
    (rayon terrestre moyen : 6 371 km).
    """
    phi1, phi2 = math.radians(latitude), math.radians(KAABA_LATITUDE)
    delta_phi = phi2 - phi1
    delta_lambda = math.radians(KAABA_LONGITUDE - longitude)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def compass_point(direction: float) -> str:
    """Point cardinal approximatif (utile pour l'affichage frontend)."""
    points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(direction / 45) % 8
    return points[index]
