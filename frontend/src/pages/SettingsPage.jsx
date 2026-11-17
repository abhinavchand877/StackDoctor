import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { systemAPI } from '../services/api';
import {
  User,
  Mail,
  Calendar,
  LogOut,
  ShieldCheck,
  Server,
  Database,
  CheckCircle2,
} from 'lucide-react';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [systemHealth, setSystemHealth] = useState(null);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await systemAPI.health();
      setSystemHealth(res.data);
    } catch {
      setSystemHealth({ status: 'unreachable', database: 'disconnected' });
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings &amp; Profile</h1>
          <p className="page-subtitle">Manage user account details and system connectivity</p>
        </div>
      </div>

      <div style={{ maxWidth: '700px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* User Profile Card */}
        <div className="card">
          <h2 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '16px', color: '#0f172a' }}>
            User Profile
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <User size={18} />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Username</div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>{user?.username}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Mail size={18} />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Email Address</div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>{user?.email}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Calendar size={18} />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Member Since</div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Active Member'}
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
            <button onClick={handleLogout} className="btn btn-danger">
              <LogOut size={16} />
              Sign Out of Account
            </button>
          </div>
        </div>

        {/* System & Architecture Status Card */}
        <div className="card">
          <h2 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '16px', color: '#0f172a' }}>
            Backend Service Status
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Server size={18} color="#2563eb" />
                <span style={{ fontSize: '14px', fontWeight: 600 }}>Flask REST API</span>
              </div>
              <span className={`badge ${systemHealth?.status === 'ok' ? 'badge-passed' : 'badge-failed'}`}>
                {systemHealth?.status === 'ok' ? 'Online' : 'Unreachable'}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Database size={18} color="#0284c7" />
                <span style={{ fontSize: '14px', fontWeight: 600 }}>Database Connectivity</span>
              </div>
              <span className={`badge ${systemHealth?.database?.includes('healthy') || systemHealth?.database === 'connected' ? 'badge-passed' : 'badge-warning'}`}>
                {systemHealth?.database || 'Checking...'}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={18} color="#16a34a" />
                <span style={{ fontSize: '14px', fontWeight: 600 }}>Static Analysis Engine</span>
              </div>
              <span className="badge badge-passed">Operational</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
