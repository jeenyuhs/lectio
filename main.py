import asyncio

import os
from lectio.lectio import Lectio

if not os.path.exists("config.py"):
    print("renaming config file")
    os.rename("config.sample.py", "config.py")
    print("please edit the config before running")
    exit(0)

from config import config


async def main() -> None:
    user = await Lectio.login(
        config["brugernavn"], config["kodeord"], config["skolekode"]
    )
    schedule = await user.schedule()
    print(schedule.get("friday"))

    absence = await user.absence()
    await user.session.close()


if __name__ == "__main__":
    asyncio.run(main())
