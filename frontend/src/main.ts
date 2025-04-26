import { stateManager } from './state';
import { router } from './router';
import { showView, setLoading, setError, renderCompanyHeader, renderCompetitorSection, renderNewsSection, renderInsightsSection, renderChatSection } from './ui';
import { api } from './api';

// Initialize the application
function init() {
    // Set up form submission handler
    const companyForm = document.getElementById('company-input-form') as HTMLFormElement;
    companyForm.addEventListener('submit', handleCompanySubmit);

    // Set up home link
    const homeLink = document.getElementById('home-link') as HTMLAnchorElement;
    homeLink.addEventListener('click', (e) => {
        e.preventDefault();
        router.navigateTo('#/landing');
    });

    // Initialize router with route handler
    router.initRouter(handleRouteChange);

    // Subscribe to state changes
    stateManager.subscribe(handleStateChange);
}

// Handle company form submission
async function handleCompanySubmit(e: Event) {
    e.preventDefault();
    const input = document.getElementById('company-name-input') as HTMLInputElement;
    const companyName = input.value.trim();

    if (!companyName) return;

    try {
        setLoading('landing-loading', true);
        setError('landing-error', null);

        const response = await api.analyzeCompany(companyName);
        router.navigateTo(`#/dashboard/${response.company_id}`);
    } catch (error) {
        setError('landing-error', error instanceof Error ? error.message : 'Failed to analyze company');
    } finally {
        setLoading('landing-loading', false);
    }
}

// Handle route changes
async function handleRouteChange() {
    const { view, companyId } = router.getCurrentRoute();

    if (view === 'dashboard' && companyId) {
        showView('dashboard-section');
        await loadDashboardData(companyId);
    } else {
        showView('landing-section');
        stateManager.resetState();
    }
}

// Load dashboard data
async function loadDashboardData(companyId: string) {
    try {
        setLoading('dashboard-loading', true);
        setError('dashboard-error', null);

        // First, get company details and show welcome message
        const companyDetails = await api.getCompanyDetails(companyId);
        stateManager.setCompanyDetails(companyDetails);
        setLoading('dashboard-loading', false, 'Loading competitors...');

        // Then get and show competitors
        const competitors = await api.getCompetitors(companyId);
        stateManager.setCompetitors(competitors);
        setLoading('dashboard-loading', false, 'Loading news...');

        // Then get and show news
        const news = await api.getCompanyNews(companyId);
        stateManager.setNews(news);
        setLoading('dashboard-loading', false, 'Loading insights...');

        // Finally get and show insights
        const insights = await api.getCompanyInsights(companyId);
        stateManager.setInsights(insights);
        setLoading('dashboard-loading', false);

    } catch (error) {
        setError('dashboard-error', error instanceof Error ? error.message : 'Failed to load dashboard data');
        setLoading('dashboard-loading', false);
    }
}

// Handle state changes
function handleStateChange(state: any) {
    const { companyId, companyDetails, competitors, news, insights } = state;

    if (companyDetails) {
        renderCompanyHeader(companyDetails);
    }
    if (competitors.length > 0 && companyId) {
        renderCompetitorSection(competitors, companyId);
    }
    if (news.length > 0) {
        renderNewsSection(news);
    }
    if (insights.length > 0 && companyId) {
        renderInsightsSection(insights, companyId);
    }
    if (companyId) {
        renderChatSection(companyId);
    }
}

// Start the application
init(); 