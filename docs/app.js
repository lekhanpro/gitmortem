const tabs = [...document.querySelectorAll(".tab-button")];
const panels = [...document.querySelectorAll(".tab-panel")];
const copyButtons = [...document.querySelectorAll(".copy-button")];
const navLinks = [...document.querySelectorAll(".site-nav a[href^='#']")];
const sections = [...document.querySelectorAll("main .section[id]")];
const revealTargets = [...document.querySelectorAll("[data-reveal]")];
const header = document.querySelector(".site-header");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const liveRegion = document.createElement("div");

liveRegion.setAttribute("aria-live", "polite");
liveRegion.className = "sr-only";
document.body.appendChild(liveRegion);

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
  tab.setAttribute("aria-selected", tab.classList.contains("is-active") ? "true" : "false");

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
    { rootMargin: "0px 0px -10% 0px", threshold: 0.16 }
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
    navObserver.observe(section);
  }
}

function syncHeaderState() {
  if (!header) {
    return;
  }
  header.classList.toggle("is-scrolled", window.scrollY > 16);
}

syncHeaderState();
window.addEventListener("scroll", syncHeaderState, { passive: true });
