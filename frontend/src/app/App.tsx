import { Route, Routes } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { DetailPage } from "../features/detail/DetailPage";
import { GalleryPage } from "../features/gallery/GalleryPage";
import { OverviewPage } from "../features/overview/OverviewPage";
import { RadarPage } from "../features/radar/RadarPage";

export function App() {
  return <AppShell><Routes>
    <Route path="/" element={<OverviewPage />} />
    <Route path="/gallery" element={<GalleryPage />} />
    <Route path="/radar" element={<RadarPage />} />
    <Route path="/samples/:id" element={<DetailPage />} />
  </Routes></AppShell>;
}
