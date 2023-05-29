from datetime import datetime
import re
import aiohttp
from bs4 import BeautifulSoup

from lectio.absence import Absence
from lectio.messages import FilterEnum, MessageInfo
from lectio.schedule import Schedule
import urllib.parse

import string


class User:
    USER_FROM_TEXT_REGEX = re.compile(
        r"^(?P<name>.*?)\s+\((?P<grade>.+?)\s+(?P<idfk>\w+)\)$"
    )

    __slots__ = (
        "school_district",
        "display_name",
        "class_name",
        "username",
        "student_id",
        "avatar_url",
        "_session",
        "_prev_url",
        "_cached_users",
    )

    def __init__(self, username: str, school_district: int) -> None:
        self.school_district: int = school_district
        self.display_name: str = ""
        self.class_name: str = ""
        self.username: str = username
        self.student_id: int = -1
        self.avatar_url: str = ""

        self._session: aiohttp.ClientSession = None
        self._prev_url: str = ""

        self._cached_users: dict = {}

    @property
    def url(self) -> str:
        return f"https://www.lectio.dk/lectio/{self.school_district}"

    # def __repr__(self) -> str:
    #     return f"Eleven {self.display_name}, {self.class_name} (ID: {self.student_id})"

    @property
    def __dict__(self):
        return {
            "username": self.username,
            "display_name": self.display_name,
            "student_id": self.student_id,
            "class_name": self.class_name,
            "school_district": self.school_district,
            "avatar_url": self.avatar_url,
        }

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def _request_to_soup(self, request_url: str) -> BeautifulSoup:
        response = await self._session.get(request_url)
        content = await response.text()
        return BeautifulSoup(content, features="html5lib")

    def update_prev_url(self, request_url) -> None:
        self._prev_url = urllib.parse.quote_plus(request_url[len(self.url) + 1 :])

    async def schedule(self, _week: int = 0) -> Schedule:
        if not _week:
            week = datetime.now().strftime("%W%Y")
        else:
            week = f"{_week}{datetime.now().strftime('%Y')}"

        request_url = (
            f"{self.url}/SkemaNy.aspx?type=elev&elevid={self.student_id}&week={week}"
        )
        soup = await self._request_to_soup(request_url)
        schedule = Schedule()
        pieces = soup.find(
            "table", id="s_m_Content_Content_SkemaNyMedNavigation_skema_skematabel"
        ).findAll("a", attrs={"class": "s2brik"})

        for piece in pieces:
            schedule.parse_lesson(piece)

        self.update_prev_url(request_url)
        return schedule

    async def absence(self) -> Absence:
        request_url = f"{self.url}/subnav/fravaerelev.aspx?elevid={self.student_id}&prevurl={self._prev_url}"
        soup = await self._request_to_soup(request_url)
        teams = soup.find(
            "table", id="s_m_Content_Content_SFTabStudentAbsenceDataTable"
        ).findAll("tr")

        absence = Absence()

        for team in teams[
            3:
        ]:  # the first 3 items, are just headers for the table on lectio.
            absence.parse(team)

        self.update_prev_url(request_url)
        return absence

    async def messages(
        self, filter: FilterEnum = FilterEnum.NEWEST
    ) -> list[MessageInfo]:
        request_url = f"{self.url}/beskeder2.aspx?type=&elevid={self.student_id}&selectedfolderid={filter.value}"
        soup = await self._request_to_soup(request_url)
        message_table = soup.find(
            "table", id="s_m_Content_Content_threadGV_ctl00"
        ).findAll("tr")
        messages: list[MessageInfo] = []

        for message in message_table:
            if not (fields := message.findAll("td")):
                continue

            title = fields[3].get_text().strip()
            creator = fields[5].find("span")["title"].split(" (")[0]
            if creator in self._cached_users:
                creator = {creator: self._cached_users[creator]}

            timestamp = fields[7].get_text()
            to = ", ".join(fields[6].find("span")["title"].split("\n"))
            id = (
                fields[3]
                .find("a")["onclick"]
                .strip("__doPostBack('__Page','$LB2$_MC_$_")
                .strip("'); return false;")
            )

            messages.append(
                MessageInfo(
                    title=title,
                    creator=creator,
                    timestamp=timestamp,
                    to=to,
                    threadid=id,
                )
            )

        self.update_prev_url(request_url)
        return messages

    # async def _cache_all_users(self):
    #     # maybe add a database?
    #     for letter in list(string.ascii_uppercase) + ["Æ", "Ø", "Å"]:
    #         url = f"{self.url}/FindSkema.aspx?type=elev&forbogstav={letter}"
    #         soup = await self._request_to_soup(url)
    #         users = soup.find("div", id="m_Content_listecontainer").findAll("li")

    #         for user in users:
    #             u = user.find("a")

    #             if not (user := User.USER_FROM_TEXT_REGEX.match(u.text)):
    #                 continue

    #             grade = user.group("grade")
    #             username = user.group("name")
    #             self._cached_users[username] = {
    #                 "id": u.attrs["data-lectiocontextcard"],
    #                 "grade": grade,
    #             }
