/**
 * Shared color logic for Soil Health Score (SHS) visualization.
 * Spreads colors across realistic ranges for Germination, Booting, and Ripening.
 */
export const getShsColor = (stage, score) => {
    if (score === null || score === undefined || score === '') return '#f3f4f6';
    const v = Number(score);
    if (isNaN(v)) return '#f3f4f6';

    const stageKey = stage?.toLowerCase() || '';

    if (stageKey === 'germination' || stageKey === 'shs_germination') {
        if (v >= 78) return '#1a9850'; // Dark Green  – Excellent
        if (v >= 77) return '#66bd63'; // Green       – Very Good
        if (v >= 76) return '#a6d96a'; // Light Green – Good
        if (v >= 75) return '#fee08b'; // Yellow      – Moderate
        if (v >= 74) return '#fdae61'; // Orange      – Poor
        return '#d73027';              // Red         – Very Poor
    } 
    
    if (stageKey === 'booting' || stageKey === 'shs_booting') {
        if (v >= 84.6) return '#1a9850';
        if (v >= 84.4) return '#66bd63';
        if (v >= 84.2) return '#a6d96a';
        if (v >= 84.0) return '#fee08b';
        if (v >= 83.8) return '#fdae61';
        return '#d73027';
    } 
    
    if (stageKey === 'ripening' || stageKey === 'shs_ripening') {
        if (v >= 78.5) return '#1a9850';
        if (v >= 78.0) return '#66bd63';
        if (v >= 77.5) return '#a6d96a';
        if (v >= 77.0) return '#fee08b';
        if (v >= 76.5) return '#fdae61';
        return '#d73027';
    }

    // Default fallback for other attributes or unknown stages
    if (v >= 80) return '#1a9850';
    if (v >= 72) return '#66bd63';
    if (v >= 64) return '#a6d96a';
    if (v >= 55) return '#fee08b';
    if (v >= 40) return '#fdae61';
    return '#d73027';
};

export const getSuitabilityCategory = (stage, score) => {
    if (score === null || score === undefined) return 'N/A';
    const v = Number(score);
    const stageKey = stage?.toLowerCase() || '';

    if (stageKey === 'booting') {
        if (v >= 84.6) return "Excellent";
        if (v >= 84.4) return "Very Good";
        if (v >= 84.2) return "Good";
        if (v >= 84.0) return "Moderate";
        if (v >= 83.8) return "Poor";
        return "Very Poor";
    }
    if (stageKey === 'ripening') {
        if (v >= 78.5) return "Excellent";
        if (v >= 78.0) return "Very Good";
        if (v >= 77.5) return "Good";
        if (v >= 77.0) return "Moderate";
        if (v >= 76.5) return "Poor";
        return "Very Poor";
    }
    // Germination default
    if (v >= 78) return "Excellent";
    if (v >= 77) return "Very Good";
    if (v >= 76) return "Good";
    if (v >= 75) return "Moderate";
    if (v >= 74) return "Poor";
    return "Very Poor";
};
