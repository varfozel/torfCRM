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

        return None, None


navigation_service = NavigationService()
