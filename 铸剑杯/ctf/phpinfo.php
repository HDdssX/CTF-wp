<?php
ini_set("display_errors", "On");
include_once("config.php");

$sourceCode = '';

if (isset($_GET['so']) && isset($_GET['key'])) {
    if (is_numeric($_GET['so']) && $_GET['key'] === $secret) {
        array_map(function ($file) {
            echo $file . "\n";
        }, glob('/tmp/*'));
        putenv("LD_PRELOAD=/tmp/" . $_GET['so'] . ".so");
    }
}

if (isset($_GET['cloversec']) && isset($_GET['ctf'])) {
    $a = new ReflectionClass($_GET['cloversec']);
    $b = $a->newInstanceArgs($_GET['ctf']);
} elseif (isset($_GET['clean'])) {
    array_map('unlink', glob('/tmp/*'));
} else {
    $welcome = 'Welcome to CloverSec-2025年“铸剑杯”全国大学生网络安全攻防竞赛!～祝大家玩的愉快. D1a0y1bb.';
    $sourceCode = htmlspecialchars(file_get_contents(__FILE__), ENT_QUOTES, 'UTF-8');
}

// 什么鬼phpinfo.html啊
?>

<?php if (!empty($sourceCode)): ?>
    <pre data-source-pre><?php echo $sourceCode; ?></pre>
<?php endif; ?>

<script>
    document.addEventListener('DOMContentLoaded', () => {
        const panel = document.querySelector('#code-panel');
        const codeTarget = document.querySelector('#code-output');
        const rawPre = document.querySelector('[data-source-pre]');
        const toggleButtons = document.querySelectorAll('[data-toggle-code]');
        const copyButton = document.querySelector('[data-copy-code]');
        const meteorOverlay = document.getElementById('meteor-overlay');
        const meteorCanvas = document.getElementById('meteor-canvas');
        const meteorCtx = meteorCanvas ? meteorCanvas.getContext('2d') : null;
        let codeText = '';
        let snippetPool = [];
        const keywordRegex = /\b(class|function|if|else|elseif|return|while|for|foreach|echo|include|require|new|public|protected|private|static|var|try|catch|switch|case|break|continue|default|throw)\b/;
        let isAnimating = false;

        const resizeCanvas = () => {
            if (!meteorCanvas) return;
            meteorCanvas.width = window.innerWidth;
            meteorCanvas.height = window.innerHeight;
        };

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

        const buildSnippetPool = () => {
            const source = codeText && codeText.length > 60 ? codeText : "<?php echo 'AI Meeting Minutes'; ?>";
            snippetPool = [];
            const poolSize = 160;
            for (let i = 0; i < poolSize; i++) {
                snippetPool.push(extractSnippet(source));
            }
        };

        const extractSnippet = (source) => {
            const lines = source.replace(/\t/g, '    ')
                .split('\n')
                .map((line) => line.trim())
                .filter(Boolean);
            const maxStart = Math.max(0, lines.length - 6);
            const startIdx = Math.floor(Math.random() * (maxStart + 1));
            const sliceLen = 2 + Math.floor(Math.random() * 4);
            return lines.slice(startIdx, startIdx + sliceLen);
        };

        const takeSnippet = () => {
            if (!snippetPool.length) return ["<?php echo 'Loading...'; ?>"];
            const index = Math.floor(Math.random() * snippetPool.length);
            return snippetPool[index];
        };

        const playMeteorShow = (duration = 4200) => {
            if (!meteorOverlay || !meteorCtx || !meteorCanvas) return Promise.resolve();
            meteorOverlay.classList.remove('fade-out');
            meteorOverlay.classList.add('active');

            const glyphChars = (codeText || 'AI Meeting Minutes · Watch Demo').replace(/\s+/g, '') || 'AMMWD';
            const glyphCount = clamp(Math.floor((meteorCanvas.width * meteorCanvas.height) / 22000), 60, 130);
            const streakCount = Math.floor(glyphCount * 0.55);
            const sparkCount = Math.floor(glyphCount * 0.65);

            const glyphs = Array.from({ length: glyphCount }, () => createGlyph());
            const streaks = Array.from({ length: streakCount }, () => createStreak());
            const sparks = Array.from({ length: sparkCount }, () => createSpark());

            function resetGlyph(glyph, fullReset = false) {
                glyph.lines = takeSnippet();
                glyph.x = Math.random() * meteorCanvas.width;
                glyph.y = fullReset ? Math.random() * meteorCanvas.height : -Math.random() * meteorCanvas.height * 0.4;
                glyph.speed = 90 + Math.random() * 220;
                glyph.drift = -50 + Math.random() * 100;
                glyph.size = 12 + Math.random() * 6;
                glyph.opacity = 0.55 + Math.random() * 0.35;
                glyph.shadow = 12 + Math.random() * 18;
                glyph.rotation = (Math.random() - 0.5) * 0.12;
            }

            function resetStreak(streak, fullReset = false) {
                streak.x = Math.random() * meteorCanvas.width;
                streak.y = fullReset ? Math.random() * meteorCanvas.height : -Math.random() * meteorCanvas.height * 0.5;
                streak.length = 80 + Math.random() * 140;
                streak.speed = 400 + Math.random() * 600;
                streak.thickness = 1 + Math.random() * 2.5;
                streak.hue = 35 + Math.random() * 35;
            }

            function resetSpark(spark, fullReset = false) {
                spark.x = Math.random() * meteorCanvas.width;
                spark.y = fullReset ? Math.random() * meteorCanvas.height : Math.random() * meteorCanvas.height * 0.5;
                spark.size = 1 + Math.random() * 2;
                spark.speed = 60 + Math.random() * 120;
                spark.alpha = 0.3 + Math.random() * 0.4;
                spark.twist = Math.random() * Math.PI * 2;
            }

            function createGlyph() {
                const glyph = {};
                resetGlyph(glyph, true);
                return glyph;
            }

            function createStreak() {
                const streak = {};
                resetStreak(streak, true);
                return streak;
            }

            function createSpark() {
                const spark = {};
                resetSpark(spark, true);
                return spark;
            }

            let start = null;
            let last = null;

            const tokenizeLine = (line) => {
                const parts = line.split(/(\s+)/);
                return parts.map((part) => {
                    if (!part.trim().length) {
                        return { text: part, color: 'rgba(226, 232, 240, 0.6)' };
                    }
                    if (/^\/\//.test(part.trim()) || /^#/.test(part.trim())) {
                        return { text: part, color: '#94a3b8' };
                    }
                    if (/^["'`].*["'`]$/.test(part)) {
                        return { text: part, color: '#34d399' };
                    }
                    if (/^\$[A-Za-z_]\w*/.test(part)) {
                        return { text: part, color: '#f472b6' };
                    }
                    if (keywordRegex.test(part)) {
                        return { text: part, color: '#fbbf24' };
                    }
                    if (/^\d+/.test(part)) {
                        return { text: part, color: '#60a5fa' };
                    }
                    return { text: part, color: 'rgba(226, 232, 240, 0.85)' };
                });
            };

            return new Promise((resolve) => {
                const draw = (timestamp) => {
                    if (!start) {
                        start = timestamp;
                        last = timestamp;
                    }
                    const elapsed = timestamp - start;
                    const delta = (timestamp - last) / 1000;
                    last = timestamp;

                    meteorCtx.fillStyle = 'rgba(2, 6, 23, 0.3)';
                    meteorCtx.fillRect(0, 0, meteorCanvas.width, meteorCanvas.height);

                    // sparks
                    sparks.forEach((spark) => {
                        spark.twist += delta * 2;
                        spark.x += Math.sin(spark.twist) * 30 * delta;
                        spark.y += spark.speed * delta;
                        if (spark.y > meteorCanvas.height + 10) resetSpark(spark);
                        meteorCtx.globalAlpha = spark.alpha;
                        meteorCtx.fillStyle = 'rgba(148, 163, 184, 0.45)';
                        meteorCtx.fillRect(spark.x, spark.y, spark.size, spark.size * 3);
                    });

                    // streaks
                    streaks.forEach((streak) => {
                        streak.y += streak.speed * delta;
                        streak.x += 30 * delta;
                        if (streak.y - streak.length > meteorCanvas.height) resetStreak(streak);
                        const gradient = meteorCtx.createLinearGradient(streak.x, streak.y, streak.x - streak.length, streak.y - streak.length);
                        gradient.addColorStop(0, `hsla(${streak.hue}, 100%, 70%, 0)`);
                        gradient.addColorStop(0.6, `hsla(${streak.hue + 10}, 95%, 72%, 0.35)`);
                        gradient.addColorStop(1, `hsla(${streak.hue + 25}, 100%, 82%, 0.95)`);
                        meteorCtx.strokeStyle = gradient;
                        meteorCtx.lineWidth = streak.thickness;
                        meteorCtx.beginPath();
                        meteorCtx.moveTo(streak.x, streak.y);
                        meteorCtx.lineTo(streak.x - streak.length, streak.y - streak.length);
                        meteorCtx.stroke();
                    });

                    // glyph snippets
                    meteorCtx.globalAlpha = 1;
                    glyphs.forEach((glyph) => {
                        glyph.y += glyph.speed * delta;
                        glyph.x += glyph.drift * delta;
                        const snippetHeight = glyph.lines.length * (glyph.size * 1.2);
                        const snippetWidth = Math.max(...glyph.lines.map((line) => line.length)) * (glyph.size * 0.6);
                        if (glyph.y - snippetHeight > meteorCanvas.height || glyph.x > meteorCanvas.width + 120 || glyph.x + snippetWidth < -120) {
                            resetGlyph(glyph);
                        }
                        meteorCtx.save();
                        meteorCtx.translate(glyph.x, glyph.y);
                        meteorCtx.rotate(glyph.rotation);
                        meteorCtx.shadowColor = `hsla(45, 100%, 80%, ${glyph.opacity})`;
                        meteorCtx.shadowBlur = glyph.shadow;
                        meteorCtx.globalAlpha = glyph.opacity;
                        meteorCtx.font = `${glyph.size}px 'JetBrains Mono', monospace`;
                        glyph.lines.forEach((line, idx) => {
                            const tokens = tokenizeLine(line);
                            let offsetX = 0;
                            tokens.forEach(({ text, color }) => {
                                meteorCtx.fillStyle = color;
                                meteorCtx.fillText(text, offsetX, idx * (glyph.size * 1.15));
                                offsetX += meteorCtx.measureText(text).width;
                            });
                        });
                        meteorCtx.restore();
                    });

                    if (elapsed < duration) {
                        requestAnimationFrame(draw);
                    } else {
                        meteorOverlay.classList.add('fade-out');
                        setTimeout(() => {
                            meteorOverlay.classList.remove('active', 'fade-out');
                            meteorCtx.clearRect(0, 0, meteorCanvas.width, meteorCanvas.height);
                            resolve();
                        }, 450);
                    }
                };
                requestAnimationFrame(draw);
            });
        };

        if (rawPre && codeTarget) {
            rawPre.classList.add('code-block');
            rawPre.style.display = 'block';
            codeText = rawPre.innerText;

            const wrapper = document.createElement('div');
            wrapper.className = 'code-output-inner';
            wrapper.appendChild(rawPre);

            codeTarget.innerHTML = '';
            codeTarget.appendChild(wrapper);
            buildSnippetPool();
        } else if (codeTarget) {
            codeTarget.innerHTML = '<p class="code-subtitle" style="margin:0;">暂无源码可显示</p>';
        }

        const updateToggleLabels = (isOpen) => {
            toggleButtons.forEach((btn) => {
                const label = btn.querySelector('span');
                if (label) {
                    label.textContent = isOpen ? '隐藏源码' : '查看源码';
                }
            });
        };

        toggleButtons.forEach((button) => {
            button.addEventListener('click', async () => {
                if (!panel || isAnimating) return;

                if (panel.classList.contains('open')) {
                    panel.classList.remove('open');
                    updateToggleLabels(false);
                    return;
                }

                isAnimating = true;
                await playMeteorShow();
                panel.classList.add('open');
                updateToggleLabels(true);
                isAnimating = false;
            });
        });

        if (panel) {
            panel.classList.remove('open');
            updateToggleLabels(false);
        }

        if (copyButton) {
            if (!codeText) {
                copyButton.disabled = true;
                copyButton.textContent = '暂无源码';
            }

            copyButton.addEventListener('click', async () => {
                if (!codeText) return;

                try {
                    await navigator.clipboard.writeText(codeText);
                    copyButton.textContent = '已复制';
                } catch (err) {
                    const textarea = document.createElement('textarea');
                    textarea.value = codeText;
                    textarea.style.position = 'fixed';
                    textarea.style.opacity = '0';
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    copyButton.textContent = '已复制';
                }

                setTimeout(() => {
                    copyButton.textContent = codeText ? '复制源码' : '暂无源码';
                }, 1600);
            });
        }
    });
</script>
</body>

</html>