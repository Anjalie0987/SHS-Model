
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FarmerMap from '../../components/map/FarmerMap';
import { STATE_DATA, INDIA_CENTER, DEFAULT_ZOOM } from '../../data/geoBounds';
import { getSuitabilityCategory, getShsColor } from '../../utils/colorUtils';

const baseUrl = process.env.REACT_APP_API_BASE_URL;

const VALIDATION_RULES = {
    n: { min: 100, max: 400, label: "Nitrogen" },
    p: { min: 5, max: 35, label: "Phosphorus" },
    k: { min: 150, max: 590, label: "Potassium" },
    ph: { min: 5.7, max: 8.5, label: "pH Level" },
    moisture: { min: 10, max: 40, label: "Moisture" },
    organic_carbon: { min: 0.2, max: 1.0, label: "Organic Carbon" },
    temperature: { min: 14, max: 30, label: "Temperature" }
};

const FarmerInputForm = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [markerPos, setMarkerPos] = useState(null);
    const [boundaryGeoJSON, setBoundaryGeoJSON] = useState(null);

    // State management for sync
    const [districtsList, setDistrictsList] = useState([]);
    const [subDistrictsList, setSubDistrictsList] = useState([]);
    const [selectedDistrict, setSelectedDistrict] = useState("");
    const [selectedSubDistrict, setSelectedSubDistrict] = useState("");

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
        stage: ''
    });

    const [analysisResult, setAnalysisResult] = useState(null);
    const [fieldErrors, setFieldErrors] = useState({});
    const [activeStage, setActiveStage] = useState('germination');

    // --- Map Logic ---

    // 1. Initial Load: Fetch State Boundaries
    React.useEffect(() => {
        const loadInitialMap = async () => {
            try {
                const res = await fetch(baseUrl + '/map/state');
                if (!res.ok) throw new Error("Backend not reachable");
                const data = await res.json();
                setBoundaryGeoJSON(data);
            } catch (e) {
                console.error("Initial map load failed:", e);
                setError("Map Service Unavailable. Please start the backend.");
            }
        };
        loadInitialMap();
    }, []);

    // 2. Handle State Change -> Load Districts
    const handleStateChange = async (e) => {
        const newState = e.target.value;
        setFormData({ ...formData, state: newState, district: '', subDistrict: '' });

        // Reset Lower Levels
        setSelectedDistrict("");
        setSelectedSubDistrict("");
        setDistrictsList([]);
        setSubDistrictsList([]);
        setFullSubDistrictData(null); // Clear stored sub-district data

        if (newState) {
            setAnalysisResult(null); // Clear previous results
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

    // Map Interaction: Click Logic
    const handleMapRegionClick = (regionName) => {
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

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });

        // Real-time validation
        if (VALIDATION_RULES[name]) {
            const rule = VALIDATION_RULES[name];
            const numVal = parseFloat(value);
            if (value && (numVal < rule.min || numVal > rule.max)) {
                setFieldErrors(prev => ({
                    ...prev,
                    [name]: `Value out of range (${rule.min}-${rule.max})`
                }));
            } else {
                setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors[name];
                    return newErrors;
                });
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setAnalysisResult(null); // Clear previous results to show a fresh state
        setLoading(true);
        setError(null);

        // Prepare payload
        const payload = {
            farmer_name: formData.name || "Unknown Farmer",
            field_id: formData.fieldId || "F-001",
            state: formData.state || "Unknown",
            district: formData.district || "Unknown",
            sub_district: formData.subDistrict || "Unknown",
            nitrogen: parseFloat(formData.n) || 0.0,
            phosphorus: parseFloat(formData.p) || 0.0,
            potassium: parseFloat(formData.k) || 0.0,
            ph: parseFloat(formData.ph) || 7.0,
            moisture: parseFloat(formData.moisture) || 0.0,
            organic_carbon: parseFloat(formData.organic_carbon) || 0.0,
            temperature: parseFloat(formData.temperature) || 0.0,
            selected_stage: formData.stage,
            coordinates: markerPos ? [markerPos.lat, markerPos.lng] : null
        };

        // Final validation before submission
        const errors = {};
        Object.keys(VALIDATION_RULES).forEach(key => {
            const rule = VALIDATION_RULES[key];
            const val = parseFloat(formData[key]);
            if (formData[key] && (val < rule.min || val > rule.max)) {
                errors[key] = `Value out of range (${rule.min}-${rule.max})`;
            }
        });

        if (Object.keys(errors).length > 0) {
            setFieldErrors(errors);
            setError("Some fields have values outside the recommended range.");
            return;
        }

        if (!formData.stage) {
            setError("Please select a growth stage (Germination, Booting, or Ripening).");
            return;
        }

        try {
            // Mock API call or real endpoint
            console.log("Submitting payload:", payload);

            // POST to Backend Analysis API
            const res = await fetch(baseUrl + '/analyze/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Analysis failed");

            const data = await res.json();
            setAnalysisResult(data);
            
            // Do NOT navigate automatically. Let the user see the result on the map.
            // console.log("Analysis Result saved to state:", data);

        } catch (err) {
            console.error("API Error:", err);
            setError("Unable to analyze soil data. Please check backend connection.");
        } finally {
            setLoading(false);
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
                    <div className="text-sm text-gray-600">
                        Welcome, Farmer
                    </div>
                </div>
            </header>

            {/* Split Layout */}
            <div className="flex-grow flex flex-col lg:flex-row overflow-hidden">

                {/* LEFT: Map Section (60%) */}
                <div className="w-full lg:w-[60%] h-[40vh] lg:h-full relative bg-gray-200 order-1 lg:order-1">
                    <FarmerMap
                        boundaryGeoJSON={boundaryGeoJSON}
                        onLocationSelect={setMarkerPos}
                        onRegionSelect={handleMapRegionClick}
                        analysisResult={analysisResult}
                        activeRegion={formData.subDistrict || formData.district || formData.state}
                        activeStage={formData.stage}
                    />
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

                        {analysisResult && (
                            <div className="mb-8 p-6 bg-green-50 rounded-xl border border-green-100 shadow-sm animate-in fade-in slide-in-from-top-4 duration-500">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-lg font-bold text-green-900">Analysis Results</h3>
                                    <span className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-bold uppercase rounded">Live</span>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="flex justify-between items-end">
                                        <div>
                                            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">{formData.stage} Score</p>
                                            <p className="text-2xl font-black text-green-800">
                                                {formData.stage === 'germination' ? analysisResult.germ_shs.toFixed(1) : 
                                                 formData.stage === 'booting' ? analysisResult.boot_shs.toFixed(1) : 
                                                 analysisResult.rip_shs.toFixed(1)}%
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Suitability</p>
                                            <p className="text-sm font-bold truncate" style={{ 
                                                color: getShsColor(formData.stage, 
                                                    formData.stage === 'germination' ? analysisResult.germ_shs : 
                                                    formData.stage === 'booting' ? analysisResult.boot_shs : 
                                                    analysisResult.rip_shs) 
                                            }}>
                                                {getSuitabilityCategory(formData.stage, 
                                                    formData.stage === 'germination' ? analysisResult.germ_shs : 
                                                    formData.stage === 'booting' ? analysisResult.boot_shs : 
                                                    analysisResult.rip_shs)}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="pt-3 border-t border-green-100 italic text-[10px] text-gray-500">
                                        Note: This result is specifically calculated for the {formData.stage} growth stage.
                                    </div>
                                </div>

                                <div className="mt-6 flex gap-3">
                                    <button 
                                        onClick={() => navigate('/germination-suitability', { state: { district: formData.district } })}
                                        className="flex-grow py-2 px-3 bg-white border border-green-200 text-green-700 text-xs font-bold rounded-lg hover:bg-green-100 transition-colors shadow-sm"
                                    >
                                        View Regional Map
                                    </button>
                                    <button 
                                        onClick={() => {
                                            setAnalysisResult(null);
                                            setFormData({...formData, n: '', p: '', k: '', ph: '', moisture: '', organic_carbon: '', temperature: ''});
                                        }}
                                        className="py-2 px-3 bg-gray-100 text-gray-600 text-xs font-bold rounded-lg hover:bg-gray-200 transition-colors"
                                    >
                                        Reset
                                    </button>
                                </div>
                            </div>
                        )}

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
                                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-green-500 focus:border-green-500 bg-white"
                                            name="state"
                                            value={formData.state}
                                            onChange={handleStateChange}
                                            required
                                        >
                                            <option value="">Select State</option>
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
                                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-green-500 focus:border-green-500 bg-white"
                                            name="district"
                                            value={formData.district}
                                            onChange={handleDistrictChange}
                                            disabled={!formData.state}
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
                                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-green-500 focus:border-green-500 bg-white"
                                            name="subDistrict"
                                            value={selectedSubDistrict}
                                            onChange={handleSubDistrictChange}
                                            disabled={!formData.district}
                                        >
                                            <option value="">Select Sub-District</option>
                                            {subDistrictsList.map(sub => (
                                                <option key={sub} value={sub}>{sub}</option>
                                            ))}
                                        </select>
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
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: 100 - 400</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="n"
                                            value={formData.n}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.n ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder="mg/kg (100 - 400)"
                                            required
                                        />
                                        {fieldErrors.n && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.n}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Phosphorus (P)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: 5 - 35</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="p"
                                            value={formData.p}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.p ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder="mg/kg (5 - 35)"
                                            required
                                        />
                                        {fieldErrors.p && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.p}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Potassium (K)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: 150 - 590</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="k"
                                            value={formData.k}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.k ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder="mg/kg (150 - 590)"
                                            required
                                        />
                                        {fieldErrors.k && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.k}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">pH Level</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: 5.7 - 8.5</span>
                                        </div>
                                        <input
                                            type="number"
                                            step="0.1"
                                            name="ph"
                                            value={formData.ph}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.ph ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder="e.g. 6.5 (5.7 - 8.5)"
                                            required
                                        />
                                        {fieldErrors.ph && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.ph}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Moisture (%)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: 10 - 40</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="moisture"
                                            value={formData.moisture}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.moisture ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder="% (10 - 40)"
                                            required
                                        />
                                        {fieldErrors.moisture && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.moisture}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Organic Carbon (%)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: 0.2 - 1.0</span>
                                        </div>
                                        <input
                                            type="number"
                                            step="0.01"
                                            name="organic_carbon"
                                            value={formData.organic_carbon}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.organic_carbon ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder="% (0.2 - 1.0)"
                                            required
                                        />
                                        {fieldErrors.organic_carbon && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.organic_carbon}</p>}
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <label className="block text-sm font-medium text-gray-700">Temperature (°C)</label>
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-1.5 rounded-full border border-green-100">Range: 14 - 30</span>
                                        </div>
                                        <input
                                            type="number"
                                            name="temperature"
                                            value={formData.temperature}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded focus:ring-green-500 focus:border-green-500 ${fieldErrors.temperature ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                            placeholder="°C (14 - 30)"
                                        />
                                        {fieldErrors.temperature && <p className="text-[10px] text-red-600 mt-1 font-bold">{fieldErrors.temperature}</p>}
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
                                            <option value="germination">Germination model</option>
                                            <option value="booting">Booting model</option>
                                            <option value="ripening">Ripening model</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Action Bar */}
                            <div className="pt-6 border-t border-gray-100">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className={`w-full text-white font-bold py-4 px-6 rounded-lg text-lg shadow-md transition-colors flex items-center justify-center gap-2 ${loading ? 'bg-gray-400 cursor-wait' : 'bg-green-800 hover:bg-green-900'
                                        }`}
                                >
                                    {loading ? (
                                        <span>Analyzing soil data...</span>
                                    ) : (
                                        <>
                                            <span>Analyze Soil Suitability Score</span>
                                        </>
                                    )}
                                </button>
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

