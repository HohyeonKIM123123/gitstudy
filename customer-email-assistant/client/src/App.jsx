import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import EmailDetail from './pages/EmailDetail';
import PensionInfo from './pages/PensionInfo';
import ResponseSettings from './pages/ResponseSettings';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/email/:id" element={<EmailDetail />} />
        <Route path="/pension-info" element={<PensionInfo />} />
        <Route path="/response-settings" element={<ResponseSettings />} />
      </Routes>
    </Layout>
  );
}

export default App;