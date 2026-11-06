// Entry point: routes + the data cache. Server data is cached for 5 minutes in the browser (the backend caches the
// gold queries for 10), so moving between pages doesn't refetch what you've already seen.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "./app";
import ActionLedger from "./pages/ActionLedger";
import AndonBoard from "./pages/AndonBoard";
import ForemanPage from "./pages/ForemanPage";
import HealthPage from "./pages/HealthPage";
import ImpactWeb from "./pages/ImpactWeb";
import PlantExplorer from "./pages/PlantExplorer";
import "./styles.css";

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 300_000, retry: 1, refetchOnWindowFocus: false } } });

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<AndonBoard />} />
            <Route path="explorer" element={<PlantExplorer />} />
            <Route path="impact" element={<ImpactWeb />} />
            <Route path="foreman" element={<ForemanPage />} />
            <Route path="ledger" element={<ActionLedger />} />
            <Route path="health" element={<HealthPage />} />
            <Route path="*" element={<AndonBoard />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
