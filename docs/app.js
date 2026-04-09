const tabs = [...document.querySelectorAll(".tab-button")];
const panels = [...document.querySelectorAll(".tab-panel")];
const copyButtons = [...document.querySelectorAll(".copy-button")];

for (const tab of tabs) {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    for (const button of tabs) {
      button.classList.toggle("is-active", button === tab);
    }
    for (const panel of panels) {
      panel.classList.toggle("is-active", panel.dataset.panel === target);
    }
  });
}

for (const button of copyButtons) {
  button.addEventListener("click", async () => {
    const code = button.parentElement?.querySelector("code");
    if (!code) {
      return;
    }
    await navigator.clipboard.writeText(code.textContent ?? "");
    const original = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => {
      button.textContent = original;
    }, 1400);
  });
}

