import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GeocoderAnswer:
    region: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None

    lat: float = 0.0
    lon: float = 0.0

    additional_information: dict[str, Any] = field(default_factory=dict)

    organizations: list[dict[str, Any]] = field(default_factory=list)


class GeocoderAnswerEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, GeocoderAnswer):
            return {'region': o.region,
                    'city': o.city,
                    'street': o.street,
                    'house_number': o.house_number,
                    'lat': o.lat,
                    'lon': o.lon,
                    'additional_information': o.additional_information,
                    'organizations': o.organizations}
        return o
