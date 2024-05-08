import aiohttp


class AsyncClient:
    def __init__(
        self,
        username: str,
        password: str,
        url: str,
        session: aiohttp.ClientSession = None,
    ):
        self._username = username
        self._password = password
        self._url = url
        self._session = session or aiohttp.ClientSession()

    async def login(self):
        async with self._session.post(
            f"{self._url}/auth/login",
            data={"email": self._username, "password": self._password},
            allow_redirects=False,
            raise_for_status=True,
        ) as r:
            if (
                "authenticated" not in r.cookies
                or r.cookies["authenticated"].value != "true"
            ):
                raise Exception("One Connect Authentication error")

    async def logout(self) -> bool:
        async with self._session.get(f"{self._url}/auth/logout", raise_for_status=True):
            return True

    async def homeworks_list(self) -> list[dict]:
        async with self._session.get(
            f"{self._url}/homeworks/list", raise_for_status=True
        ) as r:
            homeworks_list = await r.json()

        return homeworks_list

    async def homeworks(self, id: str) -> dict:
        async with self._session.get(
            f"{self._url}/homeworks/get/{id}", raise_for_status=True
        ) as r:
            homeworks = await r.json()

        return homeworks
