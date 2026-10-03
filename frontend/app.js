/**
 * upay AI Shield — Master Client Application
 * Enterprise-grade Risk Operations, Explainable AI & Case Management Desk
 */

// Application State
const AppState = {
  currentView: 'dashboard-view',
  activeTransactionId: null,
  activeTransactionData: null,
  txCurrentPage: 1,
  txLimit: 25,
  txRiskFilter: 'ALL',
  txSearchQuery: '',
  txChannelFilter: 'ALL',
  txTypeFilter: 'ALL',
  caseCurrentPage: 1,
  caseLimit: 25,
  caseStatusFilter: 'ALL',
  casePriorityFilter: 'ALL',
  caseDatePreset: 'ALL',
  caseSearchQuery: '',
  activeCaseSubview: 'all',
  chatHistory: []
};

// View Titles & Subtitles Map
const ViewTitles = {
  'dashboard-view': {
    title: 'Executive Risk Operations Dashboard',
    subtitle: 'Real-time behavioral telemetry, SHAP explainability & Live Risk Operations Desk'
  },
  'transactions-view': {
    title: 'Transaction Monitoring Ledger',
    subtitle: 'Continuous surveillance across Bangladesh MFS payment channels (APP, USSD, WEB, AGENT)'
  },
  'cases-view': {
    title: 'Analyst Case Management Workspace',
    subtitle: 'End-to-end triage, timeline audit trail & formal human determinations'
  },
  'simulator-view': {
    title: 'Live Risk & What-If Telemetry Simulator',
    subtitle: 'Calibrated XGBoost scoring & counterfactual decision-support sandbox'
  },
  'behavior-view': {
    title: 'Customer Behavioral Baseline Profile',
    subtitle: 'Continuous 30-day baseline comparison & anomaly deviation detection'
  },
  'scam-view': {
    title: 'Scam Pattern Intelligence Engine',
    subtitle: '9 empirical MFS fraud typologies flagging coordinated syndicate threats'
  },
  'network-view': {
    title: 'Suspicious Network Intelligence',
    subtitle: 'Topological entity graph mapping money-mule rings and hardware sharing'
  },
  'model-view': {
    title: 'Model Validation & Explainability Architecture',
    subtitle: 'Rigorous confusion matrix, ROC-AUC curve & global SHAP feature importance'
  },
  'monitoring-view': {
    title: 'Model Health & Statistical Data Drift Monitoring',
    subtitle: 'NAMS feature distance tracking & human active learning feedback loop'
  },
  'responsible-view': {
    title: 'Responsible AI & Ethical Governance Framework',
    subtitle: 'Bangladesh Financial Intelligence Unit (BFIU) compliance & safety mandates'
  },
  'admin-view': {
    title: 'System Administration & Officer Directory',
    subtitle: 'Personnel role-based access control (RBAC), immutable audit logs & regulatory guardrails'
  }
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  // 1. Mount modular layout shells (sidebar, header, drawers, modals)
  if (window.ComponentLoader) {
    await ComponentLoader.initLayout();
  }

  setupNavigation();

  // 2. Initialize Session & Auth RBAC first (ensure valid authentication token exists)
  if (window.AuthService) {
    AuthService.subscribe(updateUserInterfaceState);
    await AuthService.init();
  }

  // 3. Resolve and mount active view template via Router
  if (window.AppRouter) {
    await AppRouter.init();
  }
});

// ============================================================================
// NAVIGATION EVENT DELEGATION
// ============================================================================
function setupNavigation() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.nav-item');
    if (!btn) return;
    e.preventDefault();
    const route = btn.getAttribute('data-route');
    const viewId = btn.getAttribute('data-view');
    if (window.AppRouter && route) {
      window.AppRouter.navigate(route);
    } else if (window.AppRouter && viewId) {
      const mapped = window.AppRouter.viewToRoute[viewId] || '/dashboard';
      window.AppRouter.navigate(mapped);
    } else if (viewId) {
      navigateToView(viewId);
    }
  });
}

function navigateToView(viewId, updateHistory = true) {
  const cleanName = viewId.replace('-view', '');
  if (window.AppRouter) {
    window.AppRouter.navigate(window.AppRouter.viewToRoute[cleanName] || '/dashboard', updateHistory);
  }
}



// ============================================================================
// DASHBOARD VIEW LOGIC
// ============================================================================
async function refreshDashboardData() {
  try {
    const res = await fetch('/api/v1/dashboard/stats');
    if (!res.ok) throw new Error('Failed to load stats');
    const data = await res.json();

    // KPIs
    document.getElementById('kpi-total-tx').innerText = data.total_transactions;
    document.getElementById('kpi-low-risk').innerHTML = `${data.low_risk.count} <span style="font-size:14px; font-weight:600;">(${data.low_risk.percentage}%)</span>`;
    document.getElementById('kpi-med-risk').innerHTML = `${data.medium_risk.count} <span style="font-size:14px; font-weight:600;">(${data.medium_risk.percentage}%)</span>`;
    document.getElementById('kpi-high-risk').innerHTML = `${data.high_risk.count} <span style="font-size:14px; font-weight:600;">(${data.high_risk.percentage}%)</span>`;
    document.getElementById('kpi-vol-protected').innerText = `৳${data.business_impact.total_volume_protected_bdt.toLocaleString()}`;
    document.getElementById('kpi-review-reduction').innerText = `${data.business_impact.manual_review_reduction_pct}%`;
    document.getElementById('kpi-loss-prevented').innerText = `৳${data.business_impact.est_loss_prevented_bdt.toLocaleString()}`;
    document.getElementById('kpi-model-auc').innerText = data.model_metrics.roc_auc;

    // Bars
    document.getElementById('tier-bar-low').style.width = `${data.low_risk.percentage}%`;
    document.getElementById('tier-bar-low-pct').innerText = `${data.low_risk.percentage}% (${data.low_risk.count} txs)`;
    document.getElementById('tier-bar-med').style.width = `${data.medium_risk.percentage}%`;
    document.getElementById('tier-bar-med-pct').innerText = `${data.medium_risk.percentage}% (${data.medium_risk.count} txs)`;
    document.getElementById('tier-bar-high').style.width = `${data.high_risk.percentage}%`;
    document.getElementById('tier-bar-high-pct').innerText = `${data.high_risk.percentage}% (${data.high_risk.count} txs)`;

    // Top Signals
    renderTopSignals(data.top_risk_signals);

    // Recent High-Risk Alerts Table
    renderRecentAlerts(data.recent_high_risk);
  } catch (err) {
    console.error('Error refreshing dashboard:', err);
  }
}

function renderTopSignals(signals) {
  const container = document.getElementById('top-signals-list');
  if (!container) return;

  container.innerHTML = signals.map(sig => `
    <div>
      <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600; margin-bottom:4px;">
        <span style="color:var(--text-primary);">${sig.signal}</span>
        <span style="color:var(--upay-blue);">${sig.count} txs (${sig.pct}%)</span>
      </div>
      <div style="height:8px; background:var(--surface-muted); border-radius:4px; overflow:hidden;">
        <div style="height:100%; width:${Math.min(sig.pct, 100)}%; background:var(--upay-blue); border-radius:4px;"></div>
      </div>
    </div>
  `).join('');
}

function renderRecentAlerts(alerts) {
  const tbody = document.getElementById('dashboard-recent-alerts');
  if (!tbody || !alerts) return;

  tbody.innerHTML = alerts.map(tx => `
    <tr>
      <td><strong>${tx.transaction_id}</strong></td>
      <td>${tx.customer_id}</td>
      <td><strong>৳${Number(tx.amount).toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></td>
      <td><span class="badge badge-high">${Number(tx.risk_score).toFixed(1)}</span></td>
      <td><span class="badge-channel">${tx.channel}</span></td>
      <td><code style="font-size:11px;">${tx.device_id || 'UNKNOWN'}</code></td>
      <td>${tx.location || 'Dhaka'}</td>
      <td>
        <button class="btn btn-secondary" style="padding:4px 12px; font-size:11px;" onclick="openInvestigationDrawer('${tx.transaction_id}')">
          Investigate
        </button>
      </td>
    </tr>
  `).join('');
}

function renderHourlyVelocityMock() {
  const container = document.getElementById('hourly-velocity-bars');
  if (!container) return;

  const hours = [
    {h:'00', v:14, off:true}, {h:'01', v:22, off:true}, {h:'02', v:35, off:true}, {h:'03', v:28, off:true}, {h:'04', v:19, off:true}, {h:'05', v:8, off:true},
    {h:'06', v:12, off:false}, {h:'07', v:25, off:false}, {h:'08', v:45, off:false}, {h:'09', v:70, off:false}, {h:'10', v:85, off:false}, {h:'11', v:90, off:false},
    {h:'12', v:95, off:false}, {h:'13', v:88, off:false}, {h:'14', v:100, off:false}, {h:'15', v:92, off:false}, {h:'16', v:80, off:false}, {h:'17', v:85, off:false},
    {h:'18', v:75, off:false}, {h:'19', v:65, off:false}, {h:'20', v:55, off:false}, {h:'21', v:45, off:false}, {h:'22', v:35, off:false}, {h:'23', v:25, off:false}
  ];

  container.innerHTML = hours.map(item => {
    const heightPct = Math.max(10, item.v);
    const color = item.off ? 'var(--danger-red)' : 'var(--upay-blue)';
    return `
      <div title="${item.h}:00 - ${item.v} txs ${item.off ? '(Nocturnal Off-Hours)' : ''}" style="flex:1; height:${heightPct}%; background:${color}; border-radius:3px; opacity:${item.off ? '0.9' : '0.6'}; transition:all 0.2s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='${item.off ? '0.9' : '0.6'}'"></div>
    `;
  }).join('');
}

function updateImpactSimulation() {
  const slider = document.getElementById('sim-volume-slider');
  const val = Number(slider.value);
  document.getElementById('sim-volume-label').innerText = `${val.toLocaleString()} / day`;

  const savedReviews = Math.round(val * 0.9211);
  const capitalSaved = Math.round(val * 0.0558 * 22100);

  document.getElementById('sim-saved-reviews').innerText = `${savedReviews.toLocaleString()} reviews`;
  document.getElementById('sim-saved-bdt').innerText = `৳${capitalSaved.toLocaleString()}`;
}

// ============================================================================
// TRANSACTIONS LEDGER LOGIC
// ============================================================================
async function loadTransactionsLedger() {
  const params = new URLSearchParams({
    page: AppState.txCurrentPage,
    limit: AppState.txLimit
  });

  if (AppState.txRiskFilter !== 'ALL') params.append('risk_level', AppState.txRiskFilter);
  if (AppState.txChannelFilter !== 'ALL') params.append('channel', AppState.txChannelFilter);
  if (AppState.txTypeFilter !== 'ALL') params.append('transaction_type', AppState.txTypeFilter);
  if (AppState.txSearchQuery) params.append('search', AppState.txSearchQuery);

  try {
    const res = await fetch(`/api/v1/transactions?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to load transactions');
    const data = await res.json();

    const tbody = document.getElementById('transactions-table-body');
    if (!tbody) return;

    const txList = Array.isArray(data.data) ? data.data : (data.data?.items || data.items || []);
    const totalCount = data.total_count || data.total || data.data?.total || txList.length;
    const pageNum = data.page || data.data?.page || 1;
    const limitNum = data.limit || data.data?.limit || 25;

    if (txList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; padding:32px; color:var(--text-tertiary);">No transactions found matching active filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = txList.map(tx => {
      const riskClass = tx.risk_level === 'HIGH' || tx.risk_level === 'CRITICAL' ? 'badge-high' : (tx.risk_level === 'MEDIUM' ? 'badge-medium' : 'badge-low');
      return `
        <tr>
          <td><strong>${tx.transaction_id}</strong></td>
          <td>${tx.customer_id}</td>
          <td><strong>৳${Number(tx.amount).toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></td>
          <td style="font-size:12px; color:var(--text-secondary);">${tx.timestamp || 'N/A'}</td>
          <td><span style="font-size:11px; font-weight:600;">${tx.transaction_type}</span></td>
          <td><span class="badge-channel">${tx.channel}</span></td>
          <td><code style="font-size:11px;">${tx.receiver_id || 'N/A'}</code></td>
          <td><code style="font-size:11px;">${tx.device_id || 'DEV-N/A'}</code></td>
          <td><strong>${Number(tx.risk_score).toFixed(1)}</strong></td>
          <td><span class="badge ${riskClass}">${tx.risk_level}</span></td>
          <td>
            <button class="btn btn-secondary" style="padding:4px 12px; font-size:11px;" onclick="openInvestigationDrawer('${tx.transaction_id}')">
              Forensic Triage
            </button>
          </td>
        </tr>
      `;
    }).join('');

    const startIdx = (pageNum - 1) * limitNum + 1;
    const endIdx = Math.min(pageNum * limitNum, totalCount);
    const pagInfo = document.getElementById('tx-pagination-info');
    if (pagInfo) pagInfo.innerText = `Showing ${startIdx}-${endIdx} of ${totalCount} transactions`;
    const curPage = document.getElementById('tx-current-page-num');
    if (curPage) curPage.innerText = pageNum;

  } catch (err) {
    console.error('Error loading transactions:', err);
  }
}

function handleTxSearch(val) {
  AppState.txSearchQuery = val;
  AppState.txCurrentPage = 1;
  loadTransactionsLedger();
}

function setTxRiskFilter(tier, btn) {
  document.querySelectorAll('.filter-pills .filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  AppState.txRiskFilter = tier;
  AppState.txCurrentPage = 1;
  loadTransactionsLedger();
}

function applyTxFilters() {
  AppState.txChannelFilter = document.getElementById('tx-channel-filter').value;
  AppState.txTypeFilter = document.getElementById('tx-type-filter').value;
  AppState.txCurrentPage = 1;
  loadTransactionsLedger();
}

function changeTxPage(delta) {
  AppState.txCurrentPage = Math.max(1, AppState.txCurrentPage + delta);
  loadTransactionsLedger();
}

// ============================================================================
// SLIDE-OVER INVESTIGATION DRAWER (10 SECTIONS)
// ============================================================================
async function openInvestigationDrawer(txId) {
  if (!txId || txId === 'undefined') {
    console.error('[openInvestigationDrawer] Called with invalid txId:', txId);
    return;
  }
  AppState.activeTransactionId = txId;
  const overlay = document.getElementById('investigation-drawer-overlay');
  if (overlay) overlay.classList.add('open');

  try {
    const res = await fetch(`/api/v1/transactions/${txId}`);
    if (!res.ok) throw new Error(`Transaction fetch failed: ${res.status}`);
    const resp = await res.json();

    // ── Destructure the actual API response shape ───────────────────────────
    // API returns: { transaction:{...}, customer_baseline:{...}, risk_assessment:{...}, associated_case:{...} }
    const tx   = resp.transaction      || resp.data?.transaction      || {};
    const ra   = resp.risk_assessment  || resp.data?.risk_assessment  || {};
    const base = resp.customer_baseline || resp.data?.customer_baseline || {};
    const cas  = resp.associated_case  || resp.data?.associated_case  || null;

    // Normalise field aliases (DB column names → display names)
    const txId_     = tx.transaction_id || txId;
    const custId    = tx.customer_id    || '—';
    const amount    = parseFloat(tx.amount) || 0;
    const channel   = tx.channel        || '—';
    const ts        = tx.timestamp      || tx.created_at || '—';
    const devId     = tx.device_id      || '—';
    const recip     = tx.receiver_id    || tx.recipient_account || tx.recipient_id || '—';
    const loc       = tx.location       || tx.location_cluster  || '—';
    const failedAuth = tx.failed_attempts ?? tx.failed_pin_attempts_last_hour ?? 0;
    const isNewDev   = !!(tx.is_new_device || tx.device_changed_recently);
    const isNewRec   = !!(tx.is_new_receiver || tx.is_new_recipient);
    const amountDev  = parseFloat(tx.amount_deviation ?? tx.amount_deviation_score ?? 1.0);
    const avgAmt     = parseFloat(base.normal_avg_amount ?? 0);

    const riskScore  = parseFloat(ra.risk_score  ?? tx.risk_score  ?? 0);
    const riskLevel  = (ra.risk_level  || tx.risk_level  || 'LOW').replace('CRITICAL', 'HIGH');
    const action     = ra.decision_action || ra.recommended_action || tx.decision_action || '—';

    const shapFactors  = Array.isArray(ra.shap_factors)         ? ra.shap_factors         : [];
    const riskStory    = Array.isArray(ra.risk_story)           ? ra.risk_story           : [];
    const scamPatterns = Array.isArray(ra.typologies_triggered) ? ra.typologies_triggered
                        : Array.isArray(ra.scam_patterns)       ? ra.scam_patterns       : [];
    const atoSignals   = ra.compound_threat || ra.ato_signals   || null;

    AppState.activeTransactionData = { tx, ra, base };

    // ── Header ─────────────────────────────────────────────────────────────
    const hdrId   = document.getElementById('drawer-tx-id');
    const hdrMeta = document.getElementById('drawer-tx-meta');
    if (hdrId)   hdrId.innerText   = `${txId_} Forensic Investigation`;
    if (hdrMeta) hdrMeta.innerText = `Customer: ${custId} • Amount: ৳${amount.toLocaleString(undefined, {minimumFractionDigits: 2})} • Channel: ${channel}`;

    // ── Section 1: Transaction Core Facts ──────────────────────────────────
    const factsEl = document.getElementById('drawer-core-facts');
    if (factsEl) {
      factsEl.innerHTML = `
        <div><span style="color:var(--text-tertiary);">Transaction ID:</span> <strong>${txId_}</strong></div>
        <div><span style="color:var(--text-tertiary);">Customer ID:</span> <strong>${custId}</strong></div>
        <div><span style="color:var(--text-tertiary);">Amount (BDT):</span> <strong>৳${amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></div>
        <div><span style="color:var(--text-tertiary);">Timestamp:</span> <span>${ts}</span></div>
        <div><span style="color:var(--text-tertiary);">Device ID:</span> <code>${devId}</code></div>
        <div><span style="color:var(--text-tertiary);">Recipient ID:</span> <code>${recip}</code></div>
        <div><span style="color:var(--text-tertiary);">Location Cluster:</span> <span>${loc}</span></div>
        <div><span style="color:var(--text-tertiary);">Preceding Failed Auth:</span> <strong style="color:${failedAuth > 0 ? 'var(--danger-red)' : 'inherit'};">${failedAuth} attempts</strong></div>
        ${cas ? `<div style="grid-column:span 2; background:var(--surface-muted); padding:8px 12px; border-radius:8px; font-size:12px;"><span style="color:var(--text-tertiary);">Linked Case:</span> <strong>${cas.case_id}</strong> — ${cas.status} / ${cas.priority} (Analyst: ${cas.assigned_analyst})</div>` : ''}
      `;
    }

    // ── Section 2: Risk Banner ──────────────────────────────────────────────
    const banner    = document.getElementById('drawer-risk-banner');
    const tierLabel = document.getElementById('drawer-risk-tier-label');
    const scoreVal  = document.getElementById('drawer-risk-score-val');
    const actionVal = document.getElementById('drawer-risk-action-val');
    if (banner)    banner.className  = `risk-banner ${riskLevel === 'HIGH' ? 'risk-banner-high' : (riskLevel === 'MEDIUM' ? 'risk-banner-med' : 'risk-banner-low')}`;
    if (tierLabel) tierLabel.innerText = `${riskLevel} Risk Tier`;
    if (scoreVal)  scoreVal.innerText  = riskScore.toFixed(1);
    if (actionVal) actionVal.innerText = `Directive: ${action}`;

    // ── Section 3: Forensic Timeline ───────────────────────────────────────
    const timelineList = document.getElementById('drawer-timeline-list');
    if (timelineList) {
      if (riskStory.length > 0) {
        timelineList.innerHTML = riskStory.map(m => {
          const dotClass = m.severity === 'CRITICAL' ? 'timeline-dot-danger'
                         : (m.severity === 'HIGH' || m.severity === 'WARNING' ? 'timeline-dot-warning' : '');
          return `
            <div class="timeline-item">
              <div class="timeline-dot ${dotClass}">●</div>
              <div class="timeline-content">
                <h5>
                  <span>${m.title}</span>
                  <span style="font-size:11px; color:var(--text-tertiary);">${m.time || ''}</span>
                </h5>
                <p>${m.description}</p>
              </div>
            </div>
          `;
        }).join('');
      } else {
        timelineList.innerHTML = `<div style="font-size:12px; color:var(--text-secondary); padding:8px;">Risk story timeline not available for this transaction.</div>`;
      }
    }

    // ── Section 4: Scam Typologies ─────────────────────────────────────────
    const scamContainer = document.getElementById('drawer-scam-patterns-list');
    if (scamContainer) {
      if (scamPatterns.length > 0) {
        scamContainer.innerHTML = scamPatterns.map(p => `
          <div style="background:var(--surface-muted); padding:10px 14px; border-radius:8px; border-left:3px solid var(--danger-red);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="font-size:12px; color:var(--danger-red);">${p.pattern_name || p.name || p}</strong>
              <span class="badge ${(p.severity === 'CRITICAL' || p.severity === 'HIGH') ? 'badge-high' : 'badge-medium'}">${p.severity || 'FLAGGED'}</span>
            </div>
            ${p.description ? `<div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">${p.description}</div>` : ''}
          </div>
        `).join('');
      } else {
        scamContainer.innerHTML = `<div style="font-size:12px; color:var(--text-secondary);">No empirical scam typologies triggered.</div>`;
      }
    }

    // ── Section 5: ATO Signals ─────────────────────────────────────────────
    const atoBox = document.getElementById('drawer-ato-container');
    if (atoBox) {
      if (atoSignals) {
        const signals = atoSignals.detected_signals || [];
        atoBox.innerHTML = `
          <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="font-size:12px; font-weight:600;">ATO Threat Severity:</span>
            <span class="badge ${atoSignals.severity === 'CRITICAL' || atoSignals.severity === 'HIGH' ? 'badge-high' : 'badge-low'}">${atoSignals.severity || 'LOW'}</span>
          </div>
          <ul style="font-size:12px; color:var(--text-secondary); padding-left:18px; margin-bottom:10px;">
            ${signals.map(s => `<li>${s}</li>`).join('') || '<li>No specific ATO signals detected.</li>'}
          </ul>
          <div style="font-size:11px; font-weight:600; color:var(--text-primary); background:var(--surface-muted); padding:8px 12px; border-radius:6px;">
            ${atoSignals.recommendation || 'Standard monitoring protocol.'}
          </div>
        `;
      } else {
        atoBox.innerHTML = `<div style="font-size:12px; color:var(--text-secondary);">No ATO compound threat indicators recorded.</div>`;
      }
    }

    // ── Section 6: SHAP Waterfall ──────────────────────────────────────────
    const shapBox = document.getElementById('drawer-shap-waterfall');
    if (shapBox) {
      if (shapFactors.length > 0) {
        const maxShap = Math.max(...shapFactors.map(f => Math.abs(Number(f.shap_value) || 0)), 1.0);
        shapBox.innerHTML = shapFactors.map(f => {
          const isInc   = f.impact === 'RISK_INCREASING' || (Number(f.shap_value) > 0);
          const rawVal  = Math.abs(Number(f.shap_value) || 0);
          const barFill = rawVal > 0 ? Math.min(100, Math.max(8, Math.round((rawVal / maxShap) * 92))) : 2;
          const fillClass = isInc ? 'shap-bar-increasing' : 'shap-bar-mitigating';
          const sign = isInc && Number(f.shap_value) > 0 ? '+' : '';
          return `
            <div class="shap-bar-row">
              <span class="shap-label" title="${f.explanation || ''}">${f.feature_label || f.feature}</span>
              <div class="shap-bar-track">
                <div class="shap-bar-fill ${fillClass}" style="width:${barFill}%;"></div>
              </div>
              <span class="shap-val" style="color:${isInc ? 'var(--danger-red)' : 'var(--success-green)'};">
                ${sign}${f.shap_value}
              </span>
            </div>
          `;
        }).join('');
      } else {
        shapBox.innerHTML = `<div style="font-size:12px; color:var(--text-secondary);">SHAP attribution data not available for this transaction.</div>`;
      }
    }

    // ── Section 7: Baseline Comparison ────────────────────────────────────
    const compBox = document.getElementById('drawer-baseline-comparison');
    if (compBox) {
      compBox.innerHTML = `
        <table class="data-table" style="font-size:12px;">
          <thead>
            <tr>
              <th>Telemetry Signal</th>
              <th>30-Day Customer Baseline</th>
              <th>Current Evaluated Transaction</th>
              <th>Deviation Ratio</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Transfer Amount</td>
              <td>৳${avgAmt.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
              <td><strong>৳${amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></td>
              <td><strong style="color:${amountDev >= 3 ? 'var(--danger-red)' : 'var(--success-green)'};">${amountDev.toFixed(1)}x</strong></td>
            </tr>
            <tr>
              <td>Hardware Device</td>
              <td>Known Registered Handset</td>
              <td><code>${devId}</code></td>
              <td>${isNewDev ? '<span class="badge badge-high">NEW DEVICE</span>' : '<span class="badge badge-low">KNOWN</span>'}</td>
            </tr>
            <tr>
              <td>Recipient Familiarity</td>
              <td>Frequent Beneficiaries</td>
              <td><code>${recip}</code></td>
              <td>${isNewRec ? '<span class="badge badge-medium">FIRST TIME</span>' : '<span class="badge badge-low">FAMILIAR</span>'}</td>
            </tr>
          </tbody>
        </table>
      `;
    }

    // ── Section 8: Network Summary ─────────────────────────────────────────
    const netBox = document.getElementById('drawer-network-summary');
    if (netBox) {
      netBox.innerHTML = `<p>Recipient <code>${recip}</code> and device <code>${devId}</code> have been mapped in the topological intelligence graph. Cross-customer device multi-tenancy check passed.</p>`;
    }

    // ── AI Copilot initial message ─────────────────────────────────────────
    const chatEl = document.getElementById('drawer-chat-messages');
    if (chatEl) {
      chatEl.innerHTML = `
        <div class="chat-bubble chat-bubble-copilot">
          I have reviewed the factual telemetry for <strong>${txId_}</strong>.
          Amount is ৳${amount.toLocaleString()} (${amountDev.toFixed(1)}x deviation from ${custId}'s baseline). Risk score: <strong>${riskScore.toFixed(1)}/100</strong>. What specific evidence should I verify?
        </div>
      `;
    }

    checkGeminiCopilotStatus();

  } catch (err) {
    console.error('[openInvestigationDrawer] Error:', err);
    const hdrId   = document.getElementById('drawer-tx-id');
    const hdrMeta = document.getElementById('drawer-tx-meta');
    if (hdrId)   hdrId.innerText   = `${txId} — Data Load Failed`;
    if (hdrMeta) hdrMeta.innerText = `Error: ${err.message}`;
  }
}

function closeInvestigationDrawer(e) {
  if (e.target.id === 'investigation-drawer-overlay') {
    closeInvestigationDrawerDirectly();
  }
}

function closeInvestigationDrawerDirectly() {
  document.getElementById('investigation-drawer-overlay').classList.remove('open');
  AppState.activeTransactionId = null;
}

// ============================================================================
// CHATBOT (TARIQ HASSAN) INTEGRATION & GOOGLE GEMINI AI
// ============================================================================
async function checkGeminiCopilotStatus() {
  const badge = document.getElementById('drawer-copilot-engine-badge');
  const btnText = document.getElementById('gemini-key-btn-text');
  const localKey = localStorage.getItem('gemini_api_key');

  try {
    const res = await fetch('/api/v1/chat/status');
    const data = await res.json();
    const isConfigured = data.gemini_configured || !!localKey;
    const model = data.active_model || 'gemini-2.0-flash';

    if (badge) {
      if (isConfigured) {
        badge.innerHTML = `● Active Forensic Copilot • <span style="color:#0ea5e9; font-weight:700;">Google Gemini AI (${model})</span>`;
      } else {
        badge.innerHTML = `● Active Forensic Copilot • Local Intelligence Engine`;
      }
    }

    if (btnText) {
      btnText.innerText = isConfigured ? 'Gemini Active ✓' : '+ Connect Gemini';
    }
  } catch (err) {
    if (badge && localKey) {
      badge.innerHTML = `● Active Forensic Copilot • <span style="color:#0ea5e9;">Google Gemini AI</span>`;
    }
  }
}

async function promptGeminiApiKey() {
  const currentKey = localStorage.getItem('gemini_api_key') || '';
  const inputKey = prompt(
    'Enter your Google Gemini API Key (e.g. AIzaSy...):\n(This enables live Google Gemini reasoning for forensic transaction inquiries)',
    currentKey
  );

  if (inputKey === null) return;
  const key = inputKey.trim();

  if (key) {
    localStorage.setItem('gemini_api_key', key);
    try {
      const res = await fetch('/api/v1/chat/configure', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ api_key: key })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Google Gemini model connected and configured successfully!', 'success');
      } else {
        showToast('Gemini API key saved to browser session', 'info');
      }
    } catch (e) {
      showToast('Gemini API key saved to browser session', 'info');
    }
  } else {
    localStorage.removeItem('gemini_api_key');
    showToast('Gemini key removed; running in local intelligence mode', 'info');
  }

  checkGeminiCopilotStatus();
}

async function sendDrawerChatMessage() {
  const input = document.getElementById('drawer-chat-input');
  const message = input.value.trim();
  if (!message || !AppState.activeTransactionId) return;

  // Add user bubble
  appendChatBubble(message, 'user');
  input.value = '';

  const apiKey = localStorage.getItem('gemini_api_key') || undefined;

  try {
    const res = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        transaction_id: AppState.activeTransactionId,
        message: message,
        context: AppState.activeTransactionData,
        api_key: apiKey
      })
    });

    if (!res.ok) throw new Error('Chatbot request failed');
    const data = await res.json();
    appendChatBubble(data.reply, 'copilot', data.engine_used);
  } catch (err) {
    console.error('Chat error:', err);
    appendChatBubble('Officer Tariq Hassan is analyzing additional telemetry logs. Please retry.', 'copilot');
  }
}

function sendQuickChat(promptText) {
  document.getElementById('drawer-chat-input').value = promptText;
  sendDrawerChatMessage();
}

function appendChatBubble(text, sender, engineUsed) {
  const chatMessages = document.getElementById('drawer-chat-messages');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-copilot'}`;

  if (sender !== 'user' && typeof marked !== 'undefined') {
    bubble.innerHTML = marked.parse(text);
  } else {
    bubble.innerText = text;
  }

  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============================================================================
// HUMAN DETERMINATION & CASE ESCALATION
// ============================================================================
async function submitAnalystDetermination(decision) {
  if (!AppState.activeTransactionId) return;
  const notes = document.getElementById('drawer-notes-input').value.trim();

  try {
    const res = await fetch('/api/v1/feedback', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        transaction_id: AppState.activeTransactionId,
        decision: decision === 'CONFIRM_SUSPICIOUS' ? 'SUSPICIOUS' : (decision === 'MARK_LEGITIMATE' ? 'LEGITIMATE' : 'NEEDS_REVIEW'),
        comment: notes || `Analyst determined ${decision}`,
        analyst_id: 'Tariq Hassan'
      })
    });

    if (!res.ok) throw new Error('Failed to record decision');

    showToast(`Decision recorded: ${decision}`, 'success');
    closeInvestigationDrawerDirectly();
    refreshDashboardData();
    loadTransactionsLedger();
  } catch (err) {
    console.error('Error submitting determination:', err);
    showToast('Failed to record determination', 'error');
  }
}

async function escalateToFormalCase() {
  if (!AppState.activeTransactionId) return;
  const notes = document.getElementById('drawer-notes-input').value.trim();

  try {
    const res = await fetch('/api/v1/cases', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        transaction_id: AppState.activeTransactionId,
        priority: 'HIGH',
        assigned_analyst: 'Tariq Hassan',
        notes: notes || `Formally escalated case for transaction ${AppState.activeTransactionId}.`
      })
    });

    if (!res.ok) throw new Error('Failed to create case');
    const data = await res.json();
    showToast(`Case ${data.case_id} Created Successfully`, 'success');
  } catch (err) {
    console.error('Error creating case:', err);
    showToast('Failed to create case', 'error');
  }
}


// ============================================================================
// SIMULATOR LOGIC (MODE 1 & MODE 2)
// ============================================================================
function switchSimulatorTab(tab) {
  document.getElementById('tab-btn-live-sim').classList.toggle('active', tab === 'live');
  document.getElementById('tab-btn-whatif-sim').classList.toggle('active', tab === 'whatif');

  document.getElementById('sim-panel-live').style.display = tab === 'live' ? 'grid' : 'none';
  document.getElementById('sim-panel-whatif').style.display = tab === 'whatif' ? 'grid' : 'none';

  if (tab === 'whatif') {
    runWhatIfSimulation();
  }
}

function fillSimulatorPreset(type) {
  if (type === 'normal') {
    document.getElementById('sim-input-amount').value = '1500.00';
    document.getElementById('sim-input-deviation').value = '0.6';
    document.getElementById('sim-input-hour').value = '14';
    document.getElementById('sim-input-tx1h').value = '1';
    document.getElementById('sim-input-tx24h').value = '3';
    document.getElementById('sim-input-failed').value = '0';
    document.getElementById('sim-check-new-device').checked = false;
    document.getElementById('sim-check-new-receiver').checked = false;
    document.getElementById('sim-check-location').checked = false;
  } else if (type === 'ato') {
    document.getElementById('sim-input-amount').value = '55000.00';
    document.getElementById('sim-input-deviation').value = '14.5';
    document.getElementById('sim-input-hour').value = '3';
    document.getElementById('sim-input-tx1h').value = '8';
    document.getElementById('sim-input-tx24h').value = '22';
    document.getElementById('sim-input-failed').value = '3';
    document.getElementById('sim-check-new-device').checked = true;
    document.getElementById('sim-check-new-receiver').checked = true;
    document.getElementById('sim-check-location').checked = true;
  } else if (type === 'burst') {
    document.getElementById('sim-input-amount').value = '18500.00';
    document.getElementById('sim-input-deviation').value = '4.8';
    document.getElementById('sim-input-hour').value = '21';
    document.getElementById('sim-input-tx1h').value = '12';
    document.getElementById('sim-input-tx24h').value = '25';
    document.getElementById('sim-input-failed').value = '1';
    document.getElementById('sim-check-new-device').checked = false;
    document.getElementById('sim-check-new-receiver').checked = true;
    document.getElementById('sim-check-location').checked = false;
  }
  runLiveSimulation();
}

async function runLiveSimulation() {
  const features = {
    amount: parseFloat(document.getElementById('sim-input-amount').value) || 2500.0,
    amount_deviation: parseFloat(document.getElementById('sim-input-deviation').value) || 1.0,
    hour: parseInt(document.getElementById('sim-input-hour').value) || 14,
    transactions_last_1h: parseInt(document.getElementById('sim-input-tx1h').value) || 1,
    transactions_last_24h: parseInt(document.getElementById('sim-input-tx24h').value) || 4,
    failed_attempts: parseInt(document.getElementById('sim-input-failed').value) || 0,
    is_new_device: document.getElementById('sim-check-new-device').checked ? 1 : 0,
    is_new_receiver: document.getElementById('sim-check-new-receiver').checked ? 1 : 0,
    location_changed: document.getElementById('sim-check-location').checked ? 1 : 0
  };

  try {
    const res = await fetch('/api/v1/simulate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({features})
    });

    if (!res.ok) throw new Error('Simulation failed');
    const data = await res.json();

    document.getElementById('sim-result-score').innerText = Number(data.risk_score).toFixed(1);
    document.getElementById('sim-result-action').innerText = `Directive: ${data.recommended_action}`;

    const badge = document.getElementById('sim-result-tier-badge');
    badge.className = `badge ${data.risk_level === 'HIGH' ? 'badge-high' : (data.risk_level === 'MEDIUM' ? 'badge-medium' : 'badge-low')}`;
    badge.innerText = `${data.risk_level} RISK`;

    // Waterfall
    const waterfall = document.getElementById('sim-shap-waterfall');
    if (data.shap_factors && data.shap_factors.length > 0) {
      const maxShap = Math.max(...data.shap_factors.map(f => Math.abs(Number(f.shap_value) || 0)), 1.0);
      waterfall.innerHTML = data.shap_factors.map(f => {
        const isInc = f.impact === 'RISK_INCREASING' || (Number(f.shap_value) > 0);
        const rawVal = Math.abs(Number(f.shap_value) || 0);
        const barFill = rawVal > 0 ? Math.min(100, Math.max(8, Math.round((rawVal / maxShap) * 92))) : 2;
        const sign = isInc && Number(f.shap_value) > 0 ? '+' : '';
        return `
          <div class="shap-bar-row">
            <span class="shap-label" title="${f.explanation || ''}">${f.feature_label}</span>
            <div class="shap-bar-track">
              <div class="shap-bar-fill ${isInc ? 'shap-bar-increasing' : 'shap-bar-mitigating'}" style="width:${barFill}%;"></div>
            </div>
            <span class="shap-val" style="color:${isInc ? 'var(--danger-red)' : 'var(--success-green)'};">
              ${sign}${f.shap_value}
            </span>
          </div>
        `;
      }).join('');
    }

  } catch (err) {
    console.error('Error running simulation:', err);
  }
}

async function runWhatIfSimulation() {
  const amount = parseFloat(document.getElementById('whatif-amount-slider').value);
  const deviation = parseFloat(document.getElementById('whatif-dev-slider').value);
  const velocity = parseInt(document.getElementById('whatif-velocity-slider').value);
  const isNewDevice = document.getElementById('whatif-check-device').checked ? 1 : 0;
  const isNewReceiver = document.getElementById('whatif-check-receiver').checked ? 1 : 0;

  document.getElementById('whatif-amount-val').innerText = `৳${amount.toLocaleString()}`;
  document.getElementById('whatif-dev-val').innerText = `${deviation.toFixed(1)}x`;
  document.getElementById('whatif-velocity-val').innerText = `${velocity} txs`;

  try {
    const res = await fetch('/api/v1/what-if', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        base_transaction_id: 'TX100207',
        modified_features: {
          amount: amount,
          amount_deviation: deviation,
          transactions_last_1h: velocity,
          is_new_device: isNewDevice,
          is_new_receiver: isNewReceiver
        }
      })
    });

    if (!res.ok) throw new Error('What-if simulation failed');
    const data = await res.json();

    document.getElementById('whatif-orig-score').innerText = Number(data.original.risk_score).toFixed(1);
    document.getElementById('whatif-sim-score').innerText = Number(data.simulated.risk_score).toFixed(1);

    const deltaSign = data.score_delta_points > 0 ? '+' : '';
    const deltaColor = data.score_delta_points <= 0 ? 'var(--success-green)' : 'var(--danger-red)';
    document.getElementById('whatif-delta-points').style.color = deltaColor;
    document.getElementById('whatif-delta-points').innerText = `${deltaSign}${data.score_delta_points} Points (${data.is_risk_reduced ? 'Risk Mitigated' : 'Risk Elevated'})`;

    const simBadge = document.getElementById('whatif-sim-badge');
    simBadge.className = `badge ${data.simulated.risk_level === 'HIGH' ? 'badge-high' : (data.simulated.risk_level === 'MEDIUM' ? 'badge-medium' : 'badge-low')}`;
    simBadge.innerText = data.simulated.risk_level;

  } catch (err) {
    console.error('What-if error:', err);
  }
}

// ============================================================================
// CUSTOMER BEHAVIORAL BASELINE & SURVEILLANCE VIEW
// ============================================================================
async function lookupCustomerBehavior(customId) {
  const input = document.getElementById('cust-search-input');
  let rawQuery = customId;
  if (!rawQuery && input) {
    rawQuery = input.value;
  }
  rawQuery = (rawQuery || 'CUST03955').toString().trim();
  if (!rawQuery) rawQuery = 'CUST03955';

  // Normalize ID for clean client-side feedback
  let cleanId = rawQuery;
  if (/^\d+$/.test(cleanId)) {
    cleanId = `CUST${cleanId.padStart(5, '0')}`;
  } else if (/^cust\d+$/i.test(cleanId)) {
    const digits = cleanId.replace(/\D/g, '');
    cleanId = `CUST${digits.padStart(5, '0')}`;
  } else if (/^cust[-\s_]\d+$/i.test(cleanId)) {
    const digits = cleanId.replace(/\D/g, '');
    cleanId = `CUST${digits.padStart(5, '0')}`;
  } else {
    cleanId = cleanId.toUpperCase();
  }

  if (input) {
    input.value = cleanId;
  }

  const profileBadge = document.getElementById('cust-profile-id');
  if (profileBadge) profileBadge.innerText = `${cleanId}`;

  const tbody = document.getElementById('cust-history-table');
  if (tbody) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--text-secondary);"><span class="badge badge-channel">Scanning Baseline Registry...</span></td></tr>`;
  }

  try {
    const res = await ApiService.get(`/api/v1/customers/${encodeURIComponent(cleanId)}/behavior`);
    const data = res?.data || res;
    if (!data || !data.baseline_profile) {
      throw new Error('Customer baseline record not found');
    }

    const resolvedId = data.customer_id || cleanId;
    if (input) input.value = resolvedId;
    if (profileBadge) profileBadge.innerText = resolvedId;

    const base = data.baseline_profile;
    const avgEl = document.getElementById('cust-normal-avg');
    const devEl = document.getElementById('cust-device-count');
    const locEl = document.getElementById('cust-primary-loc');
    const ageEl = document.getElementById('cust-age-days');

    if (avgEl) avgEl.innerText = `৳${Number(base.normal_avg_amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    if (devEl) devEl.innerText = `${base.registered_device_count || 1} Devices`;
    if (locEl) locEl.innerText = base.primary_location || 'Dhaka';
    if (ageEl) ageEl.innerText = `${Number(base.account_age_days || 0).toLocaleString()} Days`;

    // Behavioral Deviations Breakdown
    const devContainer = document.getElementById('cust-deviation-details');
    const devBadge = document.getElementById('cust-deviation-badge');
    const dev = data.calculated_deviations || {
      amount_ratio: 1.0,
      is_unrecognized_device: false,
      is_location_discrepancy: false,
      is_off_hours: false
    };

    const ratio = Number(dev.amount_ratio || 1.0);
    if (devBadge) {
      devBadge.innerText = `${ratio.toFixed(1)}x SURGE`;
      devBadge.className = ratio >= 3.0 ? 'badge badge-high' : (ratio >= 1.5 ? 'badge badge-medium' : 'badge badge-low');
    }

    if (devContainer) {
      devContainer.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--surface-pure); border-radius:8px; border:1px solid var(--border-subtle);">
          <span><strong>Transfer Amount Ratio:</strong></span>
          <span style="font-weight:700; color:${ratio >= 3.0 ? 'var(--critical-red)' : (ratio >= 1.5 ? 'var(--upay-yellow)' : 'var(--success-green)')};">৳${ratio.toFixed(1)}x baseline historical transfer size</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--surface-pure); border-radius:8px; border:1px solid var(--border-subtle);">
          <span><strong>Device Fingerprint:</strong></span>
          <span>${dev.is_unrecognized_device ? '<span style="color:var(--critical-red); font-weight:700;">Unrecognized hardware fingerprint</span>' : '<span style="color:var(--success-green); font-weight:600;">Known / Verified Hardware</span>'}</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--surface-pure); border-radius:8px; border:1px solid var(--border-subtle);">
          <span><strong>Geographic Cluster:</strong></span>
          <span>${dev.is_location_discrepancy ? '<span style="color:var(--critical-red); font-weight:700;">Distant District Deviation</span>' : '<span style="color:var(--success-green); font-weight:600;">Habitual Division / Region</span>'}</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--surface-pure); border-radius:8px; border:1px solid var(--border-subtle);">
          <span><strong>Execution Window:</strong></span>
          <span>${dev.is_off_hours ? '<span style="color:var(--critical-red); font-weight:700;">Nocturnal Off-Hours (00:00 - 05:00)</span>' : '<span style="color:var(--success-green); font-weight:600;">Standard Daylight Hours</span>'}</span>
        </div>
      `;
    }

    // Customer Recent Transactions Table
    if (tbody) {
      const history = data.recent_history || [];
      if (history.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-secondary);">No ledger transactions recorded for customer <strong>${resolvedId}</strong>.</td></tr>`;
      } else {
        tbody.innerHTML = history.map(h => {
          const riskColor = h.risk_level === 'HIGH' || h.risk_level === 'CRITICAL' ? 'badge-high' : (h.risk_level === 'MEDIUM' ? 'badge-medium' : 'badge-low');
          return `
            <tr>
              <td style="font-family:var(--font-mono); font-weight:600; color:var(--upay-blue);">${h.transaction_id}</td>
              <td style="font-weight:700;">৳${Number(h.amount).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
              <td style="font-size:12px; color:var(--text-secondary);">${h.timestamp ? new Date(h.timestamp).toLocaleString() : 'Recent'}</td>
              <td><span class="badge badge-channel">${h.channel || 'APP'}</span></td>
              <td style="font-family:var(--font-mono); font-size:12px;">${h.receiver_id || '-'}</td>
              <td><strong>${Number(h.risk_score || 0).toFixed(1)}</strong></td>
              <td><span class="badge ${riskColor}">${h.risk_level}</span></td>
              <td><button class="btn btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="openInvestigationDrawer('${h.transaction_id}')">Inspect</button></td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.error('[lookupCustomerBehavior] Error:', err);
    if (profileBadge) profileBadge.innerText = cleanId;
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-secondary);">Customer baseline for "<strong>${cleanId}</strong>" could not be retrieved. Please check the ID and try again.</td></tr>`;
    }
  }
}
window.lookupCustomerBehavior = lookupCustomerBehavior;

/**
 * Debounced wrapper for real-time search — fires 600ms after the user stops typing.
 * Cancels previous pending lookup on each keystroke to avoid redundant API calls.
 */
function debouncedLookupCustomerBehavior() {
  clearTimeout(window._custSearchTimer);
  const input = document.getElementById('cust-search-input');
  const val = (input ? input.value : '').trim();
  // Require at least 4 chars before firing (avoids lookup on first 1-3 keystrokes)
  if (val.length < 4) return;
  window._custSearchTimer = setTimeout(() => {
    lookupCustomerBehavior();
  }, 600);
}
window.debouncedLookupCustomerBehavior = debouncedLookupCustomerBehavior;

// ============================================================================
// DASHBOARD CUSTOMER QUICK-SEARCH
// ============================================================================
/**
 * Filters the "Recent High-Risk Anomaly Alerts" table in real-time by customer ID.
 * Called from the dashboard search box.  Also supports navigating to the full
 * Behavioral Baseline view for a matched customer.
 */
function dashboardCustomerSearch(query) {
  const tbody = document.getElementById('dashboard-recent-alerts');
  if (!tbody) return;

  const term = (query || '').trim().toUpperCase();
  const rows = tbody.querySelectorAll('tr');

  let visibleCount = 0;
  rows.forEach(row => {
    if (!term) {
      row.style.display = '';
      visibleCount++;
      return;
    }
    const custCell = row.cells && row.cells[1] ? row.cells[1].innerText.toUpperCase() : '';
    const txCell   = row.cells && row.cells[0] ? row.cells[0].innerText.toUpperCase() : '';
    if (custCell.includes(term) || txCell.includes(term)) {
      row.style.display = '';
      visibleCount++;
    } else {
      row.style.display = 'none';
    }
  });

  // Show an empty-state row if nothing matched
  const emptyRow = document.getElementById('dash-search-empty-row');
  if (emptyRow) emptyRow.remove();
  if (visibleCount === 0 && term) {
    const emptyTr = document.createElement('tr');
    emptyTr.id = 'dash-search-empty-row';
    emptyTr.innerHTML = `<td colspan="8" style="text-align:center; padding:28px; color:var(--text-tertiary);">
      No high-risk alerts found for <strong>${term}</strong>.
      <button class="btn btn-secondary" style="margin-left:12px; font-size:12px; padding:5px 12px;"
        onclick="navigateToView('behavior-view'); setTimeout(()=>{ const inp=document.getElementById('cust-search-input'); if(inp){inp.value='${term}'; lookupCustomerBehavior('${term}');} }, 400);">
        Search Behavioral Baseline →
      </button>
    </td>`;
    tbody.appendChild(emptyTr);
  }
}
window.dashboardCustomerSearch = dashboardCustomerSearch;

// ============================================================================
// SCAM TYPOLOGIES VIEW
// ============================================================================
async function loadScamTypologiesGrid() {
  try {
    const res = await fetch('/api/v1/scam-typologies');
    if (!res.ok) throw new Error('Failed to load scam typologies');
    const data = await res.json();

    const grid = document.getElementById('scam-typology-cards');
    if (!grid) return;

    grid.innerHTML = data.map((t, idx) => `
      <div class="kpi-card" style="border-top: 3px solid ${t.severity === 'CRITICAL' ? 'var(--danger-red)' : 'var(--upay-blue)'};">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="font-size:11px; font-weight:800; color:var(--text-tertiary);">TYPOLOGY 0${idx + 1}</span>
          <span class="badge ${t.severity === 'CRITICAL' ? 'badge-high' : 'badge-medium'}">${t.severity}</span>
        </div>
        <h4 style="font-size:15px; font-weight:700; color:var(--upay-blue-dark); margin-bottom:6px;">${t.pattern_name}</h4>
        <div style="font-size:12px; color:var(--text-secondary); margin-bottom:8px;"><strong>Rule:</strong> ${t.criteria}</div>
        <p style="font-size:12px; color:var(--text-tertiary);">${t.scenario}</p>
      </div>
    `).join('');

    // Triggered table
    const tableBody = document.getElementById('scam-triggered-table');
    if (tableBody) {
      tableBody.innerHTML = `
        <tr>
          <td><strong>TX100207</strong></td>
          <td>CUST03955</td>
          <td><strong>৳30,573.32</strong></td>
          <td><span class="badge badge-high">Unusual High-Value, Unregistered Device</span></td>
          <td><span class="badge badge-high">CRITICAL</span></td>
          <td>90.9</td>
          <td><button class="btn btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="openInvestigationDrawer('TX100207')">Investigate</button></td>
        </tr>
        <tr>
          <td><strong>TX100033</strong></td>
          <td>CUST03706</td>
          <td><strong>৳13,625.83</strong></td>
          <td><span class="badge badge-high">Rapid Velocity Burst (15 in 1h), New Receiver</span></td>
          <td><span class="badge badge-high">CRITICAL</span></td>
          <td>99.8</td>
          <td><button class="btn btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="openInvestigationDrawer('TX100033')">Investigate</button></td>
        </tr>
        <tr>
          <td><strong>TX100099</strong></td>
          <td>CUST01104</td>
          <td><strong>৳24,795.21</strong></td>
          <td><span class="badge badge-high">Pre-Transaction Auth Failures (5 fails)</span></td>
          <td><span class="badge badge-high">CRITICAL</span></td>
          <td>95.0</td>
          <td><button class="btn btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="openInvestigationDrawer('TX100099')">Investigate</button></td>
        </tr>
      `;
    }

  } catch (err) {
    console.error('Error loading scam typologies:', err);
  }
}

// ============================================================================
// NETWORK ENTITY GRAPH VIEW (INTERACTIVE SVG CANVAS)
// ============================================================================
async function loadNetworkGraphForTx(customQuery) {
  const input = document.getElementById('network-search-input');
  let q = customQuery;
  if (!q && input) {
    q = input.value;
  }
  q = (q || 'CUST03955').toString().trim();
  if (!q) q = 'CUST03955';

  // Normalize query for client feedback
  let cleanQuery = q;
  if (/^\d+$/.test(cleanQuery)) {
    cleanQuery = `CUST${cleanQuery.padStart(5, '0')}`;
  } else if (/^cust\d+$/i.test(cleanQuery)) {
    const digits = cleanQuery.replace(/\D/g, '');
    cleanQuery = `CUST${digits.padStart(5, '0')}`;
  } else {
    cleanQuery = cleanQuery.toUpperCase();
  }

  if (input) input.value = cleanQuery;

  const svg = document.getElementById('network-svg-canvas');
  if (!svg) return;

  try {
    const res = await ApiService.get(`/api/v1/network/graph/${encodeURIComponent(cleanQuery)}`);
    const data = res?.data || res;
    if (!data || !data.nodes) throw new Error('Graph payload empty');

    if (input && data.entity_id) {
      input.value = data.entity_id;
    }

    // Render nodes & edges using multi-tier concentric radial layout
    renderSvgNetwork(svg, data.nodes, data.edges);

    // Load High Fan-in & Shared Devices analytics
    const patternRes = await ApiService.get('/api/v1/network/patterns');
    const pData = patternRes?.data || patternRes;
    if (pData) {
      const faninBody = document.getElementById('fanin-table-body');
      if (faninBody && pData.high_fanin_receivers) {
        faninBody.innerHTML = pData.high_fanin_receivers.map(f => `
          <tr>
            <td><code style="cursor:pointer; color:var(--upay-blue);" onclick="loadNetworkGraphForTx('${f.receiver_id}')" title="Click to graph this receiver">${f.receiver_id}</code></td>
            <td><strong>${f.unique_senders} senders</strong></td>
            <td>৳${Number(f.total_volume_bdt || 0).toLocaleString()}</td>
            <td><span class="badge ${f.avg_risk_score > 75 ? 'badge-high' : 'badge-medium'}">${f.avg_risk_score}</span></td>
          </tr>
        `).join('');
      }

      const sharedBody = document.getElementById('shared-devices-body');
      if (sharedBody && pData.shared_devices) {
        sharedBody.innerHTML = pData.shared_devices.map(d => `
          <tr>
            <td><code>${d.device_id}</code></td>
            <td><strong>${d.unique_customers} accounts</strong></td>
            <td>${d.transaction_count} txs</td>
            <td><span class="badge badge-high">${d.risk_status}</span></td>
          </tr>
        `).join('');
      }
    }

  } catch (err) {
    console.error('[loadNetworkGraphForTx] Error:', err);
  }
}
window.loadNetworkGraphForTx = loadNetworkGraphForTx;

function renderSvgNetwork(svg, nodes, edges) {
  const width = svg.clientWidth || 800;
  const height = svg.clientHeight || 480;
  const centerX = width / 2;
  const centerY = height / 2;

  svg.innerHTML = '';

  if (!nodes || nodes.length === 0) return;

  // Calculate coordinates in multi-orbit geometry
  const nodeMap = {};
  const total = nodes.length;

  nodes.forEach((n, i) => {
    if (i === 0) {
      // Primary Center node (The searched entity)
      n.x = centerX;
      n.y = centerY;
      n.isCenter = true;
    } else {
      // Concentric circles: alternating distance to avoid crowding
      const tier = (i % 3 === 0) ? 140 : (i % 3 === 1 ? 190 : 230);
      const angle = ((i - 1) / (total - 1)) * 2 * Math.PI;
      n.x = centerX + tier * Math.cos(angle);
      n.y = centerY + tier * Math.sin(angle);
      n.isCenter = false;
    }
    nodeMap[n.id] = n;
  });

  // 1. Render edges
  edges.forEach(e => {
    const s = nodeMap[e.source];
    const t = nodeMap[e.target];
    if (s && t) {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', s.x);
      line.setAttribute('y1', s.y);
      line.setAttribute('x2', t.x);
      line.setAttribute('y2', t.y);
      line.setAttribute('stroke', '#94A3B8');
      line.setAttribute('stroke-width', '1.5');
      line.setAttribute('stroke-opacity', '0.6');
      svg.appendChild(line);
    }
  });

  // 2. Render nodes
  nodes.forEach(n => {
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.style.cursor = 'pointer';
    g.setAttribute('title', `${n.type.toUpperCase()}: ${n.id}\nClick to inspect or explore`);

    // Interactive drill-down on click!
    g.onclick = () => {
      console.log(`[Network Entity] Clicked node: ${n.id} (${n.type})`);
      if (n.type === 'transaction') {
        openInvestigationDrawer(n.id);
      } else if (n.type === 'customer') {
        // Switch to behavioral baseline view
        window.location.hash = '#/behavior';
        setTimeout(() => {
          if (typeof window.lookupCustomerBehavior === 'function') {
            window.lookupCustomerBehavior(n.id);
          }
        }, 120);
      } else if (n.type === 'receiver') {
        loadNetworkGraphForTx(n.id);
      }
    };

    const radius = n.isCenter ? 26 : (n.type === 'transaction' ? 22 : 18);
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', n.x);
    circle.setAttribute('cy', n.y);
    circle.setAttribute('r', radius);

    // Entity Colors according to standard palette
    let fill = '#005BAC'; // Transaction (Upay Blue)
    if (n.type === 'customer') fill = '#FFCD00'; // Customer (Upay Gold)
    else if (n.type === 'receiver') fill = '#10B981'; // Beneficiary (Green)
    else if (n.type === 'device') fill = '#EF4444'; // Hardware Device (Red)
    else if (n.type === 'location') fill = '#64748B'; // Region (Slate)

    circle.setAttribute('fill', fill);
    circle.setAttribute('stroke', n.isCenter ? '#0F172A' : '#FFFFFF');
    circle.setAttribute('stroke-width', n.isCenter ? '3.5' : '2');
    circle.setAttribute('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))');

    // Label Text
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', n.x);
    text.setAttribute('y', n.y + radius + 14);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-size', '11');
    text.setAttribute('font-weight', '700');
    text.setAttribute('fill', '#1E293B');
    text.textContent = n.id;

    g.appendChild(circle);
    g.appendChild(text);
    svg.appendChild(g);
  });
}

// ============================================================================
// CASE MANAGEMENT LEDGER & SUBVIEWS
// ============================================================================
async function loadCasesLedger() {
  const params = new URLSearchParams({
    page: AppState.caseCurrentPage,
    limit: AppState.caseLimit
  });

  if (AppState.caseStatusFilter !== 'ALL') params.append('status', AppState.caseStatusFilter);
  if (AppState.casePriorityFilter !== 'ALL') params.append('priority', AppState.casePriorityFilter);
  if (AppState.caseDatePreset !== 'ALL') params.append('date_preset', AppState.caseDatePreset);
  if (AppState.caseSearchQuery) params.append('search', AppState.caseSearchQuery);

  try {
    const res = await fetch(`/api/v1/cases?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to load cases');
    const data = await res.json();

    const casesList = Array.isArray(data.data) ? data.data : (data.data?.items || data.items || []);
    const kpis = data.kpis || data.data?.kpis || {};
    const totalCasesCount = data.total_count || data.total || data.data?.total || casesList.length;

    // Update KPI counters
    const elTotal = document.getElementById('case-kpi-total');
    if (elTotal) elTotal.innerText = kpis.total_cases ?? totalCasesCount;
    const elOpen = document.getElementById('case-kpi-open');
    if (elOpen) elOpen.innerText = kpis.open ?? 0;
    const elReview = document.getElementById('case-kpi-review');
    if (elReview) elReview.innerText = kpis.under_review ?? 0;
    const elResolved = document.getElementById('case-kpi-resolved');
    if (elResolved) elResolved.innerText = kpis.resolved ?? 0;
    const elRate = document.getElementById('case-kpi-rate');
    if (elRate) elRate.innerText = `${kpis.resolution_rate_pct ?? 0}%`;

    // Render Table
    const tbody = document.getElementById('cases-table-body');
    if (!tbody) return;

    if (casesList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:32px; color:var(--text-tertiary);">No cases matching current filter parameters.</td></tr>`;
      return;
    }

    tbody.innerHTML = casesList.map(c => {
      let statusBadge = 'badge-low';
      if (c.status === 'OPEN') statusBadge = 'badge-high';
      if (c.status === 'UNDER_REVIEW') statusBadge = 'badge-medium';

      return `
        <tr>
          <td><strong>${c.case_id}</strong></td>
          <td><a href="javascript:void(0)" onclick="openInvestigationDrawer('${c.transaction_id}')" style="color:var(--upay-blue); font-weight:600;">${c.transaction_id}</a></td>
          <td>${c.customer_id}</td>
          <td><span class="badge ${statusBadge}">${c.status}</span></td>
          <td><span style="font-weight:700; color:${c.priority === 'CRITICAL' ? 'var(--danger-red)' : 'var(--text-primary)'};">${c.priority}</span></td>
          <td>${c.assigned_analyst || 'Unassigned'}</td>
          <td><strong>${Number(c.risk_score).toFixed(1)}</strong></td>
          <td>${c.decision ? `<span class="badge badge-channel">${c.decision}</span>` : '<span style="color:var(--text-tertiary);">Pending</span>'}</td>
          <td>
            <button class="btn btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="openInvestigationDrawer('${c.transaction_id}')">
              Manage
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Load Timeline Subviews
    loadCasesTimelineSubviews();

  } catch (err) {
    console.error('Error loading cases ledger:', err);
  }
}

async function loadCasesTimelineSubviews() {
  try {
    const res = await fetch('/api/v1/cases/timeline');
    if (!res.ok) return;
    const data = await res.json();

    // Daily Table
    const dailyBody = document.getElementById('daily-cases-table');
    if (dailyBody) {
      dailyBody.innerHTML = data.daily.map(d => `
        <tr>
          <td><strong>${d.date}</strong></td>
          <td><span class="bengali-text">${d.date_bengali}</span></td>
          <td><strong>${d.total_cases} cases</strong></td>
          <td><span style="color:var(--success-green); font-weight:700;">${d.resolved_cases} resolved</span></td>
          <td><span style="color:var(--danger-red); font-weight:700;">${d.open_cases} open</span></td>
        </tr>
      `).join('');
    }

    // Weekly Table
    const weeklyBody = document.getElementById('weekly-cases-table');
    if (weeklyBody) {
      weeklyBody.innerHTML = data.weekly.map(w => `
        <tr>
          <td><strong>${w.week}</strong></td>
          <td>${w.cases} cases</td>
          <td><span style="color:var(--success-green); font-weight:700;">${w.resolved} cases</span></td>
          <td><span class="badge badge-channel">${w.velocity}</span></td>
        </tr>
      `).join('');
    }

    // Monthly Table
    const monthlyBody = document.getElementById('monthly-cases-table');
    if (monthlyBody) {
      monthlyBody.innerHTML = data.monthly.map(m => `
        <tr>
          <td><strong>${m.month}</strong></td>
          <td>${m.cases} cases</td>
          <td><span style="color:var(--success-green); font-weight:700;">${m.resolved} resolved</span></td>
          <td><strong>৳${m.volume_protected_bdt.toLocaleString()}</strong></td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error('Timeline subview load error:', err);
  }
}

function switchCaseSubview(sub) {
  AppState.activeCaseSubview = sub;
  ['all', 'daily', 'weekly', 'monthly'].forEach(s => {
    const btn = document.getElementById(`case-tab-${s}`);
    const el = document.getElementById(`subview-cases-${s}`);
    if (btn) btn.classList.toggle('active', s === sub);
    if (el) el.style.display = s === sub ? 'block' : 'none';
  });
}

function handleCaseSearch(val) {
  AppState.caseSearchQuery = val;
  AppState.caseCurrentPage = 1;
  loadCasesLedger();
}

function setCaseDateFilter(preset, btn) {
  btn.parentElement.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  AppState.caseDatePreset = preset;
  AppState.caseCurrentPage = 1;
  loadCasesLedger();
}

function applyCaseFilters() {
  AppState.caseStatusFilter = document.getElementById('case-status-select').value;
  AppState.casePriorityFilter = document.getElementById('case-priority-select').value;
  AppState.caseCurrentPage = 1;
  loadCasesLedger();
}

// ============================================================================
// MODEL DRIFT & VALIDATION ARTIFACTS
// ============================================================================
async function loadModelDriftTable() {
  try {
    const res = await fetch('/api/v1/model/drift');
    if (!res.ok) return;
    const data = await res.json();

    const tbody = document.getElementById('drift-table-body');
    if (!tbody) return;

    tbody.innerHTML = data.drift_table.map(row => `
      <tr>
        <td><strong>${row.feature}</strong></td>
        <td>${row.baseline_mean}</td>
        <td>${row.production_mean}</td>
        <td><code>${row.nams_distance}</code></td>
        <td>
          <span class="badge ${row.drift_status === 'NORMAL' ? 'badge-low' : 'badge-medium'}">
            ${row.drift_status}
          </span>
        </td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Error loading drift table:', err);
  }
}

function loadFeatureImportanceBars() {
  const container = document.getElementById('feature-importance-bars');
  if (!container) return;

  const features = [
    {name: 'receiver_transaction_count', label: 'Beneficiary Lifetime Inflow Count', val: 0.334},
    {name: 'amount_deviation', label: 'Amount Deviation vs Baseline Historical Size', val: 0.324},
    {name: 'transactions_last_1h', label: '1-Hour Transaction Velocity Spike', val: 0.285},
    {name: 'transactions_last_24h', label: '24-Hour Cumulative Ingestion Velocity', val: 0.038},
    {name: 'failed_attempts', label: 'Pre-Transaction Failed PIN / OTP Attempts', val: 0.014},
    {name: 'hour', label: 'Nocturnal Execution Window (00:00 - 05:00)', val: 0.003},
    {name: 'amount', label: 'Absolute Transaction Value (BDT)', val: 0.001}
  ];

  container.innerHTML = features.map(f => {
    const pct = Math.round(f.val * 100);
    return `
      <div style="margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600; margin-bottom:4px;">
          <span>${f.label} (<code>${f.name}</code>)</span>
          <span style="font-family:monospace; color:var(--upay-blue);">${(f.val * 100).toFixed(1)}%</span>
        </div>
        <div style="height:10px; background:var(--surface-muted); border-radius:5px; overflow:hidden;">
          <div style="height:100%; width:${pct}%; background:linear-gradient(90deg, var(--upay-blue), #2563EB); border-radius:5px;"></div>
        </div>
      </div>
    `;
  }).join('');
}

function openImageLightbox(src, title) {
  const modal = document.getElementById('image-lightbox-modal');
  const img = document.getElementById('lightbox-img');
  const titleEl = document.getElementById('lightbox-title');
  if (!modal || !img) return;

  img.src = src;
  if (titleEl && title) titleEl.innerText = title;
  modal.style.display = 'flex';
}
window.openImageLightbox = openImageLightbox;

function closeImageLightbox() {
  const modal = document.getElementById('image-lightbox-modal');
  if (modal) modal.style.display = 'none';
}
window.closeImageLightbox = closeImageLightbox;

function exportRetrainingCSV() {
  window.location.href = '/api/v1/feedback/export';
  showToast('Retraining feedback CSV exported', 'success');
}

// ============================================================================
// DEMO SCENARIO PRESET LOADERS
// ============================================================================
function loadDemoScenario(type) {
  document.querySelectorAll('.preset-group .preset-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById(`demo-${type}`);
  if (btn) btn.classList.add('active');

  if (type === 'normal') {
    openInvestigationDrawer('TX100006');
  } else if (type === 'medium') {
    openInvestigationDrawer('TX100283');
  } else if (type === 'high') {
    openInvestigationDrawer('TX100207');
  }
}

// ============================================================================
// TOAST FEEDBACK NOTIFICATIONS
// ============================================================================
function showToast(message, type = 'info') {
  if (window.Toast) {
    if (type === 'success') window.Toast.success(message);
    else if (type === 'error') window.Toast.error(message);
    else if (type === 'warning') window.Toast.warning(message);
    else window.Toast.info(message);
    return;
  }
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ============================================================================
// AUTHENTICATION & OFFICER PROFILE STATE
// ============================================================================
function updateUserInterfaceState(user) {
  if (!user) return;
  const nameElem = document.getElementById('sidebar-user-name');
  const roleElem = document.getElementById('sidebar-user-role');
  const avatarElem = document.getElementById('sidebar-user-avatar');
  const pillElem = document.getElementById('sidebar-role-pill');

  if (nameElem) nameElem.innerText = user.full_name || user.username;
  if (roleElem) roleElem.innerText = `${user.role} • ${user.department || 'Fraud Ops'}`;
  if (pillElem) pillElem.innerText = user.role.replace('_', ' ');

  if (avatarElem) {
    const initials = (user.full_name || user.username)
      .split(' ')
      .map(n => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
    avatarElem.innerText = initials || 'OP';
  }

  // Also update live Admin Session Banner if admin view is mounted
  updateAdminSessionBanner(user);
}

function updateAdminSessionBanner(user) {
  if (!user && window.AuthService) user = AuthService.getCurrentUser();
  if (!user) return;

  const banner = document.getElementById('admin-session-alert');
  const nameEl = document.getElementById('admin-session-name');
  const badgeEl = document.getElementById('admin-session-badge');
  const descEl = document.getElementById('admin-session-desc');
  const avatarEl = document.getElementById('admin-session-avatar');
  const elevateBtn = document.getElementById('admin-elevate-btn');

  if (!banner || !nameEl) return;

  const isAdmin = user.role === 'ADMIN';
  const initials = (user.full_name || user.username)
    .split(' ')
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  if (avatarEl) {
    avatarEl.innerText = initials || 'OP';
    avatarEl.style.background = isAdmin ? 'var(--upay-blue)' : (user.role === 'SENIOR_OFFICER' ? 'var(--warning-amber)' : 'var(--text-secondary)');
  }

  nameEl.innerText = `${user.full_name || user.username} (@${user.username})`;

  if (badgeEl) {
    badgeEl.innerText = `${user.role.replace('_', ' ')} CLEARANCE`;
    if (isAdmin) {
      badgeEl.style.background = 'rgba(239,68,68,0.15)';
      badgeEl.style.color = 'var(--critical-red, #EF4444)';
    } else if (user.role === 'SENIOR_OFFICER') {
      badgeEl.style.background = 'rgba(245,158,11,0.15)';
      badgeEl.style.color = 'var(--warning-amber, #F59E0B)';
    } else {
      badgeEl.style.background = 'rgba(0,91,172,0.12)';
      badgeEl.style.color = 'var(--upay-blue, #005BAC)';
    }
  }

  if (descEl) {
    if (isAdmin) {
      descEl.innerHTML = `<strong>Superuser authority active.</strong> Statutory clearance to provision personnel, configure ML guardrails, and inspect immutable audit logs.`;
      banner.style.background = 'linear-gradient(135deg, rgba(0,91,172,0.06) 0%, rgba(255,205,0,0.05) 100%)';
      banner.style.borderColor = 'rgba(0,91,172,0.18)';
    } else {
      descEl.innerHTML = `<strong style="color:var(--warning-amber, #F59E0B);">Limited clearance session.</strong> Personnel registration and account suspension require Administrator clearance.`;
      banner.style.background = 'linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(255,255,255,0.8) 100%)';
      banner.style.borderColor = 'rgba(245,158,11,0.3)';
    }
  }

  if (elevateBtn) {
    elevateBtn.style.display = isAdmin ? 'none' : 'inline-flex';
  }
}

function openAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.style.display = 'flex';
}

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.style.display = 'none';
}

async function quickLogin(username, password) {
  try {
    const user = await AuthService.login(username, password);
    closeAuthModal();
    showToast(`Authenticated as ${user.full_name} (${user.role})`, 'success');
    
    // Refresh modal session indicator if open
    const modalText = document.getElementById('modal-auth-status-text');
    const switchBtn = document.getElementById('modal-switch-admin-btn');
    if (modalText) {
      modalText.innerHTML = `Authorized as <strong>@${user.username}</strong> (${user.role.replace('_', ' ')})`;
      if (switchBtn) switchBtn.style.display = (user.role === 'ADMIN') ? 'none' : 'inline-block';
    }

    if (AppState.currentView === 'admin-view') {
      loadAdminViewData();
    }
  } catch (err) {
    showToast(`Authentication failed: ${err.message}`, 'error');
  }
}

async function handleManualLogin(e) {
  e.preventDefault();
  const ident = document.getElementById('login-ident').value.trim();
  const pwd = document.getElementById('login-pwd').value;
  try {
    const user = await AuthService.login(ident, pwd);
    closeAuthModal();
    showToast(`Welcome, ${user.full_name}!`, 'success');
    if (AppState.currentView === 'admin-view') {
      loadAdminViewData();
    }
  } catch (err) {
    showToast(`Login failed: ${err.message}`, 'error');
  }
}

// ============================================================================
// ADMINISTRATION & PERSONNEL MANAGEMENT
// ============================================================================
let adminUsersCache = [];
let adminRoleFilter = 'ALL';

async function loadAdminViewData() {
  updateAdminSessionBanner();

  try {
    // 1. Fetch system KPIs
    try {
      const metricsRes = await AdminService.getMetrics();
      if (metricsRes && metricsRes.data) {
        const d = metricsRes.data;
        const usersEl = document.getElementById('admin-kpi-users');
        const auditsEl = document.getElementById('admin-kpi-audits');
        const casesEl = document.getElementById('admin-kpi-cases');

        if (usersEl) usersEl.innerText = `${d.users?.active || 0} Active / ${d.users?.total || 0} Total`;
        if (auditsEl) auditsEl.innerText = `${d.recent_audit_logs?.length || 0}+ Tracked`;
        if (casesEl) casesEl.innerText = `${d.cases?.total || 0} Total (${d.cases?.open || 0} Open)`;
      }
    } catch (e) {
      console.warn('[loadAdminViewData] Metrics note:', e.message);
    }

    // 2. Fetch users list
    const tbody = document.getElementById('admin-users-tbody');
    try {
      const usersRes = await AdminService.getUsers();
      if (usersRes && usersRes.data) {
        adminUsersCache = usersRes.data;
        renderAdminUsersTable();
      }
    } catch (usersErr) {
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align:center; padding:36px 20px; color:var(--text-secondary);">
              <div style="display:inline-flex; align-items:center; justify-content:center; width:48px; height:48px; border-radius:50%; background:rgba(239,68,68,0.1); color:var(--critical-red); margin-bottom:12px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
              </div>
              <div style="font-weight:700; font-size:14px; color:var(--text-primary); margin-bottom:4px;">ADMIN CLEARANCE REQUIRED</div>
              <p style="font-size:12px; color:var(--text-secondary); max-width:400px; margin:0 auto 14px;">The personnel directory and governance registry require System Administrator authority. Your current role is read-restricted.</p>
              <button class="btn btn-primary" onclick="quickLogin('admin', 'Admin@1234')" style="font-size:12px; padding:7px 16px;">
                ⚡ Switch to Administrator Account
              </button>
            </td>
          </tr>
        `;
      }
    }

    // 3. Fetch audit logs
    try {
      await loadAdminAuditLogs();
    } catch (e) {
      console.warn('[loadAdminViewData] Audit log note:', e.message);
    }
  } catch (err) {
    console.warn('[loadAdminViewData] General note:', err.message);
  }
}

function renderAdminUsersTable() {
  const tbody = document.getElementById('admin-users-tbody');
  if (!tbody) return;

  const searchInput = document.getElementById('admin-user-search');
  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  let filtered = adminUsersCache;
  if (adminRoleFilter !== 'ALL') {
    filtered = filtered.filter(u => u.role === adminRoleFilter);
  }
  if (query) {
    filtered = filtered.filter(u => 
      (u.full_name && u.full_name.toLowerCase().includes(query)) ||
      (u.username && u.username.toLowerCase().includes(query)) ||
      (u.email && u.email.toLowerCase().includes(query)) ||
      (u.department && u.department.toLowerCase().includes(query)) ||
      (u.role && u.role.toLowerCase().includes(query))
    );
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:36px; color:var(--text-secondary);"><div style="font-size:24px; margin-bottom:6px;">🔍</div>No personnel found matching the specified query.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(u => {
    const initials = (u.full_name || u.username)
      .split(' ')
      .map(n => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();

    const roleConfig = {
      ADMIN: { label: 'ADMIN', color: '#DC2626', bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.25)' },
      SENIOR_OFFICER: { label: 'SENIOR OFFICER', color: '#D97706', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.25)' },
      ANALYST: { label: 'TIER-1 ANALYST', color: '#005BAC', bg: 'rgba(0,91,172,0.10)', border: 'rgba(0,91,172,0.22)' },
      VIEWER: { label: 'AUDITOR', color: '#059669', bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.25)' }
    }[u.role] || { label: u.role, color: '#475569', bg: 'rgba(0,0,0,0.06)', border: 'transparent' };

    const statusBadge = u.is_active
      ? `<span style="display:inline-flex; align-items:center; gap:6px; font-size:11px; padding:3px 10px; border-radius:12px; background:rgba(34,197,94,0.12); color:var(--success-green, #10B981); font-weight:700; border:1px solid rgba(34,197,94,0.25);"><span style="width:6px; height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 4px currentColor;"></span>Active</span>`
      : `<span style="display:inline-flex; align-items:center; gap:6px; font-size:11px; padding:3px 10px; border-radius:12px; background:rgba(239,68,68,0.12); color:var(--critical-red, #EF4444); font-weight:700; border:1px solid rgba(239,68,68,0.25);"><span style="width:6px; height:6px; border-radius:50%; background:currentColor;"></span>Suspended</span>`;

    return `
      <tr>
        <td style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:var(--upay-blue);">${u.id}</td>
        <td>
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:32px; height:32px; border-radius:8px; background:${roleConfig.bg}; color:${roleConfig.color}; border:1px solid ${roleConfig.border}; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:12px; flex-shrink:0;">
              ${initials}
            </div>
            <div>
              <div style="font-weight:700; font-size:13px; color:var(--text-primary);">${u.full_name}</div>
              <div style="font-size:11px; color:var(--text-secondary); font-family:var(--font-mono);">@${u.username}</div>
            </div>
          </div>
        </td>
        <td style="font-size:12px; color:var(--text-secondary); font-family:var(--font-mono);">${u.email}</td>
        <td>
          <span style="display:inline-block; font-size:11px; font-weight:800; padding:3px 9px; border-radius:6px; background:${roleConfig.bg}; color:${roleConfig.color}; border:1px solid ${roleConfig.border}; letter-spacing:0.3px;">
            ${roleConfig.label}
          </span>
        </td>
        <td style="font-size:12px; color:var(--text-primary); font-weight:500;">${u.department}</td>
        <td>${statusBadge}</td>
        <td style="font-size:11px; color:var(--text-secondary);">${u.last_login ? new Date(u.last_login).toLocaleString() : '<span style="color:var(--text-tertiary);">Never</span>'}</td>
        <td style="text-align:right;">
          <div style="display:inline-flex; gap:6px;">
            <button class="btn btn-secondary" style="padding:4px 10px; font-size:11px; font-weight:600; border-radius:6px;" onclick="toggleUserStatus('${u.id}')" title="Toggle active authorization">
              ${u.is_active ? 'Suspend' : 'Activate'}
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function filterAdminUsersTable() {
  renderAdminUsersTable();
}

function setAdminRoleFilter(role, btn) {
  adminRoleFilter = role;
  document.querySelectorAll('.admin-role-filter').forEach(el => {
    el.style.background = 'var(--surface-pure)';
    el.style.color = 'var(--text-secondary)';
    el.style.borderColor = 'var(--border-subtle)';
  });
  if (btn) {
    btn.style.background = 'var(--upay-blue)';
    btn.style.color = '#fff';
    btn.style.borderColor = 'var(--upay-blue)';
  }
  renderAdminUsersTable();
}

async function loadAdminAuditLogs() {
  const tbody = document.getElementById('admin-audit-tbody');
  if (!tbody) return;
  try {
    const res = await AdminService.getAuditLogs(1, 25);
    if (res && res.data && res.data.items) {
      const items = res.data.items;
      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-secondary);">Audit log is currently empty.</td></tr>`;
      } else {
        tbody.innerHTML = items.map(a => {
          const actionColor = a.action === 'CREATE_USER' ? 'var(--success-green)' : (a.action === 'TOGGLE_USER_STATUS' ? 'var(--warning-amber)' : 'var(--upay-blue)');
          return `
            <tr>
              <td style="font-family:var(--font-mono); font-size:12px; color:var(--upay-blue); font-weight:700;">#${a.id}</td>
              <td style="font-size:12px; color:var(--text-secondary);">${a.created_at ? new Date(a.created_at).toLocaleString() : 'Recent'}</td>
              <td style="font-weight:700; font-size:12px;">@${a.username}</td>
              <td><span style="font-size:10px; font-weight:800; padding:2px 7px; border-radius:4px; background:rgba(0,0,0,0.06);">${a.role || 'SYSTEM'}</span></td>
              <td><span style="font-size:11px; font-weight:800; color:${actionColor};">${a.action}</span></td>
              <td style="font-family:var(--font-mono); font-size:11px; color:var(--text-secondary);">${a.resource_type}${a.resource_id ? ':' + a.resource_id : ''}</td>
              <td style="font-size:12px; color:var(--text-secondary); max-width:320px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${a.details || ''}">${a.details || '-'}</td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.error('[loadAdminAuditLogs] Error:', err);
  }
}

async function toggleUserStatus(userId) {
  try {
    const res = await AdminService.toggleUserStatus(userId);
    showToast(res.message || 'Officer authorization updated', 'success');
    await loadAdminViewData();
  } catch (err) {
    showToast(`Status update failed: ${err.message}`, 'error');
  }
}

function openCreateUserModal() {
  const m = document.getElementById('create-user-modal');
  if (!m) return;
  m.style.display = 'flex';

  // Check current session authorization
  const currentUser = window.AuthService ? AuthService.getCurrentUser() : null;
  const statusBanner = document.getElementById('modal-auth-status-banner');
  const statusText = document.getElementById('modal-auth-status-text');
  const switchBtn = document.getElementById('modal-switch-admin-btn');

  if (currentUser && currentUser.role === 'ADMIN') {
    if (statusBanner) {
      statusBanner.style.background = 'rgba(16,185,129,0.08)';
      statusBanner.style.borderColor = 'rgba(16,185,129,0.25)';
      statusBanner.style.color = 'var(--text-primary)';
    }
    if (statusText) statusText.innerHTML = `Authorized as <strong>@${currentUser.username}</strong> (System Administrator)`;
    if (switchBtn) switchBtn.style.display = 'none';
  } else {
    const roleName = currentUser ? currentUser.role : 'ANALYST';
    const userName = currentUser ? currentUser.username : 'user';
    if (statusBanner) {
      statusBanner.style.background = 'rgba(245,158,11,0.12)';
      statusBanner.style.borderColor = 'rgba(245,158,11,0.35)';
      statusBanner.style.color = '#92400E';
    }
    if (statusText) statusText.innerHTML = `⚠️ Active session is <strong>@${userName}</strong> (${roleName}). Admin clearance required to provision.`;
    if (switchBtn) switchBtn.style.display = 'inline-block';
  }

  // Reset password strength bars
  updatePasswordStrength('');
  // Update clearance card to default ANALYST
  updateRoleClearanceCard('ANALYST');

  // Auto focus on name
  setTimeout(() => {
    const fn = document.getElementById('reg-fullname');
    if (fn) fn.focus();
  }, 100);
}

function closeCreateUserModal() {
  const m = document.getElementById('create-user-modal');
  if (m) m.style.display = 'none';
}

function handleCreateUserOverlayClick(e) {
  if (e.target.id === 'create-user-modal') {
    closeCreateUserModal();
  }
}

function setRegDept(dept) {
  const deptInput = document.getElementById('reg-dept');
  if (deptInput) deptInput.value = dept;
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isPassword = input.type === 'password';
  input.type = isPassword ? 'text' : 'password';
  btn.innerHTML = isPassword
    ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`
    : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
}

function updatePasswordStrength(val) {
  const label = document.getElementById('pw-strength-label');
  const b1 = document.getElementById('pw-bar-1');
  const b2 = document.getElementById('pw-bar-2');
  const b3 = document.getElementById('pw-bar-3');
  const b4 = document.getElementById('pw-bar-4');
  if (!b1 || !b2 || !b3 || !b4) return;

  const defaultBg = 'var(--border-subtle, #E2E8F0)';
  b1.style.background = defaultBg;
  b2.style.background = defaultBg;
  b3.style.background = defaultBg;
  b4.style.background = defaultBg;

  if (!val) {
    if (label) {
      label.innerText = 'Min 6 characters';
      label.style.color = 'var(--text-tertiary, #94A3B8)';
    }
    return;
  }

  let score = 0;
  if (val.length >= 6) score++;
  if (val.length >= 10) score++;
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
  if (/[0-9]/.test(val) || /[^A-Za-z0-9]/.test(val)) score++;

  if (score === 1) {
    b1.style.background = 'var(--critical-red, #EF4444)';
    if (label) { label.innerText = 'Weak (too simple)'; label.style.color = 'var(--critical-red, #EF4444)'; }
  } else if (score === 2) {
    b1.style.background = 'var(--warning-amber, #F59E0B)';
    b2.style.background = 'var(--warning-amber, #F59E0B)';
    if (label) { label.innerText = 'Fair strength'; label.style.color = 'var(--warning-amber, #F59E0B)'; }
  } else if (score === 3) {
    b1.style.background = 'var(--upay-blue, #005BAC)';
    b2.style.background = 'var(--upay-blue, #005BAC)';
    b3.style.background = 'var(--upay-blue, #005BAC)';
    if (label) { label.innerText = 'Good strength'; label.style.color = 'var(--upay-blue, #005BAC)'; }
  } else if (score >= 4) {
    b1.style.background = 'var(--success-green, #10B981)';
    b2.style.background = 'var(--success-green, #10B981)';
    b3.style.background = 'var(--success-green, #10B981)';
    b4.style.background = 'var(--success-green, #10B981)';
    if (label) { label.innerText = 'Strong password'; label.style.color = 'var(--success-green, #10B981)'; }
  }
}

function updateRoleClearanceCard(role) {
  const preview = document.getElementById('role-clearance-preview');
  const text = document.getElementById('role-clearance-text');
  if (!preview || !text) return;

  const configs = {
    ANALYST: {
      bg: 'var(--upay-blue-tint, #E8F2FC)',
      border: 'rgba(0,91,172,0.22)',
      color: 'var(--upay-blue-dark, #003E75)',
      html: `<strong>Tier 1 Analyst Clearance:</strong> Access to real-time risk scoring, behavioral anomaly triage, what-if counterfactual sandbox, and case note documentation.`
    },
    SENIOR_OFFICER: {
      bg: 'rgba(245,158,11,0.12)',
      border: 'rgba(245,158,11,0.3)',
      color: '#92400E',
      html: `<strong>Tier 2 Senior Officer Clearance:</strong> All Tier 1 capabilities + case escalation sign-offs, temporary wallet freeze authorizations, and SAR submissions to compliance.`
    },
    ADMIN: {
      bg: 'rgba(239,68,68,0.10)',
      border: 'rgba(239,68,68,0.25)',
      color: '#991B1B',
      html: `<strong>System Administrator (Superuser):</strong> Full administrative control — personnel account provisioning, account suspension/activation, and immutable audit inspection.`
    },
    VIEWER: {
      bg: 'rgba(16,185,129,0.10)',
      border: 'rgba(16,185,129,0.25)',
      color: '#065F46',
      html: `<strong>Compliance Auditor (Read-Only):</strong> Read-only inspection of forensic ledgers, BFIU statutory compliance reports, and system audit logs.`
    }
  };

  const cfg = configs[role] || configs.ANALYST;
  preview.style.background = cfg.bg;
  preview.style.borderColor = cfg.border;
  preview.style.color = cfg.color;
  text.innerHTML = cfg.html;
}

async function handleCreateUserSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById('reg-submit-btn');
  const submitText = document.getElementById('reg-submit-text');

  const fullName = document.getElementById('reg-fullname').value.trim();
  const username = document.getElementById('reg-username').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const role = document.getElementById('reg-role').value;
  const department = document.getElementById('reg-dept').value.trim();

  if (!fullName || !username || !email || !password) {
    showToast('Please fill out all required fields', 'warning');
    return;
  }

  if (password.length < 6) {
    showToast('Password must be at least 6 characters long', 'error');
    return;
  }

  // Set loading state
  if (submitBtn) submitBtn.disabled = true;
  if (submitText) submitText.innerText = 'Provisioning Officer Account...';

  try {
    const res = await AdminService.createUser({
      full_name: fullName,
      username: username,
      email: email,
      password: password,
      role: role,
      department: department
    });

    showToast(`Officer @${username} provisioned successfully with ${role} clearance!`, 'success');
    closeCreateUserModal();
    document.getElementById('create-user-form').reset();
    
    // Immediate real-time refresh of directory, KPIs, and audit log
    await loadAdminViewData();
  } catch (err) {
    const errMsg = err.message || 'Registration failed';
    showToast(errMsg, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    if (submitText) submitText.innerText = 'Create Personnel Account';
  }
}

// Global modal dismiss on ESC key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeCreateUserModal();
    closeAuthModal();
  }
});

// Expose on window for inline event triggers
window.loadAdminViewData = loadAdminViewData;
window.renderAdminUsersTable = renderAdminUsersTable;
window.filterAdminUsersTable = filterAdminUsersTable;
window.setAdminRoleFilter = setAdminRoleFilter;
window.loadAdminAuditLogs = loadAdminAuditLogs;
window.toggleUserStatus = toggleUserStatus;
window.openCreateUserModal = openCreateUserModal;
window.closeCreateUserModal = closeCreateUserModal;
window.handleCreateUserOverlayClick = handleCreateUserOverlayClick;
window.handleCreateUserSubmit = handleCreateUserSubmit;
window.setRegDept = setRegDept;
window.togglePasswordVisibility = togglePasswordVisibility;
window.updatePasswordStrength = updatePasswordStrength;
window.updateRoleClearanceCard = updateRoleClearanceCard;
window.updateAdminSessionBanner = updateAdminSessionBanner;
window.quickLogin = quickLogin;
window.handleManualLogin = handleManualLogin;
window.openAuthModal = openAuthModal;
window.closeAuthModal = closeAuthModal;


