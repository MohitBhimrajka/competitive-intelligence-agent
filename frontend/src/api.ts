const API_BASE_URL = 'http://localhost:8000/api';

async function handleResponse(response: Response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Unknown error occurred' }));
        throw new Error(error.message || 'Request failed');
    }
    return response.json();
}

export const api = {
    async analyzeCompany(name: string) {
        const response = await fetch(`${API_BASE_URL}/company`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name }),
        });
        return handleResponse(response);
    },

    async getCompanyDetails(companyId: string) {
        const response = await fetch(`${API_BASE_URL}/company/${companyId}`);
        return handleResponse(response);
    },

    async getCompetitors(companyId: string) {
        const response = await fetch(`${API_BASE_URL}/company/${companyId}/competitors`);
        return handleResponse(response);
    },

    async getCompanyNews(companyId: string) {
        const response = await fetch(`${API_BASE_URL}/news/company/${companyId}`);
        return handleResponse(response);
    },

    async getCompanyInsights(companyId: string) {
        const response = await fetch(`${API_BASE_URL}/insights/company/${companyId}`);
        return handleResponse(response);
    },

    async refreshInsights(companyId: string) {
        const response = await fetch(`${API_BASE_URL}/insights/company/${companyId}/refresh`, {
            method: 'POST',
        });
        return handleResponse(response);
    },

    async triggerDeepResearch(competitorId: string) {
        const response = await fetch(`${API_BASE_URL}/competitor/${competitorId}/deep-research`, {
            method: 'POST',
        });
        return handleResponse(response);
    },

    async triggerMultiDeepResearch(competitorIds: string[]) {
        const response = await fetch(`${API_BASE_URL}/competitor/deep-research/multiple`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ competitor_ids: competitorIds }),
        });
        return handleResponse(response);
    },

    async askChat(companyId: string, query: string) {
        const response = await fetch(`${API_BASE_URL}/chat/${companyId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });
        return handleResponse(response);
    },

    getDeepResearchDownloadUrl(competitorId: string): string {
        return `${API_BASE_URL}/competitor/${competitorId}/deep-research/download`;
    },
}; 