type RouteHandler = (params: { view: string; companyId?: string }) => void;

class Router {
    private currentRoute: { view: string; companyId?: string } = { view: 'landing' };
    private handler: RouteHandler | null = null;

    constructor() {
        window.addEventListener('hashchange', () => this.handleRouteChange());
    }

    initRouter(handler: RouteHandler) {
        this.handler = handler;
        this.handleRouteChange();
    }

    private handleRouteChange() {
        const hash = window.location.hash.slice(1);
        const [view, companyId] = hash.split('/');
        
        this.currentRoute = {
            view: view || 'landing',
            companyId: companyId || undefined
        };

        if (this.handler) {
            this.handler(this.currentRoute);
        }
    }

    navigateTo(hash: string) {
        window.location.hash = hash;
    }

    getCurrentRoute() {
        return { ...this.currentRoute };
    }
}

export const router = new Router(); 