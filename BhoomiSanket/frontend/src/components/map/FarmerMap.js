import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { INDIA_CENTER, DEFAULT_ZOOM } from '../../data/geoBounds';
import { getShsColor } from '../../utils/colorUtils';

// Fix for default marker icon in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Styles
const STYLES = {
    default: {
        color: "#2e7d32",    // User Req: #2e7d32
        weight: 2,           // User Req: 2
        fillColor: "#81c784", // User Req: #81c784
        fillOpacity: 0.4,    // User Req: 0.4
    },
    hover: {
        weight: 3,           // User Req: 3
        fillOpacity: 0.6,    // User Req: 0.6
        color: "#1b9e20"     // Slightly darker border for hover
    }
};

// Helper component to handle GeoJSON lifecycle & updates
const GeoJsonController = ({ data, onRegionSelect, onMapClick, analysisResult, activeRegion, activeStage }) => {
    const map = useMap();
    const geoJsonLayerRef = useRef(null);

    useEffect(() => {
        if (!data) return;

        // Cleanup previous layer
        if (geoJsonLayerRef.current) {
            map.removeLayer(geoJsonLayerRef.current);
            geoJsonLayerRef.current = null;
        }

        const onEachFeature = (feature, layer) => {
            const props = feature.properties;
            const regionName = (props.TEHSIL || props.TEHSIL_NAM || props.sub_dist ||
                props.DISTRICT || props.DIST_NAME || props.dtname || props.District ||
                props.STATE || props.ST_NAME || props.ST_NM || props.State || 'Region').trim();

            const regionType = props.TEHSIL || props.sub_dist ? 'Sub-district' :
                props.DISTRICT || props.District ? 'District' : 'State';

            // Hover Effects
            layer.on({
                mouseover: (e) => {
                    const l = e.target;
                    l.setStyle(STYLES.hover);
                    l.bringToFront();
                },
                mouseout: (e) => {
                    const l = e.target;
                    if (geoJsonLayerRef.current) {
                        geoJsonLayerRef.current.resetStyle(l);
                    }
                },
                mousemove: (e) => {
                    const { lat, lng } = e.latlng;
                    const isResultRegion = analysisResult && activeRegion && regionName.toUpperCase() === activeRegion.toUpperCase();
                    const score = isResultRegion ? (
                        activeStage === 'germination' ? analysisResult.germ_shs :
                            activeStage === 'booting' ? analysisResult.boot_shs :
                                analysisResult.rip_shs
                    ) : null;

                    let tooltipHtml = `
                        <div class="p-2 min-w-[120px]">
                            <div class="text-[10px] font-bold text-gray-400 uppercase">${regionType}</div>
                            <div class="text-sm font-bold text-gray-800">${regionName}</div>
                    `;

                    tooltipHtml += `
                            <div class="text-[10px] text-gray-500 mt-1 border-t pt-1">
                                Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}
                            </div>
                        </div>
                    `;
                    layer.setTooltipContent(tooltipHtml);
                },
                click: (e) => {
                    if (onMapClick) {
                        onMapClick(e.latlng);
                    }
                    if (onRegionSelect && regionName) {
                        onRegionSelect(regionName);
                    }
                }
            });

            layer.bindTooltip("", {
                sticky: true,
                className: 'custom-map-tooltip',
                direction: 'top',
                offset: [0, -10]
            });
        };

        // Create new layer
        geoJsonLayerRef.current = L.geoJson(data, {
            style: () => {
                return STYLES.default;
            },
            onEachFeature: onEachFeature
        }).addTo(map);

        // Auto-zoom to bounds ONLY if it's the first load or data changed WITHOUT a map click
        const bounds = geoJsonLayerRef.current.getBounds();
        const shouldFitBounds = bounds.isValid() && !data.isFromClick;

        if (shouldFitBounds) {
            map.fitBounds(bounds, {
                padding: [20, 20],
                animate: true,
                duration: 0.6
            });
        }

        // Cleanup on unmount or data change
        return () => {
            if (geoJsonLayerRef.current) {
                map.removeLayer(geoJsonLayerRef.current);
            }
        };
    }, [data, map, onRegionSelect, onMapClick, analysisResult, activeRegion, activeStage]);

    return null;
};

const LocationMarker = ({ point, isActive, onSelect, activeStage }) => {
    const markerRef = useRef(null);

    useEffect(() => {
        if (markerRef.current && isActive) {
            markerRef.current.openPopup();
        }
    }, [isActive, point.analysisResult]);

    if (!point || !point.lat || !point.lng) return null;

    const position = { lat: point.lat, lng: point.lng };
    const score = point.analysisResult ? (
        activeStage === 'germination' ? point.analysisResult.germ_shs :
            activeStage === 'booting' ? point.analysisResult.boot_shs :
                point.analysisResult.rip_shs
    ) : null;

    // Create a true heatmap visual using CSS radial gradients
    const heatColor = point.analysisResult ? getShsColor(activeStage, score) : '#000000';
    
    // Pulse animation ONLY for the active point
    const activeClass = isActive ? "animate-pulse" : "";
    const borderStyle = isActive ? "border: 3px solid #00ff00;" : (point.analysisResult ? "border: none;" : "border: 2px solid #fff;");
    
    const heatmapIcon = L.divIcon({
        className: 'custom-heatmap-icon bg-transparent border-0',
        html: point.analysisResult ? `
            <div style="
                width: 150px;
                height: 150px;
                transform: translate(-50%, -50%);
                border-radius: 50%;
                background: radial-gradient(circle, ${heatColor}dd 0%, ${heatColor}88 30%, ${heatColor}00 70%);
                pointer-events: auto;
                cursor: pointer;
                ${isActive ? 'box-shadow: 0 0 20px 5px rgba(0,255,0,0.5); border: 2px solid #00ff00;' : ''}
            " class="${activeClass}"></div>
        ` : `
            <div style="
                width: 14px;
                height: 14px;
                background-color: #000;
                ${borderStyle}
                border-radius: 50%;
                transform: translate(-50%, -50%);
                pointer-events: auto;
                box-shadow: ${isActive ? '0 0 10px #00ff00' : 'none'};
            "></div>
        `,
        iconSize: [0, 0], // Handled by transform
        iconAnchor: [0, 0], // Center
        popupAnchor: [0, point.analysisResult ? -20 : -10]
    });

    return (
        <Marker
            ref={markerRef}
            position={position}
            icon={heatmapIcon}
            eventHandlers={{
                click: () => onSelect(point.id)
            }}
        >
            <Popup className="coordinates-popup">
                <div className="p-1 min-w-[140px]">
                    <div className="text-[10px] font-bold text-green-700 uppercase tracking-wider mb-2 border-b pb-1 flex justify-between">
                        <span>Point ${point.id}</span>
                        {isActive && <span className="text-blue-600 bg-blue-50 px-1 rounded">Active</span>}
                    </div>
                    {point.analysisResult && score !== null && (
                        <div className="mb-2 bg-green-50 rounded p-2 border border-green-100">
                            <div className="text-[10px] text-green-800 font-bold mb-1 uppercase">{activeStage} SUITABILITY</div>
                            <div className="text-xl font-black" style={{ color: getShsColor(activeStage, score) }}>
                                {score.toFixed(2)}%
                            </div>
                        </div>
                    )}
                    <div className="space-y-1.5">
                        <div className="flex justify-between items-center gap-3">
                            <span className="text-[10px] text-gray-500 font-medium">Lat:</span>
                            <span className="text-xs font-mono font-bold text-gray-800">{position.lat.toFixed(6)}</span>
                        </div>
                        <div className="flex justify-between items-center gap-3">
                            <span className="text-[10px] text-gray-500 font-medium">Lng:</span>
                            <span className="text-xs font-mono font-bold text-gray-800">{position.lng.toFixed(6)}</span>
                        </div>
                    </div>
                    {!point.analysisResult && (
                        <div className="mt-2 text-[9px] text-gray-400 italic">
                            Enter soil data and analyze
                        </div>
                    )}
                </div>
            </Popup>
        </Marker>
    );
};


const FarmerMap = ({ boundaryGeoJSON, points, activePointId, onMapClick, onPointSelect, activeRegion, activeStage }) => {
    // Check if any point has been analyzed to show the legend
    const hasAnyResults = points && points.some(pt => pt.analysisResult != null);

    return (
        <div className="h-full w-full z-0 relative bg-white">
            <style>{`
                .custom-map-tooltip {
                    background: white !important;
                    border: none !important;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
                    border-radius: 8px !important;
                    padding: 0 !important;
                    opacity: 1 !important;
                }
            `}</style>
            <MapContainer
                center={INDIA_CENTER}
                zoom={DEFAULT_ZOOM}
                style={{ height: '100%', width: '100%', background: '#ffffff' }} // White background
                scrollWheelZoom={true}
            >
                {/* No TileLayer - Pure Vector Map */}
                <GeoJsonController
                    data={boundaryGeoJSON}
                    onRegionSelect={() => {}} // No longer coloring region, just map clicks
                    onMapClick={onMapClick}
                    activeRegion={activeRegion}
                    activeStage={activeStage}
                />

                {points && points.map(pt => (
                    <LocationMarker 
                        key={pt.id}
                        point={pt} 
                        isActive={pt.id === activePointId}
                        onSelect={onPointSelect} 
                        activeStage={activeStage} 
                    />
                ))}

                {/* Floating Legend - Only show after at least one analysis */}
                {hasAnyResults && (
                    <div className="absolute bottom-6 left-6 bg-white/95 p-4 rounded-2xl shadow-xl z-[1000] border border-green-100 min-w-[220px] animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <h4 className="text-[13px] font-black text-slate-700 mb-3 tracking-tight border-b border-slate-100 pb-2 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            {activeStage?.toUpperCase()} SUITABILITY
                        </h4>
                        <div className="space-y-2.5">
                            {[
                                { label: 'Excellent', range: activeStage === 'booting' ? '(>84.6%)' : activeStage === 'ripening' ? '(>78.5%)' : '(>78%)', color: '#1a9850' },
                                { label: 'Very Good', range: activeStage === 'booting' ? '(84.4-84.6%)' : activeStage === 'ripening' ? '(78.0-78.5%)' : '(77-78%)', color: '#66bd63' },
                                { label: 'Good', range: activeStage === 'booting' ? '(84.2-84.4%)' : activeStage === 'ripening' ? '(77.5-78.0%)' : '(76-77%)', color: '#a6d96a' },
                                { label: 'Moderate', range: activeStage === 'booting' ? '(84.0-84.2%)' : activeStage === 'ripening' ? '(77.0-77.5%)' : '(75-76%)', color: '#fee08b' },
                                { label: 'Poor', range: activeStage === 'booting' ? '(83.8-84.0%)' : activeStage === 'ripening' ? '(76.5-77.0%)' : '(74-75%)', color: '#fdae61' },
                                { label: 'Very Poor', range: activeStage === 'booting' ? '(<83.8%)' : activeStage === 'ripening' ? '(<76.5%)' : '(<74%)', color: '#d73027' }
                            ].map((item, idx) => (
                                <div key={idx} className="flex items-center gap-3">
                                    <div
                                        className="w-4 h-4 rounded-sm shadow-sm border border-black/5"
                                        style={{ backgroundColor: item.color }}
                                    ></div>
                                    <div className="flex items-baseline gap-1.5">
                                        <span className="text-[12px] font-bold text-slate-600">{item.label}</span>
                                        <span className="text-[10px] text-slate-400 font-medium">{item.range}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Overlay instruction */}
                <div className="absolute top-4 right-4 bg-white/95 p-3 rounded-xl shadow-lg z-[1000] text-[11px] max-w-[220px] border border-green-100">
                    <p className="font-bold text-slate-800 mb-1 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                        Interactive Map
                    </p>
                    <p className="text-slate-500 leading-relaxed font-medium">Click a state or district boundary to select and zoom. Click a point to mark your field coordinates.</p>
                </div>
            </MapContainer>
        </div>
    );
};

export default FarmerMap;

