from bs4 import BeautifulSoup


class Absence:
    def __init__(self):
        self.team_name: str = ""
        self.attendance: float = 0.0
        self.attendance_hours: str = "0/0"

        self.settled_attendance: float = 0.0
        self.settled_attendance_hours: str = "0/0"

        self.written: float = 0.0
        self.written_hours: str = "0/0"

        self.settled_written: float = 0.0
        self.settled_written_hours: str = "0/0"

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
        obj.settled_attendance = float(
            fields[1].get_text().strip("%").replace(",", ".")
        )
        obj.settled_attendance_hours = fields[2].get_text()
        obj.attendance = float(fields[3].get_text().strip("%").replace(",", "."))
        obj.attendance_hours = fields[4].get_text()

        # it's not always, that a team has written absence.
        obj.settled_written = (
            float(fields[5].get_text().strip("%").replace(",", "."))
            if fields[5].get_text()
            else 0.0
        )
        obj.settled_written_hours = (
            fields[6].get_text() if fields[5].get_text() else "0/0"
        )
        obj.written = (
            float(fields[7].get_text().strip("%").replace(",", "."))
            if fields[5].get_text()
            else 0.0
        )
        obj.written_hours = (
            fields[8].get_text().strip("%").replace(",", ".")
            if fields[5].get_text()
            else "0/0"
        )

        if data.team_name:
            self.individual.append(data)
