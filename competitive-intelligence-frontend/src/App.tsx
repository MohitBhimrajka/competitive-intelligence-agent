import * as React from "react";
import {
  ChakraProvider,
  ColorModeScript,          // v2 still has this
} from "@chakra-ui/react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import theme from "./theme";

const LandingPage          = React.lazy(() => import("./pages/LandingPage"));
const AnimatedLoadingPage  = React.lazy(() => import("./pages/AnimatedLoadingPage"));
const CompanyDashboardPage = React.lazy(() => import("./pages/CompanyDashboardPage"));
const NotFoundPage         = React.lazy(() => import("./pages/NotFoundPage"));

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/"                     element={<LandingPage />} />
        <Route path="/loading"              element={<AnimatedLoadingPage />} />
        <Route path="/dashboard/:companyId" element={<CompanyDashboardPage />} />
        <Route path="*"                     element={<NotFoundPage />} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <ChakraProvider theme={theme}>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />

      <Router>
        <React.Suspense
          fallback={<div className="flex h-screen items-center justify-center">Loading…</div>}
        >
          <AnimatedRoutes />
        </React.Suspense>
      </Router>
    </ChakraProvider>
  );
}
