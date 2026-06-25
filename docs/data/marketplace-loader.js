/**
 * AIdentify Marketplace — Dynamic Project Loader
 * 
 * Fetches project data from /data/projects.json and renders cards dynamically.
 * Falls back to static HTML if JSON is not available.
 */

(function() {
  'use strict';

  const PROJECTS_URL = 'data/projects.json';
  const FALLBACK_DELAY = 2000; // Wait 2s before showing static content

  async function loadProjects() {
    try {
      const resp = await fetch(PROJECTS_URL);
      if (!resp.ok) throw new Error('Failed to fetch projects');
      const data = await resp.json();
      if (data.projects && data.projects.length > 0) {
        renderProjects(data.projects);
        updateStats(data.projects);
        updateTimestamp(data.generated_at);
      }
    } catch (err) {
      console.log('Using static project data:', err.message);
    }
  }

  function renderProjects(projects) {
    const grid = document.getElementById('projectsGrid');
    if (!grid) return;

    // Keep the last card (CTA card) if it exists
    const ctaCard = grid.querySelector('.project-card[data-category="cta"]');
    
    // Remove existing dynamic cards
    grid.querySelectorAll('.project-card[data-dynamic]').forEach(el => el.remove());

    // Generate cards
    const cardsHtml = projects.map(p => createCardHtml(p)).join('\n');
    
    // Insert before CTA card or at the end
    const temp = document.createElement('div');
    temp.innerHTML = cardsHtml;
    while (temp.firstChild) {
      temp.firstChild.setAttribute('data-dynamic', 'true');
      if (ctaCard) {
        grid.insertBefore(temp.firstChild, ctaCard);
      } else {
        grid.appendChild(temp.firstChild);
      }
    }

    // Re-attach filter listeners
    attachFilterListeners();
  }

  function createCardHtml(p) {
    const tags = (p.tags || []).map(t => 
      `<span class="project-card__tag">${escapeHtml(t)}</span>`
    ).join('\n            ');
    
    const stars = p.stars || 0;
    const forks = p.forks || 0;
    const lang = p.language || 'Python';
    const icon = p.icon || '⚡';
    const name = escapeHtml(p.name || p.id);
    const desc = escapeHtml((p.description || '').substring(0, 120));
    const url = escapeHtml(p.github_url || '#');
    const cat = escapeHtml(p.category || 'other');

    return `<div class="project-card" data-category="${cat}" data-dynamic="true">
          <div class="project-card__header">
            <div class="project-card__icon">${icon}</div>
            <span class="project-card__badge project-card__badge--free">Free Repo</span>
          </div>
          <h3 class="project-card__name">${name}</h3>
          <p class="project-card__desc">${desc}</p>
          <div class="project-card__tags">
            ${tags}
          </div>
          <div class="project-card__meta">
            <span class="project-card__meta-item">⭐ <strong>${stars}</strong> stars</span>
            <span class="project-card__meta-item">🍴 <strong>${forks}</strong> forks</span>
            <span class="project-card__meta-item">${lang}</span>
          </div>
          <div class="project-card__actions">
            <a href="${url}" target="_blank" rel="noopener" class="btn btn--primary btn--sm">View Repo</a>
            <a href="#request" class="btn btn--outline btn--sm">Hire Setup</a>
          </div>
        </div>`;
  }

  function updateStats(projects) {
    const totalEl = document.getElementById('stat-total-projects');
    const testsEl = document.getElementById('stat-tests');
    if (totalEl) totalEl.textContent = projects.length;
    if (testsEl) {
      const totalTests = projects.reduce((sum, p) => sum + (p.agents || 4) * 4, 0);
      testsEl.textContent = totalTests;
    }
  }

  function updateTimestamp(isoDate) {
    const el = document.getElementById('marketplace-last-updated');
    if (el && isoDate) {
      const d = new Date(isoDate);
      el.textContent = d.toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
    }
  }

  function attachFilterListeners() {
    const tabs = document.querySelectorAll('.filter-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const filter = tab.dataset.filter;
        document.querySelectorAll('#projectsGrid .project-card[data-category]').forEach(card => {
          if (filter === 'all' || card.dataset.category === filter) {
            card.style.display = '';
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // Load on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadProjects);
  } else {
    loadProjects();
  }
})();
