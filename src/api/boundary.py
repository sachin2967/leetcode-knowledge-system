"""Separate the owner-only local workflow from an isolated fixture-only demo."""

import hmac
import json
import os


class ServingBoundary:
    def __init__(self, app, serving_mode: str):
        self.app = app
        self.serving_mode = serving_mode

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def reject(status, detail):
            await send(
                {
                    "type": "http.response.start",
                    "status": status,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": json.dumps({"detail": detail}).encode(),
                }
            )

        if self.serving_mode == "demo_only" and scope["path"].startswith("/personal/"):
            return await reject(
                404, "Personal code endpoints are disabled in demo-only mode."
            )
        key = os.getenv("LKS_API_KEY", "")
        if scope["path"] != "/live":
            if os.getenv("APP_ENV", "local") == "production" and (
                self.serving_mode != "demo_only" or len(key) < 32
            ):
                return await reject(
                    503,
                    "Production requires demo_only mode and a 32-character operator API key.",
                )
            if scope["path"] not in {"/health", "/ready"} and key:
                supplied = dict(scope.get("headers", [])).get(b"x-api-key", b"")
                if not hmac.compare_digest(supplied, key.encode()):
                    return await reject(401, "Valid X-API-Key required.")
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 64 * 1024:
                return await reject(413, "Request body exceeds 64 KiB.")
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        return await self.app(scope, bounded_receive, send)
