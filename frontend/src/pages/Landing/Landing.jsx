import React from 'react';
import { Link } from 'react-router-dom';
import './Landing.css';
import Navbar from '../../components/layout/Navbar';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import { TbPill, TbBellRinging, TbChartLine } from 'react-icons/tb';

const Landing = () => {
  return (
    <div className="landing-page">
      <Navbar />
      
      <main className="landing-content">
        <div className="landing-container">
          
          <div className="hero-section">
            <div className="hero-images">
              <img src="/src/assets/images/landing-family.png" alt="Family Healthcare" className="main-image" />
              
              <Card className="floating-card reminder-card">
                <div className="reminder-content">
                  <div className="reminder-icon-box">
                    <TbPill className="icon" />
                  </div>
                  <div className="reminder-details">
                    <span className="label">Next Medicine</span>
                    <span className="medicine-name">Vitamin D</span>
                    <span className="time">Today, 08:00 AM</span>
                  </div>
                  <div className="reminder-status">
                    <TbBellRinging className="icon-bell" />
                    <span>In 30 min</span>
                  </div>
                </div>
              </Card>
              
              <img src="/src/assets/images/leaf-top.png" alt="Decorative leaf" className="leaf-decor leaf-top-left" />
              <img src="/src/assets/images/leaf-bottom.png" alt="Decorative leaf" className="leaf-decor leaf-bottom-right" />
            </div>

            <div className="hero-text">
              <h1 className="hero-heading">
                Simplified Adherence,<br/>
                <span className="highlight-text">for your loved ones.</span>
              </h1>
              
              <p className="hero-description">
                PillSync helps you manage medicines, set smart reminders, and stay on track with AI-powered insights.
              </p>
              
              <div className="feature-list">
                <Card className="feature-item">
                  <div className="feature-icon bg-light-green text-primary-green">
                    <TbPill size={24} />
                  </div>
                  <div className="feature-text">
                    <h3>Manage Medicines</h3>
                    <p>Add, organize and track medicines easily.</p>
                  </div>
                </Card>
                
                <Card className="feature-item">
                  <div className="feature-icon bg-light-green" style={{color: '#8B5CF6'}}>
                    <TbBellRinging size={24} />
                  </div>
                  <div className="feature-text">
                    <h3>Smart Reminders</h3>
                    <p>Get timely alerts and never miss a dose.</p>
                  </div>
                </Card>
                
                <Card className="feature-item">
                  <div className="feature-icon" style={{backgroundColor: '#FFEDD5', color: '#EA580C'}}>
                    <TbChartLine size={24} />
                  </div>
                  <div className="feature-text">
                    <h3>AI Refill Prediction</h3>
                    <p>Never run out of medicines again.</p>
                  </div>
                </Card>
              </div>

              <div className="cta-section">
                <Link to="/register">
                  <Button variant="secondary" className="get-started-btn">
                    Get Started
                  </Button>
                </Link>
                <p className="signup-text">
                  Don't have an account? <Link to="/register" className="signup-link">Sign up</Link>
                </p>
              </div>
            </div>
            
          </div>
        </div>
      </main>
    </div>
  );
};

export default Landing;
