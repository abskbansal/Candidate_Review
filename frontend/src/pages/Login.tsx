import React, { useState } from "react";
import FormInput from "../components/FormInput";
import { Link } from "react-router-dom";

const Login: React.FC = () => {
    const [formData, setFormData] = useState({ email: "", password: "" });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log("Login Data", formData);
    };

    return (
        <div className="flex justify-center items-center h-screen bg-gray-100">
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md w-96">
                <h2 className="text-2xl font-bold text-center mb-6">Login</h2>
                <FormInput label="Email" type="email" name="email" value={formData.email} onChange={handleChange} />
                <FormInput label="Password" type="password" name="password" value={formData.password} onChange={handleChange} />
                <button
                    type="submit"
                    className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 transition"
                >
                    Login
                </button>
                <p className="mt-4 text-sm text-center">
                    Don't have an account? <Link to="/signup" className="text-blue-500 hover:underline">Sign up</Link>
                </p>
            </form>
        </div>
    );
};

export default Login;
