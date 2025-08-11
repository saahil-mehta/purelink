
import React, { useState, useEffect } from 'react';
import { AppStatus } from '../types';

interface OutputDisplayProps {
  response: string;
  status: AppStatus;
}

const Typewriter: React.FC<{ text: string }> = ({ text }) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    setDisplayedText(''); // Reset on new text
    if (text) {
      let i = 0;
      const intervalId = setInterval(() => {
        setDisplayedText(text.substring(0, i + 1));
        i++;
        if (i >= text.length) {
          clearInterval(intervalId);
        }
      }, 20); // Adjust speed of typing here
      return () => clearInterval(intervalId);
    }
  }, [text]);

  return <p className="whitespace-pre-wrap">{displayedText}<span className="inline-block w-2 h-5 bg-cyan-400 animate-pulse ml-1"></span></p>;
};

const OutputDisplay: React.FC<OutputDisplayProps> = ({ response, status }) => {
  const isError = status === AppStatus.ERROR;

  return (
    <div className="flex-grow p-6 overflow-y-auto">
      <div
        className={`w-full min-h-[200px] p-4 rounded-lg bg-black/20 font-mono text-base ${
          isError ? 'text-red-400' : 'text-gray-200'
        }`}
      >
        {status === AppStatus.PROCESSING && !response && (
            <div className="flex items-center space-x-2 text-gray-400">
                <span>Awaiting response from Oracle...</span>
            </div>
        )}
        {response && (status === AppStatus.SUCCESS || status === AppStatus.ERROR) && (
            <Typewriter text={response} />
        )}
        {status === AppStatus.IDLE && (
            <p className="text-gray-500">
                {`>>> Standby mode. The system is awaiting your query.`}
            </p>
        )}
      </div>
    </div>
  );
};

export default OutputDisplay;
