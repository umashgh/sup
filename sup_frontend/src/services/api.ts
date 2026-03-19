import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a response interceptor to handle 401 errors
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response && error.response.status === 401) {
            // Token is invalid or expired
            localStorage.removeItem('token');
            delete api.defaults.headers.common['Authorization'];
            // We could trigger a re-login here or let the component handle it
            // For now, we just clear it so the next check fails and retries login
        }
        return Promise.reject(error);
    }
);

export const setAuthToken = (token: string) => {
    if (token) {
        api.defaults.headers.common['Authorization'] = `Token ${token}`;
        localStorage.setItem('token', token);
    } else {
        delete api.defaults.headers.common['Authorization'];
        localStorage.removeItem('token');
    }
};

export const guestLogin = async () => {
    const response = await api.post('/auth/guest-login/');
    setAuthToken(response.data.token);
    return response.data;
};

export const fetchFamilyProfile = async () => {
    const response = await api.get('/finance/profile/');
    return response.data;
};

export const updateFamilyProfile = async (id: number, data: any) => {
    const response = await api.patch(`/finance/profile/${id}/`, data);
    return response.data;
};

export const fetchProjection = async (austerity: boolean = false, emergencyMonths: number = 6) => {
    const response = await api.get('/finance/profile/project/', {
        params: {
            austerity,
            emergency_months: emergencyMonths
        }
    });
    return response.data;
};

export const fetchFamilyMembers = async () => {
    const response = await api.get('/finance/members/');
    return response.data;
};

export const addFamilyMember = async (data: any) => {
    const response = await api.post('/finance/members/', data);
    return response.data;
};

export const deleteFamilyMember = async (id: number) => {
    await api.delete(`/finance/members/${id}/`);
};

export const calculateDefaults = async (id: number) => {
    const response = await api.post(`/finance/profile/${id}/calculate_defaults/`);
    return response.data;
};

// Add more API calls as needed

export default api;
