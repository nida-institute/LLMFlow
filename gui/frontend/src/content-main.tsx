import React from 'react';
import ReactDOM from 'react-dom/client';
import ContentApp from './components/ContentApp';
import { Project } from './types';
import './index.css';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Failed to find the root element');

// Get project from global context or URL parameter
const getProjectFromContext = (): Project => {
  // This would be populated by the backend
  return (window as any).__PROJECT__ || { name: 'Unknown', path: '' };
};

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <ContentApp project={getProjectFromContext()} />
  </React.StrictMode>,
);
