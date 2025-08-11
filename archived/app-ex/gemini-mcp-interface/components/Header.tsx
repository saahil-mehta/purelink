
import React from 'react';
import { FontFamily } from '../types';

interface HeaderProps {
  currentFont: FontFamily;
  onFontChange: (font: FontFamily) => void;
}

const fontOptions = [
  { id: FontFamily.INTER, name: 'Inter' },
  { id: FontFamily.MANROPE, name: 'Manrope' },
];

const Header: React.FC<HeaderProps> = ({ currentFont, onFontChange }) => {
  return (
    <header className="flex items-center justify-between p-4 border-b border-cyan-400/20 bg-gray-900/50 backdrop-blur-sm">
      <h1 className="text-xl font-bold tracking-widest text-cyan-300 uppercase">
        MCP // Agent Interface
      </h1>
      <div className="flex items-center space-x-4">
        <span className="text-sm text-gray-400 uppercase">System Font</span>
        <div className="flex rounded-md bg-gray-800 p-1">
          {fontOptions.map((font) => (
            <button
              key={font.id}
              onClick={() => onFontChange(font.id)}
              className={`px-3 py-1 text-sm rounded ${
                currentFont === font.id
                  ? 'bg-cyan-500 text-white shadow-md'
                  : 'text-gray-300 hover:bg-gray-700'
              } transition-all duration-200`}
            >
              {font.name}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};

export default Header;
