
import React from 'react';
import SendIcon from './icons/SendIcon';
import ProcessingIcon from './icons/ProcessingIcon';

interface InputAreaProps {
  prompt: string;
  setPrompt: (prompt: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
}

const InputArea: React.FC<InputAreaProps> = ({ prompt, setPrompt, onSubmit, isLoading }) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading) {
        onSubmit(e);
      }
    }
  };

  return (
    <form onSubmit={onSubmit} className="p-4">
      <div className="relative">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter your command..."
          rows={3}
          disabled={isLoading}
          className="w-full bg-gray-800/50 border-2 border-gray-700 rounded-lg p-4 pr-16 text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all duration-200 resize-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="absolute top-1/2 right-4 -translate-y-1/2 p-2 rounded-full bg-cyan-500 text-white disabled:bg-gray-600 hover:bg-cyan-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-cyan-500 transition-all duration-200"
          aria-label="Submit prompt"
        >
          {isLoading ? (
            <ProcessingIcon className="w-6 h-6" />
          ) : (
            <SendIcon className="w-6 h-6" />
          )}
        </button>
      </div>
    </form>
  );
};

export default InputArea;
