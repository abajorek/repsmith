/**
 * RepSmith Frontend Application
 */

// Global state
let parsedSongs = [];
let currentSongs = [];
let currentPage = 1;
let currentSortBy = 'title';
let currentSortOrder = 'asc';

// Tab Management
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Load data based on tab
    if (tabName === 'browse') {
        loadSongs();
    } else if (tabName === 'dashboard') {
        loadDashboard();
    }
}

// File Upload Handling
function handleFileSelect(event) {
    const files = event.target.files;
    const uploadBtn = document.getElementById('uploadBtn');

    if (files.length > 0) {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `<i class="fas fa-upload mr-2"></i>Parse ${files.length} File(s)`;
    } else {
        uploadBtn.disabled = true;
    }
}

async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;

    if (files.length === 0) {
        alert('Please select files to upload');
        return;
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append('files[]', file);
    }

    // Show loading
    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Parsing...';
    uploadBtn.disabled = true;

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.parsed_songs) {
            parsedSongs = data.parsed_songs;
            displayPreview(data.parsed_songs);

            if (data.errors && data.errors.length > 0) {
                alert(`Parsed ${data.parsed_songs.length} songs with ${data.errors.length} errors`);
            } else {
                alert(`Successfully parsed ${data.parsed_songs.length} songs`);
            }
        }
    } catch (error) {
        alert('Error uploading files: ' + error.message);
    } finally {
        uploadBtn.innerHTML = '<i class="fas fa-upload mr-2"></i>Parse Files';
        uploadBtn.disabled = false;
    }
}

function displayPreview(songs) {
    const previewArea = document.getElementById('previewArea');
    const tbody = document.getElementById('previewTableBody');

    tbody.innerHTML = '';

    songs.forEach((song, index) => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td class="px-4 py-2 border">${song.title || '<span class="text-red-600">Missing</span>'}</td>
            <td class="px-4 py-2 border">${song.tone_set || '-'}</td>
            <td class="px-4 py-2 border">${song.game_type || '-'}</td>
            <td class="px-4 py-2 border">${song.tempo || '-'}</td>
            <td class="px-4 py-2 border">${song.starting_pitch || '-'}</td>
            <td class="px-4 py-2 border">
                ${song.warnings && song.warnings.length > 0 ?
                    `<span class="text-yellow-600">${song.warnings.length} warnings</span>` :
                    '<span class="text-green-600">OK</span>'
                }
            </td>
        `;
    });

    previewArea.classList.remove('hidden');
}

async function saveAllSongs() {
    if (parsedSongs.length === 0) {
        alert('No songs to save');
        return;
    }

    try {
        const response = await fetch('/api/songs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ songs: parsedSongs })
        });

        const data = await response.json();

        if (response.ok) {
            alert(data.message);
            // Clear preview
            parsedSongs = [];
            document.getElementById('previewArea').classList.add('hidden');
            document.getElementById('fileInput').value = '';
            document.getElementById('uploadBtn').disabled = true;
            document.getElementById('uploadBtn').innerHTML = '<i class="fas fa-upload mr-2"></i>Parse Files';

            // Switch to browse tab
            switchTab('browse');
        } else {
            alert('Error saving songs: ' + data.error);
        }
    } catch (error) {
        alert('Error saving songs: ' + error.message);
    }
}

// Browse & Search
async function loadSongs(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 20,
            sort_by: currentSortBy,
            sort_order: currentSortOrder
        });

        const response = await fetch(`/api/songs?${params}`);
        const data = await response.json();

        currentSongs = data.songs;
        currentPage = page;

        displaySongs(data.songs);
        displayPagination(data.page, data.pages, data.total);
    } catch (error) {
        console.error('Error loading songs:', error);
    }
}

function displaySongs(songs) {
    const tbody = document.getElementById('songListBody');
    tbody.innerHTML = '';

    if (songs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-gray-500">No songs found</td></tr>';
        return;
    }

    songs.forEach(song => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td class="px-4 py-2 border">${song.title}</td>
            <td class="px-4 py-2 border">${song.tone_set || '-'}</td>
            <td class="px-4 py-2 border">${song.game_type || '-'}</td>
            <td class="px-4 py-2 border">${song.tempo || '-'}</td>
            <td class="px-4 py-2 border">
                <button onclick="viewSong(${song.id})" class="text-blue-600 hover:text-blue-800 mr-2">
                    <i class="fas fa-eye"></i> View
                </button>
                <button onclick="deleteSong(${song.id})" class="text-red-600 hover:text-red-800">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        `;
    });
}

function displayPagination(page, totalPages, total) {
    const resultsCount = document.getElementById('resultsCount');
    resultsCount.innerHTML = `Showing ${currentSongs.length} of ${total} songs`;

    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    if (totalPages <= 1) return;

    // Previous button
    if (page > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevBtn.className = 'px-3 py-1 border rounded hover:bg-gray-100';
        prevBtn.onclick = () => loadSongs(page - 1);
        pagination.appendChild(prevBtn);
    }

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= page - 2 && i <= page + 2)) {
            const pageBtn = document.createElement('button');
            pageBtn.innerHTML = i;
            pageBtn.className = `px-3 py-1 border rounded ${i === page ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}`;
            pageBtn.onclick = () => loadSongs(i);
            pagination.appendChild(pageBtn);
        } else if (i === page - 3 || i === page + 3) {
            const dots = document.createElement('span');
            dots.innerHTML = '...';
            dots.className = 'px-2';
            pagination.appendChild(dots);
        }
    }

    // Next button
    if (page < totalPages) {
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextBtn.className = 'px-3 py-1 border rounded hover:bg-gray-100';
        nextBtn.onclick = () => loadSongs(page + 1);
        pagination.appendChild(nextBtn);
    }
}

async function searchSongs() {
    const searchTerm = document.getElementById('searchInput').value;

    if (searchTerm.length < 2 && searchTerm.length > 0) {
        return; // Wait for at least 2 characters
    }

    filterSongs();
}

async function filterSongs() {
    try {
        const params = new URLSearchParams();

        const search = document.getElementById('searchInput').value;
        if (search) params.append('search', search);

        const toneSet = document.getElementById('toneSetFilter').value;
        if (toneSet) params.append('tone_set', toneSet);

        const gameType = document.getElementById('gameTypeFilter').value;
        if (gameType) params.append('game_type', gameType);

        params.append('sort_by', currentSortBy);
        params.append('sort_order', currentSortOrder);

        const response = await fetch(`/api/songs?${params}`);
        const data = await response.json();

        displaySongs(data.songs);
        displayPagination(data.page, data.pages, data.total);
    } catch (error) {
        console.error('Error filtering songs:', error);
    }
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('toneSetFilter').value = '';
    document.getElementById('gameTypeFilter').value = '';
    loadSongs();
}

function sortBy(column) {
    if (currentSortBy === column) {
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortBy = column;
        currentSortOrder = 'asc';
    }

    if (document.getElementById('searchInput').value ||
        document.getElementById('toneSetFilter').value ||
        document.getElementById('gameTypeFilter').value) {
        filterSongs();
    } else {
        loadSongs(currentPage);
    }
}

// Song Detail Modal
async function viewSong(songId) {
    try {
        const response = await fetch(`/api/songs/${songId}`);
        const song = await response.json();

        document.getElementById('modalTitle').innerHTML = song.title;

        const content = document.getElementById('modalContent');
        content.innerHTML = `
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h3 class="font-bold text-gray-700">Musical Attributes</h3>
                    <dl class="mt-2 space-y-2">
                        ${song.alternate_titles ? `<div><dt class="text-sm text-gray-600">Alternate Titles:</dt><dd class="font-semibold">${song.alternate_titles}</dd></div>` : ''}
                        <div><dt class="text-sm text-gray-600">Tone Set:</dt><dd class="font-semibold">${song.tone_set || '-'}</dd></div>
                        <div><dt class="text-sm text-gray-600">Range:</dt><dd class="font-semibold">${song.range || '-'}</dd></div>
                        <div><dt class="text-sm text-gray-600">Starting Pitch:</dt><dd class="font-semibold">${song.starting_pitch || '-'}</dd></div>
                        <div><dt class="text-sm text-gray-600">Meter:</dt><dd class="font-semibold">${song.meter || '-'}</dd></div>
                        <div><dt class="text-sm text-gray-600">Tempo:</dt><dd class="font-semibold">${song.tempo || '-'}</dd></div>
                        ${song.character ? `<div><dt class="text-sm text-gray-600">Character:</dt><dd class="font-semibold">${song.character}</dd></div>` : ''}
                    </dl>
                </div>
                <div>
                    <h3 class="font-bold text-gray-700">Pedagogical Context</h3>
                    <dl class="mt-2 space-y-2">
                        <div><dt class="text-sm text-gray-600">Game Type:</dt><dd class="font-semibold">${song.game_type || '-'}</dd></div>
                        ${song.keywords ? `<div><dt class="text-sm text-gray-600">Keywords:</dt><dd class="font-semibold">${song.keywords}</dd></div>` : ''}
                        ${song.source ? `<div><dt class="text-sm text-gray-600">Source:</dt><dd class="font-semibold">${song.source}</dd></div>` : ''}
                        ${song.borrowed_from ? `<div><dt class="text-sm text-gray-600">Borrowed From:</dt><dd class="font-semibold">${song.borrowed_from}</dd></div>` : ''}
                    </dl>
                </div>
            </div>

            ${song.lyrics ? `
                <div class="mt-4">
                    <h3 class="font-bold text-gray-700">Lyrics</h3>
                    <pre class="mt-2 p-4 bg-gray-50 rounded whitespace-pre-wrap">${song.lyrics}</pre>
                </div>
            ` : ''}

            ${song.directions ? `
                <div class="mt-4">
                    <h3 class="font-bold text-gray-700">Directions</h3>
                    <p class="mt-2 p-4 bg-gray-50 rounded">${song.directions}</p>
                </div>
            ` : ''}

            ${song.notation_reference ? `
                <div class="mt-4">
                    <h3 class="font-bold text-gray-700">Notation</h3>
                    <p class="mt-2 text-sm text-gray-600">Original file: ${song.notation_reference}</p>
                </div>
            ` : ''}
        `;

        // Show modal
        const modal = document.getElementById('songModal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } catch (error) {
        alert('Error loading song details: ' + error.message);
    }
}

function closeModal() {
    const modal = document.getElementById('songModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

async function deleteSong(songId) {
    if (!confirm('Are you sure you want to delete this song?')) {
        return;
    }

    try {
        const response = await fetch(`/api/songs/${songId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('Song deleted successfully');
            loadSongs(currentPage);
        } else {
            alert('Error deleting song');
        }
    } catch (error) {
        alert('Error deleting song: ' + error.message);
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();

        // Update stats
        document.getElementById('totalSongs').textContent = data.total_songs;
        document.getElementById('uniqueToneSets').textContent = data.tone_set_distribution.length;
        document.getElementById('uniqueGameTypes').textContent = data.game_type_distribution.length;
        document.getElementById('uniqueSources').textContent = data.source_distribution.length;

        // Render charts
        renderBarChart('toneSetChart', data.tone_set_distribution, 'tone_set');
        renderBarChart('gameTypeChart', data.game_type_distribution, 'game_type');
        renderBarChart('tempoChart', data.tempo_distribution, 'range');
        renderBarChart('sourceChart', data.source_distribution.slice(0, 10), 'source');

        // Gap analysis
        renderGapAnalysis(data);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function renderBarChart(containerId, data, labelKey) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (data.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No data available</p>';
        return;
    }

    const maxCount = Math.max(...data.map(item => item.count));

    data.slice(0, 10).forEach(item => {
        const label = item[labelKey];
        const count = item.count;
        const percentage = (count / maxCount) * 100;

        const bar = document.createElement('div');
        bar.className = 'mb-2';
        bar.innerHTML = `
            <div class="flex justify-between text-sm mb-1">
                <span class="font-semibold">${label || '(none)'}</span>
                <span class="text-gray-600">${count}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-blue-600 h-2 rounded-full" style="width: ${percentage}%"></div>
            </div>
        `;
        container.appendChild(bar);
    });
}

function renderGapAnalysis(data) {
    const container = document.getElementById('gapAnalysis');
    container.innerHTML = '';

    const gaps = [];

    // Find tone sets with few songs
    const lowCountToneSets = data.tone_set_distribution.filter(ts => ts.count < 3);
    if (lowCountToneSets.length > 0) {
        gaps.push(`<p><i class="fas fa-exclamation-triangle text-yellow-600 mr-2"></i>
                   Only ${lowCountToneSets.length} tone sets have fewer than 3 songs</p>`);
    }

    // Find game types with few songs
    const lowCountGameTypes = data.game_type_distribution.filter(gt => gt.count < 3);
    if (lowCountGameTypes.length > 0) {
        gaps.push(`<p><i class="fas fa-exclamation-triangle text-yellow-600 mr-2"></i>
                   ${lowCountGameTypes.length} game types have fewer than 3 songs</p>`);
    }

    // Check tempo coverage
    const tempoGaps = data.tempo_distribution.filter(td => td.count === 0);
    if (tempoGaps.length > 0) {
        gaps.push(`<p><i class="fas fa-exclamation-triangle text-yellow-600 mr-2"></i>
                   No songs in ${tempoGaps.map(tg => tg.range).join(', ')} tempo ranges</p>`);
    }

    if (gaps.length === 0) {
        container.innerHTML = '<p class="text-green-600"><i class="fas fa-check-circle mr-2"></i>Your repertoire has good coverage across all categories!</p>';
    } else {
        container.innerHTML = gaps.join('');
    }
}

// Export CSV
async function exportCSV() {
    try {
        window.location.href = '/api/export/csv';
    } catch (error) {
        alert('Error exporting CSV: ' + error.message);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load browse tab data
    loadSongs();
});

// Close modal when clicking outside
document.getElementById('songModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});
