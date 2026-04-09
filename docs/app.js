const tabs = [...document.querySelectorAll(".tab-button")];
const panels = [...document.querySelectorAll(".tab-panel")];
const copyButtons = [...document.querySelectorAll(".copy-button")];
const navLinks = [...document.querySelectorAll(".site-nav a[href^='#']")];
const sections = [...document.querySelectorAll("[data-section]")];
const revealTargets = [...document.querySelectorAll("[data-reveal]")];
const header = document.querySelector(".masthead");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const signalPanel = document.querySelector(".signal-panel");
const signalTitle = document.querySelector("[data-signal-title]");
const signalBody = document.querySelector("[data-signal-body]");
const signalCaption = document.querySelector("[data-signal-caption]");
const signalDots = [...document.querySelectorAll(".signal-dots span")];

const liveRegion = document.createElement("div");
liveRegion.className = "sr-only";
liveRegion.setAttribute("aria-live", "polite");
document.body.appendChild(liveRegion);

const signalFrames = [
  {
    title: "Root Cause",
    body: "Provider fallback vanished during a config refactor.",
    caption: "Generated from diff facts, dependency hints, and nearby commit context."
  },
  {
    title: "Blast Radius",
    body: "Startup path, config loading, and report generation were all exposed.",
    caption: "Useful when the real question is who else should check their systems next."
  },
  {
    title: "Never Again",
    body: "Add startup smoke tests and release checks before the next deploy.",
    caption: "The report closes with prevention because explanation alone is not enough."
  }
];

function activateTab(tab) {
  const target = tab.dataset.tab;

  for (const [index, button] of tabs.entries()) {
    const active = button === tab;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
    button.setAttribute("tabindex", active ? "0" : "-1");
    if (active && index !== tabs.indexOf(tab)) {
      button.blur();
    }
  }

  for (const panel of panels) {
    panel.classList.toggle("is-active", panel.dataset.panel === target);
  }
}

for (const [index, tab] of tabs.entries()) {
  tab.setAttribute("role", "tab");
  tab.setAttribute("tabindex", index === 0 ? "0" : "-1");

  tab.addEventListener("click", () => activateTab(tab));
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) {
      return;
    }

    event.preventDefault();
    const currentIndex = tabs.indexOf(tab);
    let nextIndex = currentIndex;

    if (event.key === "ArrowRight") {
      nextIndex = (currentIndex + 1) % tabs.length;
    } else if (event.key === "ArrowLeft") {
      nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = tabs.length - 1;
    }

    tabs[nextIndex].focus();
    activateTab(tabs[nextIndex]);
  });
}

for (const button of copyButtons) {
  button.addEventListener("click", async () => {
    const code = button.parentElement?.querySelector("code");
    if (!code) {
      return;
    }

    try {
      await navigator.clipboard.writeText(code.textContent ?? "");
      const original = button.textContent;
      button.textContent = "Copied";
      button.classList.add("is-copied");
      liveRegion.textContent = "Command copied to clipboard.";
      setTimeout(() => {
        button.textContent = original;
        button.classList.remove("is-copied");
      }, 1400);
    } catch {
      button.textContent = "Copy failed";
      liveRegion.textContent = "Copy failed.";
      setTimeout(() => {
        button.textContent = "Copy";
      }, 1400);
    }
  });
}

for (const link of navLinks) {
  link.addEventListener("click", (event) => {
    const targetId = link.getAttribute("href");
    if (!targetId) {
      return;
    }

    const target = document.querySelector(targetId);
    if (!(target instanceof HTMLElement)) {
      return;
    }

    event.preventDefault();
    target.scrollIntoView({
      behavior: reduceMotion.matches ? "auto" : "smooth",
      block: "start"
    });
    history.replaceState(null, "", targetId);
  });
}

if (!reduceMotion.matches) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
        }
      }
    },
    { threshold: 0.14, rootMargin: "0px 0px -8% 0px" }
  );

  for (const target of revealTargets) {
    revealObserver.observe(target);
  }
} else {
  for (const target of revealTargets) {
    target.classList.add("is-visible");
  }
}

if (sections.length > 0 && navLinks.length > 0) {
  const navObserver = new IntersectionObserver(
    (entries) => {
      const visibleEntry = entries
        .filter((entry) => entry.isIntersecting)
        .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

      if (!visibleEntry) {
        return;
      }

      const activeId = `#${visibleEntry.target.id}`;
      for (const link of navLinks) {
        const active = link.getAttribute("href") === activeId;
        link.classList.toggle("is-current", active);
        if (active) {
          link.setAttribute("aria-current", "page");
        } else {
          link.removeAttribute("aria-current");
        }
      }
    },
    { threshold: [0.2, 0.45, 0.7] }
  );

  for (const section of sections) {
    if (section.id) {
      navObserver.observe(section);
    }
  }
}

function syncHeaderState() {
  if (!header) {
    return;
  }
  header.classList.toggle("is-scrolled", window.scrollY > 18);
}

syncHeaderState();
window.addEventListener("scroll", syncHeaderState, { passive: true });

if (signalPanel && signalTitle && signalBody && signalCaption && signalDots.length === signalFrames.length) {
  let signalIndex = 0;

  const renderSignal = (index) => {
    const frame = signalFrames[index];
    signalPanel.classList.add("is-changing");

    window.setTimeout(() => {
      signalTitle.textContent = frame.title;
      signalBody.textContent = frame.body;
      signalCaption.textContent = frame.caption;
      signalDots.forEach((dot, dotIndex) => {
        dot.classList.toggle("is-active", dotIndex === index);
      });
      signalPanel.classList.remove("is-changing");
    }, reduceMotion.matches ? 0 : 140);
  };

  if (!reduceMotion.matches) {
    window.setInterval(() => {
      signalIndex = (signalIndex + 1) % signalFrames.length;
      renderSignal(signalIndex);
    }, 3200);
  } else {
    renderSignal(signalIndex);
  }
}
