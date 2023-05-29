from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class AbsenceInfo:
    absence_pct: float = 0.0
    total_hours: float = 0.0
    missing_hours: float = 0.0

    settled_absence_pct: float = 0.0
    settled_total_hours: float = 0.0
    settled_missing_hours: float = 0.0


class Absence:
    def __init__(self):
        self.team_name: str = ""
        self.attendance: AbsenceInfo = AbsenceInfo()
        self.written: AbsenceInfo = AbsenceInfo()

        self.individual: list["Absence"] = []

    def parse(self, soup: BeautifulSoup) -> None:
        # TODO: redo
        # there is probably a way better way to do this
        data = Absence()
        fields = soup.findAll("td")

        if not fields:
            print("odd")
            return

        obj = data
        if (name := fields[0].get_text()) == "Samlet":
            obj = self

        obj.team_name = name

        obj.attendance.settled_absence_pct = float(
            fields[1].get_text().strip("%").replace(",", ".")
        )
        obj.attendance.settled_missing_hours, obj.attendance.settled_total_hours = (
            float(fields[2].get_text().split("/")[0].replace(",", ".")),
            float(fields[2].get_text().split("/")[1].replace(",", ".")),
        )

        obj.attendance.absence_pct = float(
            fields[3].get_text().strip("%").replace(",", ".")
        )
        obj.attendance.missing_hours, obj.attendance.total_hours = (
            float(fields[4].get_text().split("/")[0].replace(",", ".")),
            float(fields[4].get_text().split("/")[1].replace(",", ".")),
        )

        # it's not always that a team has written absence.
        obj.written.settled_absence_pct = (
            float(fields[5].get_text().strip("%").replace(",", "."))
            if fields[5].get_text()
            else 0.0
        )
        obj.written.settled_missing_hours, obj.written.settled_total_hours = (
            float(fields[6].get_text().split("/")[0].replace(",", "."))
            if fields[5].get_text()
            else 0.0,
            float(fields[6].get_text().split("/")[1].replace(",", "."))
            if fields[5].get_text()
            else 0.0,
        )
        obj.written.absence_pct = (
            float(fields[7].get_text().strip("%").replace(",", "."))
            if fields[5].get_text()
            else 0.0
        )
        obj.written.missing_hours, obj.written.total_hours = (
            float(fields[8].get_text().strip("%").replace(",", ".").split("/")[0])
            if fields[5].get_text()
            else 0.0,
            float(fields[8].get_text().strip("%").replace(",", ".").split("/")[1])
            if fields[5].get_text()
            else 0.0,
        )

        if data.team_name and name != "Samlet":
            self.individual.append(data)

    def get(self, team: str) -> "Absence":
        for individ in self.individual:
            if individ.team_name == team:
                return individ

        return None
