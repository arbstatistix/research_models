import BloombergQuantTerminal from './components/BloombergQuantTerminal';
import { PIDManager } from './components/PIDManager';
import './index.css';

function App() {
  return (
    <>
      <BloombergQuantTerminal />
      <PIDManager />
    </>
  );
}

export default App;
