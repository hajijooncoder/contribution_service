import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { DashboardPage } from './components/DashboardPage';
import { ContributionForm } from './components/ContributionForm';
import { ContributionHistory } from './components/ContributionHistory';
import { ReviewerQueue } from './components/ReviewerQueue';
import { AdminPanel } from './components/AdminPanel';
import { LoginModal } from './components/LoginModal';
import { apiClient } from './api/client';
import { UserProfile } from './types';
import { useWebSocket } from './hooks/useWebSocket';
import { Bell, X, CheckCircle, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'submit' | 'history' | 'reviewer' | 'admin'>('dashboard');
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  // Real-time WebSocket connection (Deliverable 5)
  const { latestNotification, clearLatest, isConnected } = useWebSocket(user ? user.id : null);

  useEffect(() => {
    if (latestNotification) {
      const timer = setTimeout(() => {
        clearLatest();
      }, 7000);
      return () => clearTimeout(timer);
    }
  }, [latestNotification]);

  useEffect(() => {
    if (apiClient.getToken()) {
      apiClient
        .getMe()
        .then((profile: UserProfile) => setUser(profile))
        .catch(() => apiClient.logout());
    }
  }, []);

  const handleLogout = () => {
    apiClient.logout();
    setUser(null);
    if (activeTab === 'reviewer' || activeTab === 'admin') {
      setActiveTab('dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-amber-500 selection:text-slate-950">
      <Header
        user={user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLoginClick={() => setIsLoginModalOpen(true)}
        onLogoutClick={handleLogout}
      />

      <main className="flex-1">
        {activeTab === 'dashboard' && (
          <DashboardPage
            user={user}
            onNavigate={(tab) => setActiveTab(tab)}
            onLoginClick={() => setIsLoginModalOpen(true)}
          />
        )}
        {activeTab === 'submit' && <ContributionForm onSuccess={() => setActiveTab('history')} />}
        {activeTab === 'history' && <ContributionHistory />}
        {activeTab === 'reviewer' && <ReviewerQueue />}
        {activeTab === 'admin' && <AdminPanel currentUser={user} />}
      </main>

      <Footer />

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onSuccess={(profile) => {
          setUser(profile);
          setActiveTab('dashboard');
        }}
      />

      {/* Real-time WebSocket Notification Toast (Deliverable 5) */}
      {latestNotification && (
        <div className="fixed bottom-6 right-6 z-50 max-w-sm w-full bg-slate-900 border border-amber-500/40 rounded-2xl p-4 shadow-2xl flex items-start gap-3 animate-fade-in">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center shrink-0">
            <Bell className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-bold text-white flex items-center justify-between">
              <span>اعلان زنده پلتفرم</span>
              <button
                onClick={clearLatest}
                className="text-slate-400 hover:text-white p-0.5 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              {latestNotification.message}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
