from pprint import pprint
import os
from pathlib import Path
from py_uconnect import brands, Client


def load_env(path: Path) -> None:
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


class Fiat:
    def __init__(self, env_path: Path | str | None = None):
        if env_path is None:
            env_path = Path(__file__).resolve().parents[1] / ".env"

        load_env(Path(env_path))

        self.email = os.getenv("FIAT_EMAIL")
        self.password = os.getenv("FIAT_PASSWORD")
        self.pin = os.getenv("FIAT_PIN")
        self.vin = os.getenv("FIAT_VIN")

        if not all([self.email, self.password, self.pin, self.vin]):
            raise SystemExit(
                "Missing required environment variables. Create a .env file from .env.example "
                "and set FIAT_EMAIL, FIAT_PASSWORD, FIAT_PIN, FIAT_VIN."
            )

        self.client = Client(email=self.email, password=self.password, pin=self.pin, brand=brands.FIAT_EU)
        self.vehicle = None

    def update(self) -> dict:
        print("Authentifizierung bei Stellantis...")
        self.client.refresh()

        vehicles = self.client.get_vehicles()
        if self.vin not in vehicles:
            raise ValueError(f"Fahrzeug mit VIN {self.vin} nicht gefunden")

        self.vehicle = vehicles[self.vin]
        print(f"Abfrage für Fahrzeug: {self.vehicle.model}")

        print("\nFahrzeuginformationen:")
        pprint(self.vehicle.__dict__)

        soc = self.vehicle.state_of_charge
        remaining_range = self.vehicle.range_total or self.vehicle.distance_to_empty
        charging_status = (
            "CHARGING" if self.vehicle.charging else "PLUGGED_IN" if self.vehicle.plugged_in else "DISCONNECTED"
        )
        nickname = getattr(self.vehicle, "nickname", None) or getattr(self.vehicle, "name", None) or self.vehicle.model
        odometer = (
            getattr(self.vehicle, "odometer", None)
            or getattr(self.vehicle, "odometer_value", None)
            or getattr(self.vehicle, "distance_total", None)
            or getattr(self.vehicle, "mileage", None)
        )
        odometer_unit = (
            getattr(self.vehicle, "odometer_unit", None)
            or getattr(self.vehicle, "distance_unit", None)
            or getattr(self.vehicle, "mileage_unit", None)
            or "km"
        )

        charging_level_preference = getattr(self.vehicle, "charging_level_preference", None) or getattr(self.vehicle, "preferred_charging_level", None) or "unknown"
        charging_level = getattr(self.vehicle, "charging_level", None) or getattr(self.vehicle, "current_charging_level", None) or "unknown"

        result = {
            "vehicle": self.vehicle,
            "state_of_charge": soc,
            "remaining_range": remaining_range,
            "charging_status": charging_status,
            "charging_level_preference": charging_level_preference,
            "charging_level": charging_level,
            "nickname": nickname,
            "odometer": odometer,
            "odometer_unit": odometer_unit,
        }

        print("\n" + "=" * 25)
        print(f"LADESTAND:  {soc}%")
        print(f"REICHWEITE: {remaining_range} km")
        print(f"STATUS:     {charging_status}")
        print("=" * 25)

        return result


def main():
    fiat = Fiat()
    fiat.update()


if __name__ == "__main__":
    main()
