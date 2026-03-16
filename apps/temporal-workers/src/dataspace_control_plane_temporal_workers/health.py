from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass


@dataclass
class ProbeState:
    temporal_connected: bool = False
    registry_verified: bool = False
    workers_started: bool = False
    last_error: str | None = None

    @property
    def is_ready(self) -> bool:
        return (
            self.temporal_connected
            and self.registry_verified
            and self.workers_started
            and self.last_error is None
        )

    def liveness_payload(self) -> dict[str, object]:
        return {
            "status": "ok",
            "error": self.last_error,
        }

    def readiness_payload(self) -> dict[str, object]:
        return {
            "status": "ok" if self.is_ready else "degraded",
            "dependencies": {
                "temporal": self.temporal_connected,
                "registry": self.registry_verified,
                "workers": self.workers_started,
            },
            "error": self.last_error,
        }


def render_probe_response(path: str, state: ProbeState) -> tuple[int, dict[str, object]]:
    if path in {"/health/live", "/livez"}:
        return 200, state.liveness_payload()
    if path in {"/health/ready", "/readyz"}:
        return (200 if state.is_ready else 503), state.readiness_payload()
    if path == "/health":
        return (200 if state.is_ready else 503), state.readiness_payload()
    return 404, {"status": "not_found"}


async def start_probe_server(state: ProbeState, port: int) -> asyncio.AbstractServer:
    async def handle_client(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request_line = await reader.readline()
            parts = request_line.decode(errors="ignore").strip().split()
            path = parts[1] if len(parts) >= 2 else "/"
            while True:
                line = await reader.readline()
                if not line or line == b"\r\n":
                    break

            status_code, payload = render_probe_response(path, state)
            body = json.dumps(payload).encode()
            reason = {
                200: "OK",
                404: "Not Found",
                503: "Service Unavailable",
            }.get(status_code, "OK")
            headers = [
                f"HTTP/1.1 {status_code} {reason}",
                "Content-Type: application/json",
                f"Content-Length: {len(body)}",
                "Connection: close",
                "",
                "",
            ]
            writer.write("\r\n".join(headers).encode() + body)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    return await asyncio.start_server(handle_client, host="0.0.0.0", port=port)

