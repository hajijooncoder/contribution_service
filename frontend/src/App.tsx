import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { ContributionForm } from './components/ContributionForm';
import { ContributionHistory } from './components/ContributionHistory';
import { ReviewerQueue } from './components/ReviewerQueue';
import { LoginModal } from './components/LoginModal';
import { apiClient } from './api/client';
import { UserProfile } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState<'submit' | 'history' | 'reviewer'>('submit');
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

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
    if (activeTab === 'reviewer') {
      setActiveTab('submit');
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
        {activeTab === 'submit' && <ContributionForm onSuccess={() => setActiveTab('history')} />}
        {activeTab === 'history' && <ContributionHistory />}
        {activeTab === 'reviewer' && <ReviewerQueue />}
      </main>

      <Footer />

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onSuccess={(profile) => setUser(profile)}
      />
    </div>
  );
};

export default App;
