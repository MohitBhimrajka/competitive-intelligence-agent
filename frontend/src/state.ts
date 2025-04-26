interface AppState {
    companyId: string | null;
    companyDetails: any | null;
    competitors: any[];
    news: any[];
    insights: any[];
    isLoading: {
        dashboard: boolean;
        insights: boolean;
        research: boolean;
        chat: boolean;
    };
    errors: {
        dashboard: string | null;
        insights: string | null;
        research: string | null;
        chat: string | null;
    };
}

class StateManager {
    private state: AppState;
    private subscribers: ((state: AppState) => void)[] = [];

    constructor() {
        this.state = {
            companyId: null,
            companyDetails: null,
            competitors: [],
            news: [],
            insights: [],
            isLoading: {
                dashboard: false,
                insights: false,
                research: false,
                chat: false
            },
            errors: {
                dashboard: null,
                insights: null,
                research: null,
                chat: null
            }
        };
    }

    getState(): AppState {
        return { ...this.state };
    }

    subscribe(callback: (state: AppState) => void): () => void {
        this.subscribers.push(callback);
        return () => {
            this.subscribers = this.subscribers.filter(sub => sub !== callback);
        };
    }

    private notifySubscribers() {
        this.subscribers.forEach(callback => callback(this.getState()));
    }

    // State update methods
    setCompanyId(id: string | null) {
        this.state.companyId = id;
        this.notifySubscribers();
    }

    setCompanyDetails(details: any) {
        this.state.companyDetails = details;
        this.notifySubscribers();
    }

    setCompetitors(competitors: any[]) {
        this.state.competitors = competitors;
        this.notifySubscribers();
    }

    setNews(news: any[]) {
        this.state.news = news;
        this.notifySubscribers();
    }

    setInsights(insights: any[]) {
        this.state.insights = insights;
        this.notifySubscribers();
    }

    setLoading(key: keyof AppState['isLoading'], value: boolean) {
        this.state.isLoading[key] = value;
        this.notifySubscribers();
    }

    setError(key: keyof AppState['errors'], message: string | null) {
        this.state.errors[key] = message;
        this.notifySubscribers();
    }

    resetState() {
        this.state = {
            companyId: null,
            companyDetails: null,
            competitors: [],
            news: [],
            insights: [],
            isLoading: {
                dashboard: false,
                insights: false,
                research: false,
                chat: false
            },
            errors: {
                dashboard: null,
                insights: null,
                research: null,
                chat: null
            }
        };
        this.notifySubscribers();
    }
}

export const stateManager = new StateManager(); 