export const formatIndianCurrency = (value: number): string => {
    if (value === undefined || value === null) return '';
    
    const val = Math.abs(value);
    if (val >= 10000000) {
        return `₹${(val / 10000000).toFixed(2)} Cr`;
    } else if (val >= 100000) {
        return `₹${(val / 100000).toFixed(2)} L`;
    } else if (val >= 1000) {
        return `₹${(val / 1000).toFixed(1)} K`;
    }
    return `₹${val.toFixed(0)}`;
};

export const formatIndianCurrencyInput = (value: number): string => {
    if (!value) return '';
    const val = Math.abs(value);
    if (val >= 10000000) {
        return `${(val / 10000000).toFixed(2)} Crores`;
    } else if (val >= 100000) {
        return `${(val / 100000).toFixed(2)} Lakhs`;
    } else if (val >= 1000) {
        return `${(val / 1000).toFixed(1)} Thousand`;
    }
    return `${val}`;
};
