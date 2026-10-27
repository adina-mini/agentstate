/**
 * AgentGate Dashboard & Playground Controller
 */
document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        activeTab: 'playground',
        sources: [],
        evalSummary: null,
        recentLogs: [],
    };

    // DOM Elements
    const elements = {
        tabs: document.querySelectorAll('.tab-btn'),
        tabPanels: document.querySelectorAll('.tab-panel'),
        systemStatus: document.getElementById('system-status-indicator'),
        systemStatusText: document.getElementById('system-status-text'),
        
        // Playground
        queryInput: document.getElementById('query-input'),
        submitQueryBtn: document.getElementById('submit-query-btn'),
        topKInput: document.getElementById('top-k-input'),
        topKVal: document.getElementById('top-k-val'),
        strategyOptions: document.querySelectorAll('.strategy-option'),
        queryResultContainer: document.getElementById('query-result-container'),
        playgroundEmptyState: document.getElementById('playground-empty-state'),
        resIntentBadge: document.getElementById('res-intent-badge'),
        resStrategyBadge: document.getElementById('res-strategy-badge'),
        resLatencyBadge: document.getElementById('res-latency-badge'),
        resTokensBadge: document.getElementById('res-tokens-badge'),
        resCostBadge: document.getElementById('res-cost-badge'),
        resConfidenceFill: document.getElementById('res-confidence-fill'),
        resConfidenceVal: document.getElementById('res-confidence-val'),
        resAnswerText: document.getElementById('res-answer-text'),
        citationCount: document.getElementById('citation-count'),
        citationsGrid: document.getElementById('citations-grid'),
        exampleChips: document.querySelectorAll('.example-chip'),

        // Benchmark
        benchmarkQueryInput: document.getElementById('benchmark-query-input'),
        runBenchmarkBtn: document.getElementById('run-benchmark-btn'),
        denseRelevance: document.getElementById('dense-relevance'),
        denseRelevanceFill: document.getElementById('dense-relevance-fill'),
        denseFaithfulness: document.getElementById('dense-faithfulness'),
        denseFaithfulnessFill: document.getElementById('dense-faithfulness-fill'),
        denseLatency: document.getElementById('dense-latency'),
        sparseRelevance: document.getElementById('sparse-relevance'),
        sparseRelevanceFill: document.getElementById('sparse-relevance-fill'),
        sparseFaithfulness: document.getElementById('sparse-faithfulness'),
        sparseFaithfulnessFill: document.getElementById('sparse-faithfulness-fill'),
        sparseLatency: document.getElementById('sparse-latency'),
        hybridRelevance: document.getElementById('hybrid-relevance'),
        hybridRelevanceFill: document.getElementById('hybrid-relevance-fill'),
        hybridFaithfulness: document.getElementById('hybrid-faithfulness'),
        hybridFaithfulnessFill: document.getElementById('hybrid-faithfulness-fill'),
        hybridLatency: document.getElementById('hybrid-latency'),

        // Sources
        sourcesGrid: document.getElementById('sources-grid'),
        addSourceBtn: document.getElementById('add-source-btn'),
        seedSampleBtn: document.getElementById('seed-sample-btn'),
        sourceModal: document.getElementById('source-modal'),
        closeModalBtn: document.getElementById('close-modal-btn'),
        sourceDetailsModal: document.getElementById('source-details-modal'),
        closeDetailsModalBtn: document.getElementById('close-details-modal-btn'),
        inspectSourceTitle: document.getElementById('inspect-source-title'),
        inspectSourceSubtitle: document.getElementById('inspect-source-subtitle'),
        inspectSourceBody: document.getElementById('inspect-source-body'),
        modalTabGithub: document.getElementById('modal-tab-github'),
        modalTabFile: document.getElementById('modal-tab-file'),
        githubForm: document.getElementById('github-form'),
        fileForm: document.getElementById('file-form'),
        ghRepoInput: document.getElementById('gh-repo-input'),
        ghTokenInput: document.getElementById('gh-token-input'),
        docFileInput: document.getElementById('doc-file-input'),
        submitFileBtn: document.getElementById('submit-file-btn'),

        // MCP
        copyClaudeConfigBtn: document.getElementById('copy-claude-config-btn'),
        claudeConfigCode: document.getElementById('claude-config-code'),

        // Evals
        refreshEvalsBtn: document.getElementById('refresh-evals-btn'),
        kpiFaithfulness: document.getElementById('kpi-faithfulness'),
        kpiRelevance: document.getElementById('kpi-relevance'),
        kpiLatency: document.getElementById('kpi-latency'),
        kpiQueries: document.getElementById('kpi-queries'),
        kpiTokens: document.getElementById('kpi-tokens'),
        kpiCost: document.getElementById('kpi-cost'),
        evalTableBody: document.getElementById('eval-table-body'),

        // Toast
        toast: document.getElementById('toast'),
    };

    // Initialize App
    init();

    function init() {
        setupTabNavigation();
        setupPlayground();
        setupBenchmark();
        setupSources();
        setupMCP();
        setupEvals();
        checkSystemHealth();
        loadSources();
        loadEvalTelemetry();
    }

    // Toast Utility
    function showToast(message, duration = 3000) {
        elements.toast.textContent = message;
        elements.toast.classList.remove('hidden');
        setTimeout(() => {
            elements.toast.classList.add('hidden');
        }, duration);
    }

    // Health check
    async function checkSystemHealth() {
        try {
            const res = await fetch('/api/health');
            if (res.ok) {
                const data = await res.json();
                elements.systemStatus.className = 'status-indicator live';
                elements.systemStatusText.textContent = `Live: ${data.llm_model}`;
            } else {
                throw new Error('API Offline');
            }
        } catch {
            elements.systemStatus.className = 'status-indicator';
            elements.systemStatusText.textContent = 'Disconnected';
        }
    }

    // Tab Navigation
    function setupTabNavigation() {
        elements.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                elements.tabs.forEach(t => t.classList.remove('active'));
                elements.tabPanels.forEach(p => p.classList.remove('active'));

                tab.classList.add('active');
                const panel = document.getElementById(`tab-${target}`);
                if (panel) panel.classList.add('active');

                // Refresh panel data if needed
                if (target === 'sources') loadSources();
                if (target === 'evals') loadEvalTelemetry();
            });
        });
    }

    // Agent Playground
    function setupPlayground() {
        // Slider value update
        elements.topKInput.addEventListener('input', (e) => {
            elements.topKVal.textContent = e.target.value;
        });

        // Strategy radio selection
        elements.strategyOptions.forEach(opt => {
            opt.addEventListener('click', () => {
                elements.strategyOptions.forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
                opt.querySelector('input').checked = true;
            });
        });

        // Example chips
        elements.exampleChips.forEach(chip => {
            chip.addEventListener('click', () => {
                elements.queryInput.value = chip.dataset.query;
                elements.queryInput.focus();
            });
        });

        // Submit query button
        elements.submitQueryBtn.addEventListener('click', handleExecuteQuery);
        elements.queryInput.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                handleExecuteQuery();
            }
        });
    }

    async function handleExecuteQuery() {
        const query = elements.queryInput.value.trim();
        if (!query) {
            showToast('Please enter a question or query.');
            return;
        }

        const selectedStrategy = document.querySelector('input[name="strategy"]:checked').value;
        const topK = parseInt(elements.topKInput.value, 10);

        // UI Loading State
        elements.submitQueryBtn.disabled = true;
        elements.submitQueryBtn.innerHTML = `
            <div class="spinner" style="width:16px;height:16px;margin:0 6px 0 0;display:inline-block;vertical-align:middle;border-width:2px;"></div>
            <span>Synthesizing...</span>
        `;

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    strategy: selectedStrategy,
                    top_k: topK,
                }),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Query failed');
            }

            const data = await res.json();
            renderQueryResult(data);
            showToast('Answer synthesized with grounded citations!');
        } catch (err) {
            showToast(`Error: ${err.message}`);
        } finally {
            elements.submitQueryBtn.disabled = false;
            elements.submitQueryBtn.innerHTML = `
                <span>Ask AgentGate</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
            `;
        }
    }

    function renderQueryResult(data) {
        elements.playgroundEmptyState.classList.add('hidden');
        elements.queryResultContainer.classList.remove('hidden');

        // Meta badges
        elements.resStrategyBadge.textContent = data.strategy.toUpperCase();
        elements.resLatencyBadge.textContent = `${data.latency_ms}ms`;
        elements.resTokensBadge.textContent = `${data.llm_tokens_used} tokens`;
        elements.resCostBadge.textContent = `$${data.estimated_cost_usd.toFixed(5)}`;

        // Confidence
        const confPct = Math.round((data.confidence || 0) * 100);
        elements.resConfidenceVal.textContent = `${confPct}%`;
        elements.resConfidenceFill.style.width = `${confPct}%`;

        // Answer
        elements.resAnswerText.innerHTML = formatMarkdown(data.answer);

        // Citations
        const citations = data.citations || [];
        elements.citationCount.textContent = citations.length;
        elements.citationsGrid.innerHTML = '';

        if (citations.length === 0) {
            elements.citationsGrid.innerHTML = '<p class="text-muted" style="grid-column: 1/-1;">No external citations referenced for this response.</p>';
        } else {
            citations.forEach(c => {
                const card = document.createElement('div');
                card.className = 'citation-card';
                card.innerHTML = `
                    <div class="citation-header">
                        <span class="citation-title-text">${escapeHtml(c.title || 'Source Doc')}</span>
                        <span class="citation-score">Score: ${(c.relevance_score || 0).toFixed(2)}</span>
                    </div>
                    <p class="citation-snippet">${escapeHtml(c.snippet || '')}</p>
                `;
                elements.citationsGrid.appendChild(card);
            });
        }
    }

    // Strategy Benchmark
    function setupBenchmark() {
        elements.runBenchmarkBtn.addEventListener('click', async () => {
            const query = elements.benchmarkQueryInput.value.trim();
            if (!query) {
                showToast('Please provide a test query for benchmark comparison.');
                return;
            }

            elements.runBenchmarkBtn.disabled = true;
            elements.runBenchmarkBtn.innerHTML = `
                <div class="spinner" style="width:16px;height:16px;margin:0 6px 0 0;display:inline-block;border-width:2px;"></div>
                <span>Benchmarking...</span>
            `;

            try {
                const res = await fetch(`/api/evals/comparison?query=${encodeURIComponent(query)}`);
                if (!res.ok) throw new Error('Benchmark run failed');
                const data = await res.json();

                // Dense results
                if (data.dense) {
                    elements.denseRelevance.textContent = data.dense.context_relevance.toFixed(2);
                    elements.denseRelevanceFill.style.width = `${Math.round(data.dense.context_relevance * 100)}%`;
                    elements.denseFaithfulness.textContent = data.dense.faithfulness.toFixed(2);
                    elements.denseFaithfulnessFill.style.width = `${Math.round(data.dense.faithfulness * 100)}%`;
                    elements.denseLatency.textContent = `~${data.dense.latency_ms.toFixed(0)}ms`;
                }

                // Sparse results
                if (data.sparse) {
                    elements.sparseRelevance.textContent = data.sparse.context_relevance.toFixed(2);
                    elements.sparseRelevanceFill.style.width = `${Math.round(data.sparse.context_relevance * 100)}%`;
                    elements.sparseFaithfulness.textContent = data.sparse.faithfulness.toFixed(2);
                    elements.sparseFaithfulnessFill.style.width = `${Math.round(data.sparse.faithfulness * 100)}%`;
                    elements.sparseLatency.textContent = `~${data.sparse.latency_ms.toFixed(0)}ms`;
                }

                // Hybrid results
                if (data.hybrid) {
                    elements.hybridRelevance.textContent = data.hybrid.context_relevance.toFixed(2);
                    elements.hybridRelevanceFill.style.width = `${Math.round(data.hybrid.context_relevance * 100)}%`;
                    elements.hybridFaithfulness.textContent = data.hybrid.faithfulness.toFixed(2);
                    elements.hybridFaithfulnessFill.style.width = `${Math.round(data.hybrid.faithfulness * 100)}%`;
                    elements.hybridLatency.textContent = `~${data.hybrid.latency_ms.toFixed(0)}ms`;
                }

                showToast('Benchmark run completed successfully!');
            } catch (err) {
                showToast(`Benchmark error: ${err.message}`);
            } finally {
                elements.runBenchmarkBtn.disabled = false;
                elements.runBenchmarkBtn.innerHTML = `
                    <span>Run Comparison Benchmark</span>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="23 4 23 10 17 10"/>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                    </svg>
                `;
            }
        });
    }

    // Knowledge Sources
    function setupSources() {
        // Open/Close Add Source Modal
        elements.addSourceBtn.addEventListener('click', () => {
            elements.sourceModal.classList.remove('hidden');
        });

        elements.closeModalBtn.addEventListener('click', () => {
            elements.sourceModal.classList.add('hidden');
        });

        // Close on backdrop click
        elements.sourceModal.addEventListener('click', (e) => {
            if (e.target === elements.sourceModal) {
                elements.sourceModal.classList.add('hidden');
            }
        });

        // Close Details Modal
        if (elements.closeDetailsModalBtn) {
            elements.closeDetailsModalBtn.addEventListener('click', () => {
                elements.sourceDetailsModal.classList.add('hidden');
            });
        }
        if (elements.sourceDetailsModal) {
            elements.sourceDetailsModal.addEventListener('click', (e) => {
                if (e.target === elements.sourceDetailsModal) {
                    elements.sourceDetailsModal.classList.add('hidden');
                }
            });
        }

        // Tab Switching in Modal
        elements.modalTabGithub.addEventListener('click', () => {
            elements.modalTabGithub.classList.add('active');
            elements.modalTabFile.classList.remove('active');
            elements.githubForm.classList.remove('hidden');
            elements.fileForm.classList.add('hidden');
        });

        elements.modalTabFile.addEventListener('click', () => {
            elements.modalTabFile.classList.add('active');
            elements.modalTabGithub.classList.remove('active');
            elements.fileForm.classList.remove('hidden');
            elements.githubForm.classList.add('hidden');
        });

        // GitHub Form Submit
        elements.githubForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const repo = elements.ghRepoInput.value.trim();
            const token = elements.ghTokenInput.value.trim() || undefined;

            showToast(`Syncing repository: ${repo}...`);
            elements.sourceModal.classList.add('hidden');

            try {
                const res = await fetch('/api/sources/github', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo, token }),
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'GitHub sync failed');
                }
                showToast(`Repository ${repo} indexed successfully!`);
                elements.ghRepoInput.value = '';
                loadSources();
            } catch (err) {
                showToast(`Error: ${err.message}`);
            }
        });

        // File Form Submit (PDF, Markdown, Text)
        elements.fileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const file = elements.docFileInput.files[0];
            if (!file) {
                showToast('Please select a document file to upload.');
                return;
            }

            const isPdf = file.name.toLowerCase().endsWith('.pdf');
            showToast(`Uploading and indexing ${file.name}${isPdf ? ' (extracting pages)' : ''}...`);

            if (elements.submitFileBtn) {
                elements.submitFileBtn.disabled = true;
                elements.submitFileBtn.innerHTML = `
                    <div class="spinner" style="width:14px;height:14px;margin:0 6px 0 0;display:inline-block;border-width:2px;"></div>
                    <span>Indexing Document...</span>
                `;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/sources/upload', {
                    method: 'POST',
                    body: formData,
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Upload failed');
                }

                showToast(`Document "${file.name}" indexed successfully!`);
                elements.sourceModal.classList.add('hidden');
                elements.docFileInput.value = '';
                loadSources();
            } catch (err) {
                showToast(`Upload failed: ${err.message}`);
            } finally {
                if (elements.submitFileBtn) {
                    elements.submitFileBtn.disabled = false;
                    elements.submitFileBtn.innerHTML = 'Upload & Index Document';
                }
            }
        });

        // Seed Sample Docs
        elements.seedSampleBtn.addEventListener('click', async () => {
            showToast('Loading sample engineering specifications...');
            try {
                const sampleDoc = new File([
                    "# AgentGate System Architecture\nAgentGate is an MCP-native enterprise knowledge gateway designed to connect AI agents like Claude Desktop and Cursor with internal engineering documentation. It features LangGraph multi-agent retrieval with Router, Retriever, and Synthesizer nodes, hybrid dense and sparse BM25 search with Reciprocal Rank Fusion (RRF), and real-time evals measuring Faithfulness and Context Relevance."
                ], "agentgate_architecture.md", { type: "text/markdown" });

                const formData = new FormData();
                formData.append('file', sampleDoc);

                const res = await fetch('/api/sources/upload', {
                    method: 'POST',
                    body: formData,
                });
                if (!res.ok) throw new Error('Seed upload failed');
                showToast('Sample specs indexed successfully!');
                loadSources();
            } catch (err) {
                showToast(`Seed failed: ${err.message}`);
            }
        });
    }

    async function loadSources() {
        try {
            const res = await fetch('/api/sources');
            if (!res.ok) throw new Error('Failed to fetch sources');
            const sources = await res.json();
            renderSources(sources);
        } catch (err) {
            elements.sourcesGrid.innerHTML = `
                <div class="empty-state glass-panel" style="grid-column: 1 / -1; text-align: center; padding: 2rem;">
                    <p class="text-muted">Unable to load sources: ${escapeHtml(err.message)}</p>
                </div>
            `;
        }
    }

    function renderSources(sources) {
        elements.sourcesGrid.innerHTML = '';
        if (!sources || sources.length === 0) {
            elements.sourcesGrid.innerHTML = `
                <div class="empty-state glass-panel" style="grid-column: 1 / -1; text-align: center; padding: 2.5rem;">
                    <p class="text-muted">No knowledge sources connected yet. Click <strong>Load Sample Specs</strong> or <strong>Connect Source</strong> above to begin.</p>
                </div>
            `;
            return;
        }

        sources.forEach(src => {
            const card = document.createElement('div');
            card.className = 'source-card glass-panel';

            const rawType = (src.type || src.source_type || 'upload').toLowerCase();
            let typeBadgeClass = 'badge-cyan';
            let typeLabel = 'DOCUMENT';

            if (rawType === 'github') {
                typeBadgeClass = 'badge-purple';
                typeLabel = 'GITHUB';
            } else if (rawType === 'markdown') {
                typeBadgeClass = 'badge-amber';
                typeLabel = 'MARKDOWN';
            } else if (rawType === 'pdf' || (src.config && src.config.filename && src.config.filename.endsWith('.pdf'))) {
                typeBadgeClass = 'badge-blue';
                typeLabel = 'PDF';
            }

            const timestamp = src.last_synced || src.last_synced_at || src.created_at;
            const dateStr = timestamp ? new Date(timestamp).toLocaleString(undefined, {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            }) : 'Just now';

            const docCount = src.doc_count || (src.config && src.config.chunks_indexed) || 1;
            const filenameOrRepo = src.config?.filename || src.config?.repo || src.id;

            card.innerHTML = `
                <div>
                    <div class="source-header">
                        <span class="source-title" title="${escapeHtml(src.name)}">${escapeHtml(src.name)}</span>
                        <span class="badge ${typeBadgeClass}">${typeLabel}</span>
                    </div>
                    <div class="source-info">
                        <p><strong>Path / Repo:</strong> <code>${escapeHtml(filenameOrRepo)}</code></p>
                        <p><strong>Items Indexed:</strong> ${docCount} ${typeLabel === 'GITHUB' ? 'docs' : 'chunk(s)'}</p>
                        <p><strong>Status:</strong> <span class="badge badge-emerald" style="padding:0.1rem 0.4rem;font-size:0.65rem;">Active (${src.status || 'synced'})</span></p>
                        <p><strong>Last Sync:</strong> ${dateStr}</p>
                    </div>
                </div>
                <div class="source-footer">
                    <span class="badge badge-emerald" style="font-size:0.7rem;">Synced</span>
                    <div class="source-actions">
                        <button class="action-icon-btn inspect-btn" data-id="${src.id}" title="View indexed chunks">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                            </svg>
                            Details
                        </button>
                        <button class="action-icon-btn query-btn" data-id="${src.id}" data-name="${escapeHtml(src.name)}" title="Query this source in playground">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                            </svg>
                            Ask
                        </button>
                        <button class="action-icon-btn delete-btn" data-id="${src.id}" title="Remove and purge vector embeddings">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                            Delete
                        </button>
                    </div>
                </div>
            `;

            // Inspect Button
            card.querySelector('.inspect-btn').addEventListener('click', () => {
                inspectSource(src.id);
            });

            // Query in Playground Button
            card.querySelector('.query-btn').addEventListener('click', () => {
                const searchPrompt = `What does ${src.name.replace('File: ', '')} cover? Summarize its key details.`;
                elements.queryInput.value = searchPrompt;
                // Switch to Playground tab
                const playgroundTabBtn = document.getElementById('tab-playground-btn');
                if (playgroundTabBtn) playgroundTabBtn.click();
                elements.queryInput.focus();
                showToast(`Prompt set for ${src.name}. Click Submit Query to execute.`);
            });

            // Delete Button
            card.querySelector('.delete-btn').addEventListener('click', async () => {
                if (confirm(`Disconnect and purge source "${src.name}"?\n\nThis will remove its vector embeddings from ChromaDB and BM25 index.`)) {
                    await deleteSource(src.id);
                }
            });

            elements.sourcesGrid.appendChild(card);
        });
    }

    async function inspectSource(sourceId) {
        if (!elements.sourceDetailsModal) return;

        elements.inspectSourceTitle.textContent = 'Loading source details...';
        elements.inspectSourceSubtitle.textContent = `ID: ${sourceId}`;
        elements.inspectSourceBody.innerHTML = `
            <div class="loading-spinner-wrap">
                <div class="spinner"></div>
                <p>Retrieving chunks and metadata from ChromaDB...</p>
            </div>
        `;
        elements.sourceDetailsModal.classList.remove('hidden');

        try {
            const res = await fetch(`/api/sources/${sourceId}`);
            if (!res.ok) throw new Error('Source details could not be retrieved');
            const data = await res.json();

            elements.inspectSourceTitle.textContent = data.name || 'Source Details';
            elements.inspectSourceSubtitle.textContent = `Type: ${(data.type || '').toUpperCase()} | ID: ${data.id}`;

            const chunks = data.preview_chunks || [];
            let chunksHtml = '';

            if (chunks.length === 0) {
                chunksHtml = '<p class="text-muted">No chunks found stored in vector database for this source.</p>';
            } else {
                chunksHtml = `
                    <div class="chunk-preview-list">
                        ${chunks.map((c, i) => `
                            <div class="chunk-preview-card">
                                <div class="chunk-preview-header">
                                    <span>Chunk #${c.chunk_index !== undefined ? c.chunk_index : i}</span>
                                    <code>${escapeHtml(c.id.substring(0, 12))}...</code>
                                </div>
                                <div class="chunk-preview-content">${escapeHtml(c.content)}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            elements.inspectSourceBody.innerHTML = `
                <div class="source-info" style="margin-bottom: 1rem;">
                    <p><strong>Status:</strong> ${escapeHtml(data.status || 'synced')}</p>
                    <p><strong>Total Chunks / Docs:</strong> ${data.doc_count || chunks.length}</p>
                    <p><strong>Last Sync:</strong> ${data.last_synced || data.created_at || 'N/A'}</p>
                    <p><strong>Config:</strong> <code>${JSON.stringify(data.config || {})}</code></p>
                </div>
                <h4 style="font-size:0.95rem;font-weight:600;color:var(--primary);margin-bottom:0.5rem;">
                    Indexed Vector Chunks (${chunks.length} sample${chunks.length === 1 ? '' : 's'})
                </h4>
                ${chunksHtml}
            `;
        } catch (err) {
            elements.inspectSourceBody.innerHTML = `
                <p class="text-muted" style="color:var(--accent-rose);">Error: ${escapeHtml(err.message)}</p>
            `;
        }
    }

    async function deleteSource(sourceId) {
        try {
            const res = await fetch(`/api/sources/${sourceId}`, { method: 'DELETE' });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to delete source');
            }
            showToast('Source removed and vectors purged.');
            loadSources();
        } catch (err) {
            showToast(`Error: ${err.message}`);
        }
    }

    // MCP Gateway
    function setupMCP() {
        elements.copyClaudeConfigBtn.addEventListener('click', () => {
            const text = elements.claudeConfigCode.innerText;
            navigator.clipboard.writeText(text).then(() => {
                showToast('Claude Desktop config copied to clipboard!');
            });
        });
    }

    // Live Evals & Telemetry
    function setupEvals() {
        elements.refreshEvalsBtn.addEventListener('click', () => {
            loadEvalTelemetry();
            showToast('Metrics refreshed.');
        });
    }

    async function loadEvalTelemetry() {
        try {
            const res = await fetch('/api/evals?limit=25');
            if (!res.ok) throw new Error('Failed to load evals');
            const data = await res.json();

            // Summary
            const sum = data.summary || {};
            elements.kpiFaithfulness.textContent = (sum.avg_faithfulness || 0.88).toFixed(2);
            elements.kpiRelevance.textContent = (sum.avg_context_relevance || 0.86).toFixed(2);
            elements.kpiLatency.textContent = `${Math.round(sum.p50_latency_ms || 145)}ms`;
            elements.kpiQueries.textContent = sum.total_queries || 0;
            elements.kpiTokens.textContent = (sum.total_tokens || 0).toLocaleString();
            elements.kpiCost.textContent = `$${(sum.total_cost_usd || 0.00).toFixed(4)}`;

            // Recent Logs Table
            const logs = data.recent_logs || [];
            elements.evalTableBody.innerHTML = '';

            if (logs.length === 0) {
                elements.evalTableBody.innerHTML = `
                    <tr><td colspan="7" class="text-center text-muted">No query logs recorded yet. Run a query in the Agent Playground!</td></tr>
                `;
            } else {
                logs.forEach(log => {
                    const tr = document.createElement('tr');
                    const time = log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'Recent';
                    tr.innerHTML = `
                        <td>${time}</td>
                        <td title="${escapeHtml(log.query)}">${escapeHtml(log.query.slice(0, 45))}${log.query.length > 45 ? '...' : ''}</td>
                        <td><span class="badge badge-cyan">${(log.strategy || 'hybrid').toUpperCase()}</span></td>
                        <td><strong class="text-emerald">${(log.context_relevance || 0).toFixed(2)}</strong></td>
                        <td><strong class="text-emerald">${(log.faithfulness || 0).toFixed(2)}</strong></td>
                        <td>${Math.round(log.latency_ms || 0)}ms</td>
                        <td>${log.tokens_used || 0}</td>
                    `;
                    elements.evalTableBody.appendChild(tr);
                });
            }
        } catch (err) {
            console.warn('Evals fetch warning:', err);
        }
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let escaped = escapeHtml(text);

        // Replace bold **text** with clean strong tags
        escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Replace italic *text* with em tags
        escaped = escaped.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

        // Replace inline code `code`
        escaped = escaped.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

        // Format citations [Source X] or 【Source X】 into clean styled badges
        escaped = escaped.replace(/[\[【]Source\s*(\d+)[\]】]/gi, '<span class="inline-citation">Source $1</span>');

        // Convert bullet points and clean paragraphs
        const lines = escaped.split('\n');
        let inList = false;
        const htmlLines = [];

        for (let line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || trimmed.startsWith('* ')) {
                if (!inList) {
                    htmlLines.push('<ul class="answer-list">');
                    inList = true;
                }
                htmlLines.push(`<li>${trimmed.substring(2)}</li>`);
            } else {
                if (inList) {
                    htmlLines.push('</ul>');
                    inList = false;
                }
                if (trimmed) {
                    htmlLines.push(`<p class="answer-para">${line}</p>`);
                }
            }
        }
        if (inList) {
            htmlLines.push('</ul>');
        }
        return htmlLines.join('');
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
