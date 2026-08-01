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

import {
  loginUser,
  requestForgotPasswordOTP,
  verifyForgotPasswordOTP,
  resetPasswordWithOTP,
  googleLogin,
  appleLogin,
} from "../../services/authService";
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

  // Forgot Password Workflow state
  const [isForgotMode, setIsForgotMode] = useState(false);
  const [forgotStep, setForgotStep] = useState(1);
  const [forgotData, setForgotData] = useState({
    email: "",
    otp: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [forgotMsg, setForgotMsg] = useState({ type: "", text: "" });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleForgotChange = (e) => {
    setForgotData({
      ...forgotData,
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

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      const email = prompt("Enter your Google Account email address:", "user@google.com");
      if (!email) {
        setLoading(false);
        return;
      }
      const response = await googleLogin({
        email: email,
        full_name: email.split("@")[0],
        provider: "google"
      });

      saveToken(response.access_token);
      localStorage.setItem("user", JSON.stringify(response.user));
      alert("Google Sign-In Successful");
      navigate("/dashboard");
    } catch (error) {
      alert(error.response?.data?.detail || "Google Sign-In Failed");
    } finally {
      setLoading(false);
    }
  };

  const handleAppleSignIn = async () => {
    try {
      setLoading(true);
      const email = prompt("Enter your Apple ID email address:", "user@icloud.com");
      if (!email) {
        setLoading(false);
        return;
      }
      const response = await appleLogin({
        email: email,
        full_name: email.split("@")[0],
        provider: "apple"
      });

      saveToken(response.access_token);
      localStorage.setItem("user", JSON.stringify(response.user));
      alert("Apple Sign-In Successful");
      navigate("/dashboard");
    } catch (error) {
      alert(error.response?.data?.detail || "Apple Sign-In Failed");
    } finally {
      setLoading(false);
    }
  };

  // Forgot Password Steps
  const handleRequestOTP = async (e) => {
    e.preventDefault();
    if (!forgotData.email.trim()) {
      setForgotMsg({ type: "error", text: "Please enter your email address." });
      return;
    }
    try {
      setLoading(true);
      setForgotMsg({ type: "", text: "" });
      const res = await requestForgotPasswordOTP(forgotData.email.trim());
      setForgotMsg({ type: "success", text: res.message });
      setForgotStep(2);
    } catch (err) {
      setForgotMsg({
        type: "error",
        text: err.response?.data?.detail || "Failed to send OTP.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!forgotData.otp.trim()) {
      setForgotMsg({ type: "error", text: "Please enter the 6-digit OTP." });
      return;
    }
    try {
      setLoading(true);
      setForgotMsg({ type: "", text: "" });
      const res = await verifyForgotPasswordOTP(forgotData.email.trim(), forgotData.otp.trim());
      setForgotMsg({ type: "success", text: res.message });
      setForgotStep(3);
    } catch (err) {
      setForgotMsg({
        type: "error",
        text: err.response?.data?.detail || "Invalid OTP code.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (forgotData.newPassword !== forgotData.confirmPassword) {
      setForgotMsg({ type: "error", text: "Passwords do not match." });
      return;
    }
    try {
      setLoading(true);
      setForgotMsg({ type: "", text: "" });
      const res = await resetPasswordWithOTP({
        email: forgotData.email.trim(),
        otp: forgotData.otp.trim(),
        new_password: forgotData.newPassword,
        confirm_password: forgotData.confirmPassword,
      });
      alert(res.message);
      setIsForgotMode(false);
      setForgotStep(1);
      setForgotData({ email: "", otp: "", newPassword: "", confirmPassword: "" });
      setForgotMsg({ type: "", text: "" });
    } catch (err) {
      setForgotMsg({
        type: "error",
        text: err.response?.data?.detail || "Failed to reset password.",
      });
    } finally {
      setLoading(false);
    }
  };

  const resetForgotState = () => {
    setIsForgotMode(false);
    setForgotStep(1);
    setForgotMsg({ type: "", text: "" });
  };

  return (
    <AuthLayout leftContent={<LoginIllustration />}>
      <Card className="auth-card">

        {isForgotMode ? (
          <div>
            <div className="auth-header">
              <h1>Forgot Password</h1>
              <p>
                {forgotStep === 1 && "Enter your email to receive a 6-digit OTP."}
                {forgotStep === 2 && "Enter the 6-digit OTP sent to your email."}
                {forgotStep === 3 && "Set your new account password."}
              </p>
            </div>

            {forgotMsg.text && (
              <div style={{
                marginBottom: "16px",
                padding: "12px 16px",
                borderRadius: "8px",
                fontSize: "14px",
                backgroundColor: forgotMsg.type === "success" ? "#E6FFFA" : "#FFF5F5",
                color: forgotMsg.type === "success" ? "#2F855A" : "#C53030",
                border: forgotMsg.type === "success" ? "1px solid #C6F6D5" : "1px solid #FED7D7"
              }}>
                {forgotMsg.text}
              </div>
            )}

            {forgotStep === 1 && (
              <form onSubmit={handleRequestOTP} className="auth-form">
                <Input
                  label="Email Address"
                  name="email"
                  type="email"
                  placeholder="john@example.com"
                  value={forgotData.email}
                  onChange={handleForgotChange}
                  required
                />
                <Button variant="primary" className="full-width-btn" type="submit" disabled={loading}>
                  {loading ? "Sending OTP..." : "Send OTP"}
                </Button>
              </form>
            )}

            {forgotStep === 2 && (
              <form onSubmit={handleVerifyOTP} className="auth-form">
                <Input
                  label="6-Digit OTP"
                  name="otp"
                  type="text"
                  placeholder="123456"
                  maxLength={6}
                  value={forgotData.otp}
                  onChange={handleForgotChange}
                  required
                />
                <Button variant="primary" className="full-width-btn" type="submit" disabled={loading}>
                  {loading ? "Verifying..." : "Verify OTP"}
                </Button>
              </form>
            )}

            {forgotStep === 3 && (
              <form onSubmit={handleResetPassword} className="auth-form">
                <Input
                  label="New Password"
                  name="newPassword"
                  type="password"
                  placeholder="••••••••"
                  value={forgotData.newPassword}
                  onChange={handleForgotChange}
                  required
                />
                <Input
                  label="Confirm New Password"
                  name="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={forgotData.confirmPassword}
                  onChange={handleForgotChange}
                  required
                />
                <Button variant="primary" className="full-width-btn" type="submit" disabled={loading}>
                  {loading ? "Resetting..." : "Set New Password"}
                </Button>
              </form>
            )}

            <p className="auth-bottom-text">
              <a href="#" className="auth-link" onClick={(e) => { e.preventDefault(); resetForgotState(); }}>
                Back to Login
              </a>
            </p>
          </div>
        ) : (
          <>
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
                  onClick={(e) => {
                    e.preventDefault();
                    setIsForgotMode(true);
                    setForgotStep(1);
                    setForgotMsg({ type: "", text: "" });
                  }}
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
                onClick={handleGoogleSignIn}
                disabled={loading}
              >
                <FcGoogle size={20} />
                <span>Continue with Google</span>
              </Button>

              <Button
                variant="outline"
                className="social-btn dark-btn"
                type="button"
                onClick={handleAppleSignIn}
                disabled={loading}
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
          </>
        )}

      </Card>
    </AuthLayout>
  );
}