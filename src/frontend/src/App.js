import { BrowserRouter, Routes, Route } from 'react-router-dom';
import CourseRecommender from "./components/CourseRecommender";

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<CourseRecommender/>}/>
            </Routes>
        </BrowserRouter>
    );
}
