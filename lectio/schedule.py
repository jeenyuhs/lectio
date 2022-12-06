from bs4 import Tag
from datetime import datetime
import re


class Lesson:
    def __init__(self):
        self.lesson_name: str = ""
        self.start_time: datetime = datetime.now()
        self.end_time: datetime = datetime.now()
        self.teachers: str | list[str] = "Ingen lærer"
        self.classroom: str | list[str] = "Intet lokale"
        self.notes: str = ""
        self.homework: str = ""
        self.team: str | list[str] = ""

    def __repr__(self) -> str:
        return (
            f"{self.team} {self.lesson_name} "
            f"({', '.join(self.teachers) if type(self.teachers) == list else self.teachers})"
            " | "
            f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        )


class Schedule:
    TIME_REGEX = re.compile(
        r"(?P<day>\d*)\/(?P<month>\d*)-(?P<year>\d{4}) (?P<from>\d{2}:\d{2}) til (?P<to>\d{2}:\d{2})"
    )

    def __init__(self):
        self.notes = ""
        self.lessons: list[Lesson] = []

    def parse_lesson(self, tag: Tag) -> None:
        lesson = Lesson()

        _data = tag.attrs["data-additionalinfo"]
        data = _data.split("\n")

        if data[0] != "Ændret!" and not Schedule.TIME_REGEX.match(data[0]):
            lesson.lesson_name = data[0]

        for d in (d_iter := iter(data)):
            if d == "":
                continue

            if m := Schedule.TIME_REGEX.match(d):
                s_hour, s_minutes = m.group("from").split(":")
                lesson.start_time = datetime(
                    year=int(m.group("year")),
                    month=int(m.group("month")),
                    day=int(m.group("day")),
                    hour=int(s_hour),
                    minute=int(s_minutes),
                )
                e_hour, e_minutes = m.group("to").split(":")
                lesson.end_time = datetime(
                    year=int(m.group("year")),
                    month=int(m.group("month")),
                    day=int(m.group("day")),
                    hour=int(e_hour),
                    minute=int(e_minutes),
                )
                continue

            if (teachers := d.startswith("Lærere")) or d.startswith("Lærer"):
                teachers = d.split(": ")
                lesson.teachers = teachers[1].split(", ") if teachers else teachers[1]
                continue

            if d.startswith("Hold"):
                team = d.split(": ")
                if len(d.split(", ")) > 1:
                    # there are multiple teams here.
                    lesson.team = team[1].split(", ")
                else:
                    lesson.team = team[1]

                continue

            if d.startswith("Lokale"):
                room = d.split(": ")

                if d.startswith("Lokaler"):
                    lesson.classroom = room[1].split(", ")
                else:
                    lesson.classroom = room[1]

                continue

            if d == "Note: ":
                p = next(d_iter)
                lesson.notes = p
                continue

        print(lesson)
        self.lessons.append(lesson)
