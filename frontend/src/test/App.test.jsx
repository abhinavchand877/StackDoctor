import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import LandingPage from '../pages/LandingPage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import NewScanPage from '../pages/NewScanPage';
import { AuthProvider } from '../context/AuthContext';

describe('Frontend Component Tests', () => {
  it('renders LandingPage with StackDoctor branding and CTA buttons', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    expect(screen.getAllByText(/StackDoctor/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Automated Software Project Health Analysis/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Safe Static Inspection/i)).toBeInTheDocument();
  });

  it('renders LoginPage with identifier and password inputs', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );
    expect(screen.getByPlaceholderText(/developer@example.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  it('renders RegisterPage with registration form fields', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </BrowserRouter>
    );
    expect(screen.getByPlaceholderText(/johndoe/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/john@example.com/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Get Started/i })).toBeInTheDocument();
  });

  it('renders NewScanPage with required message and upload dropzone', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <NewScanPage />
        </AuthProvider>
      </BrowserRouter>
    );
    expect(screen.getByText(/Upload your project ZIP file and StackDoctor will automatically inspect/i)).toBeInTheDocument();
    expect(screen.getByText(/Drop your project ZIP file here, or browse/i)).toBeInTheDocument();
    expect(screen.getByText(/Python \(Flask, Django, FastAPI\)/i)).toBeInTheDocument();
  });
});
