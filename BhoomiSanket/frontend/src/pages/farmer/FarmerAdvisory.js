import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function FarmerAdvisory() {
    const navigate = useNavigate();
    const location = useLocation();
    
    const [advisories, setAdvisories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [farmerProfile, setFarmerProfile] = useState(null);
    const [stage, setStage] = useState('germination');
    
    // Base URL for API
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    useEffect(() => {
        const storedProfile = localStorage.getItem('farmer');
        if (!storedProfile) {
            navigate('/login');
            return;
        }
        const profile = JSON.parse(storedProfile);
        setFarmerProfile(profile);
        
        // Extract stage from URL query params
        const params = new URLSearchParams(location.search);
        const urlStage = params.get('stage') || 'germination';
        setStage(urlStage);
        
        fetchAdvisory(profile.id, urlStage);
    }, [navigate, location.search]);

    const fetchAdvisory = async (farmerId, currentStage) => {
        try {
            setLoading(true);
            const response = await fetch(`${baseUrl}/advisory/${farmerId}?stage=${currentStage}`);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`No advisory data found for the ${currentStage} stage.`);
                }
                throw new Error('Failed to fetch advisory data');
            }
            const data = await response.json();
            setAdvisories(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        if (status === 'Good') return 'bg-green-100 text-green-800 border-green-200';
        if (status === 'Deficient') return 'bg-red-100 text-red-800 border-red-200';
        if (status === 'Excess') return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-gray-100 text-gray-800 border-gray-200';
    };

    const getScoreCategoryColor = (category) => {
        if (category === 'Excellent') return 'bg-green-500';
        if (category === 'Good') return 'bg-emerald-500';
        if (category === 'Moderate') return 'bg-yellow-500';
        if (category === 'Poor') return 'bg-red-500';
        return 'bg-gray-500';
    };

    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <button 
                            onClick={() => navigate('/farmer/form')}
                            className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Soil Health Advisory</h1>
                            <p className="text-sm text-gray-500 capitalize">{stage} Stage Recommendations</p>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-semibold text-gray-800">{farmerProfile?.full_name || 'Farmer'}</p>
                            <p className="text-xs text-gray-500 font-mono">ID: {farmerProfile?.mobile_number}</p>
                        </div>
                        <div className="w-10 h-10 rounded-full bg-green-100 border-2 border-green-300 flex items-center justify-center text-green-700 font-bold text-lg shadow-sm">
                            {farmerProfile?.full_name ? farmerProfile.full_name.charAt(0).toUpperCase() : 'F'}
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64 space-y-4">
                        <div className="w-12 h-12 border-4 border-green-200 border-t-green-600 rounded-full animate-spin"></div>
                        <p className="text-gray-600 font-medium animate-pulse">Generating your personalized advisory...</p>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-r-lg shadow-sm">
                        <div className="flex items-center">
                            <svg className="h-6 w-6 text-red-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <h3 className="text-lg font-medium text-red-800">Cannot load advisory</h3>
                        </div>
                        <p className="mt-2 text-red-700 ml-9">{error}</p>
                        <div className="mt-4 ml-9">
                            <button onClick={() => navigate('/farmer/form')} className="text-red-700 font-semibold hover:text-red-900 underline">
                                Return to Soil Analysis
                            </button>
                        </div>
                    </div>
                ) : advisories.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-100">
                        <p className="text-gray-500 text-lg">No advisory data found. Please run a soil analysis first.</p>
                        <button onClick={() => navigate('/farmer/form')} className="mt-4 px-6 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700">
                            Go to Analysis
                        </button>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {advisories.map((advisory, idx) => (
                            <div key={advisory.point_id} className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200 transition-all hover:shadow-lg">
                                {/* Card Header with Score */}
                                <div className={`${getScoreCategoryColor(advisory.shs_category)} px-6 py-4 flex justify-between items-center text-white`}>
                                    <div>
                                        <h2 className="text-xl font-bold flex items-center gap-2">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                            </svg>
                                            Point {idx + 1}
                                        </h2>
                                        <p className="text-sm opacity-90 mt-1 font-mono">Lat: {advisory.lat.toFixed(5)}, Lon: {advisory.lon.toFixed(5)}</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-extrabold">{advisory.shs_score.toFixed(1)}%</div>
                                        <div className="text-sm font-medium opacity-90">{advisory.shs_category}</div>
                                    </div>
                                </div>

                                {/* Overall Advice Banner */}
                                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex gap-3 items-start">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 text-lg">Overall Recommendation</h3>
                                        <p className="text-gray-700 mt-1">{advisory.overall_advice}</p>
                                    </div>
                                </div>

                                {/* Detailed Parameters Table */}
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-gray-100 text-gray-600 text-sm uppercase tracking-wider">
                                                <th className="px-6 py-3 font-medium">Parameter</th>
                                                <th className="px-6 py-3 font-medium">Current Value</th>
                                                <th className="px-6 py-3 font-medium">Ideal Range</th>
                                                <th className="px-6 py-3 font-medium">Status</th>
                                                <th className="px-6 py-3 font-medium">Action Required</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {advisory.parameters.map((param, pIdx) => (
                                                <tr key={pIdx} className="hover:bg-gray-50 transition-colors">
                                                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                                                        {param.name}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">
                                                        {param.value}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-gray-500 font-mono text-sm">
                                                        {param.ideal_min} - {param.ideal_max}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full border ${getStatusColor(param.status)}`}>
                                                            {param.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-700 max-w-md">
                                                        {param.advice}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
