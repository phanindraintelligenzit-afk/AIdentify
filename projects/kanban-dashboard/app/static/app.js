/**
 * AIdentify Kanban Dashboard - Frontend Application
 * Modern dark-themed Kanban board with drag-and-drop, real-time updates, and agent integration.
 */

// ─── Configuration ────────────────────────────────────────────────

const API_KEY = 'kanban-dev-key-2024';
const API_BASE = '/api';
const WS_BASE = `ws://${window.location.host}/ws`;

const AGENTS = {
    researcher: { name: 'Researcher', color: '#8b5cf6', icon: '🔬' },
    writer: { name: 'Writer', color: '#ec4899', icon: '✍️' },
    outreach: { name: 'Outreach', color: '#f59e0b', icon: '📧' },
    social: { name: 'Social', color: '#10b981', icon: '📱' },
    owl: { name: 'Owl', color: '#6366f1', icon: '🦉' },
};

const PRIORITIES = {
    low: { label: 'Low', color: '#6b7280' },
    medium: { label: 'Medium', color: '#3b82f6' },
    high: { label: 'High', color: '#f59e0b' },
    urgent: { label: 'Urgent', color: '#ef4444' },
};

const STATUSES = {
    backlog: { label: 'Backlog', color: '#6b7280' },
    in_progress: { label: 'In Progress', color: '#3b82f6' },
    review: { label: 'Review', color: '#f59e0b' },
    done: { label: 'Done', color: '#10b981' },
};

// ─── State ────────────────────────────────────────────────────────

let state = {
    boards: [],
    currentBoard: null,
    columns: [],
    tasks: [],
    labels: [],
    tags: [],
    filters: {
        assignee: '',
        priority: '',
        label: '',
        search: '',
    },
    ws: null,
    editingTaskId: null,
    selectedLabels: new Set(),
    selectedTags: new Set(),
};

// ─── API Client ───────────────────────────────────────────────────

async function api(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
            ...options.headers,
        },
    };

    const response = await fetch(url, config);
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    if (response.status === 204) return null;
    return response.json();
}

// ─── WebSocket ────────────────────────────────────────────────────

function connectWebSocket(boardId) {
    if (state.ws) {
        state.ws.close();
    }

    const wsUrl = boardId ? `${WS_BASE}/${boardId}` : `${WS_BASE}`;
    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
        updateConnectionStatus('connected');
        // Send periodic pings
        state.ws._pingInterval = setInterval(() => {
            if (state.ws?.readyState === WebSocket.OPEN) {
                state.ws.send('ping');
            }
        }, 30000);
    };

    state.ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        } catch (e) {
            // Ignore non-JSON messages
        }
    };

    state.ws.onclose = () => {
        updateConnectionStatus('disconnected');
        clearInterval(state.ws._pingInterval);
        // Reconnect after 3 seconds
        setTimeout(() => connectWebSocket(state.currentBoard?.id), 3000);
    };

    state.ws.onerror = () => {
        updateConnectionStatus('disconnected');
    };
}

function updateConnectionStatus(status) {
    const el = document.getElementById('connection-status');
    el.className = `connection-status ${status}`;
}

function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'task_created':
            state.tasks.push(message.task);
            renderBoard();
            showToast('New task created', 'success');
            break;
        case 'task_updated':
            const idx = state.tasks.findIndex(t => t.id === message.task.id);
            if (idx !== -1) state.tasks[idx] = message.task;
            renderBoard();
            break;
        case 'task_deleted':
            state.tasks = state.tasks.filter(t => t.id !== message.task_id);
            renderBoard();
            break;
        case 'task_moved':
            const moveIdx = state.tasks.findIndex(t => t.id === message.task.id);
            if (moveIdx !== -1) state.tasks[moveIdx] = message.task;
            renderBoard();
            break;
        case 'board_updated':
            loadBoard(state.currentBoard.id);
            break;
        case 'tasks_bulk_updated':
            loadTasks();
            break;
    }
}

// ─── Data Loading ─────────────────────────────────────────────────

async function loadBoards() {
    try {
        state.boards = await api('/boards');
        populateBoardSelector();
        if (state.boards.length > 0 && !state.currentBoard) {
            await loadBoard(state.boards[0].id);
        }
    } catch (error) {
        showToast('Failed to load boards', 'error');
        console.error(error);
    }
}

async function loadBoard(boardId) {
    try {
        const board = await api(`/boards/${boardId}`);
        state.currentBoard = board;
        state.columns = board.columns.sort((a, b) => a.position - b.position);
        await loadTasks();
        await loadLabels();
        await loadTags();
        populateColumnSelector();
        renderBoard();
        updateStats();
        connectWebSocket(boardId);
    } catch (error) {
        showToast('Failed to load board', 'error');
        console.error(error);
    }
}

async function loadTasks() {
    if (!state.currentBoard) return;
    try {
        const params = new URLSearchParams();
        params.set('board_id', state.currentBoard.id);
        if (state.filters.assignee) params.set('assignee', state.filters.assignee);
        if (state.filters.priority) params.set('priority', state.filters.priority);
        if (state.filters.label) params.set('label_id', state.filters.label);
        if (state.filters.search) params.set('search', state.filters.search);

        state.tasks = await api(`/tasks?${params}`);
        renderBoard();
        updateStats();
    } catch (error) {
        showToast('Failed to load tasks', 'error');
        console.error(error);
    }
}

async function loadLabels() {
    try {
        state.labels = await api('/tasks/labels');
    } catch (error) {
        console.error('Failed to load labels', error);
    }
}

async function loadTags() {
    try {
        state.tags = await api('/tasks/tags');
    } catch (error) {
        console.error('Failed to load tags', error);
    }
}

async function loadStats() {
    if (!state.currentBoard) return;
    try {
        const stats = await api(`/boards/${state.currentBoard.id}/stats`);
        renderStats(stats);
    } catch (error) {
        console.error('Failed to load stats', error);
    }
}

// ─── Rendering ────────────────────────────────────────────────────

function populateBoardSelector() {
    const select = document.getElementById('board-selector');
    select.innerHTML = state.boards.map(b =>
        `<option value="${b.id}">${b.name}</option>`
    ).join('');
}

function populateColumnSelector() {
    const select = document.getElementById('task-column-input');
    select.innerHTML = state.columns.map(c =>
        `<option value="${c.id}">${c.name}</option>`
    ).join('');
}

function populateFilters() {
    const assigneeSelect = document.getElementById('filter-assignee');
    const prioritySelect = document.getElementById('filter-priority');
    const labelSelect = document.getElementById('filter-label');

    assigneeSelect.innerHTML = '<option value="">All Agents</option>' +
        Object.entries(AGENTS).map(([key, agent]) =>
            `<option value="${key}">${agent.icon} ${agent.name}</option>`
        ).join('');

    prioritySelect.innerHTML = '<option value="">All Priorities</option>' +
        Object.entries(PRIORITIES).map(([key, p]) =>
            `<option value="${key}">${p.label}</option>`
        ).join('');

    labelSelect.innerHTML = '<option value="">All Labels</option>' +
        state.labels.map(l =>
            `<option value="${l.id}">${l.name}</option>`
        ).join('');
}

function renderBoard() {
    const board = document.getElementById('board');
    populateFilters();

    board.innerHTML = state.columns.map(column => {
        const columnTasks = state.tasks
            .filter(t => t.column_id === column.id)
            .sort((a, b) => a.position - b.position);

        return `
            <div class="column" data-column-id="${column.id}">
                <div class="column-header">
                    <div class="column-header-left">
                        <span class="column-indicator" style="background: ${column.color}"></span>
                        <span class="column-name">${escapeHtml(column.name)}</span>
                    </div>
                    <span class="column-count">${columnTasks.length}</span>
                </div>
                <div class="column-body" data-column-id="${column.id}">
                    ${columnTasks.map(task => renderTaskCard(task)).join('')}
                    ${columnTasks.length === 0 ? `
                        <div class="empty-state">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                            </svg>
                            <p>No tasks yet</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');

    setupDragAndDrop();
}

function renderTaskCard(task) {
    const assignee = AGENTS[task.assignee] || AGENTS.owl;
    const priority = PRIORITIES[task.priority] || PRIORITIES.medium;
    const status = STATUSES[task.status] || STATUSES.backlog;
    const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';

    const labelsHtml = (task.labels || []).map(l => `
        <span class="task-label" style="background: ${l.color}20; color: ${l.color}">${escapeHtml(l.name)}</span>
    `).join('');

    const tagsHtml = (task.tags || []).map(t => `
        <span class="task-tag">${escapeHtml(t.name)}</span>
    `).join('');

    const dueDateHtml = task.due_date ? `
        <span class="task-due-date ${isOverdue ? 'overdue' : ''}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            ${formatDate(task.due_date)}
        </span>
    ` : '';

    return `
        <div class="task-card priority-${task.priority}" 
             data-task-id="${task.id}"
             draggable="true">
            <div class="task-card-header">
                <span class="task-title">${escapeHtml(task.title)}</span>
                <span class="task-status-badge ${task.status}">${status.label}</span>
            </div>
            ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
            ${labelsHtml ? `<div class="task-labels">${labelsHtml}</div>` : ''}
            ${tagsHtml ? `<div class="task-tags">${tagsHtml}</div>` : ''}
            <div class="task-footer">
                <div class="task-assignee">
                    <div class="assignee-avatar ${task.assignee}" 
                         title="${assignee.name}">${assignee.icon}</div>
                </div>
                <div class="task-meta">
                    ${dueDateHtml}
                    <div class="task-actions">
                        <button class="task-action-btn edit" data-task-id="${task.id}" title="Edit">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                        </button>
                        <button class="task-action-btn delete" data-task-id="${task.id}" title="Delete">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderStats(stats) {
    document.getElementById('stat-total').textContent = stats.total_tasks;
    document.getElementById('stat-backlog').textContent = stats.by_status.backlog || 0;
    document.getElementById('stat-in_progress').textContent = stats.by_status.in_progress || 0;
    document.getElementById('stat-review').textContent = stats.by_status.review || 0;
    document.getElementById('stat-done').textContent = stats.by_status.done || 0;
    document.getElementById('stat-overdue').textContent = stats.overdue_count || 0;
}

// ─── Drag and Drop ────────────────────────────────────────────────

let draggedTask = null;

function setupDragAndDrop() {
    const taskCards = document.querySelectorAll('.task-card');
    const columnBodies = document.querySelectorAll('.column-body');

    taskCards.forEach(card => {
        card.addEventListener('dragstart', (e) => {
            draggedTask = card;
            card.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', card.dataset.taskId);
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedTask = null;
            columnBodies.forEach(col => col.classList.remove('drag-over'));
        });
    });

    columnBodies.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            column.classList.add('drag-over');
        });

        column.addEventListener('dragleave', (e) => {
            if (!column.contains(e.relatedTarget)) {
                column.classList.remove('drag-over');
            }
        });

        column.addEventListener('drop', async (e) => {
            e.preventDefault();
            column.classList.remove('drag-over');

            const taskId = e.dataTransfer.getData('text/plain');
            const columnId = parseInt(column.dataset.columnId);

            if (taskId && columnId) {
                await moveTask(parseInt(taskId), columnId);
            }
        });
    });
}

async function moveTask(taskId, columnId) {
    try {
        const tasksInColumn = state.tasks
            .filter(t => t.column_id === columnId)
            .sort((a, b) => a.position - b.position);

        const newPosition = tasksInColumn.length;

        await api(`/tasks/${taskId}/move`, {
            method: 'POST',
            body: JSON.stringify({ column_id: columnId, position: newPosition }),
        });

        // Optimistic update
        const task = state.tasks.find(t => t.id === taskId);
        if (task) {
            task.column_id = columnId;
            task.position = newPosition;
            // Update status based on column
            const column = state.columns.find(c => c.id === columnId);
            if (column) {
                const colName = column.name.toLowerCase();
                if (colName.includes('backlog') || colName.includes('todo')) {
                    task.status = 'backlog';
                } else if (colName.includes('progress') || colName.includes('doing')) {
                    task.status = 'in_progress';
                } else if (colName.includes('review')) {
                    task.status = 'review';
                } else if (colName.includes('done') || colName.includes('complete')) {
                    task.status = 'done';
                    task.is_completed = true;
                }
            }
        }

        renderBoard();
        updateStats();
    } catch (error) {
        showToast('Failed to move task', 'error');
        console.error(error);
    }
}

// ─── Task Modal ───────────────────────────────────────────────────

function openTaskModal(taskId = null) {
    const modal = document.getElementById('task-modal');
    const title = document.getElementById('modal-title');
    const form = document.getElementById('task-form');

    // Reset form
    form.reset();
    state.selectedLabels.clear();
    state.selectedTags.clear();
    state.editingTaskId = taskId;

    if (taskId) {
        title.textContent = 'Edit Task';
        const task = state.tasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('task-id').value = task.id;
            document.getElementById('task-title-input').value = task.title;
            document.getElementById('task-description-input').value = task.description || '';
            document.getElementById('task-status-input').value = task.status;
            document.getElementById('task-priority-input').value = task.priority;
            document.getElementById('task-assignee-input').value = task.assignee;
            document.getElementById('task-column-input').value = task.column_id;

            if (task.due_date) {
                const d = new Date(task.due_date);
                const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
                document.getElementById('task-duedate-input').value = local.toISOString().slice(0, 16);
            }

            state.selectedLabels = new Set((task.labels || []).map(l => l.id));
            state.selectedTags = new Set((task.tags || []).map(t => t.id));
        }
    } else {
        title.textContent = 'Create Task';
        document.getElementById('task-id').value = '';
        if (state.columns.length > 0) {
            document.getElementById('task-column-input').value = state.columns[0].id;
        }
    }

    renderLabelSelector();
    renderTagSelector();
    modal.classList.add('active');
}

function closeTaskModal() {
    document.getElementById('task-modal').classList.remove('active');
    state.editingTaskId = null;
}

function renderLabelSelector() {
    const container = document.getElementById('label-selector');
    container.innerHTML = state.labels.map(l => `
        <div class="label-option ${state.selectedLabels.has(l.id) ? 'selected' : ''}" 
             data-label-id="${l.id}">
            <span class="color-dot" style="background: ${l.color}"></span>
            ${escapeHtml(l.name)}
        </div>
    `).join('');

    container.querySelectorAll('.label-option').forEach(el => {
        el.addEventListener('click', () => {
            const id = parseInt(el.dataset.labelId);
            if (state.selectedLabels.has(id)) {
                state.selectedLabels.delete(id);
            } else {
                state.selectedLabels.add(id);
            }
            renderLabelSelector();
        });
    });
}

function renderTagSelector() {
    const container = document.getElementById('tag-selector');
    container.innerHTML = state.tags.map(t => `
        <div class="tag-option ${state.selectedTags.has(t.id) ? 'selected' : ''}" 
             data-tag-id="${t.id}">
            ${escapeHtml(t.name)}
        </div>
    `).join('');

    container.querySelectorAll('.tag-option').forEach(el => {
        el.addEventListener('click', () => {
            const id = parseInt(el.dataset.tagId);
            if (state.selectedTags.has(id)) {
                state.selectedTags.delete(id);
            } else {
                state.selectedTags.add(id);
            }
            renderTagSelector();
        });
    });
}

async function saveTask() {
    const title = document.getElementById('task-title-input').value.trim();
    if (!title) {
        showToast('Title is required', 'error');
        return;
    }

    const columnId = parseInt(document.getElementById('task-column-input').value);
    const dueDateValue = document.getElementById('task-duedate-input').value;

    const data = {
        title,
        description: document.getElementById('task-description-input').value.trim() || null,
        status: document.getElementById('task-status-input').value,
        priority: document.getElementById('task-priority-input').value,
        assignee: document.getElementById('task-assignee-input').value,
        column_id: columnId,
        label_ids: Array.from(state.selectedLabels),
        tag_ids: Array.from(state.selectedTags),
    };

    if (dueDateValue) {
        data.due_date = new Date(dueDateValue).toISOString();
    }

    try {
        if (state.editingTaskId) {
            await api(`/tasks/${state.editingTaskId}`, {
                method: 'PATCH',
                body: JSON.stringify(data),
            });
            showToast('Task updated', 'success');
        } else {
            await api('/tasks', {
                method: 'POST',
                body: JSON.stringify(data),
            });
            showToast('Task created', 'success');
        }

        closeTaskModal();
        await loadTasks();
        await loadStats();
    } catch (error) {
        showToast(error.message, 'error');
        console.error(error);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
        await api(`/tasks/${taskId}`, { method: 'DELETE' });
        state.tasks = state.tasks.filter(t => t.id !== taskId);
        renderBoard();
        updateStats();
        showToast('Task deleted', 'success');
    } catch (error) {
        showToast('Failed to delete task', 'error');
        console.error(error);
    }
}

async function editTask(taskId) {
    openTaskModal(taskId);
}

// ─── Toast Notifications ──────────────────────────────────────────

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
        <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ─── Utilities ────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date - now;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    if (days === -1) return 'Yesterday';
    if (days > 0 && days < 7) return `${days}d`;
    if (days < 0 && days > -7) return `${Math.abs(days)}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ─── Event Listeners ──────────────────────────────────────────────

function setupEventListeners() {
    // Board selector
    document.getElementById('board-selector').addEventListener('change', (e) => {
        const boardId = parseInt(e.target.value);
        if (boardId) loadBoard(boardId);
    });

    // New task button
    document.getElementById('btn-new-task').addEventListener('click', () => openTaskModal());

    // Modal close
    document.getElementById('modal-close').addEventListener('click', closeTaskModal);
    document.getElementById('modal-cancel').addEventListener('click', closeTaskModal);
    document.getElementById('task-modal').addEventListener('click', (e) => {
        if (e.target.id === 'task-modal') closeTaskModal();
    });

    // Modal save
    document.getElementById('modal-save').addEventListener('click', saveTask);

    // Filters
    document.getElementById('filter-assignee').addEventListener('change', (e) => {
        state.filters.assignee = e.target.value;
        loadTasks();
    });

    document.getElementById('filter-priority').addEventListener('change', (e) => {
        state.filters.priority = e.target.value;
        loadTasks();
    });

    document.getElementById('filter-label').addEventListener('change', (e) => {
        state.filters.label = e.target.value;
        loadTasks();
    });

    // Search (debounced)
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.filters.search = e.target.value;
            loadTasks();
        }, 300);
    });

    // Task card actions (delegation)
    document.getElementById('board').addEventListener('click', (e) => {
        const editBtn = e.target.closest('.task-action-btn.edit');
        const deleteBtn = e.target.closest('.task-action-btn.delete');

        if (editBtn) {
            e.stopPropagation();
            editTask(parseInt(editBtn.dataset.taskId));
        }

        if (deleteBtn) {
            e.stopPropagation();
            deleteTask(parseInt(deleteBtn.dataset.taskId));
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeTaskModal();
        }
        if (e.key === 'n' && !e.target.matches('input, textarea, select')) {
            e.preventDefault();
            openTaskModal();
        }
    });
}

// ─── Initialize ───────────────────────────────────────────────────

async function init() {
    setupEventListeners();
    await loadBoards();
    showToast('Welcome to AIdentify Kanban', 'info');
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
