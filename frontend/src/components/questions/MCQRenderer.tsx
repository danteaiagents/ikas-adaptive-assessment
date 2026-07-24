import React from 'react';
import { QuestionOption } from '../../types';

interface MCQRendererProps {
  options: QuestionOption[];
  selectedOptions: string[];
  onChange: (selectedIds: string[]) => void;
}

const MCQRenderer: React.FC<MCQRendererProps> = ({ options, selectedOptions, onChange }) => {
  const toggleOption = (id: string) => {
    if (selectedOptions.includes(id)) {
      onChange(selectedOptions.filter(opt => opt !== id));
    } else {
      onChange([...selectedOptions, id]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
      {options.map(option => {
        const isSelected = selectedOptions.includes(option.id);
        return (
          <label 
            key={option.id} 
            className={`checkbox-container ${isSelected ? 'selected' : ''}`}
          >
            <input 
              type="checkbox" 
              checked={isSelected} 
              onChange={() => toggleOption(option.id)} 
            />
            <span style={{ fontSize: '1rem', lineHeight: 1.5, paddingTop: '2px', color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
              {option.text}
            </span>
          </label>
        );
      })}
    </div>
  );
};

export default MCQRenderer;
