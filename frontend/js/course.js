// ===== Course Creator Frontend Module =====

async function renderCourse() {
  content.innerHTML = `
    <div class="grid-2" style="align-items: start;">
      <div class="card">
        <div class="card-header">Course Blueprint</div>
        <div class="form-group">
          <label class="form-label">Course Title</label>
          <input type="text" id="course-title" placeholder="Python for Beginners" />
        </div>
        <div class="form-group">
          <label class="form-label">Topic</label>
          <input type="text" id="course-topic" placeholder="Python programming" />
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">Audience</label>
            <select id="course-audience">
              <option value="beginners">Beginners</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Difficulty</label>
            <select id="course-difficulty">
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Reference Links (optional, one per line)</label>
          <textarea id="course-references" rows="3" placeholder="https://realpython.com/&#10;https://docs.python.org/3/"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Modules (optional — leave blank to let AI create a full blueprint)</label>
          <textarea id="course-modules" rows="6" placeholder="Variables &amp; Data Types | Learn basic Python types | variables&#10;Control Flow | If/else and loops | control-flow&#10;Functions | Write reusable code | functions&#10;OOP | Classes and objects | oop"></textarea>
        </div>
        <div class="flex gap-1">
          <button class="btn btn-primary" onclick="generateCourse()">▶ Generate Blueprint & Course</button>
          <button class="btn" onclick="generateCourseBlueprint()">🧠 Generate Blueprint</button>
          <button class="btn" onclick="loadBlueprintExample()">Load Example</button>
        </div>
      </div>

      <div id="course-results">
        <div class="card">
          <div class="card-header">Output</div>
          <div class="text-muted text-sm">Fill in the blueprint and click Generate Course.</div>
        </div>
      </div>
    </div>
  `;
}

window.loadBlueprintExample = function() {
  document.getElementById('course-title').value = 'Python for Beginners';
  document.getElementById('course-topic').value = 'Python programming fundamentals';
  document.getElementById('course-audience').value = 'beginners';
  document.getElementById('course-difficulty').value = 'beginner';
  document.getElementById('course-references').value = 'https://realpython.com/\nhttps://docs.python.org/3/';
  document.getElementById('course-modules').value = '';
};

function parseModules(modulesText) {
  return modulesText.split('\n').filter(Boolean).map((line, i) => {
    const parts = line.split('|').map(s => s.trim());
    return {
      title: parts[0] || `Module ${i + 1}`,
      description: parts[1] || '',
      slug: parts[2] || `module-${i + 1}`
    };
  });
}

function parseReferences(value) {
  return value.split('\n').map(s => s.trim()).filter(Boolean);
}

window.generateCourseBlueprint = async function() {
  const title = document.getElementById('course-title').value.trim();
  const topic = document.getElementById('course-topic').value.trim();
  if (!title && !topic) {
    terminalLog('Please enter a course title or topic first', 'warn');
    return;
  }

  const resultsDiv = document.getElementById('course-results');
  resultsDiv.innerHTML = `
    <div class="card">
      <div class="card-header">Generating Blueprint...</div>
      <div class="loading"><div class="spinner"></div></div>
      <div class="text-muted text-sm">The AI is creating a full course structure from your topic and references.</div>
    </div>
  `;

  try {
    const payload = {
      title,
      topic,
      audience: document.getElementById('course-audience').value,
      difficulty: document.getElementById('course-difficulty').value,
      references: parseReferences(document.getElementById('course-references').value),
      generate_assets: true,
      auto_generate_blueprint: true
    };
    const res = await api_post('/api/course/blueprint', payload);
    resultsDiv.innerHTML = `
      <div class="card" style="border-color: var(--success);">
        <div class="card-header" style="color: var(--success);">🧠 Blueprint Ready</div>
        <div class="card-title">${res.blueprint.title || title || topic}</div>
        <div class="card-subtitle">${res.blueprint.modules.length} modules • ${res.blueprint.estimated_duration_hours || '?'} hours</div>
        <div class="card-header mt-2">Blueprint</div>
        <pre class="json">${JSON.stringify(res.blueprint, null, 2)}</pre>
      </div>
    `;
    terminalLog(`Blueprint generated for: ${res.blueprint.title || title || topic}`, 'success');
  } catch (e) {
    terminalLog(`Blueprint generation failed: ${e.message}`, 'error');
    resultsDiv.innerHTML = `
      <div class="card" style="border-color: var(--danger);">
        <div class="card-header" style="color: var(--danger);">✕ Blueprint Failed</div>
        <div class="text-muted">${e.message}</div>
      </div>
    `;
  }
};

window.generateCourse = async function() {
  const title = document.getElementById('course-title').value.trim();
  const topic = document.getElementById('course-topic').value.trim();
  const audience = document.getElementById('course-audience').value;
  const difficulty = document.getElementById('course-difficulty').value;
  const modulesText = document.getElementById('course-modules').value.trim();
  const references = parseReferences(document.getElementById('course-references').value);

  if (!title && !topic) {
    terminalLog('Please fill in a course title or topic', 'warn');
    return;
  }

  let payload = {
    title,
    topic,
    audience,
    difficulty,
    references,
    generate_assets: true,
    auto_generate_blueprint: !modulesText
  };

  let modules = [];
  if (modulesText) {
    modules = parseModules(modulesText);
    payload.modules = modules;
  }

  const resultsDiv = document.getElementById('course-results');
  resultsDiv.innerHTML = `
    <div class="card">
      <div class="card-header">Generating Course...</div>
      <div class="loading"><div class="spinner"></div></div>
      <div class="text-muted text-sm">${modulesText ? 'Using your module plan.' : 'The AI is creating a full blueprint and course from your topic.'}</div>
    </div>
  `;

  terminalLog(`Generating course: "${title || topic}" (${modules.length || 'AI-generated'} modules)`, 'info');

  try {
    let res;
    if (!modulesText) {
      const blueprintRes = await api_post('/api/course/blueprint', payload);
      payload = {
        ...payload,
        ...blueprintRes.blueprint,
        modules: blueprintRes.blueprint.modules || [],
        auto_generate_blueprint: false
      };
      res = await api_post('/api/course/create', payload);
    } else {
      res = await api_post('/api/course/create', payload);
    }

    terminalLog(`Course created: ${res.modules_count} modules at ${res.course_path}`, 'success');

    resultsDiv.innerHTML = `
      <div class="card" style="border-color: var(--success);">
        <div class="card-header" style="color: var(--success);">✓ Course Generated</div>
        <div class="card-title">${res.blueprint?.title || title || topic}</div>
        <div class="card-subtitle">${res.modules_count} modules | ${res.manifest.estimated_duration_hours || '?'} hours</div>
        <div class="text-xs text-muted mb-1">Path: ${res.course_path}</div>
        ${res.site_url ? `<div class="text-xs mb-1"><a href="${res.site_url}" target="_blank" rel="noopener">Open course preview</a></div>` : ''}
        <div class="card-header mt-2">Blueprint</div>
        <pre class="json">${JSON.stringify(res.blueprint || payload, null, 2)}</pre>
        <div class="card-header mt-2">Modules</div>
        ${res.modules.map(m => `
          <div class="module-item">
            <span class="module-title">${m.title}</span>
            <span class="badge badge-success">${m.status}</span>
          </div>
        `).join('')}
        <div class="card-header mt-2">Manifest</div>
        <pre class="json">${JSON.stringify(res.manifest, null, 2)}</pre>
      </div>
    `;
  } catch (e) {
    terminalLog(`Course generation failed: ${e.message}`, 'error');
    resultsDiv.innerHTML = `
      <div class="card" style="border-color: var(--danger);">
        <div class="card-header" style="color: var(--danger);">✕ Generation Failed</div>
        <div class="text-muted">${e.message}</div>
      </div>
    `;
  }
};
