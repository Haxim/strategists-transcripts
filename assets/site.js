/* site.js
 *
 * Shared JS for postmic-rendered sites.
 * - Transcript interaction
 * - Timestamp deep-linking
 * - Clipboard helpers
 * - Sticky audio player support
 *
 * No framework. No build step. Cloudflare-safe.
 */

(function () {
  "use strict";

  /* -------------------------------------------------
     Utilities
  ------------------------------------------------- */

  function secondsToClock(s) {
    s = Math.max(0, Math.floor(Number(s) || 0));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const ss = s % 60;
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
    return `${m}:${String(ss).padStart(2, "0")}`;
  }

  function copyText(text) {
    if (navigator.clipboard?.writeText) {
      return navigator.clipboard.writeText(text).then(() => true).catch(() => false);
    }

    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      return Promise.resolve(ok);
    } catch {
      return Promise.resolve(false);
    }
  }

  function getTimeFromURL() {
    const u = new URL(window.location.href);
    if (u.searchParams.has("t")) {
      return Number(u.searchParams.get("t"));
    }
    if (u.hash.startsWith("#t=")) {
      return Number(u.hash.slice(3));
    }
    return null;
  }

  function setURLTime(t) {
    const u = new URL(window.location.href);
    u.searchParams.set("t", String(Math.max(0, Math.floor(t))));
    history.replaceState(null, "", u.toString());
  }

  /* -------------------------------------------------
     Acast postMessage helper
  ------------------------------------------------- */

  function acastPost(eventName, data) {
    const iframe = document.getElementById("acast-player");
    if (!iframe || !iframe.contentWindow) return;

    try {
      iframe.contentWindow.postMessage(
        JSON.stringify({ eventName, data: data || {} }),
        "*"
      );
    } catch {
      /* ignore */
    }
  }

  /* -------------------------------------------------
     Transcript normalization
  ------------------------------------------------- */

  function ensureTurnBlocks() {
    const list = document.getElementById("transcript-list");
    if (!list) return;

    // Already in new format
    if (list.querySelector(".turn")) return;

    const paras = Array.from(list.querySelectorAll("p[data-start]"));
    if (!paras.length) return;

    for (const p of paras) {
      const start = Number(p.getAttribute("data-start") || 0);
      const speaker = p.getAttribute("data-speaker") || "Speaker";

      const turn = document.createElement("div");
      turn.className = "turn";
      turn.dataset.start = start;

      const who = document.createElement("div");
      who.className = "who";

      const spk = document.createElement("div");
      spk.className = "spk";
      spk.textContent = speaker;

      const ts = document.createElement("span");
      ts.className = "ts";
      ts.textContent = secondsToClock(start);

      who.appendChild(spk);
      who.appendChild(ts);

      const said = document.createElement("div");
      said.className = "said";
      said.textContent = p.textContent || "";

      turn.appendChild(who);
      turn.appendChild(said);

      p.replaceWith(turn);
    }
  }

  /* -------------------------------------------------
     Transcript interaction
  ------------------------------------------------- */

  function enableTranscriptInteraction() {
    const list = document.getElementById("transcript-list");
    if (!list) return;

    let selectedStart = null;

    function activateTurn(turn) {
      list.querySelectorAll(".turn.active").forEach(el => el.classList.remove("active"));
      turn.classList.add("active");

      const start = Number(turn.dataset.start || 0);
      selectedStart = start;

      setURLTime(start);
      acastPost("postmessage:do:seek", { position: start });
      acastPost("postmessage:do:play");
    }

    list.addEventListener("click", (e) => {
      const turn = e.target.closest(".turn");
      if (!turn) return;
      activateTurn(turn);
    });

    // Deep-link on load
    const t = getTimeFromURL();
    if (t != null && !Number.isNaN(t)) {
      const turns = Array.from(list.querySelectorAll(".turn[data-start]"));
      let best = null;
      let bestDist = Infinity;

      for (const el of turns) {
        const s = Number(el.dataset.start || 0);
        const d = Math.abs(s - t);
        if (d < bestDist) {
          bestDist = d;
          best = el;
        }
      }

      if (best) {
        best.classList.add("active");
        selectedStart = Number(best.dataset.start || 0);
        acastPost("postmessage:do:seek", { position: selectedStart });
        best.scrollIntoView({ block: "center" });
      }
    }

    // Clipboard buttons (optional)
    const btnCopy = document.getElementById("btn-copy");
    const btnCopyTs = document.getElementById("btn-copy-ts");

    if (btnCopy) {
      btnCopy.addEventListener("click", async () => {
        const ok = await copyText(window.location.href.split("?")[0]);
        btnCopy.textContent = ok ? "Copied!" : "Copy failed";
        setTimeout(() => (btnCopy.textContent = "Copy link"), 1200);
      });
    }

    if (btnCopyTs) {
      btnCopyTs.addEventListener("click", async () => {
        const t = selectedStart ?? getTimeFromURL() ?? 0;
        const u = new URL(window.location.href);
        u.searchParams.set("t", String(t));
        const ok = await copyText(u.toString());
        btnCopyTs.textContent = ok ? "Copied!" : "Copy failed";
        setTimeout(() => (btnCopyTs.textContent = "Copy link + timestamp"), 1200);
      });
    }
  }

  /* -------------------------------------------------
     Sticky player support
  ------------------------------------------------- */

  function enableStickyPlayer() {
    const wrapper = document.getElementById("player-wrapper");
    const sentinel = document.getElementById("player-sentinel");

    if (!wrapper || !sentinel || !("IntersectionObserver" in window)) return;

    const io = new IntersectionObserver(entries => {
      const e = entries[0];
      if (!e) return;
      wrapper.classList.toggle("sticky", !e.isIntersecting);
    });

    io.observe(sentinel);
  }

  /* -------------------------------------------------
     Boot
  ------------------------------------------------- */

  document.addEventListener("DOMContentLoaded", () => {
    ensureTurnBlocks();
    enableTranscriptInteraction();
    enableStickyPlayer();
  });

})();
