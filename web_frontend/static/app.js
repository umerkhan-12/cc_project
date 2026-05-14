const sampleCode = `int i = 0;
int sum = 0;

while (i < 5) {
  sum = sum + i;
  i = i + 1;
}

if (sum >= 10) {
  print(sum);
} else {
  print(0);
}`;

const sourceElement = document.getElementById("source");
const phaseElement = document.getElementById("phase");
const plainElement = document.getElementById("plain");
const showBeforeAfterElement = document.getElementById("showBeforeAfter");
const fromSourceElement = document.getElementById("fromSource");
const outputElement = document.getElementById("output");
const runButton = document.getElementById("runButton");
const loadSampleButton = document.getElementById("loadSample");

function setOutput(message, isError = false) {
  outputElement.textContent = message;
  outputElement.classList.toggle("error", isError);
}

function setLoading(isLoading) {
  runButton.disabled = isLoading;
  runButton.classList.toggle("loading", isLoading);
  if (isLoading) {
    setOutput("Running compiler...");
  }
}

async function runCompile() {
  setLoading(true);

  const payload = {
    source: sourceElement.value,
    phase: phaseElement.value,
    plain: plainElement.checked,
    showBeforeAfter: showBeforeAfterElement.checked,
    fromSource: fromSourceElement.checked,
  };

  try {
    const response = await fetch("/api/compile", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      setOutput(result.error || "Unknown error", true);
      return;
    }

    setOutput(result.output || "(no output)");
  } catch (err) {
    setOutput(`Network error: ${err.message}`, true);
  } finally {
    setLoading(false);
  }
}

runButton.addEventListener("click", runCompile);
loadSampleButton.addEventListener("click", () => {
  sourceElement.value = sampleCode;
  setOutput("Sample source loaded.");
  sourceElement.focus();
});

sourceElement.value = sampleCode;
setOutput("Ready. Paste code and click Run.");
