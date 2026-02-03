// Kitchen Companion App

const API_BASE = '/api';

// State
let recipes = [];
let additionalItems = [];
let currentRecipeHtml = '';
let currentRecipeId = null;
let touchStartX = 0;
let touchEndX = 0;

// Font size levels
const FONT_SIZES = ['font-sm', 'font-md', 'font-lg', 'font-xl'];
let currentFontIndex = 1; // Default to medium

// Timer state
let timers = new Map(); // id -> Timer instance
let timerIdCounter = 0;

// Timer class
class Timer {
    constructor(id, durationMs, label) {
        this.id = id;
        this.duration = durationMs;
        this.remaining = durationMs;
        this.label = label;
        this.status = 'stopped'; // stopped, running, paused, complete
        this.interval = null;
        this.startTime = null;
        this.pausedTime = null;
    }

    start() {
        if (this.status === 'running') return;

        this.status = 'running';
        this.startTime = Date.now() - (this.duration - this.remaining);

        this.interval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            this.remaining = Math.max(0, this.duration - elapsed);

            if (this.remaining === 0) {
                this.complete();
            }

            updateTimerDisplay(this.id);
        }, 100); // Update every 100ms for smooth display

        updateTimerDisplay(this.id);
    }

    pause() {
        if (this.status !== 'running') return;

        this.status = 'paused';
        clearInterval(this.interval);
        this.interval = null;
        this.pausedTime = Date.now();

        updateTimerDisplay(this.id);
    }

    stop() {
        this.status = 'stopped';
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        this.remaining = this.duration;
        this.startTime = null;
        this.pausedTime = null;

        updateTimerDisplay(this.id);
    }

    reset() {
        this.stop();
        updateTimerDisplay(this.id);
    }

    complete() {
        this.status = 'complete';
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        this.remaining = 0;

        onTimerComplete(this.id);
    }
}

// Timer utility functions
function parseDuration(durationStr) {
    // Match patterns like "15m", "1h30m", "45s", "1h"
    const hours = /(\d+)h/.exec(durationStr)?.[1] || 0;
    const minutes = /(\d+)m/.exec(durationStr)?.[1] || 0;
    const seconds = /(\d+)s/.exec(durationStr)?.[1] || 0;

    return (parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds)) * 1000;
}

function formatDuration(ms) {
    const totalSeconds = Math.ceil(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function createTimer(durationStr, label) {
    const durationMs = parseDuration(durationStr);
    if (durationMs === 0) {
        console.error('Invalid duration:', durationStr);
        return null;
    }

    const id = timerIdCounter++;
    const timer = new Timer(id, durationMs, label || 'Timer');
    timers.set(id, timer);

    addTimerToPanel(timer);
    showTimerPanel();

    return timer;
}

function deleteTimer(id) {
    const timer = timers.get(id);
    if (timer) {
        timer.stop();
        timers.delete(id);
        removeTimerFromPanel(id);
        updateTimerPanelTitle();
    }
}

function onTimerComplete(id) {
    const timer = timers.get(id);
    if (!timer) return;

    // Update UI
    updateTimerDisplay(id);

    // Play sound
    playTimerSound();

    // Show browser notification
    showTimerNotification(timer.label);

    // Expand panel if collapsed
    const timerPanel = document.getElementById('timer-panel');
    if (timerPanel.classList.contains('collapsed')) {
        timerPanel.classList.remove('collapsed');
    }
}

// Timer sound (simple beep using Web Audio API)
let audioContext = null;

function playTimerSound() {
    try {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Create a simple beep sound
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.value = 800;
        oscillator.type = 'sine';

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);

        // Play three beeps
        setTimeout(() => {
            const osc2 = audioContext.createOscillator();
            const gain2 = audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(audioContext.destination);
            osc2.frequency.value = 800;
            osc2.type = 'sine';
            gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            osc2.start(audioContext.currentTime);
            osc2.stop(audioContext.currentTime + 0.5);
        }, 200);

        setTimeout(() => {
            const osc3 = audioContext.createOscillator();
            const gain3 = audioContext.createGain();
            osc3.connect(gain3);
            gain3.connect(audioContext.destination);
            osc3.frequency.value = 800;
            osc3.type = 'sine';
            gain3.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain3.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            osc3.start(audioContext.currentTime);
            osc3.stop(audioContext.currentTime + 0.5);
        }, 400);
    } catch (e) {
        console.log('Audio playback failed:', e);
    }
}

function showTimerNotification(label) {
    if ('Notification' in window) {
        if (Notification.permission === 'granted') {
            new Notification('Timer Complete! ⏱️', {
                body: label,
                requireInteraction: true,
                tag: 'timer-complete',
            });
        } else if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification('Timer Complete! ⏱️', {
                        body: label,
                        requireInteraction: true,
                        tag: 'timer-complete',
                    });
                }
            });
        }
    }
}

// Views
const views = {
    home: document.getElementById('home-view'),
    cooking: document.getElementById('cooking-view'),
    shopping: document.getElementById('shopping-view'),
    upload: document.getElementById('upload-view'),
};

// DOM Elements - Home
const recipeGrid = document.getElementById('recipe-grid');
const shoppingBtn = document.getElementById('shopping-btn');
const newRecipeBtn = document.getElementById('new-recipe-btn');
const refreshBtn = document.getElementById('refresh-btn');
const errorBanner = document.getElementById('error-banner');
const errorText = document.getElementById('error-text');
const errorClose = document.getElementById('error-close');

// DOM Elements - Cooking
const cookingBackBtn = document.getElementById('cooking-back-btn');
const cookingTitle = document.getElementById('cooking-title');
const cookingContent = document.getElementById('cooking-content');
const cookingHeader = document.getElementById('cooking-header');
const cookingCopyBtn = document.getElementById('cooking-copy-btn');
const fontDecrease = document.getElementById('font-decrease');
const fontIncrease = document.getElementById('font-increase');

// DOM Elements - Timer Panel
const timerPanel = document.getElementById('timer-panel');
const timerPanelToggle = document.getElementById('timer-panel-toggle');
const timerPanelTitle = document.getElementById('timer-panel-title');
const activeTimersContainer = document.getElementById('active-timers');
const addCustomTimerBtn = document.getElementById('add-custom-timer');

// DOM Elements - Custom Timer Modal
const customTimerModal = document.getElementById('custom-timer-modal');
const timerHoursInput = document.getElementById('timer-hours');
const timerMinutesInput = document.getElementById('timer-minutes');
const timerSecondsInput = document.getElementById('timer-seconds');
const timerCustomLabel = document.getElementById('timer-custom-label');
const createTimerBtn = document.getElementById('create-timer-btn');
const cancelTimerBtn = document.getElementById('cancel-timer-btn');

// DOM Elements - Shopping
const shoppingBackBtn = document.getElementById('shopping-back-btn');
const shoppingRefreshBtn = document.getElementById('shopping-refresh-btn');
const shoppingTitle = document.getElementById('shopping-title');
const recipeStep = document.getElementById('recipe-step');
const additionalStep = document.getElementById('additional-step');
const resultStep = document.getElementById('result-step');
const recipeList = document.getElementById('recipe-list');
const additionalItemsList = document.getElementById('additional-items-list');
const selectAllBtn = document.getElementById('select-all-btn');
const clearAllBtn = document.getElementById('clear-all-btn');
const nextToAdditionalBtn = document.getElementById('next-to-additional-btn');
const skipToListBtn = document.getElementById('skip-to-list-btn');
const backToRecipesBtn = document.getElementById('back-to-recipes-btn');
const generateListBtn = document.getElementById('generate-list-btn');
const editSelectionsBtn = document.getElementById('edit-selections-btn');
const shoppingList = document.getElementById('shopping-list');
const pantrySection = document.getElementById('pantry-section');
const pantryList = document.getElementById('pantry-list');
const copyBtn = document.getElementById('copy-btn');

// DOM Elements - Upload
const uploadBackBtn = document.getElementById('upload-back-btn');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const recipeFilename = document.getElementById('recipe-filename');
const recipeContent = document.getElementById('recipe-content');
const uploadError = document.getElementById('upload-error');
const saveRecipeBtn = document.getElementById('save-recipe-btn');

// Servings options
const SERVINGS_OPTIONS = [2, 4, 6, 8, 12];

// ============ View Navigation ============

function showView(viewName) {
    Object.values(views).forEach(view => view.classList.remove('active'));
    views[viewName].classList.add('active');
}

function goHome() {
    showView('home');
}

// ============ API Functions ============

async function fetchRecipes() {
    const response = await fetch(`${API_BASE}/recipes`);
    if (!response.ok) throw new Error('Failed to fetch recipes');
    return response.json();
}

async function fetchAdditionalItems() {
    const response = await fetch(`${API_BASE}/additional-items`);
    if (!response.ok) throw new Error('Failed to fetch additional items');
    const data = await response.json();
    return data.items;
}

async function fetchRecipeDetail(id) {
    const response = await fetch(`${API_BASE}/recipes/${id}`);
    if (!response.ok) throw new Error('Failed to fetch recipe');
    return response.json();
}

async function generateShoppingListApi(selections, includePantry) {
    const response = await fetch(`${API_BASE}/shopping-list`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            selections,
            include_pantry: includePantry,
        }),
    });
    if (!response.ok) throw new Error('Failed to generate shopping list');
    return response.json();
}

async function refreshRecipesApi() {
    const response = await fetch(`${API_BASE}/refresh`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to refresh recipes');
    return response.json();
}

async function uploadRecipeApi(filename, content) {
    const response = await fetch(`${API_BASE}/recipes/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, content }),
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upload recipe');
    }
    return response.json();
}

// ============ UI Functions ============

function showError(message) {
    errorText.textContent = message;
    errorBanner.classList.remove('hidden');
}

function hideError() {
    errorBanner.classList.add('hidden');
}

// ============ Home View ============

function renderRecipeGrid() {
    if (recipes.length === 0) {
        recipeGrid.innerHTML = '<p class="placeholder">No recipes found. Add recipes to get started.</p>';
        return;
    }

    // Check for any errors
    const errorRecipes = recipes.filter(r => r.has_error);
    if (errorRecipes.length > 0) {
        showError(`${errorRecipes.length} recipe(s) have parsing errors.`);
    }

    recipeGrid.innerHTML = recipes.map(recipe => `
        <div class="recipe-card ${recipe.has_error ? 'has-error' : ''}" data-id="${recipe.id}">
            <h3>${recipe.name}</h3>
            <p class="servings">Serves ${recipe.servings}</p>
        </div>
    `).join('');

    // Add click handlers
    recipeGrid.querySelectorAll('.recipe-card').forEach(card => {
        card.addEventListener('click', () => openCookingView(parseInt(card.dataset.id)));
    });
}

// ============ Cooking View ============

function loadFontSize() {
    const saved = localStorage.getItem('recipe-font-size');
    if (saved) {
        const index = FONT_SIZES.indexOf(saved);
        if (index !== -1) {
            currentFontIndex = index;
        }
    }
    applyFontSize();
}

function applyFontSize() {
    FONT_SIZES.forEach(size => cookingContent.classList.remove(size));
    cookingContent.classList.add(FONT_SIZES[currentFontIndex]);
}

function saveFontSize() {
    localStorage.setItem('recipe-font-size', FONT_SIZES[currentFontIndex]);
}

function increaseFontSize() {
    if (currentFontIndex < FONT_SIZES.length - 1) {
        currentFontIndex++;
        applyFontSize();
        saveFontSize();
    }
}

function decreaseFontSize() {
    if (currentFontIndex > 0) {
        currentFontIndex--;
        applyFontSize();
        saveFontSize();
    }
}

async function openCookingView(id) {
    try {
        const recipe = await fetchRecipeDetail(id);
        currentRecipeId = id;
        currentRecipeHtml = recipe.html_content;

        cookingTitle.textContent = recipe.name;

        if (recipe.has_error) {
            cookingContent.innerHTML = `
                <div style="color: var(--error); margin-bottom: 1rem;">
                    <strong>Parse Error:</strong> ${recipe.error_message}
                </div>
                ${recipe.html_content}
            `;
        } else {
            cookingContent.innerHTML = recipe.html_content;
        }

        // Reset scroll position and show header
        cookingContent.scrollTop = 0;
        lastScrollTop = 0;
        headerOffset = 0;
        cookingHeader.style.transform = 'translateY(0)';

        showView('cooking');
    } catch (err) {
        showError('Failed to load recipe');
    }
}

// Scroll detection for cooking view header
let lastScrollTop = 0;
let headerOffset = 0;
const HEADER_HEIGHT = 90; // Header height in pixels (including padding and border)
const SHOW_HEADER_THRESHOLD = 150; // Only show header when within this many pixels from top

function handleCookingScroll() {
    const currentScroll = cookingContent.scrollTop;
    const scrollDiff = currentScroll - lastScrollTop;

    // Ignore very small scroll movements
    if (Math.abs(scrollDiff) < 2) {
        return;
    }

    // Update header offset based on scroll direction
    if (scrollDiff > 0) {
        // Scrolling down - move header up
        headerOffset = Math.min(HEADER_HEIGHT, headerOffset + scrollDiff);
    } else {
        // Scrolling up - only bring header back if we're near the top
        if (currentScroll < SHOW_HEADER_THRESHOLD) {
            headerOffset = Math.max(0, headerOffset + scrollDiff);
        }
    }

    // Apply the transform
    cookingHeader.style.transform = `translateY(-${headerOffset}px)`;

    lastScrollTop = currentScroll;
}

// Swipe detection for cooking view
function handleTouchStart(e) {
    touchStartX = e.changedTouches[0].screenX;
}

function handleTouchEnd(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}

function handleSwipe() {
    const swipeThreshold = 100;
    const diff = touchEndX - touchStartX;

    // Swipe right to go back
    if (diff > swipeThreshold && views.cooking.classList.contains('active')) {
        goHome();
    }
}

async function copyRecipeForEmail() {
    try {
        const blob = new Blob([currentRecipeHtml], { type: 'text/html' });
        const item = new ClipboardItem({ 'text/html': blob });
        await navigator.clipboard.write([item]);
        cookingCopyBtn.innerHTML = '&#10003;';
        setTimeout(() => {
            cookingCopyBtn.innerHTML = '&#10064;';
        }, 2000);
    } catch (err) {
        // Fallback to plain text
        const temp = document.createElement('div');
        temp.innerHTML = currentRecipeHtml;
        await navigator.clipboard.writeText(temp.textContent);
        cookingCopyBtn.innerHTML = '&#10003;';
        setTimeout(() => {
            cookingCopyBtn.innerHTML = '&#10064;';
        }, 2000);
    }
}

// ============ Timer Panel UI ============

function showTimerPanel() {
    timerPanel.classList.remove('hidden');
    updateTimerPanelTitle();
}

function hideTimerPanel() {
    if (timers.size === 0) {
        timerPanel.classList.add('hidden');
    }
}

function toggleTimerPanel() {
    timerPanel.classList.toggle('collapsed');
}

function updateTimerPanelTitle() {
    const count = timers.size;
    timerPanelTitle.textContent = `Timers (${count})`;
    
    if (count === 0) {
        hideTimerPanel();
    }
}

function addTimerToPanel(timer) {
    const timerItem = document.createElement('div');
    timerItem.className = 'timer-item';
    timerItem.dataset.timerId = timer.id;
    
    timerItem.innerHTML = `
        <div class="timer-item-info">
            <div class="timer-label">${timer.label}</div>
            <div class="timer-display">${formatDuration(timer.remaining)}</div>
        </div>
        <div class="timer-controls">
            <button class="btn-icon timer-play" title="Start">&#9654;</button>
            <button class="btn-icon timer-pause hidden" title="Pause">&#10073;&#10073;</button>
            <button class="btn-icon timer-stop" title="Stop">&#9632;</button>
            <button class="btn-icon timer-reset hidden" title="Reset">&#8635;</button>
            <button class="btn-icon timer-delete" title="Delete">&times;</button>
        </div>
    `;
    
    activeTimersContainer.appendChild(timerItem);
    
    // Add event listeners
    const playBtn = timerItem.querySelector('.timer-play');
    const pauseBtn = timerItem.querySelector('.timer-pause');
    const stopBtn = timerItem.querySelector('.timer-stop');
    const resetBtn = timerItem.querySelector('.timer-reset');
    const deleteBtn = timerItem.querySelector('.timer-delete');
    
    playBtn.addEventListener('click', () => handleTimerPlay(timer.id));
    pauseBtn.addEventListener('click', () => handleTimerPause(timer.id));
    stopBtn.addEventListener('click', () => handleTimerStop(timer.id));
    resetBtn.addEventListener('click', () => handleTimerReset(timer.id));
    deleteBtn.addEventListener('click', () => handleTimerDelete(timer.id));
    
    updateTimerPanelTitle();
}

function removeTimerFromPanel(id) {
    const timerItem = activeTimersContainer.querySelector(`[data-timer-id="${id}"]`);
    if (timerItem) {
        timerItem.remove();
    }
    updateTimerPanelTitle();
}

function updateTimerDisplay(id) {
    const timer = timers.get(id);
    if (!timer) return;
    
    const timerItem = activeTimersContainer.querySelector(`[data-timer-id="${id}"]`);
    if (!timerItem) return;
    
    const displayEl = timerItem.querySelector('.timer-display');
    const playBtn = timerItem.querySelector('.timer-play');
    const pauseBtn = timerItem.querySelector('.timer-pause');
    const stopBtn = timerItem.querySelector('.timer-stop');
    const resetBtn = timerItem.querySelector('.timer-reset');
    
    displayEl.textContent = formatDuration(timer.remaining);
    
    // Update button visibility based on status
    timerItem.classList.remove('running', 'complete');
    
    if (timer.status === 'running') {
        timerItem.classList.add('running');
        playBtn.classList.add('hidden');
        pauseBtn.classList.remove('hidden');
        stopBtn.classList.remove('hidden');
        resetBtn.classList.add('hidden');
    } else if (timer.status === 'paused') {
        playBtn.classList.remove('hidden');
        pauseBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');
        resetBtn.classList.remove('hidden');
    } else if (timer.status === 'complete') {
        timerItem.classList.add('complete');
        playBtn.classList.add('hidden');
        pauseBtn.classList.add('hidden');
        stopBtn.classList.add('hidden');
        resetBtn.classList.remove('hidden');
    } else {
        // stopped
        playBtn.classList.remove('hidden');
        pauseBtn.classList.add('hidden');
        stopBtn.classList.add('hidden');
        resetBtn.classList.add('hidden');
    }
}

function handleTimerPlay(id) {
    const timer = timers.get(id);
    if (timer) {
        timer.start();
    }
}

function handleTimerPause(id) {
    const timer = timers.get(id);
    if (timer) {
        timer.pause();
    }
}

function handleTimerStop(id) {
    const timer = timers.get(id);
    if (timer) {
        timer.stop();
    }
}

function handleTimerReset(id) {
    const timer = timers.get(id);
    if (timer) {
        timer.reset();
    }
}

function handleTimerDelete(id) {
    deleteTimer(id);
}

function handleInlineTimerClick(event) {
    const button = event.target.closest('.timer-btn');
    if (!button) return;
    
    const duration = button.dataset.duration;
    const label = button.dataset.label || 'Timer';
    
    const timer = createTimer(duration, label);
    if (timer) {
        timer.start();
        
        // Visual feedback
        button.style.opacity = '0.5';
        setTimeout(() => {
            button.style.opacity = '1';
        }, 200);
    }
}

function openCustomTimerModal() {
    customTimerModal.classList.remove('hidden');
    timerHoursInput.value = '0';
    timerMinutesInput.value = '0';
    timerSecondsInput.value = '0';
    timerCustomLabel.value = '';
    timerMinutesInput.focus();
}

function closeCustomTimerModal() {
    customTimerModal.classList.add('hidden');
}

function createCustomTimer() {
    const hours = parseInt(timerHoursInput.value) || 0;
    const minutes = parseInt(timerMinutesInput.value) || 0;
    const seconds = parseInt(timerSecondsInput.value) || 0;
    const label = timerCustomLabel.value.trim() || 'Custom Timer';
    
    const totalSeconds = hours * 3600 + minutes * 60 + seconds;
    
    if (totalSeconds === 0) {
        alert('Please enter a duration greater than 0');
        return;
    }
    
    // Build duration string
    let durationStr = '';
    if (hours > 0) durationStr += `${hours}h`;
    if (minutes > 0) durationStr += `${minutes}m`;
    if (seconds > 0) durationStr += `${seconds}s`;
    
    const timer = createTimer(durationStr, label);
    if (timer) {
        timer.start();
        closeCustomTimerModal();
    }
}

// ============ Shopping View ============

let currentShoppingStep = 1;

function showShoppingStep(step) {
    currentShoppingStep = step;
    
    // Hide all steps
    recipeStep.classList.remove('active');
    additionalStep.classList.remove('active');
    resultStep.classList.remove('active');
    
    // Show current step
    if (step === 1) {
        recipeStep.classList.add('active');
        shoppingTitle.textContent = 'Select Recipes';
    } else if (step === 2) {
        additionalStep.classList.add('active');
        shoppingTitle.textContent = 'Additional Items';
    } else if (step === 3) {
        resultStep.classList.add('active');
        shoppingTitle.textContent = 'Shopping List';
    }
}

function renderRecipeList() {
    if (recipes.length === 0) {
        recipeList.innerHTML = '<p class="placeholder">No recipes found.</p>';
        return;
    }

    recipeList.innerHTML = recipes.map(recipe => {
        const servingsOptions = SERVINGS_OPTIONS.map(s =>
            `<option value="${s}" ${s === recipe.servings ? 'selected' : ''}>${s}</option>`
        ).join('');

        return `
            <div class="recipe-item ${recipe.has_error ? 'has-error' : ''}" data-id="${recipe.id}">
                <input type="checkbox" id="recipe-${recipe.id}" ${recipe.has_error ? 'disabled' : ''}>
                <span class="recipe-name">${recipe.name}</span>
                <span class="recipe-servings">(serves ${recipe.servings})</span>
                <select class="servings-select" data-id="${recipe.id}" ${recipe.has_error ? 'disabled' : ''}>
                    ${servingsOptions}
                </select>
            </div>
        `;
    }).join('');
}

function renderShoppingList(data) {
    const { shopping_items, pantry_items } = data;

    if (shopping_items.length === 0 && pantry_items.length === 0) {
        shoppingList.innerHTML = '<p class="placeholder">No items in shopping list</p>';
        pantrySection.classList.add('hidden');
        return;
    }

    // Render shopping items as flat list
    const html = shopping_items.map(item =>
        `<div class="shopping-item">${item.display}</div>`
    ).join('');
    shoppingList.innerHTML = html || '<p class="placeholder">No shopping items (all matched pantry)</p>';

    // Render pantry items
    if (pantry_items.length > 0) {
        pantrySection.classList.remove('hidden');
        pantryList.innerHTML = pantry_items.map(item => `
            <label class="pantry-item">
                <input type="checkbox" value="${item}">
                ${item}
            </label>
        `).join('');
    } else {
        pantrySection.classList.add('hidden');
    }
}

function getSelectedRecipes() {
    const selections = [];
    recipeList.querySelectorAll('.recipe-item').forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            const id = parseInt(item.dataset.id);
            const select = item.querySelector('.servings-select');
            const targetServings = parseInt(select.value);
            selections.push({ recipe_id: id, target_servings: targetServings });
        }
    });
    return selections;
}

function getSelectedPantryItems() {
    const items = [];
    pantryList.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        items.push(cb.value);
    });
    return items;
}

function getSelectedAdditionalItems() {
    const items = [];
    additionalItemsList.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        items.push(cb.value);
    });
    return items;
}

function renderAdditionalItems() {
    if (additionalItems.length === 0) {
        additionalItemsList.innerHTML = '<p class="placeholder">No additional items configured</p>';
        return;
    }

    additionalItemsList.innerHTML = additionalItems.map(item => `
        <div class="additional-item">
            <input type="checkbox" id="add-${item.replace(/\s+/g, '-')}" value="${item}">
            <label for="add-${item.replace(/\s+/g, '-')}">${item}</label>
        </div>
    `).join('');
}

async function generateShoppingListApi(selections, includePantry, additionalItems = []) {
    const response = await fetch(`${API_BASE}/shopping-list`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            selections,
            include_pantry: includePantry,
            additional_items: additionalItems,
        }),
    });
    if (!response.ok) throw new Error('Failed to generate shopping list');
    return response.json();
}

async function handleGenerate() {
    const selections = getSelectedRecipes();
    const additionalItemsSelected = getSelectedAdditionalItems();
    
    if (selections.length === 0 && additionalItemsSelected.length === 0) {
        showError('Please select at least one recipe or additional item');
        return;
    }

    generateListBtn.disabled = true;
    generateListBtn.textContent = 'Generating...';

    try {
        const data = await generateShoppingListApi(selections, [], additionalItemsSelected);
        renderShoppingList(data);
        showShoppingStep(3);
        hideError();
    } catch (err) {
        showError('Failed to generate shopping list');
    } finally {
        generateListBtn.disabled = false;
        generateListBtn.textContent = 'Generate Shopping List';
    }
}

async function handleCopyShoppingList() {
    const selections = getSelectedRecipes();
    const pantryItems = getSelectedPantryItems();
    const additionalItemsSelected = getSelectedAdditionalItems();

    try {
        const data = await generateShoppingListApi(selections, pantryItems, additionalItemsSelected);
        await navigator.clipboard.writeText(data.formatted_text);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = 'Copy to Clipboard';
        }, 2000);
    } catch (err) {
        showError('Failed to copy to clipboard');
    }
}

function handleSelectAll() {
    recipeList.querySelectorAll('input[type="checkbox"]:not(:disabled)').forEach(cb => {
        cb.checked = true;
    });
}

function handleClearAll() {
    recipeList.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    shoppingList.innerHTML = '<p class="placeholder">Select recipes and click Generate</p>';
    pantrySection.classList.add('hidden');
    copyBtn.disabled = true;
}

// ============ Upload View ============

function validateRecipeContent(content) {
    if (!content.trim()) {
        return 'Recipe content is empty';
    }
    if (!content.toLowerCase().includes('## ingredients')) {
        return 'Recipe must have an "## Ingredients" section';
    }
    return null;
}

function updateSaveButton() {
    const content = recipeContent.value;
    const filename = recipeFilename.value.trim();
    const error = validateRecipeContent(content);

    if (error) {
        uploadError.textContent = error;
        uploadError.classList.remove('hidden');
        saveRecipeBtn.disabled = true;
    } else if (!filename) {
        uploadError.textContent = 'Please enter a filename';
        uploadError.classList.remove('hidden');
        saveRecipeBtn.disabled = true;
    } else {
        uploadError.classList.add('hidden');
        saveRecipeBtn.disabled = false;
    }
}

function extractTitleFromContent(content) {
    const match = content.match(/^#\s+(.+)$/m);
    if (match) {
        return match[1].toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    }
    return '';
}

function handleFileSelect(file) {
    if (!file.name.endsWith('.md')) {
        showError('Please select a .md file');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        recipeContent.value = e.target.result;
        recipeFilename.value = file.name;
        updateSaveButton();
    };
    reader.readAsText(file);
}

function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

async function handleSaveRecipe() {
    let filename = recipeFilename.value.trim();
    const content = recipeContent.value;

    // Ensure .md extension
    if (!filename.endsWith('.md')) {
        filename += '.md';
    }

    saveRecipeBtn.disabled = true;
    saveRecipeBtn.textContent = 'Saving...';

    try {
        await uploadRecipeApi(filename, content);

        // Refresh recipes
        await refreshRecipesApi();
        recipes = await fetchRecipes();
        renderRecipeGrid();
        renderRecipeList();

        // Clear form and go home
        recipeFilename.value = '';
        recipeContent.value = '';
        uploadError.classList.add('hidden');

        goHome();
    } catch (err) {
        uploadError.textContent = err.message;
        uploadError.classList.remove('hidden');
    } finally {
        saveRecipeBtn.disabled = false;
        saveRecipeBtn.textContent = 'Save Recipe';
        updateSaveButton();
    }
}

// ============ Refresh ============

async function handleRefresh() {
    refreshBtn.disabled = true;

    try {
        await refreshRecipesApi();
        recipes = await fetchRecipes();
        renderRecipeGrid();
        renderRecipeList();
        hideError();
    } catch (err) {
        showError('Failed to refresh recipes');
    } finally {
        refreshBtn.disabled = false;
    }
}

// ============ Initialize ============

function setupAutoRefresh() {
    // Set up EventSource for automatic recipe updates
    try {
        const eventSource = new EventSource(`${API_BASE}/events`);
        
        eventSource.onmessage = async (event) => {
            if (event.data === 'recipe_update') {
                console.log('Recipe update detected, refreshing...');
                try {
                    recipes = await fetchRecipes();
                    additionalItems = await fetchAdditionalItems();
                    renderRecipeGrid();
                    renderRecipeList();
                    renderAdditionalItems();
                    
                    // Show subtle notification
                    const banner = document.createElement('div');
                    banner.className = 'auto-refresh-banner';
                    banner.textContent = 'Recipes updated';
                    document.body.appendChild(banner);
                    
                    setTimeout(() => {
                        banner.classList.add('fade-out');
                        setTimeout(() => banner.remove(), 300);
                    }, 2000);
                } catch (err) {
                    console.error('Auto-refresh failed:', err);
                }
            }
        };
        
        eventSource.onerror = (error) => {
            console.log('EventSource connection lost, will retry automatically');
        };
        
        console.log('Auto-refresh enabled');
    } catch (err) {
        console.log('Auto-refresh not available:', err);
    }
}

async function init() {
    // Load font size preference
    loadFontSize();

    // Load recipes and additional items
    try {
        recipes = await fetchRecipes();
        additionalItems = await fetchAdditionalItems();
        renderRecipeGrid();
        renderRecipeList();
        renderAdditionalItems();
    } catch (err) {
        showError('Failed to load recipes. Make sure the server is running.');
    }
    
    // Set up auto-refresh
    setupAutoRefresh();

    // Home view events
    shoppingBtn.addEventListener('click', () => {
        showView('shopping');
        showShoppingStep(1);
    });
    newRecipeBtn.addEventListener('click', () => showView('upload'));
    refreshBtn.addEventListener('click', handleRefresh);
    errorClose.addEventListener('click', hideError);

    // Cooking view events
    cookingBackBtn.addEventListener('click', goHome);
    cookingCopyBtn.addEventListener('click', copyRecipeForEmail);
    fontDecrease.addEventListener('click', decreaseFontSize);
    fontIncrease.addEventListener('click', increaseFontSize);

    // Scroll detection for header hide/show
    cookingContent.addEventListener('scroll', handleCookingScroll, { passive: true });

    // Swipe detection
    cookingContent.addEventListener('touchstart', handleTouchStart, { passive: true });
    cookingContent.addEventListener('touchend', handleTouchEnd, { passive: true });

    // Timer panel events
    timerPanelToggle.addEventListener('click', toggleTimerPanel);
    addCustomTimerBtn.addEventListener('click', openCustomTimerModal);
    
    // Custom timer modal events
    createTimerBtn.addEventListener('click', createCustomTimer);
    cancelTimerBtn.addEventListener('click', closeCustomTimerModal);
    customTimerModal.querySelector('.modal-overlay').addEventListener('click', closeCustomTimerModal);
    
    // Inline timer button delegation (for dynamically created buttons)
    cookingContent.addEventListener('click', handleInlineTimerClick);

    // Shopping view events
    shoppingBackBtn.addEventListener('click', goHome);
    shoppingRefreshBtn.addEventListener('click', handleRefresh);
    selectAllBtn.addEventListener('click', handleSelectAll);
    clearAllBtn.addEventListener('click', handleClearAll);
    nextToAdditionalBtn.addEventListener('click', () => showShoppingStep(2));
    skipToListBtn.addEventListener('click', handleGenerate);
    backToRecipesBtn.addEventListener('click', () => showShoppingStep(1));
    generateListBtn.addEventListener('click', handleGenerate);
    editSelectionsBtn.addEventListener('click', () => showShoppingStep(1));
    copyBtn.addEventListener('click', handleCopyShoppingList);

    // Upload view events
    uploadBackBtn.addEventListener('click', goHome);
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // Paste content validation
    recipeContent.addEventListener('input', () => {
        // Auto-generate filename from title if empty
        if (!recipeFilename.value && recipeContent.value) {
            const title = extractTitleFromContent(recipeContent.value);
            if (title) {
                recipeFilename.value = title + '.md';
            }
        }
        updateSaveButton();
    });
    recipeFilename.addEventListener('input', updateSaveButton);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!customTimerModal.classList.contains('hidden')) {
                closeCustomTimerModal();
            } else if (!views.home.classList.contains('active')) {
                goHome();
            }
        }
    });
}

init();
