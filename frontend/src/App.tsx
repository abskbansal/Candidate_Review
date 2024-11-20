import { BrowserRouter, Routes, Route } from "react-router-dom";
import Signup from "./pages/Signup";
import ProfileDetails from "./pages/ProfileDetails";

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/signup" element={<Signup />} />
                <Route path="/profile-details" element={<ProfileDetails />} />
                <Route path="*" element={<Signup />} />
            </Routes>
        </BrowserRouter>
    );
};

export default App;
