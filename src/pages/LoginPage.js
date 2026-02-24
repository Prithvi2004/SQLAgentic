import React from 'react';
import LoginForm from '../components/LoginForm';
import './LoginPage.css';

const LoginPage = () => {
  const handleLogin = (loginData) => {
    console.log('Login attempt:', loginData);
    // Here you would typically make an API call to authenticate the user
    alert(`Login successful for: ${loginData.email}`);
  };

  return (
    <div className="login-page">
      <LoginForm onLogin={handleLogin} />
    </div>
  );
};

export default LoginPage;