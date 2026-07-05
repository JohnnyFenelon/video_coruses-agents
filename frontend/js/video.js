// ===== Video Studio Frontend Module =====

async function renderVideo() {
  content.innerHTML = `
    <div class="grid-2 video-page-grid" style="align-items: start; gap: 24px;">
      <div class="card video-left-panel">
        <div class="card-header">Video Blueprint</div>
        <div class="form-group">
          <label class="form-label">Story / Concept</label>
          <textarea id="video-story" rows="5" placeholder="A robot learns to paint..."></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Style</label>
          <select id="video-style">
            <option value="cinematic_realism">Cinematic Realism</option>
            <option value="3d_animation">3D Animation (Toy Story-style)</option>
            <option value="2d_anime">2D Anime</option>
            <option value="singing_avatar">Singing Avatar</option>
          </select>
        </div>

        <div class="card video-agent-card">
          <div class="card-header">Character Creator</div>
          <div class="text-sm text-muted mb-1">Auto-generate consistent characters from your story or define them manually.</div>
          <div class="form-group">
            <label class="form-label">Character Archetype</label>
            <input id="character-type" placeholder="e.g. Hero, Mentor, Villain" />
          </div>
          <div class="flex gap-1" style="flex-wrap: wrap; margin-bottom: 12px;">
            <button class="btn btn-primary" onclick="autoCreateCharacters()">Auto create characters</button>
            <button class="btn" onclick="clearCharacterFields()">Clear character fields</button>
          </div>
          <div class="tool-grid">
            <div class="tool-card">
              <div class="tool-card-title">Character 1</div>
              <input id="character-name-1" placeholder="Name" />
              <input id="character-desc-1" placeholder="Description" />
              <input id="character-personality-1" placeholder="Personality / voice" />
            </div>
            <div class="tool-card">
              <div class="tool-card-title">Character 2</div>
              <input id="character-name-2" placeholder="Name" />
              <input id="character-desc-2" placeholder="Description" />
              <input id="character-personality-2" placeholder="Personality / voice" />
            </div>
            <div class="tool-card">
              <div class="tool-card-title">Character 3</div>
              <input id="character-name-3" placeholder="Name" />
              <input id="character-desc-3" placeholder="Description" />
              <input id="character-personality-3" placeholder="Personality / voice" />
            </div>
          </div>
        </div>

        <div class="card video-agent-card">
          <div class="card-header">Agent Tools</div>
          <div class="text-sm text-muted mb-1">Orchestrator is always available. Open other agent tools as needed.</div>
          <div class="tool-toolbar">
            <button class="btn btn-tool active" data-agent="orchestrator" onclick="toggleAgentPanel('orchestrator')">Orchestrator</button>
            <button class="btn btn-tool" data-agent="context" onclick="toggleAgentPanel('context')">Context</button>
            <button class="btn btn-tool" data-agent="research" onclick="toggleAgentPanel('research')">Research</button>
            <button class="btn btn-tool" data-agent="critic" onclick="toggleAgentPanel('critic')">Critic</button>
            <button class="btn btn-tool" data-agent="fact-check" onclick="toggleAgentPanel('fact-check')">Fact-check</button>
          </div>

          <div id="agent-panel-orchestrator" class="tool-content open">
            <div class="form-group">
              <label class="form-label">Team Goal</label>
              <input id="orchestrator-goal" placeholder="What should the producer focus on?" />
            </div>
            <div class="form-group">
              <label class="form-label">Production Notes</label>
              <textarea id="orchestrator-notes" rows="3" placeholder="High-level direction for the orchestrator."></textarea>
            </div>
          </div>

          <div id="agent-panel-context" class="tool-content">
            <div class="form-group">
              <label class="form-label">Brand Voice</label>
              <input id="context-brand-voice" placeholder="Brand voice, mood, or tone" />
            </div>
            <div class="form-group">
              <label class="form-label">Target Audience</label>
              <input id="context-audience" placeholder="Who should this video speak to?" />
            </div>
            <div class="form-group">
              <label class="form-label">Visual Direction</label>
              <input id="context-visual-direction" placeholder="Visual style and atmosphere" />
            </div>
          </div>

          <div id="agent-panel-research" class="tool-content">
            <div class="form-group">
              <label class="form-label">Research Focus</label>
              <input id="research-focus" placeholder="What research should the AI emphasize?" />
            </div>
            <div class="form-group">
              <label class="form-label">Inspiration Notes</label>
              <textarea id="research-inspiration" rows="3" placeholder="Reference artists, films, themes, or genres."></textarea>
            </div>
          </div>

          <div id="agent-panel-critic" class="tool-content">
            <div class="form-group">
              <label class="form-label">Critic Notes</label>
              <textarea id="critic-notes" rows="3" placeholder="What should the critic review focus on?"></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Critic Goal</label>
              <input id="critic-goal" placeholder="Review clarity, pacing, or emotional arc" />
            </div>
          </div>

          <div id="agent-panel-fact-check" class="tool-content">
            <div class="form-group">
              <label class="form-label">Fact-check Focus</label>
              <input id="fact-check-focus" placeholder="What should be verified?" />
            </div>
            <div class="form-group">
              <label class="form-label">Fact-check Notes</label>
              <textarea id="fact-check-notes" rows="3" placeholder="Notes for consistency or logic review."></textarea>
            </div>
          </div>
        </div>

        <div class="flex gap-1" style="margin-top: 12px;">
          <button class="btn btn-primary" onclick="generateVideo()">▶ Generate Video Pipeline</button>
          <button class="btn" onclick="loadVideoExample()">Load Example</button>
        </div>
      </div>

      <div id="video-results" class="video-right-panel">
        <div class="card video-output-card">
          <div class="card-header">Output</div>
          <div class="text-muted text-sm">Enter a story concept and click Generate Video Pipeline.</div>
        </div>
      </div>
    </div>
  `;
}

window.loadVideoExample = function() {
  document.getElementById('video-story').value =
    'A young robot named Pixel lives in a scrap yard and dreams of becoming an artist. ' +
    'One day, she finds a broken paintbrush and teaches herself to paint. ' +
    'Her first painting is clumsy, but with practice she creates a masterpiece. ' +
    'The other robots in the yard are inspired by her determination.';
  document.getElementById('video-style').value = '3d_animation';
  document.getElementById('orchestrator-goal').value = 'Build a cinematic emotional short film with a strong character arc and clear visual direction.';
  document.getElementById('orchestrator-notes').value = 'Keep the storytelling focused and emotional.';
  document.getElementById('context-brand-voice').value = 'Warm, inspiring, and wonder-filled.';
  document.getElementById('context-audience').value = 'General audiences who love heartfelt stories.';
  document.getElementById('context-visual-direction').value = 'Soft cinematic lighting, warm palette, hand-crafted animation style.';
  document.getElementById('research-focus').value = 'Highlight the emotional journey and cinematic beats of the protagonist.';
  document.getElementById('research-inspiration').value = 'Pixar, Studio Ghibli, heartfelt robot stories.';
  document.getElementById('critic-notes').value = 'Review the emotional arc and pacing for clarity.';
  document.getElementById('critic-goal').value = 'Ensure emotional beats land cleanly.';
  document.getElementById('fact-check-focus').value = 'Character motivations and story consistency.';
  document.getElementById('fact-check-notes').value = 'Verify the story logic and emotional progression.';
};

window.toggleAgentPanel = function(agent) {
  const agentButtons = document.querySelectorAll('.tool-toolbar .btn-tool');
  const agentPanels = document.querySelectorAll('.tool-content');
  agentButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.agent === agent));
  agentPanels.forEach((panel) => panel.classList.toggle('open', panel.id === `agent-panel-${agent}`));
};

window.clearCharacterFields = function() {
  [1, 2, 3].forEach((index) => {
    document.getElementById(`character-name-${index}`).value = '';
    document.getElementById(`character-desc-${index}`).value = '';
    document.getElementById(`character-personality-${index}`).value = '';
  });
};

window.autoCreateCharacters = function() {
  const archetype = document.getElementById('character-type').value.trim();
  const story = document.getElementById('video-story').value.trim();
  if (!archetype && !story) {
    terminalLog('Enter a character type or story idea to auto-create characters.', 'warn');
    return;
  }

  const namePrefix = archetype || 'Main Character';
  document.getElementById('character-name-1').value = `${namePrefix} A`;
  document.getElementById('character-desc-1').value = `Primary ${namePrefix.toLowerCase()} with a strong emotional arc.`;
  document.getElementById('character-personality-1').value = 'Brave, curious, and empathetic.';

  document.getElementById('character-name-2').value = `${namePrefix} B`;
  document.getElementById('character-desc-2').value = `Secondary character who supports the hero.`;
  document.getElementById('character-personality-2').value = 'Calm, wise, and grounding.';

  document.getElementById('character-name-3').value = `${namePrefix} C`;
  document.getElementById('character-desc-3').value = `A contrasting foil with compelling stakes.`;
  document.getElementById('character-personality-3').value = 'Dynamic, challenging, and memorable.';
};

window.generateVideo = async function() {
  const story = document.getElementById('video-story').value.trim();
  const style = document.getElementById('video-style').value;

  if (!story) {
    terminalLog('Please enter a story concept', 'warn');
    return;
  }

  const resultsDiv = document.getElementById('video-results');
  resultsDiv.innerHTML = `
    <div class="card">
      <div class="card-header">Generating Video Pipeline...</div>
      <div class="loading"><div class="spinner"></div></div>
      <div class="text-muted text-sm">Phase 1: Writing script with GLM-5.2...</div>
    </div>
  `;

  terminalLog(`Generating video pipeline: "${story.slice(0, 50)}..." [${style}]`, 'info');

  const characterDefinitions = [1, 2, 3].map((index) => ({
    name: document.getElementById(`character-name-${index}`).value.trim(),
    description: document.getElementById(`character-desc-${index}`).value.trim(),
    personality: document.getElementById(`character-personality-${index}`).value.trim(),
  })).filter(({ name, description, personality }) => name || description || personality);

  const agentInputs = {
    goal: document.getElementById('video-agent-goal').value.trim(),
    brand_voice: document.getElementById('video-brand-voice').value.trim(),
    research_focus: document.getElementById('video-research-focus').value.trim(),
    review_notes: document.getElementById('video-review-notes').value.trim()
  };

  const payload = { story, style, agent_inputs: agentInputs };
  if (characterDefinitions.length) {
    payload.characters = characterDefinitions;
  }

  try {
    const res = await api_post('/api/video/create', payload);

    terminalLog(`Video pipeline ready: ${res.shots_count} shots, ${res.scenes_count} scenes`, 'success');

    const agentOutputs = res.agent_outputs || {};
    const orderedAgents = ['orchestrator', 'context', 'research', 'critic', 'fact_check'];
    const agentCards = orderedAgents
      .filter((name) => name in agentOutputs)
      .map((name) => {
        const output = agentOutputs[name];
        const content = typeof output === 'string' ? output : JSON.stringify(output, null, 2);
        return `
          <div class="card" style="padding: 12px; min-width: 220px; flex: 1 1 240px;">
            <div class="card-header">${name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
            <pre class="text-sm" style="white-space: pre-wrap; max-height: 280px; overflow: auto;">${content}</pre>
          </div>
        `;
      }).join('');

    const characters = Array.isArray(res.characters) ? res.characters : (Array.isArray(res.provided_characters) ? res.provided_characters : []);
    const characterCards = characters.length
      ? characters.map((character) => `
          <div class="card" style="padding: 12px; min-width: 220px; flex: 1 1 240px;">
            <div class="card-header">${character.name || 'Unnamed Character'}</div>
            <div><strong>Description:</strong> ${character.description || '—'}</div>
            <div><strong>Personality:</strong> ${character.personality || '—'}</div>
          </div>
        `).join('')
      : '';

    const previewShots = Array.isArray(res.sample_shots) ? res.sample_shots : [];
    const shotsRows = previewShots.map(s => `
      <tr>
        <td>#${s.shot_id || '-'}</td>
        <td>${s.scene || '-'}</td>
        <td>${s.camera_angle || 'medium'}</td>
        <td>${s.lighting || 'natural'}</td>
      </tr>
    `).join('');

    const videoUrl = res.video_url || null;
    const previewBlock = videoUrl
      ? `<video class="video-preview" controls src="${videoUrl}" playsinline></video>`
      : `<div class="preview-placeholder">Preview will appear here once a generated MP4 or playable video URL is available.</div>`;

    const files = Array.isArray(res.files) ? res.files : [];

    resultsDiv.innerHTML = `
      <div class="card" style="border-color: var(--success);">
        <div class="card-header" style="color: var(--success);">✓ Pipeline Generated</div>
        <div class="card-title">${res.story}</div>
        <div class="card-subtitle">${res.scenes_count} scenes · ${res.shots_count} shots · ${style.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
        <div class="text-xs text-muted mb-1">Project: ${res.project_path}</div>
        ${res.export_url ? `<div class="text-xs text-muted mb-1">Export JSON: <a href="${res.export_url}" target="_blank">Download</a></div>` : ''}

        <div class="card-header mt-2">Agent Team Outputs</div>
        <div class="video-agent-output-grid">${agentCards}</div>

        <div class="card-header mt-2">Characters</div>
        <div class="video-agent-output-grid">
          ${characterCards || '<div class="card" style="padding: 12px; min-width: 220px; flex: 1 1 240px;"><div class="text-muted">Character details will appear here after generation.</div></div>'}
        </div>

        <div class="card-header mt-2">Video Preview</div>
        <div class="video-preview-panel">
          <div class="video-preview-wrapper">${previewBlock}</div>
        </div>

        <div class="card-header mt-2">Generated Files</div>
        <div class="flex gap-1" style="flex-wrap: wrap;">
          ${files.map(f => `<span class="badge badge-success">${f}</span>`).join('')}
        </div>

        <div class="card-header mt-2">Sample Shot Prompts</div>
        <table class="shots-table">
          <thead><tr><th>Shot</th><th>Scene</th><th>Camera</th><th>Lighting</th></tr></thead>
          <tbody>${shotsRows || '<tr><td colspan="4" class="text-muted">No shots preview available</td></tr>'}</tbody>
        </table>
      </div>
    `;

  } catch (e) {
    terminalLog(`Video pipeline failed: ${e.message}`, 'error');
    resultsDiv.innerHTML = `
      <div class="card" style="border-color: var(--danger);">
        <div class="card-header" style="color: var(--danger);">✕ Generation Failed</div>
        <div class="text-muted">${e.message}</div>
      </div>
    `;
  }
};
