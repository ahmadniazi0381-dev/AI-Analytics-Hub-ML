document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("fade");
    }, 4500);
  });

  // Global Difficulty Level Selector Handler
  const selector = document.getElementById("difficultySelector");
  if (selector) {
    const currentLevel = localStorage.getItem("difficultyLevel") || "intermediate";
    selector.value = currentLevel;

    selector.addEventListener("change", () => {
      const level = selector.value;
      localStorage.setItem("difficultyLevel", level);

      // Remove all level classes
      document.documentElement.classList.remove("level-kid", "level-intermediate", "level-expert");
      // Add the active level class
      document.documentElement.classList.add("level-" + level);

      // Dispatch event to update child components
      window.dispatchEvent(new CustomEvent("difficultyLevelChanged", { detail: { level } }));
    });
  }
});
