import React from 'react';
import type { ChatMode } from './ChatContainer';

interface ModeSelectorProps {
  currentMode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
  disabled: boolean;
}

const modes = [
  { mode: 'reasoning' as const, label: 'Reasoning', description: '基本推論モード' },
  { mode: 'streaming' as const, label: 'Streaming', description: 'リアルタイム応答' },
  { mode: 'background' as const, label: 'Background', description: 'バックグラウンド処理' },
];

const efforts = [
  { effort: 'low' as const, label: 'Low', description: '高速' },
  { effort: 'medium' as const, label: 'Medium', description: 'バランス' },
  { effort: 'high' as const, label: 'High', description: '高精度' },
];

const ModeSelector: React.FC<ModeSelectorProps> = ({ 
  currentMode, 
  onModeChange, 
  disabled 
}) => {
  const handleModeChange = (mode: ChatMode['mode']) => {
    onModeChange({ ...currentMode, mode });
  };

  const handleEffortChange = (effort: ChatMode['effort']) => {
    onModeChange({ ...currentMode, effort });
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* モード選択 */}
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium text-gray-700">モード:</label>
        <div className="flex space-x-1">
          {modes.map(({ mode, label, description }) => (
            <button
              key={mode}
              onClick={() => handleModeChange(mode)}
              disabled={disabled}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                currentMode.mode === mode
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={description}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Effort選択 */}
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium text-gray-700">精度:</label>
        <div className="flex space-x-1">
          {efforts.map(({ effort, label, description }) => (
            <button
              key={effort}
              onClick={() => handleEffortChange(effort)}
              disabled={disabled}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                currentMode.effort === effort
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={description}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* 現在の設定表示 */}
      <div className="text-xs text-gray-500">
        {currentMode.mode}/{currentMode.effort}
      </div>
    </div>
  );
};

export default ModeSelector;