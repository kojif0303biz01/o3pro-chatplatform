import React from 'react';
import Header from './Header';

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children, title }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header title={title} />
      <main className="chat-container overflow-hidden">
        {children}
      </main>
    </div>
  );
};

export default MainLayout;