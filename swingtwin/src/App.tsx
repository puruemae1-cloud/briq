import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "@/components/Shell";
import { Landing } from "@/components/Landing";
import { CompareStudio } from "@/components/CompareStudio";
import { Library } from "@/components/Library";
import { Coaching } from "@/components/Coaching";
import { Progress } from "@/components/Progress";
import { Subscribe } from "@/components/Subscribe";
import { Privacy } from "@/pages/Privacy";

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/compare" element={<CompareStudio />} />
        <Route path="/library" element={<Library />} />
        <Route path="/coaching" element={<Coaching />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/subscribe" element={<Subscribe />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
  );
}
