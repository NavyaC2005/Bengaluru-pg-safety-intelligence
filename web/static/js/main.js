/* ==========================================================================
   Bengaluru PG Safety & Price Intelligence - Interactive JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    
    // --------------------------------------------------------------------------
    // 1. Budget Range Slider Sync
    // --------------------------------------------------------------------------
    const budgetSlider = document.getElementById('budgetSlider');
    const budgetDisplay = document.getElementById('budgetDisplay');
    if (budgetSlider && budgetDisplay) {
        budgetSlider.addEventListener('input', function (e) {
            budgetDisplay.textContent = '₹' + parseInt(e.target.value).toLocaleString('en-IN');
        });
    }

    // --------------------------------------------------------------------------
    // 2. PG Finder Dynamic AJAX Search
    // --------------------------------------------------------------------------
    const finderForm = document.getElementById('finderForm');
    const resultsContainer = document.getElementById('finderResults');
    const resultsCounter = document.getElementById('resultsCounter');

    if (finderForm && resultsContainer) {
        finderForm.addEventListener('submit', function (e) {
            e.preventDefault();
            
            const budget = document.getElementById('budgetSlider').value;
            const locality = document.getElementById('localitySelect').value;
            const roomType = document.getElementById('roomTypeSelect').value;
            const foodOption = document.getElementById('foodOptionSelect').value;
            const wifiReq = document.getElementById('wifiReq')?.checked || false;
            const acReq = document.getElementById('acReq')?.checked || false;
            
            // Gather checked amenities
            const checkedAmenities = [];
            document.querySelectorAll('input[name="preferred_amenities"]:checked').forEach(cb => {
                checkedAmenities.push(cb.value);
            });

            const payload = {
                budget: parseFloat(budget),
                locality: locality,
                room_type: roomType,
                food_option: foodOption,
                wifi_required: wifiReq,
                ac_required: acReq,
                preferred_amenities: checkedAmenities
            };

            resultsContainer.innerHTML = `
                <div class="card" style="text-align: center; padding: 48px;">
                    <div style="font-size: 1.1rem; color: #4f46e5; font-weight: 600;">Searching matching PG listings...</div>
                </div>
            `;

            fetch('/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (resultsCounter) {
                    resultsCounter.textContent = `${data.total_matches} Matching PG(s) Found`;
                }

                if (!data.recommendations || data.recommendations.length === 0) {
                    resultsContainer.innerHTML = `
                        <div class="card" style="text-align: center; padding: 48px;">
                            <h3 style="margin-bottom: 8px;">No Listings Match All Criteria</h3>
                            <p style="color: #64748b; margin-bottom: 20px;">${data.message || 'Try increasing your budget or choosing Any locality.'}</p>
                            <button type="button" class="btn btn-secondary" onclick="resetFinderForm()">Reset Filters</button>
                        </div>
                    `;
                    return;
                }

                let html = '';
                data.recommendations.forEach(r => {
                    const badgeClass = r.safety.badge_class || 'badge-success';
                    const warningLabel = r.safety.rule_based_warning_label || 'No Rule-Based Flag';
                    
                    let warningsHtml = '';
                    if (r.safety.warnings && r.safety.warnings.length > 0) {
                        warningsHtml = `
                            <div class="warning-box">
                                <strong style="font-size: 0.82rem; text-transform: uppercase; color: #92400e; display: block; margin-bottom: 6px;">
                                    Verification Indicators (${r.safety.warnings.length}):
                                </strong>
                                ${r.safety.warnings.map(w => `
                                    <div class="warning-item">
                                        <span>⚠️</span>
                                        <div><strong>${w.title}:</strong> ${w.message}</div>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    }

                    const amenitiesList = (r.amenities || '').split(';').map(a => a.trim()).filter(Boolean);
                    const amenitiesChips = amenitiesList.map(a => `<span class="amenity-chip">${a}</span>`).join('');

                    html += `
                        <div class="listing-card">
                            <div class="listing-header">
                                <div>
                                    <div class="listing-locality">${r.locality}</div>
                                    <div class="listing-type">${r.room_type} • Food: ${r.food_option} • Bath: ${r.bathroom_type}</div>
                                </div>
                                <div class="listing-price-box">
                                    <div class="listing-rent">₹${r.monthly_rent_inr.toLocaleString('en-IN')} <span class="listing-rent-period">/ mo</span></div>
                                    <div class="listing-deposit">Deposit: ₹${r.deposit_inr.toLocaleString('en-IN')} (${r.deposit_to_rent_ratio}x)</div>
                                </div>
                            </div>

                            <p style="font-size: 0.9rem; color: #475569; margin: 10px 0;">
                                "${r.listing_description_demo || 'Standard PG accommodation in prime locality.'}"
                            </p>

                            <div class="listing-amenities-row">
                                <span class="amenity-chip" style="background: #eef2ff; color: #4338ca; font-weight: 600;">Wi-Fi: ${r.wifi}</span>
                                <span class="amenity-chip" style="background: #eef2ff; color: #4338ca; font-weight: 600;">AC: ${r.ac}</span>
                                ${amenitiesChips}
                            </div>

                            ${warningsHtml}

                            <div class="listing-footer">
                                <div style="display: flex; gap: 8px; align-items: center;">
                                    <span class="badge badge-score">Match: ${r.match_score}/100</span>
                                    <span class="badge ${badgeClass}">${warningLabel}</span>
                                    <span style="font-size: 0.82rem; color: #64748b;">★ ${r.rating_demo} (${r.review_count_demo} reviews)</span>
                                </div>
                                <div>
                                    <span style="font-size: 0.82rem; color: #4f46e5; font-weight: 600;">${r.price_tag}</span>
                                </div>
                            </div>
                        </div>
                    `;
                });

                resultsContainer.innerHTML = html;
            })
            .catch(err => {
                resultsContainer.innerHTML = `
                    <div class="card" style="text-align: center; color: #dc2626; padding: 32px;">
                        Failed to fetch matching listings. Error: ${err.message}
                    </div>
                `;
            });
        });
    }

    // --------------------------------------------------------------------------
    // 3. Rent Estimator
    // --------------------------------------------------------------------------
    const estimateForm = document.getElementById('estimateForm');
    const estimateResultBox = document.getElementById('estimateResultBox');

    if (estimateForm && estimateResultBox) {
        estimateForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const checkedAmenities = [];
            document.querySelectorAll('input[name="estimator_amenities"]:checked').forEach(cb => {
                checkedAmenities.push(cb.value);
            });

            const payload = {
                locality: document.getElementById('estLocality').value,
                room_type: document.getElementById('estRoomType').value,
                food_option: document.getElementById('estFoodOption').value,
                wifi: document.getElementById('estWifi').value,
                ac: document.getElementById('estAc').value,
                bathroom_type: document.getElementById('estBathroom').value,
                amenities: checkedAmenities
            };

            estimateResultBox.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #4f46e5;">
                    Calculating fair market estimate using trained Random Forest model...
                </div>
            `;

            fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    estimateResultBox.innerHTML = `<div class="warning-box">Error: ${data.error}</div>`;
                    return;
                }

                estimateResultBox.innerHTML = `
                    <div style="text-align: center; padding: 20px 0;">
                        <span class="badge badge-success" style="margin-bottom: 12px;">Machine Learning Prediction</span>
                        <div style="font-size: 0.95rem; color: #64748b; font-weight: 600;">Estimated Monthly Rent for ${payload.locality} (${payload.room_type})</div>
                        <div style="font-family: var(--font-heading); font-size: 3rem; font-weight: 800; color: #4f46e5; line-height: 1.1; margin: 12px 0;">
                            ₹${data.estimated_rent_inr.toLocaleString('en-IN')}
                            <span style="font-size: 1.1rem; color: #64748b; font-weight: 500;">/ month</span>
                        </div>
                        <div style="font-size: 0.95rem; color: #334155; margin-bottom: 16px;">
                            Expected Market Range: <strong>₹${data.range_low_inr.toLocaleString('en-IN')} – ₹${data.range_high_inr.toLocaleString('en-IN')}</strong>
                        </div>
                        <p style="font-size: 0.85rem; color: #64748b; max-width: 500px; margin: 0 auto; line-height: 1.5;">
                            Generated by ${data.model_name}. Rent may vary based on exact building age, road accessibility, and negotiated utilities.
                        </p>
                    </div>
                `;
            })
            .catch(err => {
                estimateResultBox.innerHTML = `<div class="warning-box">Prediction failed: ${err.message}</div>`;
            });
        });
    }

    // --------------------------------------------------------------------------
    // 4. Safety Verifier
    // --------------------------------------------------------------------------
    const verifyForm = document.getElementById('verifyForm');
    const verifyResultBox = document.getElementById('verifyResultBox');

    if (verifyForm && verifyResultBox) {
        verifyForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const rent = parseFloat(document.getElementById('verRent').value || 0);
            const deposit = parseFloat(document.getElementById('verDeposit').value || 0);
            const locality = document.getElementById('verLocality').value;
            const roomType = document.getElementById('verRoomType').value;
            const description = document.getElementById('verDescription').value;
            const payBefore = document.getElementById('verPayBefore').checked ? 1 : 0;
            const ac = document.getElementById('verAc').value;

            const payload = {
                monthly_rent_inr: rent,
                deposit_inr: deposit,
                locality: locality,
                room_type: roomType,
                listing_description_demo: description,
                pay_before_visit_indicator: payBefore,
                ac: ac
            };

            verifyResultBox.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #4f46e5;">
                    Evaluating listing against transparent safety rules...
                </div>
            `;

            fetch('/api/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    verifyResultBox.innerHTML = `<div class="warning-box">Error: ${data.error}</div>`;
                    return;
                }

                let warningsMarkup = '';
                if (data.warnings && data.warnings.length > 0) {
                    warningsMarkup = `
                        <div style="margin-top: 18px;">
                            <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 10px; color: #991b1b;">
                                Triggered Verification Indicators (${data.warnings.length}):
                            </h4>
                            ${data.warnings.map(w => `
                                <div class="warning-box" style="margin-bottom: 12px; background: #fff1f2; border-color: #fecdd3;">
                                    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px;">
                                        <span class="badge ${w.severity === 'HIGH' ? 'badge-danger' : 'badge-warning'}">${w.severity} PRIORITY</span>
                                        <strong style="color: #9f1239;">${w.title}</strong>
                                    </div>
                                    <p style="font-size: 0.88rem; color: #4c0519; margin: 0;">${w.message}</p>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    warningsMarkup = `
                        <div class="warning-box" style="background: #f0fdf4; border-color: #bbf7d0; margin-top: 16px;">
                            <strong style="color: #166534;">No Rule-Based Flags Triggered</strong>
                            <p style="font-size: 0.88rem; color: #14532d; margin-top: 4px;">
                                Deposit ratio is within standard bounds and no high-risk phrases were detected.
                                Standard due diligence during physical visit is still recommended.
                            </p>
                        </div>
                    `;
                }

                const checklistMarkup = `
                    <div style="margin-top: 24px; padding-top: 18px; border-top: 1px solid var(--border);">
                        <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 10px;">Recommended Verification Checklist:</h4>
                        <ul style="padding-left: 20px; font-size: 0.88rem; color: #334155; line-height: 1.7;">
                            ${data.verification_checklist.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                `;

                verifyResultBox.innerHTML = `
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                            <h3 style="font-family: var(--font-heading); font-size: 1.25rem;">Evaluation Outcome</h3>
                            <span class="badge ${data.badge_class}">${data.rule_based_warning_label}</span>
                        </div>
                        <p style="font-size: 0.92rem; color: #475569;">${data.status_text}</p>
                        ${warningsMarkup}
                        ${checklistMarkup}
                        <div style="margin-top: 20px; font-size: 0.78rem; color: #94a3b8; font-style: italic;">
                            ${data.ethical_disclaimer}
                        </div>
                    </div>
                `;
            })
            .catch(err => {
                verifyResultBox.innerHTML = `<div class="warning-box">Evaluation failed: ${err.message}</div>`;
            });
        });
    }

});

function resetFinderForm() {
    const form = document.getElementById('finderForm');
    if (form) {
        form.reset();
        document.getElementById('budgetSlider').value = 15000;
        document.getElementById('budgetDisplay').textContent = '₹15,000';
        form.dispatchEvent(new Event('submit'));
    }
}
