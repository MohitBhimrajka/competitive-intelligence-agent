import { configureStore, createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';

// Define types for the app state
export interface CompanyDetails {
  id: string;
  name: string;
  industry: string;
  description: string;
  website?: string;
  founded?: string;
  headquarters?: string;
  employeeCount?: number;
  revenue?: string;
}

export interface Competitor {
  id: string;
  name: string;
  industry: string;
  description?: string;
  website?: string;
  relationshipStrength?: number; // 0-100 score
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  date: string;
  url: string;
  summary: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  companyIds: string[]; // which companies are mentioned
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  date: string;
  category: 'market' | 'competitor' | 'product' | 'strategy' | 'other';
  severity: 'low' | 'medium' | 'high';
  relatedCompanyIds: string[];
}

export interface LoadingState {
  companyDetails: boolean;
  competitors: boolean;
  news: boolean;
  insights: boolean;
}

// Define the main App State interface
export interface AppState {
  companyId: string | null;
  companyDetails: CompanyDetails | null;
  competitors: Competitor[];
  news: NewsItem[];
  insights: Insight[];
  loading: LoadingState;
  error: string | null;
}

// Initial state
const initialState: AppState = {
  companyId: null,
  companyDetails: null,
  competitors: [],
  news: [],
  insights: [],
  loading: {
    companyDetails: false,
    competitors: false,
    news: false,
    insights: false,
  },
  error: null,
};

// Create async thunk for fetching company data
export const fetchCompanyData = createAsyncThunk(
  'app/fetchCompanyData',
  async (id: string, { rejectWithValue }) => {
    try {
      // Here you would make API calls to fetch data
      // Example implementation - replace with actual API calls
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock data - replace with actual API calls
      const companyDetails: CompanyDetails = {
        id,
        name: 'Example Company',
        industry: 'Technology',
        description: 'Example company description',
      };
      
      const competitors: Competitor[] = [
        { id: '1', name: 'Competitor 1', industry: 'Technology', relationshipStrength: 75 },
        { id: '2', name: 'Competitor 2', industry: 'Technology', relationshipStrength: 60 },
      ];
      
      const news: NewsItem[] = [
        { 
          id: '1', 
          title: 'Example News', 
          source: 'Tech Daily', 
          date: new Date().toISOString(), 
          url: 'https://example.com', 
          summary: 'Example news summary',
          sentiment: 'positive',
          companyIds: [id, '1']
        },
      ];
      
      const insights: Insight[] = [
        {
          id: '1',
          title: 'Market Opportunity',
          description: 'Example insight description',
          date: new Date().toISOString(),
          category: 'market',
          severity: 'medium',
          relatedCompanyIds: [id]
        },
      ];
      
      return { companyDetails, competitors, news, insights };
    } catch (error) {
      return rejectWithValue((error as Error).message);
    }
  }
);

// Create the app slice
const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setCompanyId: (state, action: PayloadAction<string>) => {
      state.companyId = action.payload;
    },
    clearData: (state) => {
      state.companyDetails = null;
      state.competitors = [];
      state.news = [];
      state.insights = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Handle fetchCompanyData
      .addCase(fetchCompanyData.pending, (state) => {
        state.loading = {
          companyDetails: true,
          competitors: true,
          news: true,
          insights: true,
        };
        state.error = null;
      })
      .addCase(fetchCompanyData.fulfilled, (state, action) => {
        state.loading = {
          companyDetails: false,
          competitors: false,
          news: false,
          insights: false,
        };
        state.companyDetails = action.payload.companyDetails;
        state.competitors = action.payload.competitors;
        state.news = action.payload.news;
        state.insights = action.payload.insights;
      })
      .addCase(fetchCompanyData.rejected, (state, action) => {
        state.loading = {
          companyDetails: false,
          competitors: false,
          news: false,
          insights: false,
        };
        state.error = action.payload as string;
      });
  },
});

// Configure persistence
const persistConfig = {
  key: 'ci-store',
  storage,
  whitelist: ['companyId', 'companyDetails', 'competitors', 'news', 'insights'], // only persist these fields
};

const persistedReducer = persistReducer(persistConfig, appSlice.reducer);

// Configure the store
export const store = configureStore({
  reducer: {
    app: persistedReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

export const persistor = persistStore(store);

// Export actions
export const { setCompanyId, clearData } = appSlice.actions;

// Define types for hooks
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector; 