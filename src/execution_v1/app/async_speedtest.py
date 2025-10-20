import asyncio
import logging
import math
import re
import time
from statistics import mean
from typing import Any, Dict, List, Optional

import aiohttp

from core.config import settings

logger = logging.getLogger(__name__)


class AsyncSpeedtest:
    CONFIG_URL = "https://www.speedtest.net/speedtest-config.php"
    SERVER_LIST_URL = "https://www.speedtest.net/speedtest-servers-static.php"

    # Use configurable values from settings
    DOWNLOAD_CHUNK_SIZE = settings.speedtest.download_chunk_size
    UPLOAD_CHUNK_SIZE = settings.speedtest.upload_chunk_size
    TEST_COUNT = settings.speedtest.test_count
    LATENCY_TEST_COUNT = settings.speedtest.latency_test_count
    TIMEOUT = settings.speedtest.timeout

    def __init__(
        self, source_address: Optional[str] = None, debug: bool = False
    ) -> None:
        self.best_server: Optional[Dict[str, Any]] = None
        self.source_address: Optional[str] = source_address
        self.debug: bool = debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.download: float = 0.0
        self.upload: float = 0.0
        self.ping: float = 0.0
        self.public_ip: str = ""
        self.isp: str = ""

    async def fetch(
        self,
        session: aiohttp.ClientSession,
        url: str,
        method: str = "GET",
        data: Optional[bytes] = None,
    ) -> str:
        async with session.request(method, url, data=data) as response:
            result: str = await response.text()
            if self.debug:
                logging.debug(f"Fetched {url} with method {method}")
            return result

    async def get_config(self) -> bool:
        async with aiohttp.ClientSession(
            connector=self._get_connector()
        ) as session:
            try:
                response: str = await self.fetch(session, self.CONFIG_URL)
                config = re.search(
                    r'<client ip="(.*?)" lat="(.*?)" lon="(.*?)" isp="(.*?)"',
                    response,
                )
                if config:
                    self.public_ip = config.group(1)
                    self.isp = config.group(4)
                    if self.debug:
                        logging.debug(
                            f"Public IP: {self.public_ip}, ISP: {self.isp}"
                        )
                    return True
                return False
            except Exception as e:
                logging.error(f"Failed to get config: {e}")
                return False

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        R: float = 6371  # Radius of the earth in km
        dlat: float = math.radians(lat2 - lat1)
        dlon: float = math.radians(lon2 - lon1)
        a: float = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c: float = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance: float = R * c
        if self.debug:
            logging.debug(f"Calculated distance: {distance} km")
        return distance

    async def get_best_server(self) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession(
            connector=self._get_connector()
        ) as session:
            response: str = await self.fetch(session, self.SERVER_LIST_URL)

        servers: List[Dict[str, Any]] = []
        for line in response.splitlines():
            match = re.search(
                r'<server url="(http://.*?)" lat="(.*?)" lon="(.*?)" name="(.*?)" country="(.*?)" id="(.*?)"',
                line,
            )
            if match:
                servers.append(
                    {
                        "url": match.group(1),
                        "lat": float(match.group(2)),
                        "lon": float(match.group(3)),
                        "name": match.group(4),
                        "country": match.group(5),
                        "id": match.group(6),
                    }
                )

        best: Optional[Dict[str, Any]] = None
        best_latency: float = float("inf")
        user_lat: float = servers[0]["lat"]
        user_lon: float = servers[0]["lon"]

        async with aiohttp.ClientSession(
            connector=self._get_connector()
        ) as session:
            for server in servers:
                distance: float = self.calculate_distance(
                    user_lat, user_lon, server["lat"], server["lon"]
                )
                if distance > 500:
                    continue

                latencies: List[float] = []
                for _ in range(self.LATENCY_TEST_COUNT):
                    try:
                        start: float = time.time()
                        await self.fetch(session, server["url"] + "?latency")
                        latency: float = (
                            time.time() - start
                        ) * 1000  # Convert to milliseconds
                        latencies.append(latency)
                    except Exception:
                        latencies.append(float("inf"))

                avg_latency: float = mean(latencies)
                if avg_latency < best_latency:
                    best_latency = avg_latency
                    best = server

        self.best_server = best
        if self.debug:
            logging.debug(f"Best server: {best}")
        return best

    async def measure_latency(self) -> None:
        latencies: List[float] = []
        async with aiohttp.ClientSession(
            connector=self._get_connector()
        ) as session:
            for _ in range(self.LATENCY_TEST_COUNT):
                try:
                    start: float = time.time()
                    await self.fetch(
                        session, self.best_server["url"] + "?latency"
                    )
                    latency: float = (
                        time.time() - start
                    ) * 1000  # Convert to milliseconds
                    latencies.append(latency)
                except Exception as e:
                    logging.debug(f"Latency test failed: {e}")
                    latencies.append(float("inf"))
        self.ping = mean(latencies) if latencies else float("inf")
        if self.debug:
            logging.debug(f"Ping latency: {self.ping:.2f} ms")

    async def measure_download_speed(self) -> None:
        total_data: int = 0
        start_time: float = time.time()
        url = self.best_server["url"]

        async def download_chunk(session: aiohttp.ClientSession, url: str):
            nonlocal total_data
            try:
                async with session.get(url, timeout=self.TIMEOUT) as response:
                    while True:
                        chunk = await response.content.read(
                            self.DOWNLOAD_CHUNK_SIZE
                        )
                        if (
                            not chunk
                            or time.time() - start_time
                            > settings.speedtest.max_download_time
                        ):
                            break
                        total_data += len(chunk)
                        logging.debug(
                            f"Downloaded chunk: {len(chunk)} bytes, Total: {total_data} bytes"
                        )
            except Exception as e:
                logging.debug(f"Download chunk failed: {e}")

        async with aiohttp.ClientSession(
            connector=self._get_connector()
        ) as session:
            tasks = [
                download_chunk(session, url + "/random4000x4000.jpg")
                for _ in range(self.TEST_COUNT)
            ]
            await asyncio.gather(*tasks)

        elapsed_time: float = time.time() - start_time
        self.download = total_data / elapsed_time if elapsed_time else 0.0
        logging.debug(
            f"Total downloaded data: {total_data} bytes in {elapsed_time:.2f} seconds"
        )
        logging.debug(f"Download speed: {self.download:.2f} Bps")

    async def measure_upload_speed(self) -> None:
        total_data: int = 0
        data: bytes = b"0" * self.UPLOAD_CHUNK_SIZE
        url = self.best_server["url"]

        async with aiohttp.ClientSession(
            connector=self._get_connector()
        ) as session:
            start_time: float = time.time()
            try:
                while (
                    time.time() - start_time
                    < settings.speedtest.max_upload_time
                ):
                    async with session.post(
                        url + "/upload", data=data, timeout=self.TIMEOUT
                    ) as response:
                        await response.read()
                    total_data += self.UPLOAD_CHUNK_SIZE
                    logging.debug(
                        f"Uploaded chunk: {self.UPLOAD_CHUNK_SIZE} bytes, Total: {total_data} bytes"
                    )
            except Exception as e:
                logging.debug(f"Upload speed test {url} failed: {e}")

        elapsed_time: float = time.time() - start_time
        self.upload = total_data / elapsed_time if elapsed_time else 0.0
        logging.debug(
            f"Total uploaded data: {total_data} bytes in {elapsed_time:.2f} seconds"
        )
        logging.debug(f"Upload speed: {self.upload:.2f} Bps")

    def _get_connector(self) -> Optional[aiohttp.TCPConnector]:
        return (
            aiohttp.TCPConnector(local_addr=(self.source_address, 0))
            if self.source_address
            else None
        )
