(function () {
  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split("; ") : [];
    for (const cookie of cookies) {
      const parts = cookie.split("=");
      const key = decodeURIComponent(parts.shift());
      if (key === name) {
        return decodeURIComponent(parts.join("="));
      }
    }
    return "";
  }

  function setActiveTheme(theme) {
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.dataset.themeCurrent = theme;
      button.dataset.themeNext = theme === "dark" ? "light" : "dark";
    });
  }

  function saveTheme(theme) {
    const body = new URLSearchParams();
    body.set("theme", theme);

    return fetch(window.sizTheme.themeEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: body.toString(),
      credentials: "same-origin",
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!window.sizTheme || !window.sizTheme.themeEndpoint) {
      return;
    }

    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.addEventListener("click", function () {
        const theme = button.dataset.themeNext || "dark";
        const previousTheme = document.documentElement.dataset.theme || window.sizTheme.current || "light";

        setActiveTheme(theme);
        saveTheme(theme).then(function (response) {
          if (!response.ok) {
            setActiveTheme(previousTheme);
          }
        }).catch(function () {
          setActiveTheme(previousTheme);
        });
      });
    });
  });
})();
