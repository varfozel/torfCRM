from decimal import Decimal
import re
from typing import Optional, Tuple
from urllib.parse import quote_plus

from app.config import get_settings


class NavigationService:
    """
    Centralized navigation and location service.
    
    Manages the fixed warehouse origin from configuration and generates
    client-side navigation links (e.g. Waze, Google Maps).
    
    NOTE: Standard Waze URLs (`https://waze.com/ul?ll=...&navigate=yes`)
    instruct the driver's device to navigate from their *current location* to
    the destination coordinates. The standard Waze URL interface does not support
    forcing an arbitrary origin. The warehouse origin is stored centrally here
    for display, origin dispatch reference, and future routing services.
    """

    def __init__(self):
        self.settings = get_settings()

    @property
    def warehouse_info(self) -> dict:
        return {
            "name": self.settings.WAREHOUSE_NAME,
            "address": self.settings.WAREHOUSE_ADDRESS,
            "latitude": self.settings.WAREHOUSE_LAT,
            "longitude": self.settings.WAREHOUSE_LON,
        }

    def generate_waze_url(
        self,
        latitude: Optional[Decimal | float] = None,
        longitude: Optional[Decimal | float] = None,
        address: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a Waze deep link for navigation.
        
        Prioritizes coordinates (lat, lon) if available, falling back to address search.
        Returns None if neither is provided.
        """
        if latitude is not None and longitude is not None:
            # Format to 6 decimal places
            lat = f"{float(latitude):.6f}"
            lon = f"{float(longitude):.6f}"
            return f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
        elif address and address.strip():
            encoded_addr = quote_plus(address.strip())
            return f"https://waze.com/ul?q={encoded_addr}&navigate=yes"
        return None

    def generate_google_maps_url(
        self,
        latitude: Optional[Decimal | float] = None,
        longitude: Optional[Decimal | float] = None,
        address: Optional[str] = None,
        from_warehouse: bool = True,
    ) -> Optional[str]:
        """
        Generate a Google Maps directions or search URL.
        Can optionally specify origin from the central warehouse.
        """
        origin_param = ""
        if from_warehouse and self.settings.WAREHOUSE_LAT and self.settings.WAREHOUSE_LON:
            origin_param = f"&origin={self.settings.WAREHOUSE_LAT},{self.settings.WAREHOUSE_LON}"

        if latitude is not None and longitude is not None:
            dest = f"{float(latitude):.6f},{float(longitude):.6f}"
            return f"https://www.google.com/maps/dir/?api=1{origin_param}&destination={dest}"
        elif address and address.strip():
            dest = quote_plus(address.strip())
            return f"https://www.google.com/maps/dir/?api=1{origin_param}&destination={dest}"
        return None

    @staticmethod
    def parse_coordinates(text: str) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Parse latitude and longitude from manually entered coordinates or links
        (e.g., copied from Viber messages, Google Maps, or Waze links).
        
        Supports:
        - Plain coordinates: "51.298100, 25.553200" or "51.298100 25.553200"
        - Google Maps URL: "...@51.298100,25.553200..." or "...q=51.298100,25.553200..."
        - Waze URL: "...ll=51.298100,25.553200..."
        """
        if not text:
            return None, None

        # Pattern for standard decimal coordinates (lat, lon)
        patterns = [
            # In URL query or path: q=51.2981,25.5532 or ll=51.2981,25.5532 or @51.2981,25.5532
            r"[@?&](?:q|ll|query)=([+-]?\d+(?:\.\d+)?),([+-]?\d+(?:\.\d+)?)",
            r"@([+-]?\d+(?:\.\d+)?),([+-]?\d+(?:\.\d+)?)",
            # Plain numbers: 51.2981, 25.5532 or 51.2981 25.5532
            r"^\s*([+-]?\d+(?:\.\d+)?)[,\s]+([+-]?\d+(?:\.\d+)?)\s*$",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    lat = Decimal(match.group(1))
                    lon = Decimal(match.group(2))
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return lat, lon
                except Exception:
                    continue

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points on Earth in kilometers."""
        import math
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    async def calculate_route(
        self,
        address: Optional[str] = None,
        latitude: Optional[Decimal | float] = None,
        longitude: Optional[Decimal | float] = None,
    ) -> dict:
        """
        Calculate actual road distance in kilometers and estimated driving duration
        from the warehouse to destination using OSRM routing and Nominatim geocoding.
        """
        dest_lat: Optional[float] = float(latitude) if latitude is not None else None
        dest_lon: Optional[float] = float(longitude) if longitude is not None else None

        # 1. Try parsing coordinates from address string if coordinates are missing
        if (dest_lat is None or dest_lon is None) and address:
            plat, plon = self.parse_coordinates(address)
            if plat is not None and plon is not None:
                dest_lat = float(plat)
                dest_lon = float(plon)

        # 2. Geocode address via OpenStreetMap Nominatim if coordinates not yet found
        if (dest_lat is None or dest_lon is None) and address and address.strip():
            import httpx
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    geo_resp = await client.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={"q": address.strip(), "format": "json", "limit": 1, "countrycodes": "ua"},
                        headers={"User-Agent": "PeatCRM/1.0"},
                    )
                    if geo_resp.status_code == 200:
                        geo_data = geo_resp.json()
                        if geo_data and len(geo_data) > 0:
                            dest_lat = float(geo_data[0]["lat"])
                            dest_lon = float(geo_data[0]["lon"])
            except Exception:
                pass

        if dest_lat is None or dest_lon is None:
            return {
                "success": False,
                "message": "Не вдалося визначити координати адреси. Перевірте адресу або введіть кілометраж вручну.",
                "distance_km": None,
                "duration_min": None,
                "latitude": None,
                "longitude": None,
                "waze_url": self.generate_waze_url(address=address) if address else None,
            }

        wh_lat = float(self.settings.WAREHOUSE_LAT)
        wh_lon = float(self.settings.WAREHOUSE_LON)

        # 3. Request actual road driving route from OSRM
        import httpx
        try:
            osrm_url = f"https://router.project-osrm.org/route/v1/driving/{wh_lon},{wh_lat};{dest_lon},{dest_lat}?overview=false"
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(osrm_url)
                if resp.status_code == 200:
                    route_data = resp.json()
                    if route_data.get("code") == "Ok" and route_data.get("routes"):
                        route = route_data["routes"][0]
                        dist_meters = float(route.get("distance", 0))
                        dur_sec = float(route.get("duration", 0))
                        distance_km = round(dist_meters / 1000.0, 1)
                        duration_min = max(1, round(dur_sec / 60.0))

                        return {
                            "success": True,
                            "distance_km": Decimal(str(distance_km)),
                            "duration_min": duration_min,
                            "latitude": Decimal(str(round(dest_lat, 6))),
                            "longitude": Decimal(str(round(dest_lon, 6))),
                            "waze_url": self.generate_waze_url(dest_lat, dest_lon, address),
                            "google_maps_url": self.generate_google_maps_url(dest_lat, dest_lon, address),
                            "message": f"Маршрут побудовано: {distance_km} км (~{duration_min} хв)",
                        }
        except Exception:
            pass

        # 4. Fallback: haversine distance with 1.35 road network tortuosity factor
        h_km = self.haversine_distance(wh_lat, wh_lon, dest_lat, dest_lon)
        est_km = round(h_km * 1.35, 1)
        est_min = max(1, round(est_km / 60.0 * 60))

        return {
            "success": True,
            "distance_km": Decimal(str(est_km)),
            "duration_min": est_min,
            "latitude": Decimal(str(round(dest_lat, 6))),
            "longitude": Decimal(str(round(dest_lon, 6))),
            "waze_url": self.generate_waze_url(dest_lat, dest_lon, address),
            "google_maps_url": self.generate_google_maps_url(dest_lat, dest_lon, address),
            "is_estimated": True,
            "message": f"Орієнтовний маршрут: {est_km} км (~{est_min} хв)",
        }


navigation_service = NavigationService()

