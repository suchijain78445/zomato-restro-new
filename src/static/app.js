// Zomato AI Concierge - Lumina Noir Frontend Client Logic

document.addEventListener("DOMContentLoaded", async () => {
    // State management
    const state = {
        city: "",
        location: "",
        cuisines: new Set(),
        budget: "",
        minRating: 3.5,
        onlineOrder: false,
        bookTable: false,
        additionalNotes: "",
        topK: 5
    };

    // DOM Elements
    const citySelect = document.getElementById("city-select");
    const locationSelect = document.getElementById("location-select");
    const cuisinesContainer = document.getElementById("cuisines-container");
    const budgetContainer = document.getElementById("budget-container");
    const minRatingInput = document.getElementById("min-rating-input");
    const minRatingVal = document.getElementById("min-rating-val");
    const onlineOrderToggle = document.getElementById("online-order-toggle");
    const bookTableToggle = document.getElementById("book-table-toggle");
    const notesInput = document.getElementById("notes-input");
    const generateBtn = document.getElementById("generate-btn");
    const recommendationsContainer = document.getElementById("recommendations-container");
    const summaryBanner = document.getElementById("summary-banner");
    const totalMatchesBadge = document.getElementById("total-matches-badge");
    const relaxedConstraintsBadge = document.getElementById("relaxed-constraints-badge");
    const latencyBadge = document.getElementById("latency-badge");
    const apiStatusText = document.getElementById("api-status-text");

    // Initialize UI
    await init();

    async function init() {
        await loadCities();
        await loadCuisines();
        setupEventListeners();
    }

    // 1. Load Available Cities
    async function loadCities() {
        try {
            const res = await fetch("/metadata/cities");
            if (!res.ok) throw new Error("Failed to fetch cities");
            const data = await res.json();
            const cities = data.cities || [];

            citySelect.innerHTML = "";
            cities.forEach((c) => {
                const opt = document.createElement("option");
                opt.value = c;
                opt.textContent = c;
                citySelect.appendChild(opt);
            });

            if (cities.length > 0) {
                state.city = cities[0];
                citySelect.value = cities[0];
                await loadLocations(state.city);
            }
            if (apiStatusText) apiStatusText.textContent = "Backend Connected";
        } catch (err) {
            console.error("Error loading cities:", err);
            citySelect.innerHTML = '<option value="">Error loading cities</option>';
            if (apiStatusText) apiStatusText.textContent = "Offline / Connection Error";
        }
    }

    // 2. Load Locations for Selected City
    async function loadLocations(city) {
        try {
            const res = await fetch(`/metadata/locations?city=${encodeURIComponent(city)}`);
            if (!res.ok) throw new Error("Failed to fetch locations");
            const data = await res.json();
            const locations = data.locations || [];

            locationSelect.innerHTML = '<option value="">All Neighborhoods</option>';
            locations.forEach((loc) => {
                const opt = document.createElement("option");
                opt.value = loc;
                opt.textContent = loc;
                locationSelect.appendChild(opt);
            });
            state.location = "";
        } catch (err) {
            console.error("Error loading locations:", err);
            locationSelect.innerHTML = '<option value="">All Neighborhoods</option>';
        }
    }

    // 3. Load Cuisines
    async function loadCuisines() {
        try {
            const res = await fetch("/metadata/cuisines");
            if (!res.ok) throw new Error("Failed to fetch cuisines");
            const data = await res.json();
            const cuisines = data.cuisines || [];

            cuisinesContainer.innerHTML = "";
            // Show top popular cuisines as pill buttons
            cuisines.slice(0, 18).forEach((cuis) => {
                const pill = document.createElement("button");
                pill.type = "button";
                pill.className = "cuisine-pill px-3 py-1 rounded-full border border-white/10 text-on-surface-variant hover:border-primary/50 text-xs font-medium transition-all";
                pill.textContent = capitalize(cuis);
                pill.dataset.cuisine = cuis;

                pill.addEventListener("click", () => {
                    if (state.cuisines.has(cuis)) {
                        state.cuisines.delete(cuis);
                        pill.className = "cuisine-pill px-3 py-1 rounded-full border border-white/10 text-on-surface-variant hover:border-primary/50 text-xs font-medium transition-all";
                    } else {
                        state.cuisines.add(cuis);
                        pill.className = "cuisine-pill px-3 py-1 rounded-full border border-primary text-primary bg-primary/10 text-xs font-medium shadow-[0_0_10px_rgba(226,55,68,0.2)] transition-all";
                    }
                });

                cuisinesContainer.appendChild(pill);
            });
        } catch (err) {
            console.error("Error loading cuisines:", err);
        }
    }

    // 4. Setup Event Listeners
    function setupEventListeners() {
        citySelect.addEventListener("change", async (e) => {
            state.city = e.target.value;
            await loadLocations(state.city);
        });

        locationSelect.addEventListener("change", (e) => {
            state.location = e.target.value;
        });

        // Budget Chips
        const budgetChips = budgetContainer.querySelectorAll(".budget-chip");
        budgetChips.forEach((chip) => {
            chip.addEventListener("click", () => {
                budgetChips.forEach((c) => {
                    c.className = "budget-chip flex-1 py-1.5 text-xs font-semibold rounded-lg text-on-surface-variant hover:text-white transition-all";
                });
                chip.className = "budget-chip flex-1 py-1.5 text-xs font-semibold rounded-lg text-white bg-primary shadow-md transition-all";
                state.budget = chip.dataset.budget;
            });
        });

        // Min Rating Slider
        minRatingInput.addEventListener("input", (e) => {
            state.minRating = parseFloat(e.target.value);
            minRatingVal.textContent = `${state.minRating.toFixed(1)}+ ⭐`;
        });

        // Toggles
        onlineOrderToggle.addEventListener("change", (e) => {
            state.onlineOrder = e.target.checked;
        });

        bookTableToggle.addEventListener("change", (e) => {
            state.bookTable = e.target.checked;
        });

        notesInput.addEventListener("input", (e) => {
            state.additionalNotes = e.target.value;
        });

        // Submit Button
        generateBtn.addEventListener("click", handleGenerateRecommendations);
    }

    // 5. Handle Recommendation Request
    async function handleGenerateRecommendations() {
        if (!state.city) {
            alert("Please select a city.");
            return;
        }

        const startTime = performance.now();
        renderLoadingSkeletons();

        // Build UserPreferences payload
        const payload = {
            city: state.city,
            top_k: state.topK
        };

        if (state.location) payload.location = state.location;
        if (state.budget) payload.budget = state.budget;
        if (state.cuisines.size > 0) payload.cuisines = Array.from(state.cuisines);
        if (state.minRating > 0) payload.min_rating = state.minRating;
        if (state.onlineOrder) payload.online_order = true;
        if (state.bookTable) payload.book_table = true;
        if (state.additionalNotes.trim()) payload.additional_notes = state.additionalNotes.trim();

        try {
            const res = await fetch("/recommendations", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                renderError(errData.detail || `Server returned error ${res.status}`);
                return;
            }

            const data = await res.json();
            renderResults(data, elapsed);

        } catch (err) {
            console.error("Error fetching recommendations:", err);
            renderError("Unable to reach backend API server. Please check connection.");
        }
    }

    // 6. Render Results
    function renderResults(data, elapsedSec) {
        const recs = data.recommendations || [];
        const totalMatches = data.total_matches || 0;
        const relaxed = data.relaxed_constraints || [];

        // Update Summary Banner
        totalMatchesBadge.textContent = `${totalMatches} Restaurants Analyzed`;
        if (relaxed.length > 0) {
            relaxedConstraintsBadge.classList.remove("hidden");
            relaxedConstraintsBadge.textContent = `Auto-relaxed: ${relaxed.join(", ")}`;
        } else {
            relaxedConstraintsBadge.classList.add("hidden");
        }
        latencyBadge.innerHTML = `<span>⏱️ ${elapsedSec}s Response Time</span>`;

        if (recs.length === 0) {
            recommendationsContainer.innerHTML = `
                <div class="glass-panel rounded-2xl p-10 text-center flex flex-col items-center gap-3">
                    <span class="material-symbols-outlined text-4xl text-amber-400">search_off</span>
                    <h4 class="text-lg font-bold text-white">No Restaurants Found</h4>
                    <p class="text-xs text-on-surface-variant max-w-sm">Try broadening your search criteria or lowering the minimum rating.</p>
                </div>
            `;
            return;
        }

        recommendationsContainer.innerHTML = "";

        recs.forEach((item, index) => {
            const r = item.restaurant;
            const rank = item.rank || index + 1;
            const explanation = item.explanation || "Top rated match for your criteria.";
            const isTopMatch = rank === 1;

            const card = document.createElement("article");
            card.className = isTopMatch
                ? "ai-border rounded-2xl p-[1px] relative shadow-2xl transition-all duration-300"
                : "glass-panel rounded-2xl p-5 md:p-6 flex flex-col gap-4 hover:border-white/20 transition-all duration-300 shadow-xl";

            const cardInnerHtml = `
                <div class="${isTopMatch ? 'bg-surface-container-highest rounded-2xl p-5 md:p-6 flex flex-col gap-4 h-full relative' : 'flex flex-col gap-4'}">
                    ${isTopMatch ? `
                        <div class="absolute -top-3.5 right-4 bg-gradient-to-r from-tertiary to-amber-500 text-black font-bold text-xs px-3 py-1 rounded-full shadow-[0_0_15px_rgba(255,185,95,0.6)] flex items-center gap-1 z-10">
                            <span class="material-symbols-outlined text-sm">star</span> #1 TOP MATCH
                        </div>
                    ` : ''}

                    <!-- Restaurant Main Header -->
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                        <div>
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="text-xs font-bold text-secondary bg-secondary/10 px-2 py-0.5 rounded border border-secondary/20">#${rank}</span>
                                <h3 class="text-xl md:text-2xl font-bold text-white hover:text-primary transition-colors">${escapeHtml(r.name)}</h3>
                            </div>
                            <p class="text-xs text-on-surface-variant flex items-center gap-1 mt-1">
                                <span class="material-symbols-outlined text-sm">location_on</span> ${escapeHtml(r.location)}, ${escapeHtml(r.city)}
                            </p>
                        </div>

                        <!-- Rating Badge -->
                        <div class="flex items-center gap-2">
                            <div class="bg-emerald-500/20 border border-emerald-500/30 px-3 py-1.5 rounded-xl flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-emerald-400 text-sm">star</span>
                                <span class="text-emerald-300 font-bold text-sm">${r.rating ? r.rating.toFixed(1) : 'NEW'}</span>
                            </div>
                            <span class="text-xs text-on-surface-variant font-medium">(${r.votes || 0} votes)</span>
                        </div>
                    </div>

                    <!-- Meta Tags Row -->
                    <div class="flex flex-wrap gap-2 text-xs">
                        <span class="bg-white/5 border border-white/10 px-2.5 py-1 rounded-lg text-on-surface-variant flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm">restaurant_menu</span> ${r.cuisines && r.cuisines.length ? r.cuisines.map(capitalize).join(", ") : "Various"}
                        </span>
                        <span class="bg-white/5 border border-white/10 px-2.5 py-1 rounded-lg text-on-surface-variant flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm">payments</span> ₹${r.cost_for_two || 'N/A'} for two
                        </span>
                        ${r.budget_tier ? `
                            <span class="bg-white/5 border border-white/10 px-2.5 py-1 rounded-lg text-amber-300 uppercase font-semibold">
                                ${r.budget_tier} budget
                            </span>
                        ` : ''}
                        ${r.online_order ? `
                            <span class="bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg text-emerald-400 font-medium">✓ Delivery</span>
                        ` : ''}
                        ${r.book_table ? `
                            <span class="bg-purple-500/10 border border-purple-500/20 px-2.5 py-1 rounded-lg text-purple-300 font-medium">✓ Booking Available</span>
                        ` : ''}
                    </div>

                    <!-- ✨ AI Recommendation Insight Callout -->
                    <div class="bg-gradient-to-r from-secondary/15 to-primary/10 border border-secondary/30 rounded-xl p-3.5 relative overflow-hidden">
                        <div class="flex items-center gap-1.5 mb-1.5">
                            <span class="material-symbols-outlined text-secondary text-sm">auto_awesome</span>
                            <span class="text-xs text-secondary font-bold uppercase tracking-wider">AI Recommendation Insight</span>
                        </div>
                        <p class="text-sm text-on-surface italic leading-relaxed">
                            "${escapeHtml(explanation)}"
                        </p>
                    </div>

                    <!-- Card Footer: Dishes & Link -->
                    <div class="flex items-center justify-between pt-2 border-t border-white/5 gap-2">
                        <div class="flex gap-1.5 flex-wrap">
                            ${r.popular_dishes && r.popular_dishes.length > 0 ? r.popular_dishes.slice(0, 3).map(d => `
                                <span class="text-[11px] text-on-surface-variant bg-white/5 px-2 py-0.5 rounded border border-white/5">#${escapeHtml(d)}</span>
                            `).join("") : ''}
                        </div>

                        ${r.url ? `
                            <a href="${r.url}" target="_blank" class="text-xs font-bold text-primary hover:text-primary-container flex items-center gap-1 transition-colors ml-auto">
                                View on Zomato <span class="material-symbols-outlined text-sm">arrow_outward</span>
                            </a>
                        ` : `
                            <span class="text-xs text-on-surface-variant ml-auto">Zomato Listing</span>
                        `}
                    </div>
                </div>
            `;

            card.innerHTML = cardInnerHtml;
            recommendationsContainer.appendChild(card);
        });
    }

    // 7. Render Skeleton Loaders
    function renderLoadingSkeletons() {
        recommendationsContainer.innerHTML = `
            <div class="glass-panel rounded-2xl p-6 animate-pulse flex flex-col gap-4">
                <div class="h-6 bg-white/10 rounded-md w-1/3"></div>
                <div class="h-4 bg-white/5 rounded-md w-1/2"></div>
                <div class="h-20 bg-white/5 rounded-xl w-full"></div>
            </div>
            <div class="glass-panel rounded-2xl p-6 animate-pulse flex flex-col gap-4">
                <div class="h-6 bg-white/10 rounded-md w-1/4"></div>
                <div class="h-4 bg-white/5 rounded-md w-1/3"></div>
                <div class="h-20 bg-white/5 rounded-xl w-full"></div>
            </div>
        `;
    }

    // 8. Render Error
    function renderError(msg) {
        recommendationsContainer.innerHTML = `
            <div class="glass-panel rounded-2xl p-8 text-center flex flex-col items-center gap-3 border-l-4 border-l-red-500">
                <span class="material-symbols-outlined text-4xl text-red-400">error</span>
                <h4 class="text-lg font-bold text-white">Recommendation Error</h4>
                <p class="text-xs text-on-surface-variant max-w-md">${escapeHtml(msg)}</p>
            </div>
        `;
    }

    // Helper functions
    function capitalize(str) {
        if (!str) return "";
        return str.split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(" ");
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
