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
import { Bell, X } from 'lucide-react';

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'submit' | 'history' | 'reviewer' | 'admin'>('dashboard');
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  // Real-time WebSocket connection
  const { latestNotification, clearLatest } = useWebSocket(user ? user.id : null);

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
    <div className="min-h-screen bg-[#030712] text-slate-100 flex flex-col font-sans selection:bg-[#00e5ff] selection:text-[#030712] relative overflow-x-hidden">
      {/* 1. Global Fixed Checkered / Cyber Mesh Grid — seamlessly covers entire screen during all scrolling */}
      <div className="fixed inset-0 bg-knowledge-grid pointer-events-none z-0" aria-hidden="true" />

      {/* 2. Global Fixed Knowledge Graph Visual on Left — stays locked in viewport & accompanies scroll down */}
      <div
        aria-hidden="true"
        className="fixed top-0 left-0 w-[540px] sm:w-[720px] lg:w-[920px] xl:w-[1040px] h-screen pointer-events-none z-0 select-none overflow-hidden opacity-90 transition-opacity duration-700"
        style={{
          maskImage: 'linear-gradient(to right, black 50%, rgba(0,0,0,0.5) 75%, transparent 100%)',
          WebkitMaskImage: 'linear-gradient(to right, black 50%, rgba(0,0,0,0.5) 75%, transparent 100%)',
        }}
      >
        {/* Ambient glowing radial cyan spots */}
        <div className="absolute top-1/4 -left-20 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-[#00e5ff]/20 via-[#0284c7]/15 to-transparent blur-[120px]" />
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 rounded-full bg-[#00e5ff]/10 blur-[100px]" />

        <img
          src="/knowledge-graph.webp"
          alt="MAHOUNN Legal Knowledge Graph"
          className="w-full h-full object-cover object-left filter contrast-115 brightness-105"
        />
      </div>

      <Header
        user={user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLoginClick={() => setIsLoginModalOpen(true)}
        onLogoutClick={handleLogout}
      />

      <main className="flex-1 relative z-10">
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

      {/* Real-time WebSocket Notification Toast */}
      {latestNotification && (
        <div className="fixed bottom-6 right-6 z-50 max-w-sm w-full bg-[#071527] border border-[#00e5ff]/40 rounded-2xl p-4 shadow-2xl shadow-[#00e5ff]/10 flex items-start gap-3 animate-fade-in">
          <div className="w-8 h-8 rounded-lg bg-[#0b1e36] text-[#00e5ff] border border-[#00e5ff]/30 flex items-center justify-center shrink-0">
            <Bell className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-bold text-white flex items-center justify-between">
              <span>اعلان زنده پلتفرم</span>
              <button
                onClick={clearLatest}
                className="text-slate-400 hover:text-white p-0.5 rounded hover:bg-[#0b1e36]"
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
