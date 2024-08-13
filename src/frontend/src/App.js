import { BrowserRouter, Routes, Route } from 'react-router-dom';
import CourseRecommender from "./components/CourseRecommender";
import NaturalLanguage from "./components/NaturalLanguage";
import ModuleDetail from "./components/ModuleDetail";

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<CourseRecommender/>}/>
                <Route path="/recommend" element={<NaturalLanguage/>}/>
            </Routes>
        </BrowserRouter>
    );
}
