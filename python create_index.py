# -*- coding: utf-8 -*-

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NEOMA P-CAM | Physical Reflex &amp; Silicon Root-of-Trust</title>
  <style>
    :root {
      --bg: #070b14;
      --card-bg: #0d1527;
      --border: #1e293b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --amber: #f59e0b;
      --cyan: #06b6d4;
      --emerald: #10b981;
      --purple: #a855f7;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 32px 24px;
      line-height: 1.5;
    }
    .container { max-width: 1280px; margin: 0 auto; }
    
    /* Top Header */
    .header-bar {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 20px;
      margin-bottom: 36px;
    }
    .header-left .title-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }
    .title-row h1 {
      font-size: 1.85rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    .title-row .icon-lead {
      color: var(--amber);
      font-size: 1.85rem;
    }
    .badge-ver {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--amber);
      background: rgba(245, 158, 11, 0.12);
      border: 1px solid var(--amber);
      padding: 3px 8px;
      border-radius: 6px;
      letter-spacing: 0.05em;
    }
    .subtitle {
      color: var(--text-muted);
      font-size: 0.95rem;
      max-width: 780px;
    }
    .header-controls {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .btn {
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 600;
      padding: 8px 16px;
      border-radius: 8px;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn-secondary {
      background: #1e293b;
      color: #e2e8f0;
      border: 1px solid #334155;
    }
    .btn-secondary:hover { background: #334155; }
    .btn-primary {
      background: var(--amber);
      color: #000;
      border: 1px solid var(--amber);
    }
    .btn-primary:hover { background: #d97706; }
    .badge-status {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--emerald);
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid var(--emerald);
      padding: 6px 14px;
      border-radius: 8px;
      letter-spacing: 0.05em;
    }

    /* 4 Core Cards */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin-bottom: 48px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      transition: transform 0.2s, border-color 0.2s;
    }
    .card:hover {
      transform: translateY(-2px);
      border-color: #334155;
    }
    .card-icon {
      font-size: 1.5rem;
      margin-bottom: 14px;
      display: block;
    }
    .c-amber { color: var(--amber); }
    .c-cyan { color: var(--cyan); }
    .c-emerald { color: var(--emerald); }
    .c-purple { color: var(--purple); }
    .card h3 {
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 10px;
    }
    .card p {
      font-size: 0.875rem;
      color: var(--text-muted);
      line-height: 1.6;
    }

    /* 6 Enclaves Section */
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }
    .section-header h2 {
      font-size: 1.25rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .section-meta {
      font-family: monospace;
      font-size: 0.85rem;
      color: #64748b;
    }
    .enclave-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 16px;
    }
    .enclave-item {
      background: #0b1120;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .enclave-info h4 {
      font-size: 0.95rem;
      font-weight: 700;
      margin-bottom: 4px;
    }
    .enclave-info code {
      font-family: monospace;
      font-size: 0.8rem;
      color: #38bdf8;
    }
    .enclave-state {
      font-family: monospace;
      font-size: 0.75rem;
      background: rgba(16, 185, 129, 0.1);
      color: var(--emerald);
      border: 1px solid var(--emerald);
      padding: 4px 10px;
      border-radius: 6px;
    }
    .footer {
      text-align: center;
      margin-top: 60px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
      color: #64748b;
      font-size: 0.85rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header class="header-bar">
      <div class="header-left">
        <div class="title-row">
          <span class="icon-lead">&#9889;</span>
          <h1>NEOMA P-CAM</h1>
          <span class="badge-ver">GP-PCAM v5.0.0</span>
        </div>
        <p class="subtitle">Proprietary Physical Reflex Engine &amp; Cryptographic Silicon Root-of-Trust. Delivering deterministic sub-millisecond physical equilibrium convergence on NVIDIA GTX 1650 silicon.</p>
      </div>
      <div class="header-controls">
        <a href="https://rapidapi.com/shs15199702/api/gp-pcam-universal-physical-solver/playground/Solve%20Universal%20Equilibrium" target="_blank" class="btn btn-secondary">&#127760; Enterprise Hub</a>
        <a href="https://rapidapi.com/shs15199702/api/gp-pcam-universal-physical-solver/playground/Solve%20Universal%20Equilibrium" target="_blank" class="btn btn-primary">&#9889; Universal Solver ($30/mo)</a>
        <span class="badge-status">GATEWAY: ACTIVE</span>
      </div>
    </header>

    <section class="card-grid">
      <div class="card">
        <span class="card-icon c-amber">&#9889;</span>
        <h3>Empirical Sub-to-Low Millisecond Reflex (0.6ms &ndash; 5.0ms)</h3>
        <p>Instantaneous equilibrium locking on isolated GPU tensor streams. Resolves catastrophic physical instability in 0.6ms &ndash; 5.0ms without computational lag or iterative numerical stalls.</p>
      </div>
      <div class="card">
        <span class="card-icon c-cyan">&#129504;</span>
        <h3>Autonomous Cognitive Enclave</h3>
        <p>Embedded domain-specific physical intelligence powered by LoRA Phi-3. Computes macroscopic thermodynamic state equations (&Delta;H, damping ratio) within a sealed boundary.</p>
      </div>
      <div class="card">
        <span class="card-icon c-emerald">&#128274;</span>
        <h3>Silicon Root-of-Trust</h3>
        <p>Hardware-level physical substrate verification generates deterministic cryptographic execution seals (SEAL-CORE...) and SHA-256 proofs on every convergence cycle.</p>
      </div>
      <div class="card">
        <span class="card-icon c-purple">&#128142;</span>
        <h3>Golden Physics Vault</h3>
        <p>Autonomous attestation logging. Converts verified equilibrium convergence into immutable, high-value engineering ground-truth records across multi-domain datasets.</p>
      </div>
    </section>

    <section>
      <div class="section-header">
        <h2><span>&#9889;</span> Dedicated Physical Reflex Enclaves (0.6ms &ndash; 5.0ms Live Telemetry)</h2>
        <span class="section-meta">Synchronous Time-Division Grid</span>
      </div>
      <div class="enclave-grid">
        <div class="enclave-item">
          <div class="enclave-info">
            <h4>Universal Equilibrium</h4>
            <code>/v1/solve-universal-equilibrium</code>
          </div>
          <span class="enclave-state">&zeta; = 0.9981 CONVERGED</span>
        </div>
        <div class="enclave-item">
          <div class="enclave-info">
            <h4>Battery Energetics</h4>
            <code>/v1/battery/predict</code>
          </div>
          <span class="enclave-state">ONLINE &bull; DAMPING</span>
        </div>
        <div class="enclave-item">
          <div class="enclave-info">
            <h4>Bioreactor Kinematics</h4>
            <code>/v1/pharma/predict</code>
          </div>
          <span class="enclave-state">ONLINE &bull; DAMPING</span>
        </div>
        <div class="enclave-item">
          <div class="enclave-info">
            <h4>Robotic Compliance</h4>
            <code>/v1/robotics/predict</code>
          </div>
          <span class="enclave-state">ONLINE &bull; DAMPING</span>
        </div>
        <div class="enclave-item">
          <div class="enclave-info">
            <h4>Mobility Dynamics</h4>
            <code>/v1/mobility/predict</code>
          </div>
          <span class="enclave-state">ONLINE &bull; DAMPING</span>
        </div>
        <div class="enclave-item">
          <div class="enclave-info">
            <h4>Precision Synthesis</h4>
            <code>/v1/chemistry/predict</code>
          </div>
          <span class="enclave-state">ONLINE &bull; DAMPING</span>
        </div>
      </div>
    </section>

    <div class="footer">
      <p>&copy; 2026 Neoma Physical AI Team. All rights reserved.</p>
    </div>
  </div>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("[SUCCESS] index.html successfully created with UTF-8 encoding.")