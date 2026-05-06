import React from 'react';
import Header from '../components/Header';

const Contact = () => {
    return (
        <div className="flex flex-col min-h-screen bg-slate-50 text-slate-900 font-sans">
            <Header />

            <main className="flex-grow">
                {/* Hero Section */}
                <section className="bg-brand-dark text-white py-16">
                    <div className="container mx-auto px-6 text-center">
                        <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">Contact Us</h1>
                        <p className="text-lg md:text-xl text-emerald-100 max-w-2xl mx-auto font-medium">
                            Reach out to us for official communication and support.
                        </p>
                    </div>
                </section>

                {/* Organization Header Section */}
                <section className="pt-16 pb-8">
                    <div className="container mx-auto px-6 text-center">
                        <h2 className="text-xs md:text-sm uppercase tracking-[0.3em] text-brand-primary font-bold mb-4">
                            Official Organization
                        </h2>
                        <h3 className="text-3xl md:text-4xl font-extrabold text-slate-900 max-w-3xl mx-auto leading-tight">
                            Centre for Development of Advanced Computing
                        </h3>
                    </div>
                </section>

                {/* Contact Cards Section */}
                <section className="py-12">
                    <div className="container mx-auto px-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">

                            {/* Address Card */}
                            <div className="bg-white p-8 rounded-3xl shadow-xl border border-slate-100 flex flex-col items-center text-center transition-all hover:shadow-2xl hover:-translate-y-1">
                                <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 mb-6">
                                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                    </svg>
                                </div>
                                <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-3">Address</h4>
                                <p className="text-slate-700 font-semibold leading-relaxed">
                                    B-30, Institutional Area, Phase 2<br />
                                    Industrial Area, Sector 62<br />
                                    Noida, Uttar Pradesh – 201309<br />
                                    India
                                </p>
                            </div>

                            {/* Phone Card */}
                            <div className="bg-white p-8 rounded-3xl shadow-xl border border-slate-100 flex flex-col items-center text-center transition-all hover:shadow-2xl hover:-translate-y-1">
                                <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 mb-6">
                                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                    </svg>
                                </div>
                                <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-3">Phone</h4>
                                <p className="text-xl font-bold text-slate-800">
                                    +91-120-3063200
                                </p>
                            </div>

                            {/* Email Card */}
                            <div className="bg-white p-8 rounded-3xl shadow-xl border border-slate-100 flex flex-col items-center text-center transition-all hover:shadow-2xl hover:-translate-y-1">
                                <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 mb-6">
                                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-3">Email</h4>
                                <p className="text-xl font-bold text-slate-800">
                                    contact-noida@cdac.in
                                </p>
                            </div>

                        </div>
                    </div>
                </section>

                {/* Map Section */}
                <section className="pt-8 pb-24">
                    <div className="container mx-auto px-6 text-center">
                        <div className="max-w-6xl mx-auto rounded-3xl overflow-hidden shadow-2xl h-[450px] border-8 border-white">
                            <iframe
                                title="C-DAC Noida Location"
                                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3502.4034293043!2d77.35928667613567!3d28.61767667567119!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x390ce544f84f7089%3A0xe549303d779e549a!2sC-DAC!5e0!3m2!1sen!2sin!4v1713250000000!5m2!1sen!2sin"
                                width="100%"
                                height="100%"
                                style={{ border: 0 }}
                                allowFullScreen=""
                                loading="lazy"
                                referrerPolicy="no-referrer-when-downgrade"
                            ></iframe>
                        </div>
                    </div>
                </section>
            </main>

            {/* Simple Footer Section */}
            <footer className="bg-slate-900 text-white py-12">
                <div className="container mx-auto px-6 text-center">
                    <p className="text-slate-500 text-sm">
                        &copy; 2026 Soil Health Intelligence Platform. All rights reserved.
                    </p>
                </div>
            </footer>
        </div>
    );
};

export default Contact;
