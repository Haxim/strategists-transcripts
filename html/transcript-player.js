(() => {
  const AC_ORIGIN = "https://embed.acast.com";
  const POLL_MS = 300;

  // --------------------------------------------------
  // Messaging handshake (first inbound message wins)
  // --------------------------------------------------
  let acastWindow = null;

  function post(msg) {
    if (!acastWindow) return;
    acastWindow.postMessage(JSON.stringify(msg), AC_ORIGIN);
  }

  function parseMsg(data) {
    if (typeof data === "string") {
      try { return JSON.parse(data); } catch {}
    }
    return data && typeof data === "object" ? data : null;
  }

  // --------------------------------------------------
  // Transcript index
  // --------------------------------------------------
  const transcript = document.getElementById("transcript");
  if (!transcript) return;

  const paras = Array.from(transcript.querySelectorAll("p[data-start]"))
    .map(p => ({ el: p, t: Number(p.dataset.start) }))
    .filter(x => Number.isFinite(x.t))
    .sort((a, b) => a.t - b.t);

  if (!paras.length) return;

  // --------------------------------------------------
  // Mapping state (RELATIVE ONLY)
  // --------------------------------------------------
  let baseProgress = null;   // stitched progress at known transcript time
  let baseTime = null;       // transcript seconds at that moment
  let scale = null;          // seconds per stitched-unit
  let mappingReady = false;

  let lastProgress = null;
  let forwardTicks = 0;
  let adPlaying = true;

  let pendingSeekTime = null;

  // --------------------------------------------------
  // Highlight logic
  // --------------------------------------------------
  let activeIndex = -1;

  function updateHighlight(seconds) {
    if (!mappingReady) return;

    let lo = 0, hi = paras.length - 1, idx = 0;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (paras[mid].t <= seconds) {
        idx = mid;
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }

    if (idx === activeIndex) return;

    if (activeIndex >= 0) {
      paras[activeIndex].el.classList.remove("active");
    }

    activeIndex = idx;
    const el = paras[idx].el;
    el.classList.add("active");

    const r = el.getBoundingClientRect();
    if (r.top < 80 || r.bottom > window.innerHeight - 80) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  // --------------------------------------------------
  // Transcript → Player (intent always captured)
  // --------------------------------------------------
  paras.forEach(({ el, t }) => {
    el.addEventListener("click", () => {
      pendingSeekTime = t;

      // Optimistic UI
      if (mappingReady) updateHighlight(t);

      // Force playback; seek resolves later
      post({ eventName: "postmessage:do:play" });
    });
  });

  // --------------------------------------------------
  // Progress handling (RELATIVE)
  // --------------------------------------------------
  function handleProgress(p) {
    if (!Number.isFinite(p)) {
      adPlaying = true;
      forwardTicks = 0;
      return;
    }

    // --- detect forward motion ---
    if (lastProgress != null && p > lastProgress) {
      forwardTicks++;
    } else {
      forwardTicks = 0;
    }

    adPlaying = forwardTicks < 2;
    lastProgress = p;

    // --------------------------------------------------
    // Establish baseline when we have intent or playback
    // --------------------------------------------------
    if (baseProgress === null && !adPlaying) {
      baseProgress = p;
      baseTime = pendingSeekTime ?? paras[0].t;
      return;
    }

    // --------------------------------------------------
    // Lock scale by crossing transcript boundaries
    // --------------------------------------------------
    if (!mappingReady && baseProgress != null) {
      const dp = p - baseProgress;
      if (dp <= 0) return;

      let crossedIdx = -1;
      for (let i = 1; i < paras.length; i++) {
        if (paras[i].t - baseTime <= dp) crossedIdx = i;
        else break;
      }

      if (crossedIdx >= 1) {
        scale = (paras[crossedIdx].t - baseTime) / dp;
        if (Number.isFinite(scale) && scale > 0) {
          mappingReady = true;
          console.log("[acast] mapping locked", {
            baseProgress,
            baseTime,
            scale
          });
        }
      }
      return;
    }

    // --------------------------------------------------
    // Normal playback
    // --------------------------------------------------
    if (mappingReady) {
      const seconds = baseTime + (p - baseProgress) * scale;
      updateHighlight(seconds);
    }

    // --------------------------------------------------
    // Resolve queued seek once safe
    // --------------------------------------------------
    if (pendingSeekTime != null && mappingReady && !adPlaying) {
      const seekProgress =
        baseProgress + (pendingSeekTime - baseTime) / scale;

      post({
        eventName: "postmessage:do:seek",
        data: { position: seekProgress }
      });

      pendingSeekTime = null;
    }
  }

  // --------------------------------------------------
  // Message listener
  // --------------------------------------------------
  window.addEventListener("message", e => {
    if (e.origin !== AC_ORIGIN) return;

    if (!acastWindow) {
      acastWindow = e.source;
      console.log("[acast] messaging established");
    }

    const msg = parseMsg(e.data);
    if (!msg?.eventName) return;

    if (
      msg.eventName === "postmessage:on:progress" ||
      msg.eventName === "postmessage:get:progress" ||
      msg.eventName === "postmessage:on:seek"
    ) {
      const p = Number(msg.data?.progress);
      handleProgress(p);
    }
  });

  // --------------------------------------------------
  // Polling
  // --------------------------------------------------
  setInterval(() => {
    post({ eventName: "postmessage:get:progress" });
  }, POLL_MS);
})();
