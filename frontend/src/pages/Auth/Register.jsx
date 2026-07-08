import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Register.css";

import AuthLayout from "../../components/layout/AuthLayout";
import Input from "../../components/common/Input";
import Button from "../../components/common/Button";
import Card from "../../components/common/Card";

import { FcGoogle } from "react-icons/fc";
import { FaApple } from "react-icons/fa";

import { registerUser } from "../../services/authService";

const RegisterIllustration = () => (
  <div className="register-illustration-container">

    <div className="welcome-text">
      <h2>
        Take Control of
        <br />
        <span className="text-primary-green">
          Your Health Today
        </span>
      </h2>

      <p>
        Join PillSync and never miss a dose.
        Smarter reminders, better health
        for you and your loved ones.
      </p>
    </div>

    <div className="register-content-wrapper">
      <img
        src="/src/assets/images/register-family.png"
        className="register-main-img"
        alt="Family"
      />
    </div>

    <img
      src="/src/assets/images/leaf-bottom.png"
      className="leaf-decor reg-leaf"
      alt=""
    />

    <img
      src="/src/assets/images/leaf-top.png"
      className="leaf-decor reg-leaf-top"
      alt=""
    />

  </div>
);

export default function Register() {

  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);

  const [role, setRole] = useState("patient");

  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    phone: "",
  });

  const handleChange = (e) => {

    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });

  };

  const handleSubmit = async (e) => {

    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {

      alert("Passwords do not match");

      return;

    }

    try {

      setLoading(true);

      const response = await registerUser({

        full_name: formData.fullName,

        email: formData.email,

        phone: formData.phone,

        password: formData.password,

        confirm_password: formData.confirmPassword,

        role: role,

      });

      alert(response.message);

      navigate("/login");

    } catch (error) {

      alert(
        error.response?.data?.detail ||
        "Registration Failed"
      );

    } finally {

      setLoading(false);

    }

  };
   return (
    <AuthLayout leftContent={<RegisterIllustration />}>
      <Card className="auth-card reg-card">

        <div className="auth-header">
          <h1>Create Your Account</h1>
          <p>Start your journey to better health.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>

          <Input
            label="Full Name"
            name="fullName"
            placeholder="John Doe"
            value={formData.fullName}
            onChange={handleChange}
            required
          />

          <Input
            label="Email Address"
            name="email"
            type="email"
            placeholder="john@example.com"
            value={formData.email}
            onChange={handleChange}
            required
          />

          <Input
            label="Password"
            name="password"
            type="password"
            placeholder="••••••••"
            value={formData.password}
            onChange={handleChange}
            required
          />

          <Input
            label="Confirm Password"
            name="confirmPassword"
            type="password"
            placeholder="••••••••"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
          />

          <Input
            label="Phone Number (Optional)"
            name="phone"
            type="tel"
            placeholder="+91 9876543210"
            value={formData.phone}
            onChange={handleChange}
          />

          <div className="role-selection">

            <label className="role-label">
              Select Role
              <span> (You can change it later)</span>
            </label>

            <div className="role-cards">

              <div
                className={`role-card ${
                  role === "patient" ? "selected" : ""
                }`}
                onClick={() => setRole("patient")}
              >
                <div className="role-icon">👤</div>

                <div className="role-text">
                  <h5>Patient</h5>
                  <p>I am managing my health</p>
                </div>

              </div>

              <div
                className={`role-card ${
                  role === "caregiver" ? "selected" : ""
                }`}
                onClick={() => setRole("caregiver")}
              >
                <div className="role-icon">👨‍⚕️</div>

                <div className="role-text">
                  <h5>Caregiver</h5>
                  <p>I manage someone else's medicines</p>
                </div>

              </div>

            </div>

          </div>

          <Button
            type="submit"
            variant="primary"
            className="full-width-btn"
            disabled={loading}
          >
            {loading ? "Creating Account..." : "Create Account"}
          </Button>

        </form>

        <div className="divider">
          <span>or</span>
        </div>

        <div className="social-login">

          <Button
            variant="outline"
            className="social-btn"
            type="button"
          >
            <FcGoogle size={20} />
            <span>Continue with Google</span>
          </Button>

          <Button
            variant="outline"
            className="social-btn dark-btn"
            type="button"
          >
            <FaApple size={20} />
            <span>Continue with Apple</span>
          </Button>

        </div>

        <p className="auth-bottom-text">
          Already have an account?

          <Link
            to="/login"
            className="auth-link"
          >
            Log in
          </Link>
        </p>

      </Card>
    </AuthLayout>
  );
}