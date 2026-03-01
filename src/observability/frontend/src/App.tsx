import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppLayout } from '@cloudscape-design/components';
import Dashboard from './pages/Dashboard';
import TraceView from './pages/TraceView';

function App() {
  return (
    <Router>
      <AppLayout
        navigationHide
        toolsHide
        content={
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/trace/:traceId" element={<TraceView />} />
          </Routes>
        }
      />
    </Router>
  );
}

export default App;
