/* ==========================================================================
   Magische Miesmuschel — App-Logik
   Alles Vanilla JS, keine externen Libraries.
   Daten werden aus data/statistik.js gelesen (window.__MIESMUSCHEL_STAT).
   ========================================================================== */

/* ---- Service Worker registrieren (PWA / Offline-Support auf iPhone) ---- */
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(err => {
      console.warn('Service Worker konnte nicht registriert werden:', err);
    });
  });
}


/* ---- Blubberblasen-Animation ---- */
(function renderBubbles() {
  const container = document.getElementById('bubbles');
  if (!container) return;
  for (let i = 0; i < 20; i++) {
    const b = document.createElement('div');
    b.className = 'bubble';
    const size = Math.random() * 40 + 10;
    b.style.width = size + 'px';
    b.style.height = size + 'px';
    b.style.left = Math.random() * 100 + '%';
    b.style.animationDuration = (Math.random() * 15 + 10) + 's';
    b.style.animationDelay = Math.random() * 10 + 's';
    container.appendChild(b);
  }
})();

/* ---- Tab-Navigation ---- */
function showSection(id, btn) {
  document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Historie-Tab on demand rendern
  if (id === 'historie') renderHistorie();
}

/* ---- Dynamischer Header + Footer aus aktuellem tipps.json ---- */
(function renderHeaderAndFooter() {
  const data = window.__MIESMUSCHEL_TIPPS;
  if (!data) return;

  const subtitle   = document.getElementById('header-subtitle');
  const dateLine   = document.getElementById('header-dateline');
  const footerMeta = document.getElementById('footer-meta');

  const n_spiele = (data.spiele || []).length;
  const n_einzel = (data.einzeltipps || []).length;
  const n_kombi  = (data.kombis || []).length;

  if (subtitle) {
    subtitle.textContent =
      `Tipp-Dossier ${data.datum || ''} · bet365 DE · ${n_spiele} Spiele · ${n_einzel} Einzeltipps · ${n_kombi} Kombis`;
  }

  if (dateLine && data.datum) {
    const d = new Date(data.datum + 'T12:00:00');
    const wochentage = ['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];
    const monate = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'];
    let txt = `🗓️ ${wochentage[d.getDay()]}, ${d.getDate()}. ${monate[d.getMonth()]} ${d.getFullYear()}`;
    if (data.hinweis) txt += ` · ${data.hinweis}`;
    dateLine.textContent = txt;
  }

  if (footerMeta) {
    footerMeta.textContent =
      `Dossier ${data.datum || ''} · ${n_spiele} Spiele · ${n_einzel} Einzeltipps · ${n_kombi} Kombi-Stufen · Bleib ehrlich mit dir 🍀`;
  }
})();

/* ---- Risiko-Kombi-Tabs ---- */
function showRisk(id, tab) {
  document.querySelectorAll('.risk-content').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.risk-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  tab.classList.add('active');
}

/* ==========================================================================
   Historie-Dashboard
   Liest window.__MIESMUSCHEL_STAT (aus data/statistik.js).
   Wird gefüllt, wenn der User scripts/statistik_berechnen.bat läuft.
   ========================================================================== */

function fmtNum(v, dec = 0) {
  if (v === null || v === undefined || isNaN(v)) return '–';
  return Number(v).toLocaleString('de-DE', {
    minimumFractionDigits: dec, maximumFractionDigits: dec
  });
}

function fmtSigned(v, suffix = '') {
  if (v === null || v === undefined || isNaN(v)) return '–';
  const sign = v > 0 ? '+' : '';
  return sign + fmtNum(v, 1) + suffix;
}

function klasse(v) {
  if (v === null || v === undefined || isNaN(v)) return '';
  if (v > 0) return 'pos';
  if (v < 0) return 'neg';
  return '';
}

function renderKpiBlock(label, stat) {
  if (!stat) return '';
  const roiCls = klasse(stat.roi_prozent);
  const nettoCls = klasse(stat.netto);
  return `
    <div class="breakdown-card">
      <h4>${label}</h4>
      <div class="historie-kpis">
        <div class="kpi-tile"><div class="kpi-val">${fmtNum(stat.tipps)}</div><div class="kpi-lbl">Tipps</div></div>
        <div class="kpi-tile"><div class="kpi-val">${fmtNum(stat.trefferquote, 1)}%</div><div class="kpi-lbl">Trefferquote</div></div>
        <div class="kpi-tile ${roiCls}"><div class="kpi-val">${fmtSigned(stat.roi_prozent, '%')}</div><div class="kpi-lbl">ROI</div></div>
        <div class="kpi-tile ${nettoCls}"><div class="kpi-val">${fmtSigned(stat.netto, ' €')}</div><div class="kpi-lbl">Netto</div></div>
      </div>
    </div>
  `;
}

function renderBreakdown(title, dict) {
  if (!dict || Object.keys(dict).length === 0) {
    return `<div class="breakdown-card"><h4>${title}</h4><p style="color:#8fb4d8;font-size:0.88em;">Noch keine Daten.</p></div>`;
  }
  const rows = Object.entries(dict)
    .sort((a, b) => (b[1].tipps || 0) - (a[1].tipps || 0))
    .map(([key, s]) => {
      const roiCls = klasse(s.roi_prozent);
      return `
        <tr>
          <td>${key}</td>
          <td class="num">${fmtNum(s.tipps)}</td>
          <td class="num">${fmtNum(s.trefferquote, 1)}%</td>
          <td class="num ${roiCls}">${fmtSigned(s.roi_prozent, '%')}</td>
        </tr>
      `;
    }).join('');
  return `
    <div class="breakdown-card">
      <h4>${title}</h4>
      <table class="breakdown-table">
        <thead><tr><th>Name</th><th>Tipps</th><th>Quote</th><th>ROI</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderStopSignals(stat) {
  if (!stat) return '';
  const alerts = [];
  const check = (dict, prefix) => {
    if (!dict) return;
    Object.entries(dict).forEach(([k, s]) => {
      if ((s.tipps || 0) >= 20 && (s.trefferquote || 0) < 40) {
        alerts.push(`${prefix}: <strong>${k}</strong> — ${fmtNum(s.trefferquote, 1)}% bei ${s.tipps} Tipps`);
      }
    });
  };
  check(stat.nach_liga, 'Liga');
  check(stat.nach_markt, 'Markt');
  check(stat.nach_kategorie, 'Kategorie');
  if (alerts.length === 0) return '';
  return `
    <div class="stop-signal">
      <h4>🚨 Stop-Signal — hier verlierst du Geld</h4>
      <p>Bei folgenden Bereichen liegt die Trefferquote unter 40 % (mind. 20 Tipps). Überleg ob du diese Märkte streichst:</p>
      <ul>${alerts.map(a => `<li>${a}</li>`).join('')}</ul>
    </div>
  `;
}

function renderLessons(lessons) {
  if (!lessons || lessons.length === 0) {
    return '<p style="color:#8fb4d8;font-size:0.9em;">Noch keine Lessons vermerkt.</p>';
  }
  return lessons
    .slice()
    .sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
    .map(l => `
      <div class="lesson-item">
        <span class="lesson-date">${l.datum || '–'}</span>
        <span class="lesson-cat">${l.kategorie || 'Allgemein'}</span>
        <div class="lesson-txt">${l.lesson || ''}</div>
      </div>
    `).join('');
}

/* ==========================================================================
   Tages-Dossier rendern (aus data/tipps.js -> window.__MIESMUSCHEL_TIPPS)
   Ersetzt die statischen Sections #spiele, #einzel, #risiko wenn Daten da sind.
   ========================================================================== */

const KAT_REIHENFOLGE = { safe: 0, value: 1, wackel: 2, risk: 3, moonshot: 4 };

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function fmtQuote(q) { return (Number(q) || 0).toFixed(2); }
function fmtTime(iso) {
  try { return new Date(iso).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr'; }
  catch (e) { return iso || ''; }
}

function renderSpieleTab(data) {
  const sec = document.getElementById('spiele');
  if (!sec) return;
  const tagDatum = new Date(data.datum + 'T00:00:00').toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' });
  let html = `<h2>📊 Spiele-Analyse — ${escapeHtml(tagDatum)}</h2>`;
  html += `<div class="box orange"><strong>⏰ ${data.spiele.length} Spiele · erstellt ${escapeHtml((data.erstellt_am||'').replace('T',' '))}.</strong> Quoten bei bet365 live prüfen, sie können sich bis zum Anpfiff noch bewegen.</div>`;
  html += `<div class="rating-legend">
    <div class="rating-legend-item"><span class="rating rating-safe">SAFE</span><span><strong>Fast ne Garantie</strong> — sollte immer reinkommen (~75-90%)</span></div>
    <div class="rating-legend-item"><span class="rating rating-value">VALUE</span><span><strong>Mitnehmen</strong> — Quote höher als faire Wahrscheinlichkeit</span></div>
    <div class="rating-legend-item"><span class="rating rating-wackel">WACKEL</span><span><strong>Kann-muss-nicht</strong> — spürbares Risiko mit Argumenten</span></div>
  </div>`;

  data.spiele.forEach(s => {
    html += `
      <div class="game-card">
        <div class="game-header">
          <div>
            <div class="league-tag">${escapeHtml(s.liga)}</div>
            <div class="game-title">${escapeHtml(s.heim)} vs. ${escapeHtml(s.gast)}</div>
          </div>
          <div class="game-meta">${fmtTime(s.anstoss)}</div>
        </div>
        <div class="section-title">News & Kontext</div>
        <div class="news-list">
          ${(s.news || []).map(n => `<div class="news-item">${escapeHtml(n)}</div>`).join('')}
        </div>
        <div class="section-title">Wett-Märkte</div>
        <div class="markets-grid">
          ${(s.tipps || []).map(t => {
            const cls = (t.kategorie === 'safe' || t.kategorie === 'value') ? 'market edge' : 'market';
            const edgeSign = (t.edge_prozent || 0) > 0 ? '+' : '';
            const edgeCls = (t.edge_prozent || 0) < 0 ? 'edge-val neutral' : 'edge-val';
            return `
              <div class="${cls}">
                <div class="market-top">
                  <span class="market-name">${escapeHtml(t.markt)} <span class="rating rating-${escapeHtml(t.kategorie)}">${escapeHtml((t.kategorie||'').toUpperCase())}</span></span>
                  <span class="market-odd">${fmtQuote(t.quote)}</span>
                </div>
                <div class="market-meta">
                  <span>Fair ~${fmtQuote(t.faire_quote)}</span>
                  <span class="${edgeCls}">${edgeSign}${t.edge_prozent || 0}%</span>
                </div>
                <div style="font-size:0.82em;color:#b8d4e8;margin-top:8px;line-height:1.55;">${escapeHtml(t.begruendung)}</div>
              </div>`;
          }).join('')}
        </div>
      </div>`;
  });
  sec.innerHTML = html;
}

function renderEinzelTab(data) {
  const sec = document.getElementById('einzel');
  if (!sec) return;
  let html = `<h2>🎯 Einzeltipps</h2>
    <div class="box gold"><strong>Kassenregel:</strong> 1-2% der Kasse pro Einzeltipp. Reihenfolge: SAFE → VALUE → WACKEL.</div>`;

  const sorted = (data.einzeltipps || []).slice().sort((a, b) => {
    const ka = KAT_REIHENFOLGE[a.kategorie] ?? 9;
    const kb = KAT_REIHENFOLGE[b.kategorie] ?? 9;
    return ka - kb;
  });

  sorted.forEach((et, idx) => {
    const spiel = data.spiele.find(s => s.id === et.spiel_id);
    const vollTipp = spiel && spiel.tipps ? spiel.tipps.find(t => t.id === et.tipp_id) : null;
    const match = spiel ? `${spiel.heim} vs. ${spiel.gast}` : '(unbekanntes Spiel)';
    const liga = spiel ? spiel.liga : '';
    html += `
      <div class="tip-card ${escapeHtml(et.kategorie)}">
        <div class="tip-header">
          <div class="tip-meta">
            <div class="tip-num">TIPP #${idx + 1} · ${escapeHtml((et.kategorie||'').toUpperCase())}</div>
            <div class="tip-match">${liga ? '<span class="league-tag">'+escapeHtml(liga)+'</span>' : ''}${escapeHtml(match)}</div>
            <div class="tip-pick">${escapeHtml(et.markt)}</div>
            <div class="tip-badges">
              <span class="tip-badge ${escapeHtml(et.kategorie)}-tag">${escapeHtml((et.kategorie||'').toUpperCase())}</span>
            </div>
          </div>
          <div class="tip-quote-box">${fmtQuote(et.quote)}<span class="tip-quote-sub">${et.empfohlener_einsatz_prozent}% Einsatz</span></div>
        </div>
        ${vollTipp ? `
        <div class="tip-body">
          <div class="analysis-block">
            <h4>🔥 Begründung</h4>
            <p style="color:#b8d4e8;font-size:0.92em;line-height:1.7;">${escapeHtml(vollTipp.begruendung)}</p>
          </div>
          <div class="value-calc">
            <strong>Faire Quote:</strong> ~${fmtQuote(vollTipp.faire_quote)} · <strong>Edge:</strong> ${(vollTipp.edge_prozent||0) > 0 ? '+' : ''}${vollTipp.edge_prozent||0}%
          </div>
        </div>` : ''}
      </div>`;
  });

  sec.innerHTML = html;
}

function renderRisikoTab(data) {
  const sec = document.getElementById('risiko');
  if (!sec) return;
  const kombis = data.kombis || [];
  if (kombis.length === 0) {
    sec.innerHTML = '<h2>🚀 Risiko-Kombis</h2><div class="box">Heute keine Kombis vorgeschlagen.</div>';
    return;
  }

  const stufeEmoji = { safe: '🟢', value: '🟡', wackel: '🟠', risk: '🔴', moonshot: '🔥' };

  let tabs = '<div class="risk-tabs">';
  let contents = '';
  kombis.forEach((k, idx) => {
    const active = idx === 0 ? ' active' : '';
    const stufe = k.stufe || k.kategorie || 'value';
    const emoji = stufeEmoji[stufe] || '⚽';
    tabs += `<div class="risk-tab${active}" onclick="showRiskKombi(${idx})">
      <h4>${emoji} ${fmtQuote(k.gesamtquote)}x</h4>
      <div class="target">${escapeHtml(k.name || '')}</div>
    </div>`;

    // Beine (neu) ODER tipps (alt) lesen
    const beine = k.beine || k.tipps || [];
    const legs = beine.map(leg => {
      // Match-Titel: spiel_id->Spiel suchen, sonst Prefix aus markt, sonst leer
      let matchTitle = '';
      if (leg.spiel_id) {
        const s = data.spiele.find(sp => sp.id === leg.spiel_id);
        if (s) matchTitle = `${s.heim} vs. ${s.gast}`;
      }
      if (!matchTitle && leg.markt && leg.markt.includes(':')) {
        matchTitle = leg.markt.split(':')[0].trim();
      }
      // Pick-Text: bei "Prefix: Pick" nur den Pick-Teil
      const pickText = (leg.markt || '').includes(':')
        ? leg.markt.split(':').slice(1).join(':').trim()
        : (leg.markt || '');
      const tipLine = matchTitle
        ? `<div class="combi-leg-match">${escapeHtml(matchTitle)}</div>
           <div class="combi-leg-tip">${escapeHtml(pickText)}</div>`
        : `<div class="combi-leg-match">${escapeHtml(leg.markt || '(kein Markt)')}</div>`;
      const reason = leg.kurz_begruendung
        ? `<div class="combi-leg-reason">${escapeHtml(leg.kurz_begruendung)}</div>`
        : '';
      return `
        <div class="combi-leg">
          <div class="combi-leg-info">${tipLine}${reason}</div>
          <span class="mini-quote">${fmtQuote(leg.quote)}</span>
        </div>`;
    }).join('');

    const legsHtml = legs || '<div class="combi-leg"><div class="combi-leg-info" style="color:#ffa94d;">Keine Beine in dieser Kombi (kombis[].beine fehlt in der JSON).</div></div>';

    contents += `
      <div class="risk-content${active}" id="kombi-${idx}">
        <div class="tip-card ${escapeHtml(stufe)}">
          <h3>${escapeHtml(k.name || '')} — Gesamtquote ${fmtQuote(k.gesamtquote)}x</h3>
          <div class="combi-details">${legsHtml}</div>
          <div class="combi-total">
            <div class="label">${escapeHtml(k.rechnung || 'Gesamtquote')}</div>
            <div class="value">${fmtQuote(k.gesamtquote)}x</div>
            ${k.wahrscheinlichkeit_prozent !== undefined ? `<div class="prob">Wahrscheinlichkeit: ~${k.wahrscheinlichkeit_prozent}%</div>` : ''}
            <div class="prob">Empfohlener Einsatz: ${k.empfohlener_einsatz_prozent || 0}% der Kasse</div>
          </div>
          ${k.warnung ? `<div class="box red" style="margin-top:14px;"><strong>⚠️ ${escapeHtml(k.warnung)}</strong></div>` : ''}
          ${k.begruendung ? `<div class="box" style="margin-top:14px;"><strong>Begründung:</strong> ${escapeHtml(k.begruendung)}</div>` : ''}
        </div>
      </div>`;
  });
  tabs += '</div>';

  sec.innerHTML = `<h2>🚀 Risiko-Kombis</h2>${tabs}${contents}`;
}

function showRiskKombi(idx) {
  document.querySelectorAll('#risiko .risk-tab').forEach((t, i) => t.classList.toggle('active', i === idx));
  document.querySelectorAll('#risiko .risk-content').forEach((c, i) => c.classList.toggle('active', i === idx));
}

function renderTagesdossier() {
  const data = window.__MIESMUSCHEL_TIPPS;
  if (!data || !Array.isArray(data.spiele) || data.spiele.length === 0) return;
  try {
    renderSpieleTab(data);
    renderEinzelTab(data);
    renderRisikoTab(data);
    // Header-Untertitel aktualisieren
    const sub = document.querySelector('header .subtitle');
    if (sub) sub.textContent = `Tipp-Dossier · ${data.spiele.length} Spiele · ${data.einzeltipps?.length||0} Einzeltipps · ${data.kombis?.length||0} Kombis`;
    const dateLine = document.querySelector('header .date-line');
    if (dateLine) dateLine.textContent = '🗓️ ' + new Date(data.datum+'T00:00:00').toLocaleDateString('de-DE',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
  } catch (e) {
    console.error('Tipp-Render-Fehler:', e);
  }
}

// Beim Laden automatisch rendern
renderTagesdossier();


function renderHistorie() {
  const root = document.getElementById('historie-content');
  if (!root) return;

  const stat = window.__MIESMUSCHEL_STAT;
  const lessons = (window.__MIESMUSCHEL_LESSONS && window.__MIESMUSCHEL_LESSONS.lessons) || [];

  if (!stat || !stat.gesamt || stat.gesamt.tipps === 0) {
    root.innerHTML = `
      <div class="historie-empty">
        <h3>📊 Noch keine Daten</h3>
        <p>Spiele ein paar Tipps ab, lass <code>scripts/ergebnisse_holen.bat</code> laufen, dann erscheinen hier deine Kennzahlen.</p>
      </div>
    `;
    return;
  }

  const lastRun = stat.letzte_berechnung
    ? new Date(stat.letzte_berechnung).toLocaleString('de-DE')
    : '—';

  root.innerHTML = `
    <div class="historie-hero">
      <h3>🐚 Deine Bilanz</h3>
      <div class="sub">Letzte Berechnung: ${lastRun}</div>
      <div class="breakdown-grid">
        ${renderKpiBlock('Letzte 30 Tage', stat.letzte_30_tage || stat.gesamt)}
        ${renderKpiBlock('Letzte 90 Tage', stat.letzte_90_tage || stat.gesamt)}
        ${renderKpiBlock('Gesamt', stat.gesamt)}
      </div>
    </div>

    ${renderStopSignals(stat)}

    <h3 style="margin-top:20px;">Aufschlüsselung</h3>
    <div class="breakdown-grid">
      ${renderBreakdown('Nach Liga', stat.nach_liga)}
      ${renderBreakdown('Nach Markt', stat.nach_markt)}
      ${renderBreakdown('Nach Quoten-Range', stat.nach_quoten_range)}
      ${renderBreakdown('Nach Kategorie', stat.nach_kategorie)}
    </div>

    <h3 style="margin-top:20px;">📝 Lessons Learned</h3>
    <div class="lessons-list">
      ${renderLessons(lessons)}
    </div>
  `;
}
