import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FarmerMap from '../../components/map/FarmerMap';
import { STATE_DATA, INDIA_CENTER, DEFAULT_ZOOM } from '../../data/geoBounds';
import { getSuitabilityCategory, getShsColor } from '../../utils/colorUtils';

const baseUrl = process.env.REACT_APP_API_BASE_URL;

const VALIDATION_RULES = {
    common: {
        n: { min: 100, max: 400, label: "Nitrogen" },
        p: { min: 5, max: 35, label: "Phosphorus" },
        k: { min: 150, max: 590, label: "Potassium" },
        ph: { min: 5.5, max: 8.5, label: "pH Level" },
        organic_carbon: { min: 0.2, max: 1.0, label: "Organic Carbon" },
    },
    germination: {
        moisture: { min: 10, max: 25, label: "Moisture" },
        temperature: { min: 14, max: 28, label: "Temperature" }
    },
    booting: {
        moisture: { min: 10, max: 30, label: "Moisture" },
        temperature: { min: 15, max: 30, label: "Temperature" }
    },
    ripening: {
        moisture: { min: 15, max: 40, label: "Moisture" },
        temperature: { min: 18, max: 32, label: "Temperature" }
    }
};

const FarmerInputForm = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [points, setPoints] = useState([]);
    const [activePointId, setActivePointId] = useState(null);
    const [isAnalyzingMultiple, setIsAnalyzingMultiple] = useState(false);
    const [boundaryGeoJSON, setBoundaryGeoJSON] = useState(null);
    const [farmerProfile, setFarmerProfile] = useState(null);

    React.useEffect(() => {
        try {
            const profile = JSON.parse(localStorage.getItem('farmer'));
            if (profile) setFarmerProfile(profile);
        } catch (e) {}
    }, []);

    // State management for sync
    const [districtsList, setDistrictsList] = useState([]);
    const [subDistrictsList, setSubDistrictsList] = useState([]);
    const [selectedDistrict, setSelectedDistrict] = useState("");
    const [selectedSubDistrict, setSelectedSubDistrict] = useState("");
    const [lockedLocation, setLockedLocation] = useState(false);

    // Store full sub-district data to allow filtering without re-fetching
    const [fullSubDistrictData, setFullSubDistrictData] = useState(null);

    const [formData, setFormData] = useState({
        name: '',
        fieldId: '',
        state: '',
        district: '',
        subDistrict: '', // Added to form data
        n: '',
        p: '',
        k: '',
        ph: '',
        moisture: '',
        organic_carbon: '',
        temperature: '',
        stage: 'germination'
    });

    const [fieldErrors, setFieldErrors] = useState({});
    const [activeStage, setActiveStage] = useState('germination');

    // Helper to get active rules based on stage
    const getActiveRules = () => {
        const stageRules = VALIDATION_RULES[formData.stage] || VALIDATION_RULES.germination;
        return { ...VALIDATION_RULES.common, ...stageRules };
    };

    // NEW: Centralized validation and "Calculate Again" logic
    React.useEffect(() => {
        const activeRules = getActiveRules();
        const newFieldErrors = { ...fieldErrors };
        let errorsChanged = false;

        // 1. Re-validate all fields against current rules (handles Stage Change Sync)
        Object.keys(activeRules).forEach(name => {
            const rule = activeRules[name];
            const value = formData[name];

            if (value) {
                const numVal = parseFloat(value);
                if (numVal < rule.min || numVal > rule.max) {
                    const errorMsg = `Value out of range (${rule.min}-${rule.max})`;
                    if (newFieldErrors[name] !== errorMsg) {
                        newFieldErrors[name] = errorMsg;
                        errorsChanged = true;
                    }
                } else if (newFieldErrors[name]) {
                    delete newFieldErrors[name];
                    errorsChanged = true;
                }
            } else if (newFieldErrors[name]) {
                // Clear error if field is empty (optional, but cleaner)
                delete newFieldErrors[name];
                errorsChanged = true;
            }
        });

        // Remove errors for fields that are NO LONGER in the active rules (e.g. NDVI when switching to Germination)
        Object.keys(newFieldErrors).forEach(name => {
            if (!activeRules[name]) {
                delete newFieldErrors[name];
                errorsChanged = true;
            }
        });

        if (errorsChanged) {
            setFieldErrors(newFieldErrors);
        }

        // 2. Auto-clear top-level error box if all fields are now valid
        if (Object.keys(newFieldErrors).length === 0 && error) {
            setError(null);
        }

        // 3. "Calculate Again" Logic: Clear results if soil parameters or stage change
    }, [
        formData.n, formData.p, formData.k, formData.ph,
        formData.moisture, formData.organic_carbon, formData.temperature,
        formData.stage
    ]);



    // --- Map Logic ---

    // 1. Initial Load: Fetch State Boundaries or Prepopulate Profile
    React.useEffect(() => {
        const loadInitialMap = async () => {
            let userProfile = null;
            try {
                userProfile = JSON.parse(localStorage.getItem('farmer'));
            } catch(e) {}

            if (userProfile && userProfile.state) {
                // Lock fields to farmer profile
                setLockedLocation(true);
                setFormData(prev => ({
                    ...prev,
                    state: userProfile.state || '',
                    district: userProfile.district || '',
                    subDistrict: userProfile.village || ''
                }));
                if (userProfile.district) {
                    setDistrictsList([userProfile.district]);
                    setSelectedDistrict(userProfile.district);
                }
                if (userProfile.village) {
                    setSubDistrictsList([userProfile.village]);
                    setSelectedSubDistrict(userProfile.village);
                }

                try {
                    setLoading(true);
                    // Fetch appropriate map level
                    if (userProfile.village && userProfile.district) {
                        const res = await fetch(`${baseUrl}/map/subdistrict?state=${userProfile.state}&district=${userProfile.district}`);
                        if (res.ok) {
                            const data = await res.json();
                            setFullSubDistrictData(data);
                            const feature = data.features.find(f => {
                                const props = f.properties;
                                const name = props.TEHSIL || props.TEHSIL_NAM || props.sub_dist || props.District;
                                return name && name.toLowerCase() === userProfile.village.toLowerCase();
                            });
                            if (feature) {
                                setBoundaryGeoJSON({ type: "FeatureCollection", features: [feature] });
                            } else {
                                setBoundaryGeoJSON(data);
                            }
                        }
                    } else if (userProfile.district) {
                        const res = await fetch(`${baseUrl}/map/district?state=${userProfile.state}`);
                        if (res.ok) setBoundaryGeoJSON(await res.json());
                    } else {
                        const res = await fetch(baseUrl + '/map/state');
                        if (res.ok) setBoundaryGeoJSON(await res.json());
                    }
                } catch (e) {
                    console.error("Profile map load failed:", e);
                } finally {
                    setLoading(false);
                }
            } else {
                try {
                    const res = await fetch(baseUrl + '/map/state');
                    if (!res.ok) throw new Error("Backend not reachable");
                    const data = await res.json();
                    setBoundaryGeoJSON(data);
                } catch (e) {
                    console.error("Initial map load failed:", e);
                    setError("Map Service Unavailable. Please start the backend.");
                }
            }
        };
        loadInitialMap();
    }, []);

    // 2. Handle State Change -> Load Districts
    const handleStateChange = async (e) => {
        if (lockedLocation) return;
        const newState = e.target.value;
        setFormData({ ...formData, state: newState, district: '', subDistrict: '' });

        // Reset Lower Levels
        setSelectedDistrict("");
        setSelectedSubDistrict("");
        setDistrictsList([]);
        setSubDistrictsList([]);
        setFullSubDistrictData(null); // Clear stored sub-district data

        if (newState) {
            try {
                setLoading(true);
                const res = await fetch(`${baseUrl}/map/district?state=${newState}`);
                if (res.ok) {
                    const data = await res.json();
                    if (e.isFromClick) data.isFromClick = true;
                    setBoundaryGeoJSON(data); // Render Districts

                    // Extract District Names for Dropdown
                    const dists = data.features.map(f =>
                        f.properties.DISTRICT || f.properties.DIST_NAME || f.properties.dtname || f.properties.District
                    ).filter(Boolean);
                    setDistrictsList([...new Set(dists)].sort());
                } else {
                    console.warn("District fetch failed, reverting to state");
                    // Fallback to State Map if district fetch fails
                    const stateRes = await fetch(baseUrl + '/map/state');
                    if (stateRes.ok) setBoundaryGeoJSON(await stateRes.json());
                }
            } catch (e) {
                console.error("District load error", e);
                // Fallback
                try {
                    const stateRes = await fetch(baseUrl + '/map/state');
                    if (stateRes.ok) setBoundaryGeoJSON(await stateRes.json());
                } catch (err) { }
            } finally {
                setLoading(false);
            }
        } else {
            // Reset to State Map
            const res = await fetch(baseUrl + '/map/state');
            if (res.ok) setBoundaryGeoJSON(await res.json());
        }
    };

    // 3. Handle District Change -> Load Sub-Districts
    const handleDistrictChange = async (e) => {
        if (lockedLocation) return;
        const newDistrict = e.target.value;
        setFormData({ ...formData, district: newDistrict, subDistrict: '' });

        setSelectedDistrict(newDistrict);
        setSelectedSubDistrict("");
        setSubDistrictsList([]);

        if (newDistrict && formData.state) {
            try {
                setLoading(true);
                const res = await fetch(`${baseUrl}/map/subdistrict?state=${formData.state}&district=${newDistrict}`);
                if (res.ok) {
                    const data = await res.json();
                    if (e.isFromClick) data.isFromClick = true;
                    setBoundaryGeoJSON(data); // Render all Sub-Districts initially
                    setFullSubDistrictData(data); // Store for later filtering

                    // Extract Sub-District Names for Dropdown
                    const subs = data.features.map(f =>
                        f.properties.TEHSIL || f.properties.TEHSIL_NAM || f.properties.sub_dist || f.properties.District
                    ).filter(Boolean);
                    setSubDistrictsList([...new Set(subs)].sort());

                    // Clear district selection highlight because we are now showing sub-districts
                    // Use selectedSubDistrict for highlighting specific tehsils
                    setSelectedDistrict("");
                }
            } catch (e) {
                console.error("Sub-district load error", e);
                // Fallback? Keep district view or revert?
                // Ideally stick to district view but we might have lost it if we tried to replace.
                // Re-fetch district map to be safe
                const distRes = await fetch(`${baseUrl}/map/district?state=${formData.state}`);
                if (distRes.ok) setBoundaryGeoJSON(await distRes.json());
            } finally {
                setLoading(false);
            }
        }
    };

    // 4. Handle Sub-District Change -> Filter & Zoom
    const handleSubDistrictChange = (e) => {
        if (lockedLocation) return;
        const newSub = e.target.value;
        setFormData({ ...formData, subDistrict: newSub });
        setSelectedSubDistrict(newSub);

        // Filter valid data to just this sub-district and update map to force zoom
        if (newSub && fullSubDistrictData) {
            const feature = fullSubDistrictData.features.find(f => {
                const props = f.properties;
                const name = props.TEHSIL || props.TEHSIL_NAM || props.sub_dist || props.District;
                return name === newSub;
            });

            if (feature) {
                // Pass ONLY this feature to map -> map detects new data -> auto zooms
                const filteredData = {
                    type: "FeatureCollection",
                    features: [feature]
                };
                if (e.isFromClick) filteredData.isFromClick = true;
                setBoundaryGeoJSON(filteredData);
            }
        } else if (!newSub && fullSubDistrictData) {
            // Restore full view if cleared
            setBoundaryGeoJSON(fullSubDistrictData);
        }
    };

    // Reset View Logic
    const handleResetView = async () => {
        if (lockedLocation) {
            setFormData(prev => ({
                ...prev,
                n: '', p: '', k: '', ph: '', moisture: '', organic_carbon: '', temperature: ''
            }));
            setPoints([]);
            setActivePointId(null);
            setError(null);
            setFieldErrors({});
            return;
        }

        setLoading(true);
        try {
            // Reset form fields
            setFormData(prev => ({
                ...prev,
                state: '',
                district: '',
                subDistrict: '',
                n: '', p: '', k: '', ph: '', moisture: '', organic_carbon: '', temperature: '', stage: '', points: ''
            }));

            // Reset UI state
            setSelectedDistrict("");
            setSelectedSubDistrict("");
            setDistrictsList([]);
            setSubDistrictsList([]);
            setFullSubDistrictData(null);
            setPoints([]);
            setActivePointId(null);
            setError(null);
            setFieldErrors({});

            // Re-fetch initial state map
            const res = await fetch(baseUrl + '/map/state');
            if (res.ok) {
                const data = await res.json();
                setBoundaryGeoJSON(data);
            }
        } catch (e) {
            console.error("Reset view failed:", e);
            setError("Failed to reset map view.");
        } finally {
            setLoading(false);
        }
    };

    // Map Interaction: Click Logic
    const handleMapRegionClick = (regionName) => {
        if (lockedLocation) return;
        // Logic to determine if we clicked a State, District, or Sub-District
        // If we have no state selected, we probably clicked a state? (Not supported yet per requirements, assume State is selected via dropdown or we are in State View)

        // Case 1: In State View (District List Empty) -> Clicked State? 
        if (!formData.state) {
            // If we had logic to map RegionName -> State Code, we would trigger handleStateChange
            // For now, prompt implies: "Click... Trigger correct drill-down".
            // We'll try to find if valid state.
            const states = ["Punjab", "Haryana", "Uttar Pradesh"]; // Hardcoded for simplified check
            const matchedState = states.find(s => s.toLowerCase() === regionName.toLowerCase());
            if (matchedState) {
                // Mark that this state change is coming from a map click
                handleStateChange({ target: { value: matchedState }, isFromClick: true });
            }
            return;
        }

        // Case 2: In District View (SubDistrict List Empty) -> Clicked District
        if (formData.state && (!subDistrictsList || subDistrictsList.length === 0)) {
            if (districtsList.includes(regionName)) {
                handleDistrictChange({ target: { value: regionName }, isFromClick: true });
            }
            return;
        }

        // Case 3: In Sub-District View -> Clicked Sub-District
        if (formData.district && subDistrictsList.length > 0) {
            if (subDistrictsList.includes(regionName)) {
                handleSubDistrictChange({ target: { value: regionName }, isFromClick: true });
            }
        }
    };

    // Check if the current active point has all required soil parameters filled
    const isCurrentPointFilled = () => {
        if (!activePointId) return true; // No active point, allow freely
        const activePoint = points.find(p => p.id === activePointId);
        if (!activePoint) return true;
        const { n, p, k, ph, moisture, organic_carbon, temperature } = activePoint.data;
        return [n, p, k, ph, moisture, organic_carbon, temperature].every(
            v => v !== '' && v !== null && v !== undefined
        );
    };

    // Handle Map Click to Add Points
    const handleMapClick = (latlng) => {
        // Stop adding points if an analysis has already been performed
        if (isAnalyzingMultiple || points.some(pt => pt.analysisResult != null)) {
            return;
        }

        // Block adding a new point if the current active point isn't filled yet
        if (!isCurrentPointFilled()) {
            setError('⚠️ Please fill in all soil parameters for the current point before adding a new one.');
            return;
        }

        setError(null);
        const newPoint = {
            id: Date.now(),
            lat: latlng.lat,
            lng: latlng.lng,
            data: { n: '', p: '', k: '', ph: '', moisture: '', organic_carbon: '', temperature: '' },
            analysisResult: null
        };
        setPoints(prev => [...prev, newPoint]);
        setActivePointId(newPoint.id);
        
        // Reset form for the new point
        setFormData(prev => ({
            ...prev,
            n: '', p: '', k: '', ph: '', moisture: '', organic_carbon: '', temperature: ''
        }));
    };

    // Handle Selecting an Existing Point
    const handlePointSelect = (id) => {
        // If switching away from an unfilled point, warn the user
        if (id !== activePointId && !isCurrentPointFilled()) {
            setError('⚠️ Please fill in all soil parameters for the current active point before switching.');
            return;
        }
        setError(null);
        setActivePointId(id);
        const pt = points.find(p => p.id === id);
        if (pt) {
            setFormData(prev => ({ ...prev, ...pt.data }));
            setFieldErrors({}); // Reset errors for new context
        }
    };

    // Input changes map back to the active point
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
        
        if (activePointId && ['n','p','k','ph','moisture','organic_carbon','temperature'].includes(name)) {
            setPoints(prev => prev.map(pt => 
                pt.id === activePointId 
                    ? { ...pt, data: { ...pt.data, [name]: value }, analysisResult: null }
                    : pt
            ));
        } else if (name === 'stage') {
            // If they change the global growth stage, wipe all results so they must re-analyze
            setPoints(prev => prev.map(pt => ({ ...pt, analysisResult: null })));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (points.length === 0) {
            setError("Please select at least one point on the map.");
            return;
        }

        if (!formData.stage) {
            setError("Please select a growth stage (Germination, Booting, or Ripening).");
            return;
        }

        // Validate all points
        const activeRules = getActiveRules();
        let hasErrors = false;
        
        for (const pt of points) {
            Object.keys(activeRules).forEach(key => {
                const rule = activeRules[key];
                const val = parseFloat(pt.data[key]);
                if (pt.data[key] && (val < rule.min || val > rule.max)) {
                    hasErrors = true;
                }
                if (!pt.data[key]) hasErrors = true; // Required fields
            });
        }

        if (hasErrors) {
            setError("Some points have missing or invalid soil data. Please click each point on the map and verify the inputs.");
            return;
        }

        setIsAnalyzingMultiple(true);
        setError(null);
        setFieldErrors({});

        try {
            // Process all points concurrently
            const promises = points.map(async (pt) => {
                const payload = {
                    farmer_name: farmerProfile?.full_name || formData.name || "Unknown Farmer",
                    farmer_id: farmerProfile?.id || null,
                    field_id: formData.fieldId || "F-001",
                    state: formData.state || "Unknown",
                    district: formData.district || "Unknown",
                    sub_district: formData.subDistrict || "Unknown",
                    nitrogen: parseFloat(pt.data.n) || 0.0,
                    phosphorus: parseFloat(pt.data.p) || 0.0,
                    potassium: parseFloat(pt.data.k) || 0.0,
                    ph: parseFloat(pt.data.ph) || 7.0,
                    moisture: parseFloat(pt.data.moisture) || 0.0,
                    organic_carbon: parseFloat(pt.data.organic_carbon) || 0.0,
                    temperature: parseFloat(pt.data.temperature) || 0.0,
                    selected_stage: formData.stage,
                    coordinates: [pt.lat, pt.lng]
                };

                const res = await fetch(baseUrl + '/analyze/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!res.ok) throw new Error(`Analysis failed for point ${pt.id}`);
                const data = await res.json();
                return { id: pt.id, result: data };
            });

            const results = await Promise.all(promises);

            // Update points with their results
            setPoints(prev => prev.map(pt => {
                const found = results.find(r => r.id === pt.id);
                return found ? { ...pt, analysisResult: found.result } : pt;
            }));

        } catch (err) {
            console.error("API Error:", err);
            setError("Unable to analyze all points. Please check backend connection.");
        } finally {
            setIsAnalyzingMultiple(false);
        }
    };

    return (
        <div className="h-screen flex flex-col bg-gray-50 font-sans overflow-hidden">
            {/* Header */}
            <header className="py-3 bg-white shadow-sm border-b border-gray-200 z-20">
                <div className="container mx-auto px-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-xl font-bold text-gray-800 tracking-tight">
                            Field Details
                        </h1>
                    </div>
                    <div className="flex items-center gap-4">
                        {/* Download CSV Button */}
                        {farmerProfile?.id && (
                            <a
                                href={`${baseUrl}/farmers/${farmerProfile.id}/results/download?stage=${formData.stage || 'germination'}`}
                                download={`my_soil_results_${formData.stage || 'germination'}.csv`}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-700 hover:bg-green-800 text-white text-xs font-bold rounded-lg shadow transition-all hover:scale-105 active:scale-95"
                                title="Download your past soil analysis results as CSV"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                Download History
                            </a>
                        )}
                        {/* Farmer Profile Badge */}
                        <div className="flex items-center gap-3">
                        <div className="text-right">
                            <p className="text-sm font-semibold text-gray-800">
                                {farmerProfile?.full_name || 'Farmer'}
                            </p>
                            {farmerProfile?.mobile_number && (
                                <p className="text-xs text-gray-500 font-mono">ID: {farmerProfile.mobile_number}</p>
                            )}
                        </div>
                        <div className="w-8 h-8 rounded-full bg-green-100 border-2 border-green-300 flex items-center justify-center text-green-700 font-bold text-sm">
                            {farmerProfile?.full_name ? farmerProfile.full_name.charAt(0).toUpperCase() : 'F'}
                        </div>
                    </div>
                    </div>
                </div>
            </header>

            {/* Split Layout */}
            <div className="flex-grow flex flex-col lg:flex-row overflow-hidden">

                {/* LEFT: Map Section (60%) */}
                <div className="w-full lg:w-[60%] h-[40vh] lg:h-full relative bg-gray-200 order-1 lg:order-1">
                    <FarmerMap
                        boundaryGeoJSON={boundaryGeoJSON}
                        points={points}
                        activePointId={activePointId}
                        onMapClick={handleMapClick}
                        onPointSelect={handlePointSelect}
                        onRegionSelect={handleMapRegionClick}
                        activeRegion={formData.subDistrict || formData.district || formData.state}
                        activeStage={formData.stage}
                    />

                    {/* Reset View Button */}
                    <button
                        onClick={handleResetView}
                        className="absolute bottom-4 right-4 z-[1000] px-5 py-2.5 bg-white/95 border border-slate-200 rounded-xl shadow-xl text-sm font-bold text-slate-700 hover:bg-slate-50 flex items-center gap-2.5 transition-all hover:scale-105 active:scale-95 group"
                        title="Reset map to national view"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 text-green-600 transition-transform group-hover:rotate-180 duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        RESET VIEW
                    </button>
                </div>

                {/* RIGHT: Form Section (40%) */}
                <div className="w-full lg:w-[40%] h-full overflow-y-auto bg-white shadow-xl z-10 order-2 lg:order-2 flex flex-col">
                    <div className="flex-grow p-6 md:p-8">
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-gray-800">Field & Soil Details</h2>
                            <p className="text-gray-500 text-sm mt-1">
                                Enter your field data or select locations on the map.
                            </p>
                            {error && (
                                <div className="mt-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
                                    {error}
                                </div>
                            )}
                        </div>


                        <form onSubmit={handleSubmit} className="space-y-6">

                            {/* Section A: Field Information */}
                            <div>
                                <h3 className="text-sm font-semibold text-green-800 uppercase tracking-wide border-b border-green-100 pb-2 mb-4">
                                    A. Field Information
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                                        <select
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${lockedLocation ? 'bg-gray-100 text-gray-500 cursor-not-allowed border-gray-200' : 'bg-white border-gray-300'}`}
                                            name="state"
                                            value={formData.state}
                                            onChange={handleStateChange}
                                            disabled={lockedLocation}
                                            required
                                        >
                                            <option value="">Select State</option>
                                            {lockedLocation && formData.state && !["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"].includes(formData.state) ? (
                                                <option value={formData.state}>{formData.state}</option>
                                            ) : null}
                                            {[
                                                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                                                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                                                "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                                                "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                                                "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                                                "Uttar Pradesh", "Uttarakhand", "West Bengal",
                                                "Andaman and Nicobar Islands", "Chandigarh",
                                                "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
                                                "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
                                            ].sort().map(s => (
                                                <option key={s} value={s}>{s}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">District</label>
                                        <select
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${lockedLocation ? 'bg-gray-100 text-gray-500 cursor-not-allowed border-gray-200' : 'bg-white border-gray-300'}`}
                                            name="district"
                                            value={formData.district}
                                            onChange={handleDistrictChange}
                                            disabled={lockedLocation || !formData.state}
                                            required
                                        >
                                            <option value="">Select District</option>
                                            {districtsList.map(dist => (
                                                <option key={dist} value={dist}>{dist}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Sub-District / Tehsil</label>
                                        <select
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${lockedLocation ? 'bg-gray-100 text-gray-500 cursor-not-allowed border-gray-200' : 'bg-white border-gray-300'}`}
                                            name="subDistrict"
                                            value={selectedSubDistrict}
                                            onChange={handleSubDistrictChange}
                                            disabled={lockedLocation || !formData.district}
                                        >
                                            <option value="">Select Sub-District</option>
                                            {subDistrictsList.map(sub => (
                                                <option key={sub} value={sub}>{sub}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Growth Stage</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Model Selector</span>
                                        </div>
                                        <select
                                            name="stage"
                                            value={formData.stage}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-green-500 focus:border-green-500 bg-white"
                                            required
                                        >
                                            <option value="">Select Stage</option>
                                            <option value="germination">Germination Stage</option>
                                            <option value="booting">Booting Stage</option>
                                            <option value="ripening">Ripening Stage</option>
                                        </select>
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Active Point (Lat, Lon)</label>
                                            <span className="text-[10px] font-bold text-gray-500 bg-gray-100 px-1.5 rounded-full border border-gray-200">Point {activePointId ? activePointId : 'None'}</span>
                                        </div>
                                        <input
                                            type="text"
                                            value={activePointId ? `${points.find(p => p.id === activePointId)?.lat.toFixed(5)}, ${points.find(p => p.id === activePointId)?.lng.toFixed(5)}` : ''}
                                            readOnly
                                            className="w-full px-3 py-2 border border-gray-300 rounded bg-gray-50 text-gray-600"
                                            placeholder="Click on map to add point"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Section B: Soil Parameters */}
                            <div>
                                <h3 className="text-sm font-semibold text-green-800 uppercase tracking-wide border-b border-green-100 pb-2 mb-4">
                                    B. Soil Parameters
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Nitrogen (N)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: {getActiveRules().n.min} - {getActiveRules().n.max}</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="n"
                                            value={formData.n}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.n ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder={`mg/kg (${getActiveRules().n.min} - ${getActiveRules().n.max})`}
                                            required
                                        />
                                        {fieldErrors.n && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.n}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Phosphorus (P)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: {getActiveRules().p.min} - {getActiveRules().p.max}</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="p"
                                            value={formData.p}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.p ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder={`mg/kg (${getActiveRules().p.min} - ${getActiveRules().p.max})`}
                                            required
                                        />
                                        {fieldErrors.p && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.p}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Potassium (K)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: {getActiveRules().k.min} - {getActiveRules().k.max}</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="k"
                                            value={formData.k}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.k ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder={`mg/kg (${getActiveRules().k.min} - ${getActiveRules().k.max})`}
                                            required
                                        />
                                        {fieldErrors.k && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.k}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">pH Level</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: {getActiveRules().ph.min} - {getActiveRules().ph.max}</span>
                                        </div>
                                        <input
                                            type="number"
                                            step="0.1"
                                            name="ph"
                                            value={formData.ph}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.ph ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder={`e.g. 6.5 (${getActiveRules().ph.min} - ${getActiveRules().ph.max})`}
                                            required
                                        />
                                        {fieldErrors.ph && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.ph}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Moisture (%)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: {getActiveRules().moisture.min} - {getActiveRules().moisture.max}</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="moisture"
                                            value={formData.moisture}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.moisture ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder={`% (${getActiveRules().moisture.min} - ${getActiveRules().moisture.max})`}
                                            required
                                        />
                                        {fieldErrors.moisture && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.moisture}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Organic Carbon (%)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: {getActiveRules().organic_carbon.min} - {getActiveRules().organic_carbon.max}</span>
                                        </div>
                                        <input
                                            type="number"
                                            step="0.01"
                                            name="organic_carbon"
                                            value={formData.organic_carbon}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.organic_carbon ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder={`% (${getActiveRules().organic_carbon.min} - ${getActiveRules().organic_carbon.max})`}
                                            required
                                        />
                                        {fieldErrors.organic_carbon && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.organic_carbon}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Temperature (°C)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: {getActiveRules().temperature.min} - {getActiveRules().temperature.max}</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="temperature"
                                            value={formData.temperature}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.temperature ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder={`°C (${getActiveRules().temperature.min} - ${getActiveRules().temperature.max})`}
                                        />
                                        {fieldErrors.temperature && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.temperature}</p>}
                                    </div>
                                </div>
                            </div>

                            {/* Action Bar */}
                            <div className="pt-6 border-t border-gray-100 space-y-3">
                                <button
                                    type="submit"
                                    disabled={loading || isAnalyzingMultiple}
                                    className={`w-full text-white font-bold py-4 px-6 rounded-lg text-lg shadow-md transition-colors flex items-center justify-center gap-2 ${(loading || isAnalyzingMultiple) ? 'bg-gray-400 cursor-wait' : 'bg-green-800 hover:bg-green-900'
                                        }`}
                                >
                                    {(loading || isAnalyzingMultiple) ? (
                                        <span>Analyzing all points...</span>
                                    ) : (
                                        <>
                                            <span>Analyze All Points ({points.length})</span>
                                        </>
                                    )}
                                </button>
                                
                                {points.some(pt => pt.analysisResult != null) && (
                                    <button
                                        type="button"
                                        onClick={() => navigate(`/farmer/advisory?stage=${formData.stage || 'germination'}`)}
                                        className="w-full text-white font-bold py-4 px-6 rounded-lg text-lg shadow-md transition-colors flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 mt-3"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        Get Advisory
                                    </button>
                                )}
                            </div>

                        </form>
                    </div>

                    {/* Footer inside Scrollable Area */}
                    <div className="bg-gray-50 border-t border-gray-200 py-4 px-6 text-center">
                        <p className="text-xs text-gray-400">
                            © 2024 BhoomiSanket. Government of India.
                        </p>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default FarmerInputForm;
