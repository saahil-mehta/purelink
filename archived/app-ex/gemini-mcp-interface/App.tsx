
import React, { useState, useCallback } from 'react';
import { AppStatus, FontFamily } from './types';
import { runQuery } from './services/geminiService';
import Header from './components/Header';
import StatusPanel from './components/StatusPanel';
import InputArea from './components/InputArea';
import OutputDisplay from './components/OutputDisplay';

const App: React.FC = () => {
  const [prompt, setPrompt] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [status, setStatus] = useState<AppStatus>(AppStatus.IDLE);
  const [font, setFont] = useState<FontFamily>(FontFamily.INTER);

  const fontClassMap = {
    [FontFamily.INTER]: 'font-inter',
    [FontFamily.MANROPE]: 'font-manrope',
  };

  const handleFontChange = (newFont: FontFamily) => {
    setFont(newFont);
  };

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setStatus(AppStatus.PROCESSING);
    setResponse('');

    const result = await runQuery(prompt);

    setResponse(result);
    if (result.startsWith(">>> SYSTEM ALERT:") || result.startsWith(">>> ERROR:")) {
        setStatus(AppStatus.ERROR);
    } else {
        setStatus(AppStatus.SUCCESS);
    }
    setPrompt(''); // Clear input field after submission
  }, [prompt]);

  return (
    <div className={`h-screen w-full bg-gray-900 text-white flex flex-col ${fontClassMap[font]}`}>
      <div className="m-4 border-2 border-cyan-400/30 rounded-lg shadow-[0_0_20px_rgba(45,212,191,0.1)] flex flex-col flex-grow bg-gray-900/30 overflow-hidden">
        <Header currentFont={font} onFontChange={handleFontChange} />
        <StatusPanel status={status} />
        <main className="flex flex-col flex-grow">
          <OutputDisplay response={response} status={status} />
          <div className="border-t border-cyan-400/20">
            <InputArea
              prompt={prompt}
              setPrompt={setPrompt}
              onSubmit={handleSubmit}
              isLoading={status === AppStatus.PROCESSING}
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
