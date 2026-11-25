"""Read the island census data used for the regional progress breakdown."""
import csv
import os

CSV_FILE = os.path.join(os.path.dirname(__file__), "islands.csv")

with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    list_of_islands = list(reader)


def inhabited_islands(islands_list):
    """Return islands with a positive population in the 2021 census column."""
    result = []
    for island in islands_list:
        try:
            if int(island.get(" Population", 0)) > 0:
                result.append(island)
        except (TypeError, ValueError):
            print(f"Invalid population value for island: {island}")
    return result


inhabited_islands = inhabited_islands(list_of_islands)


def list_of_names(islands):
    """Return island names with ', Greece' appended."""
    return [row["Island"] + ", Greece" for row in islands]


names = list_of_names(inhabited_islands)
