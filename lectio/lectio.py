from datetime import datetime
import pprint
import re

import aiohttp
from bs4 import BeautifulSoup

from lectio.absence import Absence
from lectio.schedule import Schedule
from lectio.user import User


class Lectio:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.user: User
        self._prev_url: str = ""

    @property
    def url(self):
        return f"https://www.lectio.dk/lectio/{self.user.school_district}/"

    @classmethod
    async def login(
        cls, username: str, password: str, school_district: int
    ) -> "Lectio":
        c = cls()
        c.user = User(username, school_district)

        raw = await c.session.get(
            c.url + "/login.aspx?prevurl=forside.aspx%3FLI?prevurl=forside.aspx%3fLI"
        )
        soup = BeautifulSoup(await raw.text(), features="html5lib")
        payload = {
            "__EVENTTARGET": "m$Content$submitbtn2",
            "__VIEWSTATEX": c._get_value_from_id(soup, "__VIEWSTATEX"),
            "__EVENTVALIDATION": c._get_value_from_id(soup, "__EVENTVALIDATION"),
            "__EVENTARGUMENT": "",
            "m$Content$username": username,
            "m$Content$password": password,
        }

        response = await c.session.post(
            c.url
            + "/login.aspx?prevurl=forside.aspx%3fLI%3fprevurl%3dforside.aspx%3fLI",
            data=payload,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 OPR/91.0.4516.72",
                "content-type": "application/x-www-form-urlencoded",
            },
        )
        response_soup = BeautifulSoup(await response.text(), features="html5lib")
        c.user.student_id = int(
            response_soup.find(id="s_m_masterleftDiv")
            .findAll()[-1]["href"]  # type: ignore
            .split("elevid=")[1]
        )
        _user_info = response_soup.find(
            id="s_m_HeaderContent_MainTitle"
        ).string.strip()  # type: ignore

        if user_info := re.compile(r"Eleven (.*), (\w*)").match(_user_info):
            c.user.display_name = user_info.group(1)
            c.user.class_name = user_info.group(2)
        else:
            print("failed to match any patterns in user info.")
            exit(1)

        c.user.avatar_url = (
            "https://www.lectio.dk/lectio/"
            + response_soup.find(id="s_m_HeaderContent_picctrlthumbimage")["src"][  # type: ignore
                8:
            ]
            + "&fullsize=1"
        )

        return c

    async def _request_to_soup(self, request_url: str) -> BeautifulSoup:
        response = await self.session.get(request_url)
        content = await response.text()
        return BeautifulSoup(content, features="html5lib")

    def _get_value_from_id(self, soup: BeautifulSoup, id: str) -> str:
        return soup.find(id=id)["value"]  # type: ignore

    async def schedule(self, _week: int = 0) -> Schedule:
        if not _week:
            week = datetime.now().strftime("%W%Y")
        else:
            week = f"{_week}{datetime.now().strftime('%Y')}"

        request_url = f"{self.url}/SkemaNy.aspx?type=elev&elevid={self.user.student_id}&week={week}"
        soup = await self._request_to_soup(request_url)
        schedule = Schedule()
        pieces = soup.find(
            "table", id="s_m_Content_Content_SkemaNyMedNavigation_skema_skematabel"
        ).findAll("a", attrs={"class": "s2brik"})

        for piece in pieces:
            schedule.parse_lesson(piece)

        self._prev_url = request_url[: len(self.url) - 1]
        return schedule

    async def absence(self) -> Absence:
        request_url = f"{self.url}/subnav/fravaerelev.aspx?elevid={self.user.student_id}&prevurl={self._prev_url}"
        soup = await self._request_to_soup(request_url)
        teams = soup.find(
            "table", id="s_m_Content_Content_SFTabStudentAbsenceDataTable"
        ).findAll("tr")

        absence = Absence()

        for team in teams[
            3:
        ]:  # the first 3 items, are just headers for the table on lectio.
            absence.parse(team)

        self._prev_url = request_url
        return absence
