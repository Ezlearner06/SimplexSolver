// static/app.js - Simplex Solver Frontend UI Logic

const app = {
    state: {
        goal: 'maximize',
        variables: ['x1', 'x2'],
        constraints: [
            { id: 1, coeffs: [1, 2], sign: '<=', rhs: 10 },
            { id: 2, coeffs: [3, 1], sign: '<=', rhs: 15 }
        ],
        objCoeffs: [3, 5],
        currentProblemCache: null, // used for PDF generation
        result: null,
        currentTableauIdx: 0,
    },

    // --- View Routing ---
    showView(viewId) {
        document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
        document.getElementById(`view-${viewId}`).classList.add('active');
        
        document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
        const nav = document.getElementById(`nav-${viewId}`);
        if(nav) nav.classList.add('active');

        // Show/hide sidebar links based on if result exists
        if(this.state.result) {
            document.getElementById('sidebar-results').classList.remove('hidden');
            document.getElementById('sidebar-steps').classList.remove('hidden');
        }
    },

    // --- Problem Entry Forms ---
    setGoal(goal) {
        this.state.goal = goal;
        document.getElementById('btn-goal-max').className = goal === 'maximize' 
            ? "px-4 py-1 text-xs font-bold rounded-full bg-primary text-on-primary" 
            : "px-4 py-1 text-xs font-bold rounded-full text-on-surface-variant hover:text-on-surface cursor-pointer";
        document.getElementById('btn-goal-min').className = goal === 'minimize' 
            ? "px-4 py-1 text-xs font-bold rounded-full bg-primary text-on-primary" 
            : "px-4 py-1 text-xs font-bold rounded-full text-on-surface-variant hover:text-on-surface cursor-pointer";
        this.renderPreview();
    },

    addVariable() {
        const i = this.state.variables.length + 1;
        this.state.variables.push(`x${i}`);
        this.state.objCoeffs.push(0);
        this.state.constraints.forEach(c => c.coeffs.push(0));
        this.renderForms();
    },

    removeVariable() {
        if (this.state.variables.length <= 1) return;
        this.state.variables.pop();
        this.state.objCoeffs.pop();
        this.state.constraints.forEach(c => c.coeffs.pop());
        this.renderForms();
    },

    addConstraint() {
        const id = this.state.constraints.length ? Math.max(...this.state.constraints.map(c=>c.id))+1 : 1;
        this.state.constraints.push({
            id: id,
            coeffs: Array(this.state.variables.length).fill(0),
            sign: '<=',
            rhs: 0
        });
        this.renderForms();
    },

    removeConstraint(index) {
        this.state.constraints.splice(index, 1);
        this.renderForms();
    },

    renderForms() {
        const objDiv = document.getElementById('form-objective');
        const consDiv = document.getElementById('form-constraints');

        // Render Objective
        let objHtml = `<span class="text-secondary text-2xl font-bold mr-2">Z =</span>`;
        this.state.variables.forEach((v, i) => {
            const prefix = i > 0 ? `<span class="text-outline mx-2">+</span>` : ``;
            objHtml += `${prefix}<div class="flex items-center gap-2">
                <input class="w-16 bg-surface-container-high border-none focus:ring-1 focus:ring-secondary rounded-lg text-center font-bold text-primary" 
                    type="number" step="any" value="${this.state.objCoeffs[i]}" onchange="app.state.objCoeffs[${i}]=parseFloat(this.value)||0; app.renderPreview()">
                <span class="text-on-surface-variant text-lg">x<sub>${i+1}</sub></span>
            </div>`;
        });
        objHtml += `
            <button onclick="app.addVariable()" class="w-10 h-10 rounded-full border border-dashed border-outline-variant flex items-center justify-center text-on-surface-variant hover:text-primary hover:border-primary transition-all ml-4">
                <span class="material-symbols-outlined text-sm">add</span></button>
            <button onclick="app.removeVariable()" class="w-10 h-10 rounded-full border border-dashed border-error flex items-center justify-center text-on-surface-variant hover:text-error hover:border-error transition-all ml-2">
                <span class="material-symbols-outlined text-sm">remove</span></button>
        `;
        objDiv.innerHTML = objHtml;

        // Render Constraints
        let consHtml = '';
        this.state.constraints.forEach((c, idx) => {
            let eqHtml = `<div class="glass-panel rounded-xl p-4 md:p-6 flex items-center justify-between group">
                <div class="flex flex-wrap items-center gap-2 md:gap-4 font-headline font-bold text-sm md:text-lg w-full">
                <span class="text-xs font-bold text-outline-variant bg-surface-container-lowest w-6 h-6 flex items-center justify-center rounded mr-2">${c.id}</span>`;
            
            this.state.variables.forEach((v, i) => {
                const prefix = i > 0 ? `<span class="text-outline">+</span>` : ``;
                eqHtml += `${prefix}<div class="flex items-center gap-1">
                    <input class="w-14 bg-surface-container-lowest border-none focus:ring-1 focus:ring-secondary rounded-lg text-center text-on-surface" 
                        type="number" step="any" value="${c.coeffs[i]}" onchange="app.state.constraints[${idx}].coeffs[${i}]=parseFloat(this.value)||0; app.renderPreview()">
                    <span class="text-on-surface-variant text-base">x<sub>${i+1}</sub></span>
                </div>`;
            });

            eqHtml += `<select onchange="app.state.constraints[${idx}].sign=this.value; app.renderPreview()" class="bg-surface-container-lowest border-none focus:ring-1 focus:ring-secondary rounded-lg text-sm font-bold text-secondary mx-2">
                <option value="<=" ${c.sign==='<='?'selected':''}>≤</option>
                <option value=">=" ${c.sign==='>='?'selected':''}>≥</option>
                <option value="=" ${c.sign==='='?'selected':''}>=</option>
            </select>
            <input class="w-16 bg-surface-container-lowest border-none focus:ring-1 focus:ring-secondary rounded-lg text-center text-primary-container" 
                type="number" step="any" value="${c.rhs}" onchange="app.state.constraints[${idx}].rhs=parseFloat(this.value)||0; app.renderPreview()">
            </div>
            <button onclick="app.removeConstraint(${idx})" class="opacity-0 group-hover:opacity-100 material-symbols-outlined text-error hover:bg-error-container/20 p-2 rounded transition-all ml-2 flex-shrink-0">delete</button>
            </div>`;
            consHtml += eqHtml;
        });
        consDiv.innerHTML = consHtml;
        this.renderPreview();
    },

    renderPreview() {
        const parts = [];
        this.state.objCoeffs.forEach((c, i) => {
            if(c !== 0) {
                const sign = c > 0 ? (parts.length ? '-' : '-') : '+';
                parts.push(`${sign} ${Math.abs(c)}x${i+1}`);
            }
        });
        document.getElementById('preview-obj').innerText = `Z ${parts.join(' ')} = 0`;

        let consParts = '';
        this.state.constraints.forEach(c => {
            const row = c.coeffs.map((coeff, i) => coeff === 0 ? '' : (coeff > 0 ? `+${coeff}x${i+1}` : `${coeff}x${i+1}`)).join(' ').replace(/^\+/, '');
            consParts += `<p class="font-mono pt-1 text-on-surface">${row || '0'} ${c.sign} ${c.rhs}</p>`;
        });
        document.getElementById('preview-cons').innerHTML = consParts;
    },

    // --- File Upload ---
    async handleFileUpload(e) {
        const file = e.target.files[0];
        if(!file) return;
        
        const preview = document.getElementById('upload-preview');
        preview.classList.remove('hidden');
        preview.innerHTML = `<span class="material-symbols-outlined animate-spin text-secondary">sync</span> Parsing ${file.name}...`;
        
        const fd = new FormData();
        fd.append('file', file);
        
        try {
            const res = await fetch('/api/upload', {method: 'POST', body: fd});
            const data = await res.json();
            if(!res.ok) throw new Error(data.error || "Upload failed");
            
            this.state.currentProblemCache = data;
            
            preview.innerHTML = `
                <div class="text-secondary mb-2 font-bold">Successfully Parsed: ${data.variables.length} vars, ${data.constraints.length} constraints</div>
                <div class="text-on-surface/80 text-xs">${data.goal.toUpperCase()} Z = [${data.objective.join(', ')}]</div>
            `;
            document.getElementById('btn-upload-solve').classList.remove('hidden');
            
        } catch(err) {
            preview.innerHTML = `<div class="text-error font-bold w-full">${err.message}</div>`;
        }
    },

    // --- API Calls ---
    async apiSolve() {
        const btnId = document.getElementById('view-manual').classList.contains('active') ? 'btn-solve' : 'btn-upload-solve';
        const start = performance.now();
        document.getElementById(btnId).innerHTML = `Solving... <span class="material-symbols-outlined animate-spin">sync</span>`;
        
        try {
            let problem = this.state.currentProblemCache;
            // If from manual entry, generate problem JSON
            if(document.getElementById('view-manual').classList.contains('active')) {
                problem = {
                    goal: this.state.goal,
                    variables: this.state.variables,
                    objective: this.state.objCoeffs,
                    constraints: this.state.constraints.map(c => ({
                        coefficients: c.coeffs, sign: c.sign, rhs: c.rhs
                    }))
                };
            }
            this.state.currentProblemCache = problem; // save for PDF

            const res = await fetch('/api/solve', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(problem)
            });
            const result = await res.json();
            
            this.state.result = result;
            this.state.currentTableauIdx = (result.tableaux || []).length > 0 ? result.tableaux.length - 1 : 0;
            
            this.renderResults();
            this.renderTableau();
            this.showView('results');
            
        } catch(err) {
            alert('Error solving: ' + err.message);
        } finally {
            document.getElementById('btn-solve').innerHTML = `Solve Problem <span class="material-symbols-outlined">bolt</span>`;
            document.getElementById('btn-upload-solve').innerHTML = `Analyze & Solve File <span class="material-symbols-outlined">bolt</span>`;
            document.getElementById('footer-latency').innerText = `Latency: ${(performance.now() - start).toFixed(0)}ms`;
        }
    },

    async downloadPdf() {
        if(!this.state.currentProblemCache) return;
        try {
            const res = await fetch('/api/pdf', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(this.state.currentProblemCache)
            });
            if(!res.ok) throw new Error("Failed to generate PDF");
            
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `simplex_report_${new Date().getTime()}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch(e) {
            console.error(e);
            alert("Error downloading PDF");
        }
    },

    // --- Renderers ---
    renderResults() {
        const r = this.state.result;
        
        // Status & Objective
        const badge = document.getElementById('res-status-badge');
        const badgeText = document.getElementById('res-status-text');
        
        if (r.status === 'optimal') {
            badgeText.innerText = "Optimal Solution Found";
            badge.className = "inline-flex items-center gap-2 px-3 py-1 rounded-full border text-[10px] font-bold tracking-widest uppercase mb-4 text-secondary bg-secondary/10 border-secondary/20";
            badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span> Optimization Complete`;
            document.getElementById('res-opt-z').innerText = `Z = ${(r.optimal_value || 0).toFixed(4).replace(/\\.?0+$/, '')}`;
        } else {
            badgeText.innerText = `${r.status.toUpperCase()} MODEL`;
            badge.className = "inline-flex items-center gap-2 px-3 py-1 rounded-full border text-[10px] font-bold tracking-widest uppercase mb-4 text-error bg-error/10 border-error/20";
            badge.innerHTML = `<span class="material-symbols-outlined text-[10px]">error</span> Optimization Failed`;
            document.getElementById('res-opt-z').innerText = (r.status === 'unbounded') ? 'Z = ∞' : 'Z = ---';
        }

        // Variables
        const grid = document.getElementById('res-variables-grid');
        let varHtml = '';
        if(r.variables) {
            for(let [vName, vVal] of Object.entries(r.variables)) {
                varHtml += `
                <div class="bg-surface-container-low ghost-border p-5 rounded-xl hover:bg-surface-container transition-all group">
                    <p class="text-[10px] font-bold text-on-surface-variant/40 group-hover:text-primary transition-colors mb-1 uppercase tracking-tighter">${vName}</p>
                    <p class="text-2xl font-headline font-bold text-on-surface">${vVal.toFixed(4).replace(/\.0000$/, '')}</p>
                </div>`;
            }
        }
        grid.innerHTML = varHtml;

        // Sensitivity
        const sensPanel = document.getElementById('res-sensitivity-panel');
        if(r.sensitivity && r.sensitivity.objective_ranges) {
            sensPanel.classList.remove('hidden');
            let oHtml = '', rHtml = '';
            
            r.sensitivity.objective_ranges.forEach(obj => {
                const lower = obj.allowable_decrease === null ? '-∞' : (obj.current_value - obj.allowable_decrease).toFixed(4);
                const upper = obj.allowable_increase === null ? '∞' : (obj.current_value + obj.allowable_increase).toFixed(4);
                oHtml += `<tr class="border-b border-outline-variant/5">
                    <td class="py-2 font-bold">${obj.variable}</td>
                    <td class="py-2">${obj.current_value.toFixed(4)}</td>
                    <td class="py-2">${lower}</td>
                    <td class="py-2">${upper}</td>
                </tr>`;
            });
            document.getElementById('res-table-obj').innerHTML = oHtml;

            r.sensitivity.rhs_ranges.forEach(rhs => {
                const lower = rhs.allowable_decrease === null ? '-∞' : (rhs.current_rhs - rhs.allowable_decrease).toFixed(4);
                const upper = rhs.allowable_increase === null ? '∞' : (rhs.current_rhs + rhs.allowable_increase).toFixed(4);
                rHtml += `<tr class="border-b border-outline-variant/5">
                    <td class="py-2">C${rhs.constraint_index}</td>
                    <td class="py-2">${rhs.current_rhs.toFixed(4)}</td>
                    <td class="py-2 text-secondary font-bold">${rhs.shadow_price.toFixed(4)}</td>
                    <td class="py-2">${lower}</td>
                    <td class="py-2">${upper}</td>
                </tr>`;
            });
            document.getElementById('res-table-rhs').innerHTML = rHtml;
        } else {
            sensPanel.classList.add('hidden');
        }

        // Graphical
        const graphPanel = document.getElementById('res-graphical-panel');
        if(r.graph_json) {
            graphPanel.classList.remove('hidden');
            Plotly.newPlot('plotly-div', r.graph_json.data, r.graph_json.layout, {responsive: true});
        } else {
            graphPanel.classList.add('hidden');
            document.getElementById('plotly-div').innerHTML = '';
        }
    },

    stepTableau(dir) {
        if(!this.state.result || !this.state.result.tableaux) return;
        const total = this.state.result.tableaux.length;
        this.state.currentTableauIdx += dir;
        
        if(this.state.currentTableauIdx < 0) this.state.currentTableauIdx = 0;
        if(this.state.currentTableauIdx >= total) this.state.currentTableauIdx = total - 1;
        
        this.renderTableau();
    },

    async saveToHistory() {
        if (!this.state.result || !this.state.currentProblemCache) {
            alert('No solved problem to save. Please solve a problem first.');
            return;
        }
        const name = prompt('Enter a name for this computation (optional):') || '';
        const btn = document.getElementById('btn-save-history');
        btn.innerHTML = `<span class="material-symbols-outlined animate-spin">sync</span> Saving...`;
        btn.disabled = true;

        try {
            const res = await fetch('/api/history', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    problem: this.state.currentProblemCache,
                    result: {
                        status: this.state.result.status,
                        optimal_value: this.state.result.optimal_value,
                        iterations: this.state.result.iterations
                    },
                    name: name
                })
            });
            if (!res.ok) throw new Error('Failed to save');
            btn.innerHTML = `<span class="material-symbols-outlined">check_circle</span> Saved!`;
            btn.className = btn.className.replace('text-secondary', 'text-green-400').replace('border-secondary/20', 'border-green-400/30');
            await this.loadHistory();
            setTimeout(() => {
                btn.innerHTML = `<span class="material-symbols-outlined">bookmark_add</span> Save to History`;
                btn.className = "w-full py-4 bg-secondary/10 border border-secondary/20 rounded-xl text-xs font-bold font-headline tracking-widest uppercase text-secondary hover:bg-secondary/20 transition-all active:scale-95 flex items-center justify-center gap-2";
                btn.disabled = false;
            }, 2000);
        } catch (e) {
            alert('Error saving to history: ' + e.message);
            btn.innerHTML = `<span class="material-symbols-outlined">bookmark_add</span> Save to History`;
            btn.disabled = false;
        }
    },

    async loadHistory() {
        try {
            const res = await fetch('/api/history');
            const history = await res.json();
            this._renderHistoryList(history, 'history-list', true);
            this._renderHistoryList(history, 'view-history-list', false);
        } catch (e) {
            console.error('Failed to load history', e);
        }
    },

    _renderHistoryList(history, containerId, compact) {
        const el = document.getElementById(containerId);
        if (!el) return;
        if (!history || history.length === 0) {
            el.innerHTML = `<div class="text-sm text-outline-variant italic p-4">No history saved yet. Solve a problem and click "Save to History".</div>`;
            return;
        }
        el.innerHTML = history.map((h, i) => `
            <div class="glass-panel ghost-border rounded-xl p-4 space-y-2 hover:bg-surface-container transition-all">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-on-surface truncate max-w-[60%]">${h.name || 'Unnamed'}</span>
                    <span class="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${h.status === 'optimal' ? 'bg-secondary/10 text-secondary' : 'bg-error/10 text-error'}">${h.status}</span>
                </div>
                <div class="text-[10px] text-outline-variant">${h.timestamp}</div>
                <div class="flex items-center justify-between mt-1">
                    <span class="text-sm font-bold text-primary">Z = ${h.optimal_value || '—'}</span>
                    ${!compact ? `<button onclick="app.loadFromHistory(${i})" class="text-[10px] text-secondary font-bold uppercase tracking-widest hover:underline flex items-center gap-1"><span class="material-symbols-outlined text-sm">restart_alt</span>Reload</button>` : ''}
                </div>
            </div>
        `).join('');
        // store history for reload
        this._historyCache = history;
    },

    loadFromHistory(index) {
        const h = this._historyCache && this._historyCache[index];
        if (!h || !h.problem) return;
        // Restore problem state
        const p = h.problem;
        this.state.goal = p.goal || 'maximize';
        this.state.variables = p.variables || ['x1', 'x2'];
        this.state.objCoeffs = p.objective || [];
        this.state.constraints = (p.constraints || []).map((c, i) => ({
            id: i + 1,
            coeffs: c.coefficients || [],
            sign: c.sign || '<=',
            rhs: c.rhs || 0
        }));
        this.state.currentProblemCache = p;
        this.renderForms();
        this.showView('manual');
    },

    showHistoryView() {
        this.showView('history');
        this.loadHistory();
    },

    renderTableau() {
        if(!this.state.result) return;
        const i = this.state.currentTableauIdx;
        const tabs = this.state.result.tableaux;
        if(!tabs || !tabs.length) return;
        
        document.getElementById('step-title').innerText = `Iteration ${i+1} of ${tabs.length}`;
        const tab = tabs[i];
        
        // Find Pivot
        const pivot = this.state.result.pivot_cells && i < this.state.result.pivot_cells.length ? this.state.result.pivot_cells[i] : null;

        let thHtml = '';
        tab.columns.forEach(c => {
            const isPcol = pivot && String(c) === String(pivot.column);
            const clr = isPcol ? 'text-secondary bg-secondary/10 shadow-[0_4px_10px_rgba(127,214,203,0.1)]' : '';
            thHtml += `<th class="py-4 px-4 font-label font-bold text-[10px] tracking-widest uppercase ${clr}">${c}</th>`;
        });
        
        let tbHtml = '';
        tab.data.forEach(r => {
            const basis = String(r.Basis);
            const isProw = pivot && basis === String(pivot.row);
            const rbg = isProw ? 'bg-primary/5 border-y border-primary/20 pivot-glow' : 'border-b border-outline-variant/5 hover:bg-surface-variant/20';
            
            let rowHtml = `<tr class="${rbg}">`;
            tab.columns.forEach(c => {
                const isPcol = pivot && String(c) === String(pivot.column);
                let val = r[c];
                if(typeof val === 'number') val = val.toFixed(4).replace(/\.0000$/, '');
                
                let cellClass = 'py-4 px-4 font-mono text-sm ';
                if(c === 'Basis') cellClass += 'font-bold text-on-surface ';
                else if(c === 'RHS') cellClass += 'font-bold text-secondary ';
                
                if(isPcol) {
                    if(isProw) cellClass += " bg-secondary/20 text-secondary font-black border-2 border-secondary/40 shadow-[0_0_20px_rgba(127,214,203,0.3)] ";
                    else cellClass += " bg-secondary/10 border-x border-secondary/10 ";
                }
                
                if(isProw && c === 'Basis') cellClass += 'text-primary ';
                
                rowHtml += `<td class="${cellClass}">${val}</td>`;
            });
            rowHtml += `</tr>`;
            tbHtml += rowHtml;
        });

        const html = `
        <table class="w-full text-left border-collapse whitespace-nowrap">
            <thead>
                <tr class="text-on-surface-variant border-b border-outline-variant/10">
                    ${thHtml}
                </tr>
            </thead>
            <tbody class="text-sm font-body">
                ${tbHtml}
            </tbody>
        </table>`;
        
        document.getElementById('tableau-container').innerHTML = html;
        
        let msg = 'Displaying Tableau iteration step.';
        if(pivot) msg = `Found Pivot at Row <b>${pivot.row}</b>, Column <b>${pivot.column}</b> with value <b>${pivot.value.toFixed(4)}</b>`;
        document.getElementById('tableau-info').innerHTML = msg;
    }
};

window.onload = () => {
    app.renderForms();
};
