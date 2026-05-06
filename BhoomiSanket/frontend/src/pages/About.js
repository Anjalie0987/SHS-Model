import React from 'react';
import Header from '../components/Header';

const stageData = [
    {
        title: 'Germination Stage',
        description: 'Focus on seed emergence and early growth. The model evaluates initial soil conditions that support healthy seedling development.',
        ranges: [
            { label: 'Nitrogen (N)', value: '100 – 400' },
            { label: 'Phosphorus (P)', value: '5 – 35' },
            { label: 'Potassium (K)', value: '150 – 590' },
            { label: 'Soil pH', value: '5.5 – 8.5' },
            { label: 'Moisture', value: '10 – 25%' },
            { label: 'Organic Carbon', value: '0.2 – 1%' },
            { label: 'Temperature', value: '14 – 28°C' },
        ],
        note: 'NDVI is excluded because canopy has not yet developed.',
    },
    {
        title: 'Booting Stage',
        description: 'Canopy development and nutrient demand increase. The model incorporates remote sensing insights for more refined crop support.',
        ranges: [
            { label: 'Nitrogen (N)', value: '100 – 400' },
            { label: 'Phosphorus (P)', value: '5 – 35' },
            { label: 'Potassium (K)', value: '150 – 590' },
            { label: 'Soil pH', value: '5.5 – 8.5' },
            { label: 'Moisture', value: '10 – 30%' },
            { label: 'Organic Carbon', value: '0.2 – 1%' },
            { label: 'Temperature', value: '15 – 30°C' },
        ],
        note: 'NDVI becomes a key indicator at this stage.',
    },
    {
        title: 'Ripening Stage',
        description: 'Grain filling and yield formation are critical. Temperature dynamics and moisture balance are especially important.',
        ranges: [
            { label: 'Nitrogen (N)', value: '100 – 400' },
            { label: 'Phosphorus (P)', value: '5 – 35' },
            { label: 'Potassium (K)', value: '150 – 590' },
            { label: 'Soil pH', value: '5.5 – 8.5' },
            { label: 'Moisture', value: '15 – 40%' },
            { label: 'Organic Carbon', value: '0.2 – 1%' },
            { label: 'Temperature', value: '18 – 32°C' },
        ],
        note: 'Temperature plays a critical role due to heat stress risks.',
    },
];

const justifiedTextStyle = "text-justify leading-[1.6] tracking-[0.3px] [word-spacing:1px] [hyphens:auto]";

const About = () => {
    return (
        <div className="flex flex-col min-h-screen bg-slate-50 text-slate-900">
            <Header />

            <main className="flex-grow">
                <section className="relative overflow-hidden bg-gradient-to-br from-emerald-700 via-teal-700 to-slate-900 text-white">
                    <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.35),_transparent_50%)]" />
                    <div className="relative max-w-7xl mx-auto px-6 py-20 lg:px-12">
                        <div className="max-w-3xl">
                            <p className="text-sm uppercase tracking-[0.24em] text-emerald-200 mb-6">Soil Health Intelligence</p>
                            <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-6 text-left">AI-Enabled Soil Health Intelligence System</h1>
                            <p className="text-lg sm:text-xl text-emerald-100 max-w-2xl leading-relaxed mb-6">
                                A stage-wise, data-driven soil analysis platform designed for wheat cultivation using continuous scoring.
                            </p>
                            <p className="text-base sm:text-lg text-emerald-200 max-w-2xl leading-relaxed">
                                This system combines agricultural science, fuzzy logic, and decision models to generate accurate soil health insights.
                            </p>
                        </div>
                    </div>
                </section>

                <section className="max-w-7xl mx-auto px-6 py-16 lg:px-12">
                    <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr]">
                        <article className="space-y-8">
                            <div className="rounded-3xl bg-white shadow-2xl border border-slate-200 p-10">
                                <h2 className="text-3xl font-semibold text-slate-900 mb-4 text-left">About the Platform</h2>
                                <p className={`text-slate-700 ${justifiedTextStyle} mb-4`}>
                                    The platform evaluates soil health using a stage-wise Soil Health Score (SHS) model specifically designed for wheat cultivation in India. Unlike traditional systems, this model adapts to crop phenology across germination, booting, and ripening stages.
                                </p>
                                <p className={`text-slate-700 ${justifiedTextStyle}`}>
                                    Each stage has different soil requirements, and the system dynamically adjusts its evaluation to reflect nutrient availability, moisture balance, pH, organic carbon, temperature, and remote sensing indicators.
                                </p>
                            </div>

                            <div className="grid gap-6 sm:grid-cols-2">
                                <div className="rounded-3xl bg-emerald-50 border border-emerald-100 p-8">
                                    <h3 className="text-xl font-semibold text-emerald-900 mb-3 text-left">Scientific Foundation</h3>
                                    <ul className="space-y-3 text-slate-700">
                                        <li className="font-semibold text-left text-emerald-900">Fuzzy Logic</li>
                                        <li className={justifiedTextStyle}>Handles gradual changes in soil suitability and avoids rigid thresholds.</li>
                                        <li className="font-semibold text-left text-emerald-900 mt-2">AHP (Analytical Hierarchy Process)</li>
                                        <li className={justifiedTextStyle}>Assigns parameter importance using structured expert-driven weights.</li>
                                        <li className="font-semibold text-left text-emerald-900 mt-2">Continuous Score (0–100)</li>
                                        <li className={justifiedTextStyle}>Delivers precise evaluation without loss of information.</li>
                                    </ul>
                                </div>

                                <div className="rounded-3xl bg-emerald-50 border border-emerald-100 p-8">
                                    <h3 className="text-xl font-semibold text-emerald-900 mb-3 text-left">Core Analysis Parameters</h3>
                                    <p className={`${justifiedTextStyle} text-slate-700 mb-4`}>
                                        The model evaluates soil using scientifically validated parameters that impact crop growth differently across the development cycle.
                                    </p>
                                    <ul className="space-y-2 text-slate-700">
                                        <li>• Nitrogen (N)</li>
                                        <li>• Phosphorus (P)</li>
                                        <li>• Potassium (K)</li>
                                        <li>• Soil pH</li>
                                        <li>• Moisture</li>
                                        <li>• Organic Carbon</li>
                                        <li>• Temperature</li>
                                        <li>• NDVI (for later stages)</li>
                                    </ul>
                                </div>
                            </div>
                        </article>

                        <aside className="space-y-6">
                            <div className="rounded-3xl bg-white shadow-2xl border border-slate-200 p-8">
                                <h3 className="text-2xl font-semibold text-slate-900 mb-4 text-left">Why Continuous Score Model?</h3>
                                <p className={`text-slate-700 ${justifiedTextStyle} mb-5`}>
                                    Generating a continuous Soil Health Score from 0 to 100 gives a more precise view of soil condition than discrete categories. This improves decision support, GIS mapping, and dashboard visualizations.
                                </p>
                                <ul className="space-y-3 text-slate-700">
                                    <li>• More precise than fixed classes</li>
                                    <li>• Reflects gradual changes in soil quality</li>
                                    <li>• Better for spatial analysis and GIS</li>
                                    <li>• Flexible for dynamic dashboards and reporting</li>
                                </ul>
                            </div>

                            <div className="rounded-3xl bg-white shadow-2xl border border-slate-200 p-8">
                                <h3 className="text-2xl font-semibold text-slate-900 mb-4 text-left">GIS & Visualization</h3>
                                <p className={`text-slate-700 ${justifiedTextStyle} mb-4`}>
                                    The platform supports state and district-level mapping, pixel-wise soil analysis, choropleth visualization, and NDVI-supported crop-stage analysis for richer agronomic context.
                                </p>
                                <div className="space-y-3 text-slate-700 text-left">
                                    <p>• State and district-level maps</p>
                                    <p>• Pixel-wise soil health evaluation</p>
                                    <p>• Choropleth visualizations for spatial intelligence</p>
                                    <p>• NDVI-supported crop-stage analysis</p>
                                </div>
                            </div>
                        </aside>
                    </div>
                </section>

                <section className="max-w-7xl mx-auto px-6 py-16 lg:px-12">
                    <div className="space-y-8">
                        <div className="rounded-3xl bg-white shadow-xl border border-slate-200 p-10">
                            <h2 className="text-3xl font-semibold text-slate-900 mb-4 text-left">Stage-wise Analysis with Ranges</h2>
                            <p className={`text-slate-700 ${justifiedTextStyle} max-w-3xl`}>
                                Each wheat growth stage is evaluated with a tailored parameter range that reflects the crop's changing physiology. These ranges are central to the Soil Health Score and support stage-specific recommendations.
                            </p>
                        </div>

                        <div className="grid gap-8 xl:grid-cols-3">
                            {stageData.map((stage) => (
                                <div key={stage.title} className="rounded-3xl bg-white shadow-2xl border border-slate-200 p-8">
                                    <h3 className="text-2xl font-semibold text-slate-900 mb-3 text-left">{stage.title}</h3>
                                    <p className={`text-slate-600 ${justifiedTextStyle} mb-5`}>{stage.description}</p>

                                    <div className="space-y-3 mb-5">
                                        {stage.ranges.map((range) => (
                                            <div key={range.label} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                                                <span className="text-slate-700 font-medium">{range.label}</span>
                                                <span className="text-slate-900 font-semibold">{range.value}</span>
                                            </div>
                                        ))}
                                    </div>

                                    <p className="text-sm text-emerald-700 font-medium">{stage.note}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                <section className="max-w-7xl mx-auto px-6 pb-20 lg:px-12">
                    <div className="rounded-3xl bg-emerald-900 text-white p-10 shadow-2xl border border-emerald-700">
                        <h2 className="text-3xl font-semibold mb-4 text-left">Why This Platform?</h2>
                        <div className="grid gap-6 lg:grid-cols-2">
                            <div className="space-y-4">
                                <p className={`text-slate-100 ${justifiedTextStyle}`}>
                                    Built on established soil health and agronomic research and tailored for India-specific wheat cultivation, this platform combines AI, GIS, and soil science to deliver stage-wise intelligence for better farming decisions.
                                </p>
                                <ul className="space-y-3 text-slate-100 text-left">
                                    <li>• Established soil health and agronomic research basis</li>
                                    <li>• India-specific agronomic model</li>
                                    <li>• Stage-wise soil intelligence</li>
                                    <li>• AI-enabled decision support</li>
                                </ul>
                            </div>
                            <div className="space-y-4">
                                <p className={`text-slate-100 ${justifiedTextStyle}`}>
                                    The design supports translation of soil analysis into actionable insights, enabling scalable and intelligent soil management for modern agriculture.
                                </p>
                                <ul className="space-y-3 text-slate-100">
                                    <li>• Supports soil health improvements</li>
                                    <li>• Supports farm-level and landscape-level planning</li>
                                    <li>• Supports dynamic dashboards and mapping</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="max-w-7xl mx-auto px-6 pb-24 lg:px-12">
                    <div className="rounded-3xl bg-white shadow-2xl border border-slate-200 p-10">
                        <h2 className="text-3xl font-semibold text-slate-900 mb-4 text-left">Research Basis</h2>
                        <p className={`text-slate-700 ${justifiedTextStyle} mb-6`}>
                            The platform is based on established soil health assessment principles, wheat crop-stage requirements, fuzzy logic theory, AHP-based decision modelling, and NDVI-supported crop monitoring.
                        </p>
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            {['Established soil health and agronomic research', 'Soil Health Card framework', 'Fuzzy Logic theory', 'AHP-based decision modelling', 'NDVI-supported crop monitoring', 'Stage-wise crop logic'].map((item) => (
                                <div key={item} className="rounded-3xl bg-slate-50 border border-slate-200 p-5 text-slate-700 text-left h-full">
                                    {item}
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                <section className="bg-slate-900 text-white py-16">
                    <div className="max-w-7xl mx-auto px-6 lg:px-12 text-center">
                        <p className={`text-xl sm:text-2xl font-semibold ${justifiedTextStyle}`}>
                            This platform transforms traditional soil analysis into a data-driven, intelligent, and scalable system for modern agriculture.
                        </p>
                    </div>
                </section>
            </main>
        </div>
    );
};

export default About;
