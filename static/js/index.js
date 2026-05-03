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

function setupTeaserLayoutScale() {
    const shell = document.querySelector('.teaser-layout-shell');
    const layout = document.querySelector('.teaser-layout');

    if (!shell || !layout) return;

    function updateScale() {
        layout.style.transform = 'none';
        shell.style.width = '';
        shell.style.height = '';
        shell.style.removeProperty('--teaser-layout-scale');
        shell.style.removeProperty('--teaser-inverse-scale');
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

        if (availableWidth < wideWidth * 0.82) {
            shell.classList.add('is-stacked');
        }

        const baseWidth = layout.offsetWidth;
        if (!baseWidth) return;
        const scale = Math.min(1, availableWidth / baseWidth);

        shell.style.width = `${baseWidth * scale}px`;
        layout.style.transform = `scale(${scale})`;
        shell.style.height = `${layout.offsetHeight * scale}px`;
        shell.style.setProperty('--teaser-layout-scale', String(scale));
        shell.style.setProperty('--teaser-inverse-scale', String(1 / scale));
    }

    window._updateTeaserLayoutScale = updateScale;
    updateScale();
    window.addEventListener('resize', updateScale);
    window.addEventListener('load', updateScale);
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
    setupDemoVideoSync();
    setupNmrChart();
    setupDemoTopHeightBalance();
});

function setupMotivationVideoAutoplay() {
    const videos = document.querySelectorAll('.motivation-task-col video');
    if (videos.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const video = entry.target;
            if (entry.isIntersecting) {
                video.play().catch(() => {});
            } else {
                video.pause();
            }
        });
    }, { threshold: 0.25 });

    videos.forEach(video => observer.observe(video));
}

function setupDemoVideoSync() {
    const demo = document.getElementById('close-jar-demo');
    if (!demo) return;

    const videos = Array.from(demo.querySelectorAll('video.demo-sync-video'));
    if (videos.length < 2) return;

    const overviewVideo = demo.querySelector('video.demo-overview-video');
    if (!overviewVideo) return;

    let restarting = false;

    function resetAll() {
        videos.forEach(video => {
            video.loop = false;
            video.pause();
            if (Number.isFinite(video.duration)) {
                video.currentTime = 0;
            }
        });
    }

    function playAll() {
        videos.forEach(video => video.play().catch(() => {}));
    }

    function restartFromOverview() {
        if (restarting) return;
        restarting = true;
        resetAll();
        requestAnimationFrame(function() {
            playAll();
            restarting = false;
        });
    }

    videos.forEach(video => {
        video.loop = false;
        if (video !== overviewVideo) {
            video.addEventListener('ended', function() {
                video.pause();
            });
        }
    });

    overviewVideo.addEventListener('ended', restartFromOverview);
    overviewVideo.addEventListener('pause', function() {
        videos.forEach(video => {
            if (video !== overviewVideo) video.pause();
        });
    });
    overviewVideo.addEventListener('play', function() {
        videos.forEach(video => {
            if (video !== overviewVideo && !video.ended) {
                video.play().catch(() => {});
            }
        });
    });

    window.addEventListener('load', function() {
        resetAll();
        playAll();
    });
    resetAll();
    playAll();
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
            renderNmrChart(chart, points);

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
    const width = 860;
    const height = 360;
    const margin = { top: 24, right: 142, bottom: 44, left: 58 };
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
    const xTicks = [minStep, 25, 50, 75, 100, 125, 150, maxStep].filter((tick, index, ticks) => (
        tick >= minStep && tick <= maxStep && ticks.indexOf(tick) === index
    ));

    const yGrid = yTicks.map(tick => `
        <line class="grid-line" x1="${margin.left}" y1="${y(tick).toFixed(2)}" x2="${width - margin.right}" y2="${y(tick).toFixed(2)}"></line>
        <text x="${margin.left - 10}" y="${(y(tick) + 4).toFixed(2)}" text-anchor="end">${tick.toFixed(1)}</text>
    `).join('');

    const xLabels = xTicks.map(tick => `
        <text x="${x(tick).toFixed(2)}" y="${height - 14}" text-anchor="middle">${tick}</text>
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
    const legendX = width - margin.right + 20;
    const legendItems = series.map((item, index) => {
        const legendY = margin.top + 10 + index * 22;
        return `
            <line x1="${legendX}" y1="${legendY}" x2="${legendX + 28}" y2="${legendY}" stroke="${item.color}" stroke-width="${item.width}"></line>
            <text x="${legendX + 38}" y="${legendY + 4}">${item.label}</text>
        `;
    }).join('');

    container.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="nmr-chart-title">
            <title id="nmr-chart-title">NMR@10 over rollout steps by view</title>
            ${yGrid}
            <line class="axis-line" x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height - margin.bottom}"></line>
            <line class="axis-line" x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}"></line>
            ${seriesPaths}
            <line class="nmr-mean-line" x1="${margin.left}" y1="${meanY}" x2="${width - margin.right}" y2="${meanY}"></line>
            ${xLabels}
            <g class="nmr-legend">
                ${legendItems}
                <line x1="${legendX}" y1="${margin.top + 98}" x2="${legendX + 28}" y2="${margin.top + 98}" class="nmr-mean-line"></line>
                <text x="${legendX + 38}" y="${margin.top + 102}">mean=${meanNmr.toFixed(4)}</text>
            </g>
            <text x="${margin.left + plotWidth / 2}" y="${height - 2}" text-anchor="middle">Step</text>
            <text x="18" y="${margin.top + plotHeight / 2}" text-anchor="middle" transform="rotate(-90 18 ${margin.top + plotHeight / 2})">NMR@10</text>
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
