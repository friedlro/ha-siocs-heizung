"""SIOCS-Webportal -> kleine REST-Schnittstelle fuer Home Assistant.

GET  /state                      aktuelle Werte als JSON
POST /mode   {"mode": "auto"}    auto|off|setback|heat|schedule|party
POST /offset {"value": 0.5}      Raumtemperatur-Korrektur in K
"""
import asyncio
import json
import re
import time

from aiohttp import web
from playwright.async_api import async_playwright

opts = json.load(open("/data/options.json"))
URL = opts["url"].rstrip("/") + "/"
USER = opts["username"]
PASSWORD = opts["password"]
POLL = int(opts.get("poll_seconds", 60))

MODES = {"auto": "0", "off": "1", "setback": "2", "heat": "3", "schedule": "4", "party": "5"}
MODE_BY_VALUE = {v: k for k, v in MODES.items()}

LABELS = {
    "Leistung": "power_kw",
    "Spreizung": "spread_k",
    "Wärmemenge": "energy_kwh",
    "Volumen": "volume_m3",
    "für Regelung": "outdoor_avg_control",
    "für Abschaltung": "outdoor_avg_shutdown",
    "Raumsoll.:": "room_setpoint",
}

# Die Element-IDs des Wt-Portals aendern sich je Sitzung. Werte werden deshalb ueber
# die Beschriftung in derselben Zeile gefunden, die Bedienelemente per data-ha markiert.
EXTRACT_JS = """
(labels) => {
  const parse = t => {
    const m = t.match(/^(-?\\d+(?:[.,]\\d+)?)\\s*(°C|kW|kWh|m3|l\\/h|%)?$/);
    return m ? parseFloat(m[1].replace(',', '.')) : null;
  };
  const leaves = [...document.querySelectorAll('body *')]
    .filter(e => e.children.length === 0 && e.textContent.trim()
                 && e.getBoundingClientRect().width > 0)
    .map(e => { const r = e.getBoundingClientRect();
                return {e, t: e.textContent.trim(), x: r.x, y: r.y, n: null}; });
  leaves.forEach(l => l.n = parse(l.t));
  const out = {};
  for (const [label, key] of Object.entries(labels)) {
    const lab = leaves.find(l => l.t === label);
    if (!lab) continue;
    let best = null, bd = 1e9;
    for (const l of leaves) {
      if (l.n === null || Math.abs(l.y - lab.y) > 6) continue;
      const d = Math.abs(l.x - lab.x);
      if (d < bd) { bd = d; best = l; }
    }
    if (best) out[key] = best.n;
  }
  const ref = leaves.find(l => l.t === 'Raumsoll.:');
  if (ref) {
    const temps = leaves.filter(l => l.t.endsWith('°C') && l.n !== null && l.x > ref.x - 40 && l.x < ref.x + 200
                                     && l.y > ref.y + 20 && l.y < ref.y + 200)
                        .sort((a, b) => a.y - b.y);
    if (temps.length >= 2) {
      temps[0].e.setAttribute('data-ha', 'offset'); out.offset = temps[0].n;
      temps[1].e.setAttribute('data-ha', 'room_temp'); out.room_temp = temps[1].n;
      const modeEl = leaves.filter(l => l.x > ref.x - 40 && l.x < ref.x + 200 && l.y > temps[1].y + 40
                                        && l.y < temps[1].y + 250 && l.t.length > 2)
                           .sort((a, b) => a.y - b.y)[0];
      if (modeEl) { modeEl.e.setAttribute('data-ha', 'mode'); out.mode_status = modeEl.t; }
    }
  }
  return out;
}
"""

state = {"mode_selected": None, "updated": None, "ok": False}
lock = asyncio.Lock()
page = None


async def login():
    await page.goto(URL, wait_until="load")
    await asyncio.sleep(3)  # Wt-JavaScript muss erst Handler anhaengen, sonst geht der Klick ins Leere
    # Die Felder haben keinen placeholder: erstes Textfeld, Passwortfeld, Button "Anmelden".
    user_box = page.locator("input[type=text]:visible").first
    pass_field = page.locator("input[type=password]:visible")
    if await pass_field.count():
        pw_box = pass_field.first
        for _ in range(3):
            # Wie ein Mensch tippen, damit Wt die Tastatur-Ereignisse mitbekommt.
            await user_box.click()
            await user_box.fill("")
            await user_box.press_sequentially(USER, delay=40)
            await pw_box.click()
            await pw_box.fill("")
            await pw_box.press_sequentially(PASSWORD, delay=40)
            await page.locator("button:has-text('Anmelden')").first.click()
            await asyncio.sleep(6)
            if not await pass_field.count():
                break
            print("login: Formular noch sichtbar, neuer Versuch", flush=True)
    # Im DOM liegen versteckte Vorlagen mit demselben Text - auf ein sichtbares Element warten.
    try:
        await page.wait_for_function(
            "() => [...document.querySelectorAll('body *')].some(e => e.children.length === 0"
            " && e.textContent.trim() === 'Raumsoll.:' && e.getBoundingClientRect().width > 0)",
            timeout=60000,
        )
    except Exception:  # noqa: BLE001
        text = await page.evaluate("() => document.body.innerText.slice(0, 1500)")
        print("nach login:", page.url, repr(text), flush=True)
        raise


async def click_btn(name):
    await page.locator("button", has_text=re.compile(rf"^\s*{name}\s*$", re.I)).last.click()


async def read_mode_selected():
    """Oeffnet den Auswahl-Dialog, liest die gewaehlte Betriebsart, bricht ab."""
    await page.locator("[data-ha=mode]").click()
    sel = page.locator("select:visible").last
    await sel.wait_for(state="visible", timeout=10000)
    value = await sel.evaluate("s => s.value")
    await click_btn("abbrechen")
    await page.locator("select:visible").last.wait_for(state="hidden", timeout=10000)
    state["mode_selected"] = MODE_BY_VALUE.get(value, value)


async def poll_once(read_mode=False):
    data = {}
    for _ in range(10):  # das Portal baut die Seite schrittweise auf
        data = await page.evaluate(EXTRACT_JS, LABELS)
        if "room_temp" in data:
            break
        await asyncio.sleep(1)
    if "room_temp" not in data:
        print("auslese unvollstaendig:", data, flush=True)
        raise RuntimeError("Werte nicht gefunden - Sitzung abgelaufen?")
    state.update(data)
    state["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    state["ok"] = True
    if read_mode:
        await read_mode_selected()


async def poller():
    last_mode_read = 0
    last_reload = 0  # erster Durchlauf meldet sich an
    while True:
        async with lock:
            try:
                if time.time() - last_reload > 1800:
                    await login()
                    last_reload = time.time()
                due = time.time() - last_mode_read > 900
                await poll_once(read_mode=due)
                if due:
                    last_mode_read = time.time()
            except Exception as exc:  # noqa: BLE001
                state["ok"] = False
                print("poll fehler:", exc, flush=True)
                try:
                    await login()
                    last_reload = time.time()
                except Exception as exc2:  # noqa: BLE001
                    print("login fehler:", exc2, flush=True)
        await asyncio.sleep(POLL)


async def set_mode(mode):
    await page.locator("[data-ha=mode]").click()
    sel = page.locator("select:visible").last
    await sel.wait_for(state="visible", timeout=10000)
    await sel.select_option(value=MODES[mode])
    await click_btn("ok")
    await page.locator("select:visible").last.wait_for(state="hidden", timeout=10000)
    state["mode_selected"] = mode


async def set_offset(value):
    # Der Klick links im Korrektur-Feld oeffnet den Zahlen-Dialog (am Portal getestet).
    await page.locator("[data-ha=offset]").click(position={"x": 27, "y": 13})
    box = page.locator("input.Wt-spinbox:visible").last
    await box.wait_for(state="visible", timeout=10000)
    await box.fill(f"{value:.1f}")
    await box.press("Tab")
    await click_btn("ok")
    await page.locator("input.Wt-spinbox:visible").last.wait_for(state="hidden", timeout=10000)


async def h_state(_):
    return web.json_response(state)


async def h_debug(_):
    """Zeigt, was der Browser im Container gerade sieht (zur Fehlersuche)."""
    try:
        text = await page.evaluate("() => document.body.innerText.slice(0, 1500)")
        fields = await page.evaluate(
            "() => [...document.querySelectorAll('input,button,select')].map(e => ({"
            "tag: e.tagName, type: e.type, id: e.id, name: e.name, cls: e.className.toString().slice(0, 40),"
            "ph: e.placeholder, aria: e.getAttribute('aria-label'), txt: e.textContent.trim().slice(0, 30),"
            "vis: e.getBoundingClientRect().width > 0})).slice(0, 40)"
        )
        return web.json_response({"url": page.url, "title": await page.title(), "text": text,
                                  "fields": fields})
    except Exception as exc:  # noqa: BLE001
        return web.json_response({"error": str(exc)})


async def h_mode(request):
    body = await request.json()
    mode = body.get("mode")
    if mode not in MODES:
        return web.json_response({"error": f"mode muss in {list(MODES)} liegen"}, status=400)
    async with lock:
        await set_mode(mode)
        await poll_once()
    return web.json_response(state)


async def h_offset(request):
    body = await request.json()
    value = float(body["value"])
    if not -5.0 <= value <= 5.0:
        return web.json_response({"error": "value muss zwischen -5 und 5 liegen"}, status=400)
    async with lock:
        await set_offset(value)
        await asyncio.sleep(2)
        await poll_once()
    return web.json_response(state)


async def main():
    global page
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(args=["--no-sandbox"])
    ctx = await browser.new_context(viewport={"width": 731, "height": 698}, locale="de-AT")
    page = await ctx.new_page()
    asyncio.create_task(poller())
    app = web.Application()
    app.add_routes([web.get("/state", h_state), web.get("/debug", h_debug),
                    web.post("/mode", h_mode),
                    web.post("/offset", h_offset)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 8099).start()
    await asyncio.Event().wait()


asyncio.run(main())
