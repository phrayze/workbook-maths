document.addEventListener("DOMContentLoaded", function () {
  const finishBtn = document.getElementById("finish-quiz");
  if (!finishBtn) return;

  finishBtn.addEventListener("click", function () {
    if (finishBtn.disabled) return;

    const questions = document.querySelectorAll(".quiz-question");
    const topicScores = {};
    let correctCount = 0;
    let attemptedCount = 0;

    questions.forEach(function (q) {
      const topic = q.dataset.topic;
      const correctIndex = q.dataset.correct;
      const selected = q.querySelector("input[type=radio]:checked");
      const attempted = !!selected;
      const isCorrect = attempted && selected.value === correctIndex;

      if (!topicScores[topic]) topicScores[topic] = { correct: 0, attempted: 0, not_attempted: 0 };
      if (attempted) {
        topicScores[topic].attempted += 1;
        attemptedCount += 1;
        if (isCorrect) {
          topicScores[topic].correct += 1;
          correctCount += 1;
        }
      } else {
        topicScores[topic].not_attempted += 1;
      }

      q.querySelectorAll("input[type=radio]").forEach(function (input) {
        input.disabled = true;
        const label = input.closest("label");
        if (parseInt(input.value, 10) === parseInt(correctIndex, 10)) {
          label.classList.add("option-correct");
        } else if (input === selected) {
          label.classList.add("option-incorrect");
        }
      });

      if (!attempted) {
        q.classList.add("not-attempted");
      }

      const solutionEl = q.querySelector(".q-solution");
      if (solutionEl) {
        solutionEl.hidden = false;
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise([solutionEl]);
        }
      }
    });

    finishBtn.disabled = true;
    finishBtn.textContent = "Test Finished";

    const total = questions.length;
    const notAttempted = total - attemptedCount;
    const overallEl = document.getElementById("overall-score");
    const breakdownEl = document.getElementById("topic-breakdown");
    const saveStatusEl = document.getElementById("save-status");
    const resultsEl = document.getElementById("quiz-results");

    const attemptedPct = attemptedCount ? Math.round((100 * correctCount) / attemptedCount) : 0;
    overallEl.innerHTML =
      `Score on attempted questions: <strong>${correctCount} / ${attemptedCount}</strong> (${attemptedPct}%)` +
      (notAttempted ? `<br>${notAttempted} of ${total} question${total === 1 ? "" : "s"} not attempted (not counted against your score).` : "");

    breakdownEl.innerHTML = "";
    Object.keys(topicScores).forEach(function (topic) {
      const s = topicScores[topic];
      const li = document.createElement("li");
      const pct = s.attempted ? Math.round((100 * s.correct) / s.attempted) : 0;
      let text = `${topic.replace(/_/g, " ")}: ${s.correct}/${s.attempted} attempted (${pct}%)`;
      if (s.not_attempted) text += ` — ${s.not_attempted} not attempted`;
      li.textContent = text;
      breakdownEl.appendChild(li);
    });
    resultsEl.hidden = false;
    resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });

    fetch("/quiz/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student: window.QUIZ_STUDENT,
        stage: window.QUIZ_STAGE,
        topic_scores: topicScores,
      }),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("Save failed");
        return resp.json();
      })
      .then(function () {
        saveStatusEl.textContent = "Result saved. View it any time under Past Test Results.";
      })
      .catch(function () {
        saveStatusEl.textContent = "Could not save this result, but your score above is accurate.";
      });
  });
});
