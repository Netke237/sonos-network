import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.modules.sonos_telemetry import FakeSonosAdapter

async def test():
    fake_adapter = FakeSonosAdapter(probe_interval_sec=0.0)
    fake_adapter.inject_ghost_group(
        rincon_uuid="RINCON_B8E937E6098401400",
        corrupted_group_id="RINCON_347E5C3828B001400:77",
        has_vanished_devices=True,
    )
    app = create_app(database_url="sqlite+aiosqlite:///:memory:", sonos_adapter=fake_adapter)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            poll_resp = await client.post("/api/actions/poll-now")
            poll_json = poll_resp.json()
            print("POLL BATCH:", poll_json["batch_id"])

            telem_resp = await client.get("/api/sonos/telemetry")
            telem_json = telem_resp.json()
            print("TELEM BATCH:", telem_json["batch_id"])
            for p in telem_json["players"]:
                if p["rincon_uuid"] == "RINCON_B8E937E6098401400":
                    print("TELEM PLAYER ESSTISCH:", p["group_id"], p["is_ghost_group"])

            print("ADAPTER ESSTISCH AFTER TELEM:", fake_adapter._state_by_uuid["RINCON_B8E937E6098401400"]["group_id"])

asyncio.run(test())
