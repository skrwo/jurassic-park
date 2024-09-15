"""
We collect the dataset containing the information about the dinosaurs (A - Z) from the National History Museum's API.
"""
from requests import Session
from requests.exceptions import HTTPError
from csv import DictWriter

# Filename of the CSV sheet
sheet_filename: str = "data/data.csv"

# Determines whether list of dinosaurs will include the full information (False)
# (and we won't fetch each dino's info separately), or just names (True).
# Default (False) means it will.
use_short_dino_list: bool = False

session = Session()

def get_dinosaurs_list(short: bool) -> list[dict]:
    """Fetches dinosaurs list from the National History Museum's API"""
    # 'short' param adds ?view=genus query which makes the response much smaller
    # (we must fetch each dino's details then, but we get the list a lot faster)
    # may be very slow without the 'short' param.
    parameters = {"view": "genus"} if short else None
    response = session.get("https://www.nhm.ac.uk/api/dino-directory-api/dinosaurs", params=parameters)
    response.raise_for_status()

    return response.json()

# not needed if ?view=genus in get_dinosaurs_list() is not used
# may be less reliable due to random 504 responses
def get_dinosaur_details(genus: str) -> dict[str, object]:
    """Fetches dinosaur's details from the National History Museum's API using its genus"""
    response = session.get(f"https://www.nhm.ac.uk/api/dino-directory-api/dinosaurs/{genus}")
    response.raise_for_status()

    return response.json()

with open(sheet_filename, "w", encoding="utf-8") as file:
    fields = ("name", "diet", "period", "lived_in", "type", "length", "taxonomy", "named_by", "species", "link")

    sheetwriter = DictWriter(file, fields, lineterminator="\n")
    sheetwriter.writeheader()

    print("Getting dinosaurs list...")
    dinosaurs_list = get_dinosaurs_list(use_short_dino_list)

    for dino in dinosaurs_list:

        genus = dino["genus"].lower()

        print(f"Getting {genus} details...")
        try:
            details = dino if not use_short_dino_list else get_dinosaur_details(genus)
        except HTTPError:
            print(f"Skipped {genus} due to HTTP error...")
            continue

        period = details["period"]
        period_years = tuple(
            map(lambda x: int(x) if x else None,
                (details["myaFrom"], details["myaTo"]))
        )
        period_years_text = (
            f"{period_years[0]}-{period_years[1]} million years ago"
        ) if (period_years[0] or period_years[1]) else ""

        row = {
            "name": genus,
            "diet": details["dietTypeName"],
            "period":
                f'{period["period"] if period else ""} {period_years_text}'.strip(),
            "lived_in": details["countries"][0]["country"],
            "type": details["bodyShape"]["bodyShape"].lower(),
            "length": f'{details["lengthFrom"]}m',
            "taxonomy": details["taxTaxon"]["taxonomyCSV"].replace(",", " "),
            "named_by": f'{details["genusNamedBy"]} ({details["genusYear"]})',
            "species": details["species"],
            "link": f'https://www.nhm.ac.uk/discover/dino-directory/{genus}.html'
        }
        try:
            sheetwriter.writerow(row)
        except Exception as e:
            print(f"! ERROR on {genus}: {e!r}")
            print("! Row data:", row)