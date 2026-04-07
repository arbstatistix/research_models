import React from 'react';
import './index.css';

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
}

export const Container: React.FC<ContainerProps> = ({ children, className = '' }) => {
  return <div className={`container ${className}`}>{children}</div>;
};
