import React from 'react';

interface HeaderProps {
  title?: string;
}

const Header: React.FC<HeaderProps> = ({ title = 'O3-Pro Chat Platform' }) => {
  return (
    <header className="bg-slate-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold">
                {title}
              </h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-300">
              POC Version
            </span>
            <div className="w-2 h-2 bg-green-400 rounded-full" title="Connected"></div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;