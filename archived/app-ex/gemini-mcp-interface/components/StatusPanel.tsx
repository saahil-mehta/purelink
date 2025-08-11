
import React, { useState, useEffect } from 'react';
import { AppStatus } from '../types';

interface StatusPanelProps {
  status: AppStatus;
}

const StatusIndicator: React.FC<{ status: AppStatus }> = ({ status }) => {
  const statusConfig = {
    [AppStatus.IDLE]: { text: 'Online', color: 'text-green-400', pulseColor: 'bg-green-400' },
    [AppStatus.SUCCESS]: { text: 'Online', color: 'text-green-400', pulseColor: 'bg-green-400' },
    [AppStatus.PROCESSING]: { text: 'Processing', color: 'text-yellow-400', pulseColor: 'bg-yellow-400' },
    [AppStatus.ERROR]: { text: 'System Error', color: 'text-red-500', pulseColor: 'bg-red-500' },
  };

  const { text, color, pulseColor } = statusConfig[status];

  return (
    <div className="flex items-center space-x-2">
      <span className={`relative flex h-3 w-3`}>
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${pulseColor} opacity-75`}></span>
        <span className={`relative inline-flex rounded-full h-3 w-3 ${pulseColor}`}></span>
      </span>
      <span className={`${color} font-mono uppercase text-sm`}>{text}</span>
    </div>
  );
};


const StatusPanel: React.FC<StatusPanelProps> = ({ status }) => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timerId = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timerId);
  }, []);

  return (
    <div className="flex items-center justify-between p-3 bg-gray-800/60 border-y border-cyan-400/10 text-gray-400">
      <div className="flex items-center space-x-4">
        <span className="font-mono text-sm">AGENT STATUS:</span>
        <StatusIndicator status={status} />
      </div>
      <div className="font-mono text-sm">
        SYS_TIME: {time.toLocaleTimeString()}
      </div>
    </div>
  );
};

export default StatusPanel;
