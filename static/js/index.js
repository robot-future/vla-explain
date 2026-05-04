function showCopiedFeedback(button, copyText) {
    button.classList.add('copied');
    copyText.textContent = 'Cop';
    setTimeout(function() {
        button.classList.remove('copied');
        copyText.textContent = 'Copy';
    }, 2000);
}

// Copy BibTeX to clipboard
function copyBibTeX() {
    const bibtexElement = document.getElementById('bibtex-code');
    const button = document.querySelector('.copy-bibtex-btn');
    const copyText = button.querySelector('.copy-text');

    if (bibtexElement) {
        navigator.clipboard.writeText(bibtexElement.textContent).then(function() {
            showCopiedFeedback(button, copyText);
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            const textArea = document.createElement('textarea');
            textArea.value = bibtexElement.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showCopiedFeedback(button, copyText);
        });
    }
}

// Scroll to top functionality
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Show/hide scroll to top button
const _scrollToTopBtn = document.querySelector('.scroll-to-top');
window.addEventListener('scroll', function() {
    if (!_scrollToTopBtn) return;
    if (window.pageYOffset > 300) {
        _scrollToTopBtn.classList.add('visible');
    } else {
        _scrollToTopBtn.classList.remove('visible');
    }
});

function setupAbstractToggle() {
    const toggle = document.querySelector('.abstract-toggle');
    const panel = document.getElementById('paper-abstract-content');

    if (!toggle || !panel) return;

    const label = toggle.querySelector('.abstract-toggle-text');
    let expanded = toggle.getAttribute('aria-expanded') === 'true';

    toggle.addEventListener('click', function() {
        expanded = !expanded;
        toggle.setAttribute('aria-expanded', String(expanded));
        if (label) {
            label.textContent = expanded ? 'Hide Abstract' : 'Read Full Abstract';
        }

        if (!expanded) {
            panel.classList.remove('is-visible');
            panel.hidden = true;
        } else {
            panel.hidden = false;
            requestAnimationFrame(function() {
                panel.classList.add('is-visible');
            });
        }
    });
}

function setupTeaserHover() {
    const caption = document.querySelector('.teaser-caption');
    const triggers = [
        { key: 'fail',    item: document.querySelector('.teaser-index-fail') },
        { key: 'success', item: document.querySelector('.teaser-index-success') }
    ];

    function clearActive(exceptKey) {
        triggers.forEach(function({ key, item }) {
            if (key === exceptKey) return;
            const overlay = document.getElementById('overlay-' + key);
            const video   = document.getElementById('video-' + key);
            [overlay, video, item].filter(Boolean).forEach(el => el.classList.remove('active'));
            if (item) item.setAttribute('aria-pressed', 'false');
        });
        if (!exceptKey && caption) {
            caption.removeAttribute('data-active-trial');
        }
    }

    triggers.forEach(function({ key, item }) {
        if (!item) return;
        const overlay = document.getElementById('overlay-' + key);
        const video   = document.getElementById('video-' + key);
        const targets = [overlay, video, item].filter(Boolean);

        item.setAttribute('tabindex', '0');
        item.setAttribute('role', 'button');
        item.setAttribute('aria-pressed', 'false');
        item.setAttribute('aria-controls', 'teaser-trial-detail');

        function activate() {
            clearActive(key);
            targets.forEach(el => el.classList.add('active'));
            item.setAttribute('aria-pressed', 'true');
            if (caption) {
                caption.setAttribute('data-active-trial', key);
            }
        }

        item.addEventListener('mouseenter', activate);
        item.addEventListener('focus', activate);
        item.addEventListener('click', function(event) {
            event.stopPropagation();
            activate();
        });
        item.addEventListener('keydown', function(event) {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            activate();
        });
    });

    if (caption) {
        caption.addEventListener('mouseleave', function() {
            clearActive();
        });
        caption.addEventListener('focusout', function(event) {
            if (event.relatedTarget && caption.contains(event.relatedTarget)) return;
            clearActive();
        });
    }

    document.addEventListener('click', function() {
        clearActive();
    });
}

// Fireworks effect for venue badge
(function () {
    const canvas = document.getElementById('fireworks-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const COLORS = ['#CC3300', '#1A6FA8', '#F5A623', '#2D7A4F', '#FFD700', '#E85D75', '#5B9BD5'];
    let particles = [];
    let animFrame = null;

    function resize() {
        if (particles.length === 0) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
    }
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    window.addEventListener('resize', resize);

    function getFireworkScale() {
        const viewport = Math.min(window.innerWidth || 0, window.innerHeight || 0);
        return Math.max(0.42, Math.min(1, viewport / 900));
    }

    function spawnSideBurst(x, y, side) {
        const scale = getFireworkScale();
        const count = Math.max(8, Math.round(22 * scale));
        const biasAngle = side === 'left' ? Math.PI : 0;
        for (let i = 0; i < count; i++) {
            const spread = (Math.random() - 0.5) * (Math.PI * 1.1);
            const angle = biasAngle + spread;
            const speed = (3.5 + Math.random() * 5) * scale;
            particles.push({
                x, y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed + (Math.random() - 0.5) * 4 * scale,
                color: COLORS[Math.floor(Math.random() * COLORS.length)],
                alpha: 1,
                radius: (2.5 + Math.random() * 3) * scale,
                gravity: 0.10 * scale,
                decay: 0.014 + Math.random() * 0.01
            });
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let live = 0;
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.vy += p.gravity;
            p.vx *= 0.97;
            p.alpha -= p.decay;
            if (p.alpha <= 0.02) continue;
            ctx.globalAlpha = p.alpha;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
            particles[live++] = p;
        }
        particles.length = live;
        ctx.globalAlpha = 1;
        if (live > 0) {
            animFrame = requestAnimationFrame(animate);
        } else {
            animFrame = null;
        }
    }

    function triggerFireworks(badge) {
        const rect = badge.getBoundingClientRect();
        const cy = rect.top + rect.height / 2;
        spawnSideBurst(rect.left + rect.width * 0.25, cy, 'left');
        setTimeout(() => spawnSideBurst(rect.left + rect.width * 0.75, cy, 'right'), 120 + Math.random() * 100);
        if (!animFrame) animFrame = requestAnimationFrame(animate);
    }

    window._triggerFireworks = triggerFireworks;
})();

function setupFireworks() {
    const badge = document.querySelector('.venue-badge');
    if (badge && window._triggerFireworks) {
        badge.addEventListener('mouseenter', () => window._triggerFireworks(badge));
    }
}

function setupMethodTriggers() {
    const overview = document.querySelector('.framework-overview');
    const triggers = document.querySelectorAll('[data-method-trigger]');

    if (!overview || triggers.length === 0) return;

    function clearActive(except) {
        triggers.forEach(trigger => {
            if (trigger === except) return;
            trigger.classList.remove('is-active');
        });
        if (!except) {
            overview.removeAttribute('data-active-method');
        }
    }

    triggers.forEach(trigger => {
        const key = trigger.getAttribute('data-method-trigger');
        trigger.setAttribute('tabindex', '0');
        trigger.setAttribute('role', 'button');

        function activate() {
            clearActive(trigger);
            overview.setAttribute('data-active-method', key);
            trigger.classList.add('is-active');
        }

        function deactivate() {
            trigger.classList.remove('is-active');
            overview.removeAttribute('data-active-method');
        }

        trigger.addEventListener('mouseenter', activate);
        trigger.addEventListener('mouseleave', deactivate);
        trigger.addEventListener('focus', activate);
        trigger.addEventListener('blur', deactivate);
        trigger.addEventListener('click', function(event) {
            event.stopPropagation();
            activate();
        });
        trigger.addEventListener('keydown', function(event) {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            activate();
        });
    });

    document.addEventListener('click', function() {
        clearActive();
    });
}

function setupExperimentTriggers() {
    const triggers = Array.from(document.querySelectorAll('[data-experiment-trigger]'));
    const result = document.querySelector('[data-experiment-result]');
    const panel = document.getElementById('experiment-result');
    if (!triggers.length || !result || !panel) return;

    const experiments = {
        'correlation': {
            src: 'assets/exp/correlation.png',
            alt: 'Correlation experiment result'
        },
        'robustness': {
            src: 'assets/exp/robustness.png',
            alt: 'Robustness experiment result'
        },
        'fidelity': {
            src: 'assets/exp/fidelity.png',
            alt: 'Fidelity experiment result'
        },
        'hyper-parameter': {
            src: 'assets/exp/hyper-parameter.png',
            alt: 'Hyper-parameter experiment result'
        }
    };

    function getGridColumnCount() {
        const grid = triggers[0].parentElement;
        if (!grid) return triggers.length;

        const columns = window.getComputedStyle(grid).gridTemplateColumns;
        const count = columns.split(' ').filter(Boolean).length;
        return count || triggers.length;
    }

    function placePanelAfterRow(trigger) {
        const triggerIndex = triggers.indexOf(trigger);
        const columnCount = getGridColumnCount();
        const rowEndIndex = Math.min(
            Math.ceil((triggerIndex + 1) / columnCount) * columnCount - 1,
            triggers.length - 1
        );
        triggers[rowEndIndex].insertAdjacentElement('afterend', panel);
    }

    function activate(trigger) {
        const key = trigger.getAttribute('data-experiment-trigger');
        const experiment = experiments[key];
        if (!experiment) return;

        triggers.forEach(item => {
            const isCurrent = item === trigger;
            item.classList.toggle('is-active', isCurrent);
            item.setAttribute('aria-expanded', String(isCurrent));
            const label = item.querySelector('.experiment-toggle-text');
            if (label) {
                label.textContent = isCurrent ? 'Hide result ↑' : 'Open result ↓';
            }
        });
        placePanelAfterRow(trigger);
        panel.hidden = false;
        result.src = experiment.src;
        result.alt = experiment.alt;
    }

    function clearActive() {
        triggers.forEach(item => {
            item.classList.remove('is-active');
            item.setAttribute('aria-expanded', 'false');
            const label = item.querySelector('.experiment-toggle-text');
            if (label) {
                label.textContent = 'Open result ↓';
            }
        });
        panel.hidden = true;
        result.removeAttribute('src');
        result.alt = '';
    }

    triggers.forEach(trigger => {
        trigger.setAttribute('tabindex', '0');
        trigger.setAttribute('role', 'button');
        trigger.setAttribute('aria-controls', 'experiment-result');
        trigger.setAttribute('aria-expanded', 'false');

        function toggle(event) {
            event.stopPropagation();
            const isActive = trigger.classList.contains('is-active');
            if (isActive) {
                clearActive();
            } else {
                activate(trigger);
            }
        }

        trigger.addEventListener('click', toggle);
        trigger.addEventListener('keydown', event => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            toggle(event);
        });
    });

    window.addEventListener('resize', () => {
        const activeTrigger = triggers.find(item => item.classList.contains('is-active'));
        if (activeTrigger && !panel.hidden) {
            placePanelAfterRow(activeTrigger);
        }
    });
}

function setupTeaserLayoutScale() {
    const shell = document.querySelector('.teaser-layout-shell');
    const layout = document.querySelector('.teaser-layout');

    if (!shell || !layout) return;

    function updateScale() {
        layout.style.transform = 'none';
        shell.style.width = '';
        shell.style.height = '';
        shell.style.removeProperty('--teaser-layout-scale');
        shell.style.removeProperty('--teaser-detail-font-size');
        shell.style.removeProperty('--teaser-detail-height');
        shell.style.removeProperty('--teaser-detail-width');
        shell.style.removeProperty('--teaser-detail-obstruction');
        shell.classList.remove('is-stacked');

        const parent = shell.parentElement;
        const parentRect = parent ? parent.getBoundingClientRect() : null;
        const viewportWidth = document.documentElement.clientWidth;
        const scrollbarWidth = Math.max(0, window.innerWidth - viewportWidth);
        const safeInset = scrollbarWidth + 12;
        const availableWidth = Math.max(0, Math.min(
            parentRect ? parentRect.width : viewportWidth,
            viewportWidth
        ) - safeInset);

        const wideWidth = layout.offsetWidth;
        if (!wideWidth || !availableWidth) return;

        const isStacked = availableWidth < wideWidth * 0.82;
        if (isStacked) {
            shell.classList.add('is-stacked');
        }

        const baseWidth = layout.offsetWidth;
        if (!baseWidth) return;
        const scale = Math.min(1, availableWidth / baseWidth);

        shell.style.width = `${baseWidth * scale}px`;
        layout.style.transform = `scale(${scale})`;
        shell.style.setProperty('--teaser-layout-scale', String(scale));
        if (isStacked) {
            const targetFontPt = 12;
            const targetHeightPx = viewportWidth <= 480 ? 64 : 60;
            const targetWidthPx = viewportWidth <= 480 ? Math.max(0, viewportWidth - 16) : null;
            shell.style.setProperty('--teaser-detail-font-size', `${targetFontPt / scale}pt`);
            shell.style.setProperty('--teaser-detail-height', `${targetHeightPx / scale}px`);
            if (targetWidthPx) {
                shell.style.setProperty('--teaser-detail-width', `${targetWidthPx / scale}px`);
            }
        }
        const detail = shell.querySelector('.teaser-trial-detail');
        const indexItems = shell.querySelectorAll('.teaser-index-item');
        if (isStacked && detail && indexItems.length) {
            const detailRect = detail.getBoundingClientRect();
            const buttonBottom = Array.from(indexItems).reduce((bottom, item) => {
                return Math.max(bottom, item.getBoundingClientRect().bottom);
            }, 0);
            const obstruction = Math.max(0, (buttonBottom - detailRect.top) / scale);
            shell.style.setProperty('--teaser-detail-obstruction', `${obstruction}px`);
        }
        shell.style.height = `${layout.offsetHeight * scale}px`;
    }

    window._updateTeaserLayoutScale = updateScale;
    updateScale();
    window.addEventListener('resize', updateScale);
    if ('ResizeObserver' in window) {
        new ResizeObserver(updateScale).observe(shell);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setupMotivationVideoAutoplay();
    setupAbstractToggle();
    setupTeaserHover();
    setupTeaserLayoutScale();
    setupFireworks();
    setupMethodTriggers();
    setupExperimentTriggers();
    setupDemoVideoSync();
    setupNmrChart();
});

function setupMotivationVideoAutoplay() {
    const taskColumns = Array.from(document.querySelectorAll('.motivation-task-col'));
    if (taskColumns.length === 0) return;

    const blankGif = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';

    function preloadImages(images) {
        images.forEach(image => {
            const src = image.dataset.syncSrc;
            if (!src) return;
            const preload = new Image();
            preload.src = src;
        });
    }

    function restartGifGroup(column) {
        const images = Array.from(column.querySelectorAll('img'));
        if (images.length === 0) return;

        images.forEach(image => {
            if (!image.dataset.syncSrc) {
                image.dataset.syncSrc = image.getAttribute('src') || '';
            }
        });

        preloadImages(images);
        images.forEach(image => {
            image.src = blankGif;
        });

        requestAnimationFrame(() => {
            images.forEach(image => {
                image.src = image.dataset.syncSrc;
            });
        });
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            restartGifGroup(entry.target);
        });
    }, { threshold: 0.25 });

    taskColumns.forEach(column => {
        Array.from(column.querySelectorAll('img')).forEach(image => {
            image.dataset.syncSrc = image.getAttribute('src') || '';
        });
        observer.observe(column);
    });
}

function setupDemoVideoSync() {
    const demo = document.getElementById('close-jar-demo');
    if (!demo) return;

    const videos = Array.from(demo.querySelectorAll('video.demo-sync-video'));
    if (videos.length < 2) return;

    let cycle = 0;
    let active = false;
    let starting = false;
    let endedCount = 0;

    function waitForReady(video) {
        if (video.readyState >= 1) return Promise.resolve();
        return new Promise(resolve => {
            video.addEventListener('loadedmetadata', resolve, { once: true });
            video.load();
        });
    }

    videos.forEach(video => {
        video.muted = true;
        video.playsInline = true;
        video.preload = 'auto';
        video.loop = false;
        video.addEventListener('ended', function() {
            if (!active || starting) return;
            endedCount += 1;
            if (endedCount === videos.length) {
                restartAll();
            }
        });
    });

    function restartAll() {
        if (!active || starting) return;

        starting = true;
        endedCount = 0;
        cycle += 1;
        const currentCycle = cycle;

        Promise.all(videos.map(waitForReady)).then(function() {
            if (!active || currentCycle !== cycle) return;

            videos.forEach(video => {
                video.pause();
                video.currentTime = 0;
            });

            requestAnimationFrame(function() {
                if (!active || currentCycle !== cycle) return;

                videos.forEach(video => {
                    video.play().catch(() => {});
                });
                starting = false;
            });
        });
    }

    function pauseAll() {
        active = false;
        cycle += 1;
        starting = false;
        videos.forEach(video => video.pause());
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                active = true;
                restartAll();
            } else {
                pauseAll();
            }
        });
    }, { threshold: 0.2 });

    observer.observe(demo);
    window.addEventListener('load', function() {
        if (active) restartAll();
    });
}

function setupNmrChart() {
    const chart = document.getElementById('nmr-chart');
    if (!chart) return;

    const source = chart.getAttribute('data-src');
    if (!source) return;

    fetch(source)
        .then(response => {
            if (!response.ok) throw new Error('Unable to load NMR data');
            return response.text();
        })
        .then(text => {
            const rows = parseCsv(text);
            const points = rows
                .map(row => ({
                    step: Number(row.step),
                    nmr: Number(row.nmr),
                    nmr_front: Number(row.nmr_front),
                    nmr_wrist: Number(row.nmr_wrist),
                    nmr_overhead: Number(row.nmr_overhead)
                }))
                .filter(point => (
                    Number.isFinite(point.step) &&
                    Number.isFinite(point.nmr) &&
                    Number.isFinite(point.nmr_front) &&
                    Number.isFinite(point.nmr_wrist) &&
                    Number.isFinite(point.nmr_overhead)
                ));

            if (points.length === 0) throw new Error('No valid NMR rows found');
            let renderFrame = null;
            function scheduleRender() {
                if (renderFrame) cancelAnimationFrame(renderFrame);
                renderFrame = requestAnimationFrame(function() {
                    renderFrame = null;
                    renderNmrChart(chart, points);
                });
            }
            scheduleRender();
            window.addEventListener('resize', scheduleRender);

            const latestRow = rows[rows.length - 1];
            updateNmrValue('nmr-front-value', latestRow.nmr_front);
            updateNmrValue('nmr-overhead-value', latestRow.nmr_overhead);
            updateNmrValue('nmr-wrist-value', latestRow.nmr_wrist);
            updateNmrValue('nmr-latest-value', latestRow.nmr);
        })
        .catch(error => {
            chart.innerHTML = `<div class="demo-chart-error">${error.message}</div>`;
            ['nmr-front-value', 'nmr-overhead-value', 'nmr-wrist-value', 'nmr-latest-value'].forEach(id => {
                const value = document.getElementById(id);
                if (value) value.textContent = 'Unavailable';
            });
        });
}

function updateNmrValue(id, rawValue) {
    const element = document.getElementById(id);
    const value = Number(rawValue);
    if (!element) return;
    element.textContent = Number.isFinite(value) ? value.toFixed(3) : 'Unavailable';
}

function parseCsv(text) {
    const lines = text.trim().split(/\r?\n/);
    const headers = lines.shift().split(',').map(header => header.trim());
    return lines.map(line => {
        const values = line.split(',');
        return headers.reduce((row, header, index) => {
            row[header] = values[index] ? values[index].trim() : '';
            return row;
        }, {});
    });
}

function renderNmrChart(container, points) {
    const isCompact = (container.getBoundingClientRect().width || window.innerWidth) < 520;
    const width = isCompact ? 360 : 860;
    const height = isCompact ? 300 : 360;
    const margin = isCompact
        ? { top: 18, right: 14, bottom: 80, left: 54 }
        : { top: 20, right: 28, bottom: 66, left: 58 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const series = [
        { key: 'nmr', label: 'all views', color: '#181818', width: 4 },
        { key: 'nmr_front', label: 'front', color: '#7FB3D5', width: 2 },
        { key: 'nmr_wrist', label: 'wrist', color: '#F4A261', width: 2 },
        { key: 'nmr_overhead', label: 'overhead', color: '#76C27A', width: 2 }
    ];

    const minStep = Math.min(...points.map(point => point.step));
    const maxStep = Math.max(...points.map(point => point.step));
    const minNmr = 0;
    const allValues = points.flatMap(point => series.map(item => point[item.key]));
    const maxNmr = Math.max(1, Math.max(...allValues) * 1.04);
    const meanNmr = points.reduce((sum, point) => sum + point.nmr, 0) / points.length;

    const x = step => margin.left + ((step - minStep) / (maxStep - minStep || 1)) * plotWidth;
    const y = nmr => margin.top + (1 - ((nmr - minNmr) / (maxNmr - minNmr || 1))) * plotHeight;

    function makePath(key) {
        return points.map((point, index) => {
            const command = index === 0 ? 'M' : 'L';
            return `${command}${x(point.step).toFixed(2)},${y(point[key]).toFixed(2)}`;
        }).join(' ');
    }

    const yTicks = [0, 0.2, 0.4, 0.6, 0.8, 1].filter(tick => tick <= maxNmr);
    const xTickCandidates = isCompact
        ? [minStep, 50, 100, 150, maxStep]
        : [minStep, 25, 50, 75, 100, 125, 150, maxStep];
    const xTicks = xTickCandidates.filter((tick, index, ticks) => (
        tick >= minStep && tick <= maxStep && ticks.indexOf(tick) === index
    ));

    const yGrid = yTicks.map(tick => `
        <line class="grid-line" x1="${margin.left}" y1="${y(tick).toFixed(2)}" x2="${width - margin.right}" y2="${y(tick).toFixed(2)}"></line>
        <text x="${margin.left - 10}" y="${(y(tick) + 4).toFixed(2)}" text-anchor="end">${tick.toFixed(1)}</text>
    `).join('');

    const xLabels = xTicks.map(tick => `
        <text x="${x(tick).toFixed(2)}" y="${height - margin.bottom + 24}" text-anchor="middle">${tick}</text>
    `).join('');

    const seriesPaths = series.map(item => `
        <path
            class="nmr-series-line"
            d="${makePath(item.key)}"
            stroke="${item.color}"
            stroke-width="${item.width}">
        </path>
    `).join('');

    const meanY = y(meanNmr).toFixed(2);
    const legendY = isCompact ? height - 34 : height - 14;
    const legendStartX = isCompact ? margin.left : margin.left + 48;
    const legendItems = series.map((item, index) => {
        const legendX = isCompact
            ? legendStartX + (index % 3) * 98
            : legendStartX + index * 124;
        const itemLegendY = isCompact
            ? legendY + Math.floor(index / 3) * 17
            : legendY;
        return `
            <line x1="${legendX}" y1="${itemLegendY}" x2="${legendX + 24}" y2="${itemLegendY}" stroke="${item.color}" stroke-width="${item.width}"></line>
            <text x="${legendX + 32}" y="${itemLegendY + 4}">${item.label}</text>
        `;
    }).join('');
    const meanLegendX = isCompact ? legendStartX + 98 : legendStartX + 496;
    const meanLegendY = isCompact ? legendY + 17 : legendY;

    container.innerHTML = `
        <svg class="${isCompact ? 'is-compact' : ''}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="nmr-chart-title">
            <title id="nmr-chart-title">NMR@10 over entire episode by view</title>
            ${yGrid}
            <line class="axis-line" x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height - margin.bottom}"></line>
            <line class="axis-line" x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}"></line>
            ${seriesPaths}
            <line class="nmr-mean-line" x1="${margin.left}" y1="${meanY}" x2="${width - margin.right}" y2="${meanY}"></line>
            ${xLabels}
            <g class="nmr-legend">
                ${legendItems}
                <line x1="${meanLegendX}" y1="${meanLegendY}" x2="${meanLegendX + 24}" y2="${meanLegendY}" class="nmr-mean-line"></line>
                <text x="${meanLegendX + 32}" y="${meanLegendY + 4}">mean=${meanNmr.toFixed(4)}</text>
            </g>
            <text class="axis-title" x="${margin.left + plotWidth / 2}" y="${height - (isCompact ? 48 : 36)}" text-anchor="middle">Step</text>
            <text class="axis-title" x="${isCompact ? 14 : 18}" y="${margin.top + plotHeight / 2}" text-anchor="middle" transform="rotate(-90 ${isCompact ? 14 : 18} ${margin.top + plotHeight / 2})">NMR@10</text>
        </svg>
    `;
}

function setupDemoTopHeightBalance() {
    const topGrid = document.querySelector('.demo-top-grid');
    const rollout = document.querySelector('.demo-original-block');
    const comparison = document.querySelector('.demo-attribution-block');
    const overview = document.querySelector('.demo-original-layout .demo-overview-panel');

    if (!topGrid || !rollout || !comparison || !overview) return;

    let frame = null;

    function isTwoColumnLayout() {
        return window.matchMedia('(min-width: 769px)').matches;
    }

    function balance() {
        frame = null;

        if (!isTwoColumnLayout()) {
            overview.style.width = '';
            return;
        }

        overview.style.width = '';

        requestAnimationFrame(function() {
            const comparisonHeight = comparison.getBoundingClientRect().height;
            const rolloutHeight = rollout.getBoundingClientRect().height;
            const overviewHeight = overview.getBoundingClientRect().height;
            const availableWidth = overview.parentElement.getBoundingClientRect().width;

            if (!comparisonHeight || !rolloutHeight || !overviewHeight || !availableWidth) return;

            const targetOverview = overviewHeight + (comparisonHeight - rolloutHeight);
            const minOverview = availableWidth * 0.42;
            const maxOverview = availableWidth;
            const nextOverview = Math.max(minOverview, Math.min(maxOverview, targetOverview));

            overview.style.width = `${nextOverview}px`;
        });
    }

    function scheduleBalance() {
        if (frame) cancelAnimationFrame(frame);
        frame = requestAnimationFrame(balance);
    }

    window.addEventListener('resize', scheduleBalance);
    window.addEventListener('load', scheduleBalance);

    if (window.ResizeObserver) {
        const observer = new ResizeObserver(scheduleBalance);
        observer.observe(topGrid);
        observer.observe(comparison);
    }

    scheduleBalance();
}
