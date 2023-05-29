import asyncio
import re

import aiohttp
from bs4 import BeautifulSoup

from lectio.user import User


def _get_value_from_id(soup: BeautifulSoup, id: str) -> str:
    return soup.find(id=id)["value"]  # type: ignore


async def login(username: str, password: str, school_district: int) -> User | None:
    session = aiohttp.ClientSession()
    user = User(username, school_district)
    url = f"https://www.lectio.dk/lectio/{school_district}"

    raw = await session.get(
        url + "/login.aspx?prevurl=forside.aspx%3FLI?prevurl=forside.aspx%3fLI"
    )
    soup = BeautifulSoup(await raw.text(), features="html5lib")
    payload = {
        "__EVENTTARGET": "m$Content$submitbtn2",
        "__VIEWSTATEX": _get_value_from_id(soup, "__VIEWSTATEX"),
        "__EVENTVALIDATION": _get_value_from_id(soup, "__EVENTVALIDATION"),
        "__EVENTARGUMENT": "",
        "m$Content$username": username,
        "m$Content$password": password,
    }

    response = await session.post(
        url + "/login.aspx?prevurl=forside.aspx%3fLI%3fprevurl%3dforside.aspx%3fLI",
        data=payload,
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 OPR/91.0.4516.72",
            "content-type": "application/x-www-form-urlencoded",
        },
    )
    response_soup = BeautifulSoup(await response.text(), features="html5lib")
    user.student_id = int(
        response_soup.find(id="s_m_masterleftDiv")
        .findAll()[-1]["href"]  # type: ignore
        .split("elevid=")[1]
    )
    _user_info = response_soup.find(
        id="s_m_HeaderContent_MainTitle"
    ).string.strip()  # type: ignore

    if user_info := re.compile(r"Eleven (.*), (\w*)").match(_user_info):
        user.display_name = user_info.group(1)
        user.class_name = user_info.group(2)
    else:
        print(
            "failed to match any patterns in user info (most likely due to failed login)."
        )
        return

    user.avatar_url = (
        "https://www.lectio.dk/lectio/"
        + response_soup.find(id="s_m_HeaderContent_picctrlthumbimage")["src"][  # type: ignore
            8:
        ]
        + "&fullsize=1"
    )

    user._session = session

    # await user._cache_all_users()
    return user
