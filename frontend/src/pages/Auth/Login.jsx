import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Login.css";

import AuthLayout from "../../components/layout/AuthLayout";
import Input from "../../components/common/Input";
import Button from "../../components/common/Button";
import Card from "../../components/common/Card";

import { FcGoogle } from "react-icons/fc";
import { FaApple } from "react-icons/fa";

import {
  TbCalendarCheck,
  TbBellRinging,
  TbPill,
} from "react-icons/tb";

import { loginUser } from "../../services/authService";
import { saveToken } from "../../utils/token";

const LoginIllustration = () => (
  <div className="login-illustration-container">

    <div className="welcome-text">
      <h2>Welcome Back!</h2>
      <p>Let's stay on track with your medications.</p>
    </div>

    <div className="illustration-wrapper">
      <img
        src="/src/assets/images/login-illustration.png"
        alt="Login"
        className="main-ill"
      />
    </div>

    <div className="mini-features">

      <Card className="mini-feature-card">
        <div className="icon-wrapper text-primary-green">
          <TbCalendarCheck size={24}/>
        </div>

        <div className="text-wrapper">
          <h4>Calendar</h4>
          <p>View and manage your medicine schedule.</p>
        </div>
      </Card>

      <Card className="mini-feature-card">
        <div className="icon-wrapper text-primary-green">
          <TbBellRinging size={24}/>
        </div>

        <div className="text-wrapper">
          <h4>Reminder</h4>
          <p>Get timely alerts for your medicines.</p>
        </div>
      </Card>

      <Card className="mini-feature-card">
        <div className="icon-wrapper text-primary-green">
          <TbPill size={24}/>
        </div>

        <div className="text-wrapper">
          <h4>Stay on Track</h4>
          <p>Never miss a dose.</p>
        </div>
      </Card>

    </div>

  </div>
);

export default function Login() {

  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);

  const [rememberMe, setRememberMe] = useState(false);

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleChange = (e) => {

    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });

  };

  const handleSubmit = async (e) => {

    e.preventDefault();

    try {

      setLoading(true);

      const response = await loginUser({

        email: formData.email,

        password: formData.password,

      });

      saveToken(response.access_token);

      localStorage.setItem(
        "user",
        JSON.stringify(response.user)
      );

      alert("Login Successful");

      navigate("/dashboard");

    } catch (error) {

      alert(
        error.response?.data?.detail ||
        "Login Failed"
      );

    } finally {

      setLoading(false);

    }

  };
    return (
    <AuthLayout leftContent={<LoginIllustration />}>
      <Card className="auth-card">

        <div className="auth-header">
          <h1>Login to Your Account</h1>
          <p>Enter your details to continue your health journey.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>

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

          <div className="form-options">

            <label className="remember-me">

              <input
                type="checkbox"
                checked={rememberMe}
                onChange={() =>
                  setRememberMe(!rememberMe)
                }
              />

              <span>Remember Me</span>

            </label>

            <a
              href="#"
              className="forgot-password"
            >
              Forgot Password?
            </a>

          </div>

          <Button
            variant="primary"
            className="full-width-btn"
            type="submit"
            disabled={loading}
          >
            {loading ? "Logging In..." : "Login"}
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
          Don't have an account?

          <Link
            to="/register"
            className="auth-link"
          >
            Sign up
          </Link>
        </p>

      </Card>
    </AuthLayout>
  );
}