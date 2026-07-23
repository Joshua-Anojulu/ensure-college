"""Stage 2 Journey map gates.

Covers the computeJourneyMapState contract table (DESIGN.md), the rendered
marker DOM (landmarks, tombstone aggregation, frontier flag, keyboard and
click-to-checklist interaction), Save-Data raster suppression on both
signal channels, and the status-select pending guard.
"""
import time

from tests.e2e.test_e2e import fill_profile_and_submit, save_first_result, signup
from tests.e2e.test_world import wait_until


def compute(page, items):
    return page.evaluate("(items) => computeJourneyMapState(items)", items)


def mk(status="interested", *, n=1, title=None, has_catalog=True, kind="scholarship"):
    return {
        "kind": kind,
        "id": n,
        "title": title or f"Synthetic {status} {n}",
        "status": status,
        "deadlineSortKey": n,
        "hasCatalog": has_catalog,
    }


class TestStateContract:
    def test_row1_empty_is_sample_at_cabin(self, page):
        state = compute(page, [])
        assert state["sample"] is True
        assert state["frontier"] == "cabin"
        assert state["markers"] == []
        assert state["tombstoneCount"] == 0

    def test_rows_2_to_6_statuses_position_markers(self, page):
        items = [
            mk("interested", n=1),
            mk("drafting", n=2),
            mk("submitted", n=3),
            mk("awarded", n=4),
            mk("rejected", n=5),
        ]
        state = compute(page, items)
        assert state["sample"] is False
        assert [m["status"] for m in state["markers"]] == [
            "interested", "drafting", "submitted", "awarded", "rejected",
        ]
        assert state["rejected"] == 1

    def test_row7_unknown_status_defaults_to_interested(self, page):
        state = compute(page, [mk("definitely-not-a-status", n=1)])
        assert state["markers"][0]["status"] == "interested"
        assert state["frontier"] == "grove"

    def test_row8_tombstones_aggregate_not_markers(self, page):
        items = [mk("interested", n=1), mk(n=2, has_catalog=False), mk(n=3, has_catalog=False)]
        state = compute(page, items)
        assert state["tombstoneCount"] == 2
        assert len(state["markers"]) == 1

    def test_row10_frontier_tracks_most_advanced_active_item(self, page):
        assert compute(page, [mk("interested")])["frontier"] == "grove"
        assert compute(page, [mk("interested", n=1), mk("drafting", n=2)])["frontier"] == "watchtower"
        assert compute(page, [mk("drafting", n=1), mk("submitted", n=2)])["frontier"] == "summit"
        assert compute(page, [mk("awarded")])["frontier"] == "summit"

    def test_row11_all_rejected_frontier_cabin_not_sample(self, page):
        state = compute(page, [mk("rejected", n=1), mk("rejected", n=2)])
        assert state["sample"] is False
        assert state["frontier"] == "cabin"
        assert state["rejected"] == 2

    def test_row12_only_tombstones_real_map_at_cabin(self, page):
        state = compute(page, [mk(n=1, has_catalog=False)])
        assert state["sample"] is False
        assert state["frontier"] == "cabin"
        assert state["tombstoneCount"] == 1
        assert state["markers"] == []

    def test_row13_markers_order_by_deadline_then_title(self, page):
        items = [
            mk("interested", n=9, title="Bravo"),
            mk("interested", n=1, title="Zulu"),
            mk("interested", n=9, title="Alpha"),
        ]
        state = compute(page, items)
        assert [m["title"] for m in state["markers"]] == ["Zulu", "Alpha", "Bravo"]


RENDER_SYNTHETIC = """
() => {
  trackerItems = [
    { scholarship_id: 11, status: "interested",
      scholarship: { name: "Synthetic Interested Award", deadline: "2027-03-01" } },
    { scholarship_id: 12, status: "submitted",
      scholarship: { name: "Synthetic Submitted Award", deadline: "2027-04-01" } },
    { scholarship_id: 13, status: "rejected",
      scholarship: { name: "Synthetic Rejected Award", deadline: "2027-05-01" } },
    { scholarship_id: 99, status: "interested" },
  ];
  renderJourneyMap();
}
"""


class TestRenderedMap:
    def test_dom_markers_landmarks_tombstone_frontier(self, page):
        page.evaluate(RENDER_SYNTHETIC)
        scene = page.locator("#journey-map .journey-map-scene")
        assert page.locator("#journey-map .journey-landmark").count() == 4
        buttons = page.locator("#journey-map button.journey-marker")
        assert buttons.count() == 3
        tombstone = page.locator("#journey-map .journey-marker-tombstone")
        assert tombstone.count() == 1
        assert tombstone.get_attribute("aria-disabled") == "true"
        assert page.evaluate(
            "document.querySelector('#journey-map .journey-marker-tombstone').tagName"
        ) == "SPAN"
        assert page.locator("#journey-map .journey-frontier").count() == 1
        assert not scene.locator(".journey-map-fog").count()
        assert not page.locator("#journey-map .journey-stop").count()

    def test_marker_click_focuses_matching_checklist(self, page):
        page.evaluate(RENDER_SYNTHETIC)
        page.evaluate(
            """() => {
              // Focus only lands inside a visible tree: reveal the saved
              // section as the real saved view does before injecting.
              document.querySelector("#saved-section").hidden = false;
              const card = document.createElement("article");
              card.dataset.savedKind = "scholarship";
              card.dataset.savedId = "11";
              const checklist = document.createElement("div");
              checklist.className = "tracker-checklist";
              card.appendChild(checklist);
              document.querySelector("#saved-container").appendChild(card);
            }"""
        )
        page.evaluate(
            "document.querySelector('#journey-map button.journey-marker[data-saved-id=\"11\"]').click()"
        )
        assert page.evaluate(
            "document.activeElement.classList.contains('tracker-checklist')"
        )

    def test_markers_are_native_buttons_in_tab_sequence(self, page):
        page.evaluate(RENDER_SYNTHETIC)
        info = page.evaluate(
            """() => {
              const m = document.querySelector('#journey-map button.journey-marker');
              return { tag: m.tagName, tabIndex: m.tabIndex, label: m.getAttribute('aria-label') };
            }"""
        )
        assert info["tag"] == "BUTTON"
        assert info["tabIndex"] == 0
        assert "checklist" in info["label"].lower()

    def test_sample_state_markers_not_interactive(self, page):
        page.evaluate("() => { trackerItems = []; renderJourneyMap(); }")
        assert page.locator("#journey-map .journey-map-sample-note").count() == 1
        assert page.locator("#journey-map button.journey-marker").count() == 0
        assert page.locator("#journey-map .journey-marker-sample").count() >= 1


class TestTerrainChannels:
    def test_terrain_raster_attaches_normally(self, page):
        page.evaluate(RENDER_SYNTHETIC)
        src = page.evaluate(
            "document.querySelector('#journey-map img.journey-terrain').getAttribute('src')"
        )
        assert "/static/img/world/journey-terrain-" in src

    def test_save_data_header_gets_vector_map_and_zero_rasters(self, browser, live_server):
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Save-Data": "on"},
        )
        context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
        page = context.new_page()
        terrain_requests = []
        page.on(
            "request",
            lambda r: terrain_requests.append(r.url) if "journey-terrain" in r.url else None,
        )
        page.goto(live_server, wait_until="networkidle")
        page.evaluate(RENDER_SYNTHETIC)
        page.wait_for_timeout(600)
        assert page.locator("#journey-map .journey-trail-vector").count() == 1
        assert page.locator("#journey-map img.journey-terrain").count() == 0
        assert terrain_requests == []
        context.close()

    def test_save_data_js_channel_gets_vector_map_and_zero_rasters(self, browser, live_server):
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.add_init_script(
            """
            window.localStorage.setItem('site_consent_v1', 'yes');
            const conn = navigator.connection || {};
            try {
              Object.defineProperty(conn, 'saveData', { get: () => true });
              if (!navigator.connection) {
                Object.defineProperty(navigator, 'connection', { get: () => conn });
              }
            } catch (e) {}
            """
        )
        page = context.new_page()
        terrain_requests = []
        page.on(
            "request",
            lambda r: terrain_requests.append(r.url) if "journey-terrain" in r.url else None,
        )
        page.goto(live_server, wait_until="networkidle")
        page.evaluate(RENDER_SYNTHETIC)
        page.wait_for_timeout(600)
        assert page.locator("#journey-map .journey-trail-vector").count() == 1
        assert terrain_requests == []
        context.close()


class TestStatusChangeIntegration:
    def test_status_select_disables_while_pending_and_moves_marker(self, page):
        signup(page)
        fill_profile_and_submit(page)
        save_first_result(page)
        page.click("#nav-plan-btn")
        page.wait_for_selector("#saved-container .match-card", timeout=15000)
        marker_before = page.evaluate(
            "document.querySelector('#journey-map button.journey-marker').getAttribute('aria-label')"
        )
        assert "interested" in marker_before
        select = page.locator("#saved-container .tracker-status").first
        # Slow the PATCH so the pending window is observable, then assert the
        # select is disabled inside it (the race guard) and re-enabled after.
        # time.sleep in the route handler, never page.* (sync-API deadlock);
        # wait_until polls from Python because the site CSP blocks
        # wait_for_function's injected poller.
        def slow_route(route):
            time.sleep(0.4)
            route.continue_()

        page.route("**/account/saved/**", slow_route)
        select.select_option("submitted")
        assert select.is_disabled()
        wait_until(
            page,
            "!document.querySelector('#saved-container .tracker-status').disabled",
        )
        page.wait_for_timeout(300)
        marker_after = page.evaluate(
            "document.querySelector('#journey-map button.journey-marker').getAttribute('aria-label')"
        )
        assert "submitted" in marker_after
