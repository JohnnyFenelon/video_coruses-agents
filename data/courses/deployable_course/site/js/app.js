
const manifest = {
  "title": "Deployable Course",
  "topic": "Web development basics",
  "audience": "beginners",
  "difficulty": "beginner",
  "learning_objectives": [
    "Understand the core concepts of Web development basics"
  ],
  "prerequisites": [
    "Basic familiarity with the subject"
  ],
  "estimated_duration_hours": 4,
  "pedagogical_approach": "Structured, beginner-friendly explanation with practical examples",
  "modules": [
    {
      "slug": "intro",
      "title": "Intro",
      "status": "generated",
      "files": [
        "lesson_plan.json",
        "script.md",
        "quiz.json"
      ]
    }
  ],
  "generated_at": "2026-07-05T11:31:30.875898",
  "lms_ready": true,
  "format_version": "1.0"
};
const moduleList = document.getElementById('modules');
const objectivesList = document.getElementById('objectives');

manifest.learning_objectives.forEach(item => {
  const li = document.createElement('li');
  li.textContent = item;
  objectivesList.appendChild(li);
});

manifest.modules.forEach((module) => {
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `
    <h3>${module.title}</h3>
    <p>${module.status}</p>
    <p>${module.files.join(', ')}</p>
  `;
  moduleList.appendChild(card);
});
